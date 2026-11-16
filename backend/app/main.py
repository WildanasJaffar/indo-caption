import os
import sys
from pathlib import Path
from functools import wraps
from contextlib import asynccontextmanager

# Silence Windows asyncio WinError 10054 (ConnectionResetError when video scrubber/browser disconnects)
if sys.platform == "win32":
    try:
        from asyncio.proactor_events import _ProactorBasePipeTransport
        _orig_call_connection_lost = _ProactorBasePipeTransport._call_connection_lost

        @wraps(_orig_call_connection_lost)
        def _silent_call_connection_lost(self, exc):
            try:
                _orig_call_connection_lost(self, exc)
            except (ConnectionResetError, OSError):
                pass

        _ProactorBasePipeTransport._call_connection_lost = _silent_call_connection_lost
    except Exception:
        pass

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from app.database import init_db, engine
from sqlmodel import Session
from app.models.project import Project
from app.config import UPLOAD_DIR, BASE_DIR
from app.routers import projects, transcribe, subtitles, export
from app.utils.ffmpeg_check import check_ffmpeg_available
from fastapi.staticfiles import StaticFiles

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize SQLite DB
    init_db()
    ffmpeg_status = check_ffmpeg_available()
    print(f"[*] IndoCaption Backend Started. FFmpeg status: {ffmpeg_status}")
    yield

app = FastAPI(
    title="IndoCaption Backend API",
    version="1.0.0",
    description="Local AI Auto Caption Editor for Indonesian Video Content",
    lifespan=lifespan
)

# CORS configuration for local Vue 3 frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(projects.router)
app.include_router(transcribe.router)
app.include_router(subtitles.router)
app.include_router(export.router)

@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "ffmpeg": check_ffmpeg_available()
    }

@app.get("/api/media/project/{project_id}/stream")
def stream_project_video(project_id: int, request: Request):
    """
    Streams project video with HTTP Range support directly from any path
    (both uploaded storage or registered native local path).
    """
    with Session(engine) as session:
        proj = session.get(Project, project_id)
        if not proj:
            raise HTTPException(status_code=404, detail="Project tidak ditemukan")
        file_path = Path(proj.video_path)

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File video tidak ditemukan di sistem")

    file_size = file_path.stat().st_size
    range_header = request.headers.get("range")

    if range_header:
        range_value = range_header.strip().lower().replace("bytes=", "")
        parts = range_value.split("-")
        start = int(parts[0]) if parts[0] else 0
        end = int(parts[1]) if len(parts) > 1 and parts[1] else file_size - 1

        if start >= file_size:
            raise HTTPException(status_code=416, detail="Requested Range Not Satisfiable")

        chunk_size = (end - start) + 1

        def iter_file():
            with open(file_path, "rb") as f:
                f.seek(start)
                bytes_left = chunk_size
                while bytes_left > 0:
                    read_len = min(64 * 1024, bytes_left)
                    data = f.read(read_len)
                    if not data:
                        break
                    bytes_left -= len(data)
                    yield data

        headers = {
            "Content-Range": f"bytes {start}-{end}/{file_size}",
            "Accept-Ranges": "bytes",
            "Content-Length": str(chunk_size),
            "Content-Type": "video/mp4",
        }
        return StreamingResponse(iter_file(), status_code=206, headers=headers)

    def full_file_iter():
        with open(file_path, "rb") as f:
            while chunk := f.read(64 * 1024):
                yield chunk

    headers = {
        "Accept-Ranges": "bytes",
        "Content-Length": str(file_size),
        "Content-Type": "video/mp4"
    }
    return StreamingResponse(full_file_iter(), headers=headers)

@app.get("/api/media/stream/{filename}")
def stream_video(filename: str, request: Request):
    """
    Streams local video files with HTTP Range header support
    enabling smooth video scrubbing in the HTML5 video player.
    """
    file_path = UPLOAD_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File video tidak ditemukan")

    file_size = file_path.stat().st_size
    range_header = request.headers.get("range")

    if range_header:
        # Parse range header e.g. "bytes=0-1048575"
        range_value = range_header.strip().lower().replace("bytes=", "")
        parts = range_value.split("-")
        start = int(parts[0]) if parts[0] else 0
        end = int(parts[1]) if len(parts) > 1 and parts[1] else file_size - 1

        if start >= file_size:
            raise HTTPException(status_code=416, detail="Requested Range Not Satisfiable")

        chunk_size = (end - start) + 1

        def iter_file():
            with open(file_path, "rb") as f:
                f.seek(start)
                bytes_left = chunk_size
                while bytes_left > 0:
                    read_len = min(64 * 1024, bytes_left)
                    data = f.read(read_len)
                    if not data:
                        break
                    bytes_left -= len(data)
                    yield data

        headers = {
            "Content-Range": f"bytes {start}-{end}/{file_size}",
            "Accept-Ranges": "bytes",
            "Content-Length": str(chunk_size),
            "Content-Type": "video/mp4",
        }
        return StreamingResponse(iter_file(), status_code=206, headers=headers)

    # Standard full response
    def full_file_iter():
        with open(file_path, "rb") as f:
            while chunk := f.read(64 * 1024):
                yield chunk

    headers = {
        "Accept-Ranges": "bytes",
        "Content-Length": str(file_size),
        "Content-Type": "video/mp4"
    }
    return StreamingResponse(full_file_iter(), headers=headers)

# Mount built frontend dist if available for desktop app mode
def find_frontend_dist() -> Path:
    candidates = []
    if getattr(sys, "frozen", False):
        if hasattr(sys, "_MEIPASS"):
            candidates.append(Path(sys._MEIPASS) / "frontend" / "dist")
            candidates.append(Path(sys._MEIPASS) / "dist")
        candidates.append(Path(sys.executable).parent / "frontend" / "dist")
        candidates.append(Path(sys.executable).parent / "dist")
    candidates.append(BASE_DIR / "frontend" / "dist")
    candidates.append(BASE_DIR / "dist")

    for c in candidates:
        if c.exists() and (c / "index.html").exists():
            return c
    return BASE_DIR / "frontend" / "dist"

frontend_dist = find_frontend_dist()
if frontend_dist.exists() and (frontend_dist / "index.html").exists():
    app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="frontend")


