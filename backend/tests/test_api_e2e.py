import os
import sys
from pathlib import Path
from fastapi.testclient import TestClient

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from app.main import app
from app.database import init_db
from app.services.video_renderer import escape_ffmpeg_filter_path, render_hardcoded_video
from app.services.subtitle_formatter import generate_ass
from app.utils.ffmpeg_check import get_ffmpeg_path
import subprocess

def test_api_e2e():
    print("=== Testing FastAPI Endpoints End-to-End ===")
    init_db()
    client = TestClient(app)

    # 1. Health check
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    print("1. Health check:", data["status"], "FFmpeg available:", data["ffmpeg"]["available"])
    assert data["ffmpeg"]["available"]

    # 2. Hardware check
    res = client.get("/api/transcribe/hardware")
    assert res.status_code == 200
    hw = res.json()
    print("2. Hardware check: Device =", hw["device"], "Compute type =", hw["recommended_compute_type"])

    # 3. Create synthetic test video for upload
    ffmpeg_exe = get_ffmpeg_path()
    sample_mp4 = Path("sample_test.mp4").resolve()
    cmd = [
        ffmpeg_exe, "-y",
        "-f", "lavfi", "-i", "testsrc=duration=2:size=640x360:rate=30",
        "-f", "lavfi", "-i", "sine=frequency=440:duration=2",
        "-c:v", "libx264", "-c:a", "aac", "-shortest",
        str(sample_mp4)
    ]
    subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)

    # 4. Upload video via API
    with open(sample_mp4, "rb") as f:
        res = client.post(
            "/api/projects/upload",
            files={"file": ("sample_test.mp4", f, "video/mp4")},
            data={"name": "Demo Test Project"}
        )
    assert res.status_code == 200, res.text
    project = res.json()
    project_id = project["id"]
    print("3. Project uploaded successfully: ID =", project_id, "Name =", project["name"])

    # 5. Test streaming endpoint with HTTP Range header (Partial Content 206)
    filename = Path(project["video_path"]).name
    res = client.get(f"/api/media/stream/{filename}", headers={"Range": "bytes=0-1023"})
    assert res.status_code == 206
    assert "Content-Range" in res.headers
    print("4. Streaming HTTP Range request check passed (HTTP 206 Partial Content)")

    # 6. Add manual subtitle lines to test editing and formatting
    sub1_res = client.post(f"/api/subtitles/{project_id}?start_time=0.2&end_time=1.0&text=Halo%20dunia")
    assert sub1_res.status_code == 200
    sub2_res = client.post(f"/api/subtitles/{project_id}?start_time=1.1&end_time=1.9&text=Selamat%20datang")
    assert sub2_res.status_code == 200
    sub1_id = sub1_res.json()["id"]
    sub2_id = sub2_res.json()["id"]
    print(f"5. Added 2 subtitles: Sub1 ID={sub1_id}, Sub2 ID={sub2_id}")

    # 7. Update subtitle text
    update_res = client.put(f"/api/subtitles/{sub1_id}", json={"text": "Halo Indonesia!", "start_time": 0.2, "end_time": 1.0})
    assert update_res.status_code == 200
    assert update_res.json()["text"] == "Halo Indonesia!"
    print("6. Updated subtitle text to:", update_res.json()["text"])

    # 8. Test Export Endpoints
    # Standard SRT
    res_srt = client.get(f"/api/export/{project_id}/srt")
    assert res_srt.status_code == 200
    assert "Halo Indonesia!" in res_srt.text
    print("7. Export SRT verified")

    # Word-level SRT
    res_wsrt = client.get(f"/api/export/{project_id}/srt-words")
    assert res_wsrt.status_code == 200
    print("8. Export Word-level SRT verified")

    # VTT
    res_vtt = client.get(f"/api/export/{project_id}/vtt")
    assert res_vtt.status_code == 200
    assert "WEBVTT" in res_vtt.text
    print("9. Export WebVTT verified")

    # TXT
    res_txt = client.get(f"/api/export/{project_id}/txt")
    assert res_txt.status_code == 200
    print("10. Export TXT verified")

    # ASS
    res_ass = client.get(f"/api/export/{project_id}/ass")
    assert res_ass.status_code == 200
    assert "[Script Info]" in res_ass.text
    print("11. Export ASS verified")

    # 9. Test FFmpeg libass video burn-in directly
    print("\n=== Testing FFmpeg Subtitle Burn-In (Hardcoded Video Render) ===")
    ass_path = Path("test_burn.ass").resolve()
    with open(ass_path, "w", encoding="utf-8") as f:
        f.write(res_ass.text)

    output_burned = render_hardcoded_video(
        video_path=str(sample_mp4),
        ass_path=str(ass_path),
        output_filename="burned_output_test.mp4",
        total_duration=2.0
    )
    assert Path(output_burned).exists()
    print("12. Rendered hardcoded video with libass:", output_burned, "size:", Path(output_burned).stat().st_size)

    # 10. Merge subtitles test
    merge_res = client.post(f"/api/subtitles/{project_id}/merge", json={"subtitle_id_1": sub1_id, "subtitle_id_2": sub2_id})
    assert merge_res.status_code == 200
    subs_after_merge = client.get(f"/api/subtitles/{project_id}").json()
    assert len(subs_after_merge) == 1
    assert "Halo Indonesia! Selamat datang" in subs_after_merge[0]["text"]
    print("13. Subtitle merge verified: result =", subs_after_merge[0]["text"])

    # 11. Cleanup test files
    if sample_mp4.exists(): sample_mp4.unlink()
    if ass_path.exists(): ass_path.unlink()
    if Path(output_burned).exists(): Path(output_burned).unlink()
    client.delete(f"/api/projects/{project_id}")

    print("\n>>> ALL API E2E & RENDER TESTS PASSED! <<<")

if __name__ == "__main__":
    test_api_e2e()
