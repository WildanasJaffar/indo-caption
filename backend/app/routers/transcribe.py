import asyncio
import json
import logging
from concurrent.futures import ThreadPoolExecutor
from typing import Dict
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sse_starlette.sse import EventSourceResponse
from sqlmodel import Session, select
from app.database import get_session, engine
from app.models.project import Project
from app.models.subtitle import SubtitleSegment
from app.config import TEMP_AUDIO_DIR
from app.services.audio_extractor import extract_audio_wav
from app.services.whisper_engine import get_device_info, transcribe_with_progress

router = APIRouter(prefix="/api/transcribe", tags=["transcribe"])
logger = logging.getLogger(__name__)

executor = ThreadPoolExecutor(max_workers=2)

# In-memory progress event queues for SSE keyed by project_id
project_event_queues: Dict[int, asyncio.Queue] = {}

def get_or_create_queue(project_id: int) -> asyncio.Queue:
    if project_id not in project_event_queues:
        project_event_queues[project_id] = asyncio.Queue()
    return project_event_queues[project_id]

@router.get("/hardware")
def check_hardware():
    return get_device_info()

def run_transcription_worker(
    project_id: int,
    video_path: str,
    duration: float,
    model_size: str,
    language: str,
    loop: asyncio.AbstractEventLoop
):
    queue = get_or_create_queue(project_id)

    def dispatch_event(data: dict):
        loop.call_soon_threadsafe(queue.put_nowait, data)

    try:
        dispatch_event({"status": "extracting_audio", "progress": 5.0, "message": "Mengekstrak audio dari video..."})
        
        # 1. Extract audio to 16kHz WAV
        temp_wav = TEMP_AUDIO_DIR / f"project_{project_id}.wav"
        extract_audio_wav(video_path, str(temp_wav))
        
        dispatch_event({"status": "loading_model", "progress": 10.0, "message": f"Menyiapkan model AI ({model_size})..."})

        # 2. Transcribe with Faster-Whisper
        def on_segment(evt: dict):
            if evt.get("status") == "downloading_model":
                dl_pct = evt.get("download_pct", 0.0)
                mapped_pct = round(10.0 + (dl_pct * 0.25), 1) # 10% -> 35%
                dispatch_event({
                    "status": "downloading_model",
                    "progress": mapped_pct,
                    "message": evt.get("message", f"Mengunduh model {model_size}...")
                })
                return

            # Scale transcription progress between 35% and 95%
            mapped_pct = round(35.0 + (evt.get("progress", 0.0) * 0.6), 1)
            dispatch_event({
                "status": "transcribing",
                "progress": mapped_pct,
                "current_segment": evt.get("current_segment"),
                "detected_language": evt.get("detected_language")
            })

        segments = transcribe_with_progress(
            audio_path=str(temp_wav),
            language=language,
            model_size=model_size,
            total_duration=duration,
            progress_callback=on_segment
        )

        # Automatically re-segment into punchy lines (max 4 words / 26 chars)
        from app.services.subtitle_formatter import resegment_by_words_or_chars
        segments = resegment_by_words_or_chars(segments, max_words=4, max_chars=26)

        dispatch_event({"status": "saving", "progress": 98.0, "message": "Menyimpan hasil ke database..."})

        # 3. Save segments to SQLite
        with Session(engine) as session:
            # Delete any previous subtitles for this project
            old_subs = session.exec(select(SubtitleSegment).where(SubtitleSegment.project_id == project_id)).all()
            for s in old_subs:
                session.delete(s)

            for seg in segments:
                new_sub = SubtitleSegment(
                    project_id=project_id,
                    sequence=seg["sequence"],
                    start_time=seg["start"],
                    end_time=seg["end"],
                    text=seg["text"]
                )
                new_sub.set_words(seg.get("words", []))
                session.add(new_sub)

            # Update project status
            proj = session.get(Project, project_id)
            if proj:
                proj.status = "ready"
                session.add(proj)

            session.commit()

        dispatch_event({
            "status": "completed",
            "progress": 100.0,
            "message": "Transkripsi selesai!",
            "total_segments": len(segments)
        })

    except Exception as e:
        logger.exception("Transcription failed:")
        with Session(engine) as session:
            proj = session.get(Project, project_id)
            if proj:
                proj.status = "error"
                session.add(proj)
                session.commit()

        dispatch_event({
            "status": "error",
            "progress": 0.0,
            "message": f"Transkripsi gagal: {str(e)}"
        })

@router.post("/{project_id}")
async def start_transcription(
    project_id: int,
    model_size: str = "small",
    language: str = "id",
    session: Session = Depends(get_session)
):
    project = session.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project tidak ditemukan")

    project.status = "transcribing"
    session.add(project)
    session.commit()

    loop = asyncio.get_event_loop()
    executor.submit(
        run_transcription_worker,
        project_id,
        project.video_path,
        project.duration,
        model_size,
        language,
        loop
    )

    return {"message": "Transkripsi dimulai", "project_id": project_id, "status": "transcribing"}

@router.get("/events/{project_id}")
async def stream_transcription_events(project_id: int):
    queue = get_or_create_queue(project_id)

    async def event_generator():
        while True:
            try:
                # Wait for next event
                data = await queue.get()
                yield {
                    "event": "progress",
                    "data": json.dumps(data, ensure_ascii=False)
                }
                if data.get("status") in ["completed", "error"]:
                    break
            except asyncio.CancelledError:
                break

    return EventSourceResponse(event_generator())

