import os
import sys
import shutil
import subprocess
from pathlib import Path

_cached_ffmpeg_path = None

def get_ffmpeg_path() -> str:
    global _cached_ffmpeg_path
    if _cached_ffmpeg_path and Path(_cached_ffmpeg_path).exists():
        return _cached_ffmpeg_path

    # 0. Check bundled bin directory
    candidates = []
    if getattr(sys, "frozen", False):
        exe_dir = Path(sys.executable).resolve().parent
        candidates.extend([
            exe_dir / "bin" / "ffmpeg.exe",
            exe_dir / "ffmpeg.exe"
        ])
        if hasattr(sys, "_MEIPASS"):
            meipass = Path(sys._MEIPASS)
            candidates.extend([
                meipass / "bin" / "ffmpeg.exe",
                meipass / "ffmpeg.exe"
            ])

    base_dir = Path(__file__).resolve().parent.parent.parent.parent
    candidates.extend([
        base_dir / "bin" / "ffmpeg.exe",
        base_dir / "ffmpeg.exe"
    ])

    for cand in candidates:
        if cand.exists():
            _cached_ffmpeg_path = str(cand)
            return _cached_ffmpeg_path

    # 1. Check system PATH
    ffmpeg_system = shutil.which("ffmpeg")
    if ffmpeg_system:
        _cached_ffmpeg_path = ffmpeg_system
        return _cached_ffmpeg_path

    # 2. Check winget install location on Windows
    local_app_data = os.environ.get("LOCALAPPDATA", "")
    if local_app_data:
        winget_links = Path(local_app_data) / "Microsoft" / "WinGet" / "Links" / "ffmpeg.exe"
        if winget_links.exists():
            _cached_ffmpeg_path = str(winget_links)
            return _cached_ffmpeg_path

    # 3. Check imageio_ffmpeg fallback
    try:
        import imageio_ffmpeg
        exe = imageio_ffmpeg.get_ffmpeg_exe()
        if exe and Path(exe).exists():
            _cached_ffmpeg_path = exe
            return _cached_ffmpeg_path
    except Exception:
        pass

    raise RuntimeError("FFmpeg executable not found. Please ensure FFmpeg is installed.")

def check_ffmpeg_available() -> dict:
    try:
        path = get_ffmpeg_path()
        result = subprocess.run([path, "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        version_line = result.stdout.splitlines()[0] if result.stdout else "Unknown version"
        return {"available": True, "path": path, "version": version_line}
    except Exception as e:
        return {"available": False, "error": str(e)}

