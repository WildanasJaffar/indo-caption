import re
import os
import subprocess
from pathlib import Path
from typing import Optional, Callable, Dict, Any
from app.utils.ffmpeg_check import get_ffmpeg_path
from app.config import EXPORT_DIR

def escape_ffmpeg_filter_path(file_path: str) -> str:
    """
    Escapes a Windows path for FFmpeg filter arguments (e.g. ass=...).
    FFmpeg filter graph requires escaping backslashes and colons.
    Example: D:\foo\bar.ass -> D\\:/foo/bar.ass
    """
    path_str = Path(file_path).resolve().as_posix()
    # If drive letter like D:/path, escape the colon: D\:/path
    if re.match(r"^[a-zA-Z]:", path_str):
        path_str = path_str[0] + "\\:" + path_str[2:]
    return path_str

def render_hardcoded_video(
    video_path: str,
    ass_path: str,
    output_filename: str,
    total_duration: float = 0.0,
    progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None
) -> str:
    """
    Renders video with hardcoded subtitles using FFmpeg libass filter.
    Parses stderr in real time to report percentage progress.
    """
    ffmpeg_exe = get_ffmpeg_path()
    output_path = EXPORT_DIR / output_filename
    
    escaped_ass = escape_ffmpeg_filter_path(ass_path)
    filter_arg = f"ass='{escaped_ass}'"

    cmd = [
        ffmpeg_exe,
        "-y",
        "-i", video_path,
        "-vf", filter_arg,
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "22",
        "-c:a", "copy",
        str(output_path)
    ]

    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
        encoding="utf-8",
        errors="replace"
    )

    time_pattern = re.compile(r"time=(\d{2}):(\d{2}):(\d{2}\.\d+)")

    # Read stderr line-by-line
    for line in iter(process.stderr.readline, ""):
        match = time_pattern.search(line)
        if match and total_duration > 0:
            h, m, s = match.groups()
            current_seconds = int(h) * 3600 + int(m) * 60 + float(s)
            pct = min(99.0, round((current_seconds / total_duration) * 100, 1))
            if progress_callback:
                progress_callback({
                    "status": "rendering",
                    "progress": pct,
                    "current_time": current_seconds
                })

    process.wait()
    if process.returncode != 0:
        raise RuntimeError(f"FFmpeg render failed with exit code {process.returncode}")

    if progress_callback:
        progress_callback({"status": "completed", "progress": 100.0, "output_path": str(output_path)})

    return str(output_path)

