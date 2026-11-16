import asyncio
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor
from fastapi import APIRouter, Depends, HTTPException, Response, BackgroundTasks
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse
from sqlmodel import Session, select
from app.database import get_session
from app.models.project import Project
from app.models.subtitle import SubtitleSegment
from app.config import EXPORT_DIR
from app.services.subtitle_formatter import (
    generate_standard_srt,
    generate_word_level_srt,
    generate_vtt,
    generate_plain_text,
    generate_ass,
    sync_words_with_text
)
from app.services.video_renderer import render_hardcoded_video

router = APIRouter(prefix="/api/export", tags=["export"])
logger = logging.getLogger(__name__)

render_executor = ThreadPoolExecutor(max_workers=1)
render_queues: Dict[int, asyncio.Queue] = {}

def get_render_queue(project_id: int) -> asyncio.Queue:
    if project_id not in render_queues:
        render_queues[project_id] = asyncio.Queue()
    return render_queues[project_id]

class RenderRequest(BaseModel):
    style: Optional[Dict[str, Any]] = None

def get_segments_data(project_id: int, session: Session) -> list:
    subs = session.exec(
        select(SubtitleSegment)
        .where(SubtitleSegment.project_id == project_id)
        .order_by(SubtitleSegment.sequence.asc())
    ).all()
    
    return [
        {
            "sequence": s.sequence,
            "start": s.start_time,
            "end": s.end_time,
            "text": s.text,
            "words": sync_words_with_text(s.text, s.words, s.start_time, s.end_time)
        }
        for s in subs
    ]

@router.get("/{project_id}/srt")
def export_standard_srt(project_id: int, session: Session = Depends(get_session)):
    project = session.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project tidak ditemukan")

    segments = get_segments_data(project_id, session)
    srt_content = generate_standard_srt(segments)

    filename = f"{Path(project.original_filename).stem}_captions.srt"
    return Response(
        content=srt_content,
        media_type="application/x-subrip",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )

@router.get("/{project_id}/srt-words")
def export_word_level_srt(project_id: int, session: Session = Depends(get_session)):
    """
    Export word-level SRT for CapCut. Each word gets its own entry and precise timing.
    """
    project = session.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project tidak ditemukan")

    segments = get_segments_data(project_id, session)
    srt_content = generate_word_level_srt(segments)

    filename = f"{Path(project.original_filename).stem}_word_level.srt"
    return Response(
        content=srt_content,
        media_type="application/x-subrip",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )

@router.get("/{project_id}/vtt")
def export_vtt(project_id: int, session: Session = Depends(get_session)):
    project = session.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project tidak ditemukan")

    segments = get_segments_data(project_id, session)
    vtt_content = generate_vtt(segments)

    filename = f"{Path(project.original_filename).stem}_captions.vtt"
    return Response(
        content=vtt_content,
        media_type="text/vtt",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )

@router.get("/{project_id}/txt")
def export_txt(project_id: int, session: Session = Depends(get_session)):
    project = session.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project tidak ditemukan")

    segments = get_segments_data(project_id, session)
    txt_content = generate_plain_text(segments)

    filename = f"{Path(project.original_filename).stem}_transcript.txt"
    return Response(
        content=txt_content,
        media_type="text/plain; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )

@router.get("/{project_id}/ass")
def export_ass(project_id: int, session: Session = Depends(get_session)):
    project = session.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project tidak ditemukan")

    segments = get_segments_data(project_id, session)
    ass_content = generate_ass(segments, video_width=project.width or 1080, video_height=project.height or 1920)

    filename = f"{Path(project.original_filename).stem}_styled.ass"
    return Response(
        content=ass_content,
        media_type="text/x-ssa",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )

def run_render_worker(
    project_id: int,
    video_path: str,
    ass_path: str,
    output_filename: str,
    duration: float,
    loop: asyncio.AbstractEventLoop
):
    queue = get_render_queue(project_id)

    def dispatch(data: dict):
        loop.call_soon_threadsafe(queue.put_nowait, data)

    try:
        dispatch({"status": "starting", "progress": 5.0, "message": "Menyiapkan render video FFmpeg..."})

        def on_progress(p: dict):
            dispatch(p)

        output_path = render_hardcoded_video(
            video_path=video_path,
            ass_path=ass_path,
            output_filename=output_filename,
            total_duration=duration,
            progress_callback=on_progress
        )

        dispatch({
            "status": "completed",
            "progress": 100.0,
            "message": "Render video selesai!",
            "output_filename": output_filename
        })
    except Exception as e:
        logger.exception("Video render failed:")
        dispatch({"status": "error", "progress": 0.0, "message": f"Render gagal: {str(e)}"})

@router.post("/{project_id}/render-video")
async def start_render_video(
    project_id: int,
    req: RenderRequest,
    session: Session = Depends(get_session)
):
    project = session.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project tidak ditemukan")

    segments = get_segments_data(project_id, session)
    if not segments:
        raise HTTPException(status_code=400, detail="Tidak ada subtitle untuk diburn ke video")

    # Generate ASS file
    ass_content = generate_ass(
        segments,
        style=req.style,
        video_width=project.width or 1080,
        video_height=project.height or 1920
    )
    temp_ass = EXPORT_DIR / f"project_{project_id}.ass"
    with open(temp_ass, "w", encoding="utf-8") as f:
        f.write(ass_content)

    output_filename = f"captioned_{Path(project.original_filename).stem}.mp4"
    loop = asyncio.get_event_loop()

    render_executor.submit(
        run_render_worker,
        project_id,
        project.video_path,
        str(temp_ass),
        output_filename,
        project.duration,
        loop
    )

    return {"message": "Render video dimulai", "project_id": project_id}

@router.get("/render-events/{project_id}")
async def stream_render_events(project_id: int):
    queue = get_render_queue(project_id)

    async def event_generator():
        while True:
            try:
                data = await queue.get()
                yield {
                    "event": "render-progress",
                    "data": json.dumps(data, ensure_ascii=False)
                }
                if data.get("status") in ["completed", "error"]:
                    break
            except asyncio.CancelledError:
                break

    return EventSourceResponse(event_generator())

@router.get("/{project_id}/download-rendered/{filename}")
def download_rendered_video(project_id: int, filename: str):
    file_path = EXPORT_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File video hasil render tidak ditemukan")

    return FileResponse(
        path=str(file_path),
        filename=filename,
        media_type="video/mp4"
    )

