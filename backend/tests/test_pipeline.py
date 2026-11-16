import os
import sys
from pathlib import Path
import subprocess

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from app.utils.ffmpeg_check import get_ffmpeg_path, check_ffmpeg_available
from app.services.audio_extractor import extract_video_metadata, extract_audio_wav
from app.services.subtitle_formatter import (
    generate_standard_srt,
    generate_word_level_srt,
    generate_vtt,
    generate_ass,
    resegment_by_words_or_chars
)

def test_pipeline():
    print("=== 1. Testing FFmpeg ===")
    ff_status = check_ffmpeg_available()
    print("FFmpeg Status:", ff_status)
    assert ff_status["available"], "FFmpeg should be available"

    print("\n=== 2. Creating Synthetic Test Video ===")
    ffmpeg_exe = get_ffmpeg_path()
    test_video = Path("test_video.mp4").resolve()
    # Generate 3-second test video with 440Hz sine wave tone
    cmd = [
        ffmpeg_exe,
        "-y",
        "-f", "lavfi", "-i", "testsrc=duration=3:size=640x360:rate=30",
        "-f", "lavfi", "-i", "sine=frequency=440:duration=3",
        "-c:v", "libx264", "-c:a", "aac",
        "-shortest",
        str(test_video)
    ]
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if res.returncode != 0:
        print("FFmpeg error:", res.stderr)
        raise RuntimeError(f"FFmpeg command failed: {res.stderr}")
    print("Created test video:", test_video, "exists:", test_video.exists())

    print("\n=== 3. Testing Video Metadata Extraction ===")
    meta = extract_video_metadata(str(test_video))
    print("Extracted metadata:", meta)
    assert meta["width"] == 640
    assert meta["height"] == 360
    assert meta["duration"] > 2.5

    print("\n=== 4. Testing Audio WAV Extraction ===")
    test_wav = Path("test_audio.wav").resolve()
    extract_audio_wav(str(test_video), str(test_wav))
    print("Extracted audio WAV:", test_wav, "size:", test_wav.stat().st_size)
    assert test_wav.exists() and test_wav.stat().st_size > 0

    print("\n=== 5. Testing Subtitle Generators & CapCut Formats ===")
    mock_segments = [
        {
            "sequence": 1,
            "start": 0.5,
            "end": 2.8,
            "text": "Halo teman-teman semua selamat datang kembali di channel ini",
            "words": [
                {"word": "Halo", "start": 0.5, "end": 0.8, "probability": 0.99},
                {"word": "teman-teman", "start": 0.85, "end": 1.2, "probability": 0.98},
                {"word": "semua", "start": 1.25, "end": 1.5, "probability": 0.95},
                {"word": "selamat", "start": 1.55, "end": 1.8, "probability": 0.97},
                {"word": "datang", "start": 1.85, "end": 2.1, "probability": 0.96},
                {"word": "kembali", "start": 2.15, "end": 2.4, "probability": 0.99},
                {"word": "di", "start": 2.45, "end": 2.55, "probability": 0.99},
                {"word": "channel", "start": 2.58, "end": 2.7, "probability": 0.94},
                {"word": "ini", "start": 2.72, "end": 2.8, "probability": 0.98},
            ]
        }
    ]

    # Standard SRT
    srt = generate_standard_srt(mock_segments)
    print("--- Standard SRT Output ---\n", srt.strip())
    assert "00:00:00,500 --> 00:00:02,800" in srt

    # Word-level SRT for CapCut
    word_srt = generate_word_level_srt(mock_segments)
    print("\n--- Word-Level SRT Output (CapCut Ready) ---\n", word_srt.strip()[:200], "...")
    assert "Halo" in word_srt
    assert "teman-teman" in word_srt

    # ASS with styling
    ass = generate_ass(mock_segments, {"fontFamily": "Montserrat", "fontSize": 36, "textColor": "#FFFF00"})
    print("\n--- ASS Output ---\n", ass.splitlines()[0], "...", ass.splitlines()[-1])
    assert "[Script Info]" in ass
    assert "Dialogue: 0" in ass

    # Re-segmenter (TikTok short punchy lines max 3 words)
    resegmented = resegment_by_words_or_chars(mock_segments, max_words=3)
    print(f"\n--- Resegmented into {len(resegmented)} short lines (Max 3 words) ---")
    for r in resegmented:
        print(f"#{r['sequence']} [{r['start']}s -> {r['end']}s]: {r['text']}")
    assert len(resegmented) == 3

    # Cleanup test files
    if test_video.exists(): test_video.unlink()
    if test_wav.exists(): test_wav.unlink()

    print("\n>>> ALL TESTS PASSED SUCCESSFULLY! <<<")

if __name__ == "__main__":
    test_pipeline()
