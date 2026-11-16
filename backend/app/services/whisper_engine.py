import os
import sys
import gc
import time
import ctypes
import shutil
import logging
import threading
from typing import Dict, Any, Optional, Callable
from pathlib import Path

# Prevent Hugging Face Hub hangs in windowed mode (no TTY), limit MKL buffers, and configure SSL certs
os.environ.setdefault("HF_HUB_DISABLE_PROGRESS_BARS", "1")
os.environ.setdefault("HF_HUB_DISABLE_XET", "1")
os.environ.setdefault("OMP_NUM_THREADS", "4")
os.environ.setdefault("MKL_NUM_THREADS", "4")
os.environ.setdefault("MKL_DISABLE_FAST_MM", "1")
try:
    import certifi
    os.environ.setdefault("SSL_CERT_FILE", certifi.where())
    os.environ.setdefault("REQUESTS_CA_BUNDLE", certifi.where())
except Exception:
    pass

import huggingface_hub
from faster_whisper import WhisperModel
from faster_whisper.utils import _MODELS
import ctranslate2
from app.config import DEFAULT_WHISPER_MODEL, resolve_model_dir

logger = logging.getLogger(__name__)

_loaded_model_name: Optional[str] = None
_model_instance: Optional[WhisperModel] = None

MODEL_MIN_SPACE_BYTES = {
    "tiny": 150 * 1024 * 1024,
    "base": 250 * 1024 * 1024,
    "small": 600 * 1024 * 1024,
    "medium": 1800 * 1024 * 1024,
    "large-v3-turbo": 1900 * 1024 * 1024,
    "large-v3": 3500 * 1024 * 1024,
}

def get_device_info() -> Dict[str, Any]:
    cuda_count = ctranslate2.get_cuda_device_count()
    has_cuda = cuda_count > 0
    return {
        "has_cuda": has_cuda,
        "device": "cuda" if has_cuda else "cpu",
        "recommended_compute_type": "float16" if has_cuda else "int8",
        "supported_models": ["tiny", "base", "small", "medium", "large-v3", "large-v3-turbo"]
    }

def ensure_model_downloaded(
    model_size: str,
    progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None
) -> str:
    """
    Ensures the Faster-Whisper model is downloaded locally, reporting real-time MB
    download progress via progress_callback and ensuring enough free disk space.
    """
    repo_id = _MODELS.get(model_size)
    if not repo_id:
        return model_size

    target_dir = resolve_model_dir(model_size)
    target_dir.mkdir(parents=True, exist_ok=True)

    allow_patterns = [
        "config.json",
        "preprocessor_config.json",
        "model.bin",
        "tokenizer.json",
        "vocabulary.*",
    ]

    # 1. Try local cache first
    try:
        cached_path = huggingface_hub.snapshot_download(
            repo_id,
            cache_dir=str(target_dir),
            allow_patterns=allow_patterns,
            local_files_only=True,
        )
        if cached_path and (Path(cached_path) / "model.bin").exists():
            return cached_path
    except Exception:
        pass

    # 2. Verify free disk space on target_dir before downloading
    required_bytes = MODEL_MIN_SPACE_BYTES.get(model_size, 1500 * 1024 * 1024)
    free_bytes = shutil.disk_usage(target_dir).free
    if free_bytes < required_bytes:
        free_mb = round(free_bytes / (1024 * 1024))
        req_mb = round(required_bytes / (1024 * 1024))
        raise RuntimeError(
            f"Ruang penyimpanan di {target_dir.drive or target_dir} tidak cukup untuk mengunduh model {model_size} "
            f"(Tersedia: {free_mb} MB, Dibutuhkan: ~{req_mb} MB)."
        )

    # 3. Download with live byte-level progress tracking (zero console I/O)
    lock = threading.Lock()
    state = {"last_emit": 0.0}

    class LiveProgressBar:
        def __init__(self, *args, **kwargs):
            self.total = kwargs.get("total", 0) or 0
            self.n = kwargs.get("initial", 0) or 0
            self.unit = kwargs.get("unit", "")
            self.desc = str(kwargs.get("desc", ""))
            self.is_byte_tracker = (
                self.unit == "B" and "Downloading bytes" in self.desc
            )

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def __getattr__(self, item):
            return lambda *args, **kwargs: None

        def update(self, n=1):
            if n is None:
                return
            self.n += n
            if not self.is_byte_tracker or not progress_callback:
                return
            now = time.monotonic()
            with lock:
                if now - state["last_emit"] < 0.35 and self.n < self.total:
                    return
                state["last_emit"] = now

            if self.total and self.total > 0:
                dl_mb = self.n / (1024 * 1024)
                tot_mb = self.total / (1024 * 1024)
                pct = min(100.0, (self.n / self.total) * 100.0)
                progress_callback({
                    "status": "downloading_model",
                    "download_pct": round(pct, 1),
                    "message": f"Mengunduh model {model_size}: {dl_mb:.0f} / {tot_mb:.0f} MB ({pct:.0f}%)"
                })

    if progress_callback:
        progress_callback({
            "status": "downloading_model",
            "download_pct": 0.0,
            "message": f"Menghubungkan ke server model {model_size}..."
        })

    local_path = huggingface_hub.snapshot_download(
        repo_id,
        cache_dir=str(target_dir),
        allow_patterns=allow_patterns,
        tqdm_class=LiveProgressBar,
    )
    return local_path

def get_available_commit_mb() -> Optional[int]:
    """Returns available Windows virtual commit memory in MB, or None on non-Windows."""
    if sys.platform != "win32":
        return None
    try:
        class MEMORYSTATUSEX(ctypes.Structure):
            _fields_ = [
                ("dwLength", ctypes.c_ulong),
                ("dwMemoryLoad", ctypes.c_ulong),
                ("ullTotalPhys", ctypes.c_ulonglong),
                ("ullAvailPhys", ctypes.c_ulonglong),
                ("ullTotalPageFile", ctypes.c_ulonglong),
                ("ullAvailPageFile", ctypes.c_ulonglong),
                ("ullTotalVirtual", ctypes.c_ulonglong),
                ("ullAvailVirtual", ctypes.c_ulonglong),
                ("sullAvailExtendedVirtual", ctypes.c_ulonglong),
            ]
        stat = MEMORYSTATUSEX()
        stat.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
        ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat))
        return int(stat.ullAvailPageFile / (1024 * 1024))
    except Exception:
        return None

def get_whisper_model(
    model_size: str = DEFAULT_WHISPER_MODEL,
    progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None
) -> WhisperModel:
    global _loaded_model_name, _model_instance
    
    if _model_instance is not None and _loaded_model_name == model_size:
        return _model_instance
        
    device_info = get_device_info()
    device = device_info["device"]
    compute_type = device_info["recommended_compute_type"]

    logger.info(f"Loading Faster-Whisper model '{model_size}' on {device} ({compute_type})...")
    
    # Free old model if exists
    if _model_instance is not None:
        del _model_instance
        gc.collect()

    model_path = ensure_model_downloaded(model_size, progress_callback=progress_callback)

    if progress_callback:
        progress_callback({
            "status": "downloading_model",
            "download_pct": 100.0,
            "message": f"Memuat model {model_size} ke memori AI..."
        })

    # Limit CPU threads to prevent Intel MKL from over-allocating per-thread scratchpads on 8GB laptops
    is_heavy = model_size in ("medium", "large-v3", "large-v3-turbo")
    cpu_threads = 2 if (device == "cpu" and is_heavy) else min(4, os.cpu_count() or 4)

    try:
        _model_instance = WhisperModel(
            model_path,
            device=device,
            compute_type=compute_type,
            cpu_threads=cpu_threads if device == "cpu" else 4,
            local_files_only=True
        )
    except (RuntimeError, MemoryError) as exc:
        _model_instance = None
        _loaded_model_name = None
        gc.collect()
        err_str = str(exc)
        if "mkl_malloc" in err_str.lower() or "allocate memory" in err_str.lower() or isinstance(exc, MemoryError):
            avail_mb = get_available_commit_mb()
            avail_info = f" (sisa memori virtual: {avail_mb} MB)" if avail_mb is not None else ""
            raise RuntimeError(
                f"Memori RAM / Virtual Windows penuh saat memuat model '{model_size}'{avail_info}. "
                "Tutup aplikasi berat lain (seperti browser Chrome / IDE), atau gunakan model 'small' / 'base' yang jauh lebih ringan."
            ) from exc
        raise

    _loaded_model_name = model_size
    return _model_instance

def transcribe_with_progress(
    audio_path: str,
    language: str = "id",
    model_size: str = DEFAULT_WHISPER_MODEL,
    total_duration: float = 0.0,
    progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None
) -> list:
    """
    Transcribes audio file using Faster-Whisper with word-level timestamps.
    Calls progress_callback(dict) on download and each segment parsed.
    """
    model = get_whisper_model(model_size, progress_callback=progress_callback)
    
    # Configure language & code-switching behavior
    if language == "id-en":
        lang_param = None
        use_multilingual = True
        prompt_param = "Bahasa Indonesia and English."
    elif language == "auto":
        lang_param = None
        use_multilingual = True
        prompt_param = None
    else:
        lang_param = language
        use_multilingual = False
        prompt_param = None

    # Use lean beam_size for heavy models on CPU to slash peak MKL RAM by >50%
    device_info = get_device_info()
    is_heavy = model_size in ("medium", "large-v3", "large-v3-turbo")
    beam_size = 2 if (device_info["device"] == "cpu" and is_heavy) else 5

    # Run transcription
    try:
        segments_gen, info = model.transcribe(
            audio_path,
            language=lang_param,
            multilingual=use_multilingual,
            initial_prompt=prompt_param,
            task="transcribe",
            beam_size=beam_size,
            word_timestamps=True,
            vad_filter=True,
            vad_parameters=dict(min_silence_duration_ms=400)
        )

        detected_language = info.language
        duration = total_duration or info.duration or 1.0

        collected_segments = []
        
        for idx, seg in enumerate(segments_gen):
            words = []
            if seg.words:
                for w in seg.words:
                    words.append({
                        "word": w.word.strip(),
                        "start": round(w.start, 3),
                        "end": round(w.end, 3),
                        "probability": round(w.probability, 3)
                    })

            segment_data = {
                "sequence": idx + 1,
                "start": round(seg.start, 3),
                "end": round(seg.end, 3),
                "text": seg.text.strip(),
                "words": words
            }
            collected_segments.append(segment_data)

            # Calculate progress percentage based on audio timeline
            pct = min(99.0, round((seg.end / duration) * 100, 1)) if duration > 0 else 50.0

            if progress_callback:
                progress_callback({
                    "status": "processing",
                    "progress": pct,
                    "current_segment": segment_data,
                    "detected_language": detected_language
                })
    except (RuntimeError, MemoryError) as exc:
        err_str = str(exc)
        if "mkl_malloc" in err_str.lower() or "allocate memory" in err_str.lower() or isinstance(exc, MemoryError):
            gc.collect()
            avail_mb = get_available_commit_mb()
            avail_info = f" (sisa memori virtual: {avail_mb} MB)" if avail_mb is not None else ""
            raise RuntimeError(
                f"Memori RAM / Virtual Windows tidak mencukupi saat memproses model '{model_size}'{avail_info}. "
                "Tutup beberapa aplikasi lain atau pilih model 'small' / 'base'."
            ) from exc
        raise

    if progress_callback:
        progress_callback({
            "status": "completed",
            "progress": 100.0,
            "detected_language": detected_language
        })

    return collected_segments
