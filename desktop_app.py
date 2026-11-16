import os
import sys
import time
import socket
import threading
from functools import wraps
from pathlib import Path

# Safeguard for windowed PyInstaller app (console=False)
if sys.stdout is None:
    sys.stdout = open(os.devnull, "w")
if sys.stderr is None:
    sys.stderr = open(os.devnull, "w")

# Disable Hugging Face CLI progress bars and Xet in frozen/windowed environment
os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = "1"
os.environ["HF_HUB_DISABLE_XET"] = "1"
os.environ["HF_HUB_ENABLE_HF_TRANSFER"] = "0"

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

import webview
import uvicorn

# Add backend to sys.path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR / "backend"))

from app.main import app

def find_free_port(preferred=8000) -> int:
    """Finds an available TCP port on localhost, preferring 8000."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(('127.0.0.1', preferred))
            return preferred
        except OSError:
            s.bind(('127.0.0.1', 0))
            return s.getsockname()[1]

_server_port = find_free_port(8000)

# Module-level window reference and debounce guard
_desktop_window = None
_dialog_busy = False

class DesktopApi:
    def open_file_dialog(self):
        global _desktop_window, _dialog_busy
        if not _desktop_window or _dialog_busy:
            return None
        _dialog_busy = True
        try:
            # Modern FileDialog.OPEN enum (avoids OPEN_DIALOG deprecation warning)
            file_mode = getattr(webview.FileDialog, 'OPEN', getattr(webview, 'OPEN_DIALOG', 10))
            result = _desktop_window.create_file_dialog(
                file_mode,
                allow_multiple=False,
                file_types=('Video Files (*.mp4;*.mov;*.mkv;*.webm;*.avi)', 'All Files (*.*)')
            )
            if result and len(result) > 0:
                return str(Path(result[0]).resolve())
        except Exception as e:
            print(f"File dialog error: {e}")
        finally:
            _dialog_busy = False
        return None

    def download_url_to_file(self, url: str, default_filename: str):
        global _desktop_window, _dialog_busy, _server_port
        if not _desktop_window or _dialog_busy:
            return None
        _dialog_busy = True
        try:
            import urllib.request
            file_mode = getattr(webview.FileDialog, 'SAVE', getattr(webview, 'SAVE_DIALOG', 30))
            
            ext = Path(default_filename).suffix.lower()
            if ext == '.srt':
                file_types = ('SubRip Subtitle (*.srt)', 'All Files (*.*)')
            elif ext == '.vtt':
                file_types = ('WebVTT Subtitle (*.vtt)', 'All Files (*.*)')
            elif ext == '.ass':
                file_types = ('Advanced SubStation (*.ass)', 'All Files (*.*)')
            elif ext == '.txt':
                file_types = ('Text Document (*.txt)', 'All Files (*.*)')
            elif ext == '.mp4':
                file_types = ('MP4 Video (*.mp4)', 'All Files (*.*)')
            else:
                file_types = ('All Files (*.*)',)

            result = _desktop_window.create_file_dialog(
                file_mode,
                save_filename=default_filename,
                file_types=file_types
            )
            if result:
                save_path = result if isinstance(result, str) else result[0]
                full_url = url if url.startswith('http') else f"http://127.0.0.1:{_server_port}{url}"
                urllib.request.urlretrieve(full_url, save_path)
                return str(Path(save_path).resolve())
        except Exception as e:
            print(f"Download URL error: {e}")
        finally:
            _dialog_busy = False
        return None

def start_server():
    global _server_port
    uvicorn.run(app, host="127.0.0.1", port=_server_port, log_level="warning")

if __name__ == "__main__":
    print("=" * 55)
    print("   IndoCaption Desktop (Native Edge WebView2)")
    print("=" * 55)
    print(f"[*] Menjalankan backend server pada port {_server_port}...")

    # Enable native file downloads in WebView2
    webview.settings['ALLOW_DOWNLOADS'] = True

    # 1. Start FastAPI server in a background daemon thread
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()

    # Wait for server to bind port
    time.sleep(1.2)

    # 2. Setup native desktop window via pywebview
    api = DesktopApi()
    _desktop_window = webview.create_window(
        title="IndoCaption Studio — Local AI Auto Caption Editor",
        url=f"http://127.0.0.1:{_server_port}",
        width=1280,
        height=820,
        min_size=(980, 640),
        js_api=api,
        background_color="#0b0c10"
    )

    print("[*] Membuka jendela desktop native...")
    # 3. Start native GUI loop
    webview.start(debug=False)
