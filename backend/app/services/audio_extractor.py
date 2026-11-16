import os
import json
import subprocess
from pathlib import Path
from app.utils.ffmpeg_check import get_ffmpeg_path

def get_ffprobe_path() -> str:
    ffmpeg_exe = get_ffmpeg_path()
    ffprobe_candidate = Path(ffmpeg_exe).parent / "ffprobe.exe"
    if ffprobe_candidate.exists():
        return str(ffprobe_candidate)
    return "ffprobe"

def extract_video_metadata(video_path: str) -> dict:
    """
    Extracts video duration, width, height, and fps using ffprobe or ffmpeg.
    """
    ffprobe_cmd = get_ffprobe_path()
    cmd = [
        ffprobe_cmd,
        "-v", "quiet",
        "-print_format", "json",
        "-show_format",
        "-show_streams",
        video_path
    ]
    try:
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        data = json.loads(result.stdout)
        
        duration = float(data.get("format", {}).get("duration", 0.0))
        width = 0
        height = 0
        fps = 30.0

        for stream in data.get("streams", []):
            if stream.get("codec_type") == "video":
                width = int(stream.get("width", 0))
                height = int(stream.get("height", 0))
                
                # Parse FPS e.g. "30/1" or "60000/1001"
                r_frame_rate = stream.get("r_frame_rate", "30/1")
                if "/" in r_frame_rate:
                    num, den = r_frame_rate.split("/")
                    fps = float(num) / float(den) if float(den) != 0 else 30.0
                else:
                    fps = float(r_frame_rate)
                break
                
        return {
            "duration": round(duration, 3),
            "width": width,
            "height": height,
            "fps": round(fps, 2)
        }
    except Exception as e:
        # Fallback with standard defaults
        print(f"Metadata extraction warning: {e}")
        return {"duration": 0.0, "width": 1920, "height": 1080, "fps": 30.0}

def extract_audio_wav(video_path: str, output_wav_path: str) -> str:
    """
    Extracts audio to 16kHz mono WAV optimized for Faster-Whisper.
    """
    ffmpeg_exe = get_ffmpeg_path()
    cmd = [
        ffmpeg_exe,
        "-y",               # Overwrite if exists
        "-i", video_path,   # Input
        "-vn",              # Disable video
        "-acodec", "pcm_s16le", # 16-bit PCM
        "-ar", "16000",     # 16kHz sampling rate
        "-ac", "1",         # Mono 1 channel
        output_wav_path
    ]
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg audio extraction failed: {result.stderr}")
    return output_wav_path

