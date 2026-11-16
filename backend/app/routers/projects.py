import shutil
import uuid
from pathlib import Path
from typing import List, Optional
from pydantic import BaseModel
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from sqlmodel import Session, select
from app.database import get_session
from app.models.project import Project, ProjectRead, get_utc_now
from app.models.subtitle import SubtitleSegment
from app.services.audio_extractor import extract_video_metadata
from app.config import UPLOAD_DIR, STORAGE_DIR

router = APIRouter(prefix="/api/projects", tags=["projects"])

SUPPORTED_EXTENSIONS = {".mp4", ".mov", ".mkv", ".webm", ".avi"}

class RegisterLocalRequest(BaseModel):
    file_path: str
    name: Optional[str] = None

@router.post("/register-local", response_model=ProjectRead)
def register_local_video(
    req: RegisterLocalRequest,
    session: Session = Depends(get_session)
):
    path = Path(req.file_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail="File video tidak ditemukan di path lokal")

    ext = path.suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Format file '{ext}' tidak didukung. Harap pilih MP4, MOV, MKV, atau WebM."
        )

    meta = extract_video_metadata(str(path))

    project = Project(
        name=req.name or path.stem,
        original_filename=path.name,
        video_path=str(path.resolve()),
        duration=meta.get("duration", 0.0),
        width=meta.get("width", 0),
        height=meta.get("height", 0),
        fps=meta.get("fps", 30.0),
        status="draft",
        created_at=get_utc_now(),
        updated_at=get_utc_now()
    )
    session.add(project)
    session.commit()
    session.refresh(project)
    return project

@router.post("/upload", response_model=ProjectRead)
async def upload_video(
    file: UploadFile = File(...),
    name: str = Form(None),
    session: Session = Depends(get_session)
):
    ext = Path(file.filename).suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Format file '{ext}' tidak didukung. Harap upload MP4, MOV, MKV, atau WebM."
        )

    # Save to disk with unique filename to prevent collisions
    safe_name = f"{uuid.uuid4().hex[:10]}_{file.filename}"
    saved_path = UPLOAD_DIR / safe_name

    with open(saved_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Extract metadata using FFprobe / FFmpeg
    meta = extract_video_metadata(str(saved_path))

    project = Project(
        name=name or Path(file.filename).stem,
        original_filename=file.filename,
        video_path=str(saved_path),
        duration=meta.get("duration", 0.0),
        width=meta.get("width", 0),
        height=meta.get("height", 0),
        fps=meta.get("fps", 30.0),
        status="draft",
        created_at=get_utc_now(),
        updated_at=get_utc_now()
    )
    session.add(project)
    session.commit()
    session.refresh(project)
    return project

@router.get("", response_model=List[ProjectRead])
def list_projects(session: Session = Depends(get_session)):
    projects = session.exec(select(Project).order_by(Project.created_at.desc())).all()
    return projects

@router.get("/{project_id}", response_model=ProjectRead)
def get_project(project_id: int, session: Session = Depends(get_session)):
    project = session.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project tidak ditemukan")
    return project

@router.delete("/{project_id}")
def delete_project(project_id: int, session: Session = Depends(get_session)):
    project = session.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project tidak ditemukan")

    # Delete video file if exists
    try:
        video_path = Path(project.video_path)
        if video_path.exists():
            video_path.unlink()
    except Exception as e:
        print(f"Failed to delete video file: {e}")

    # Delete temp audio or exports if exists
    try:
        temp_wav = STORAGE_DIR / "temp_audio" / f"project_{project_id}.wav"
        if temp_wav.exists():
            temp_wav.unlink()
        temp_ass = STORAGE_DIR / "exports" / f"project_{project_id}.ass"
        if temp_ass.exists():
            temp_ass.unlink()
    except Exception as e:
        print(f"Failed to delete temp files: {e}")

    # Delete all subtitles associated with this project
    subs = session.exec(select(SubtitleSegment).where(SubtitleSegment.project_id == project_id)).all()
    for s in subs:
        session.delete(s)

    session.delete(project)
    session.commit()
    return {"message": "Project berhasil dihapus"}

