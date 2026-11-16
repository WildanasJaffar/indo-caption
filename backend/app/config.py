import os
import sys
import shutil
from pathlib import Path

# Paths: Use directory of executable when frozen (PyInstaller .exe), otherwise repo root
if getattr(sys, "frozen", False):
    BASE_DIR = Path(sys.executable).resolve().parent
else:
    BASE_DIR = Path(__file__).resolve().parent.parent.parent

STORAGE_DIR = BASE_DIR / "storage"
UPLOAD_DIR = STORAGE_DIR / "uploads"
TEMP_AUDIO_DIR = STORAGE_DIR / "temp_audio"
EXPORT_DIR = STORAGE_DIR / "exports"

# User-level model cache on primary OS drive (C:\Users\...\AppData\Local\IndoCaption\models)
USER_MODELS_DIR = Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "IndoCaption" / "models"

def get_models_dir() -> Path:
    primary = STORAGE_DIR / "models"
    if getattr(sys, "frozen", False):
        has_local = primary.exists() and any(primary.glob("models--*"))
        if not has_local:
            repo_models = BASE_DIR.parent.parent / "storage" / "models"
            if repo_models.exists() and any(repo_models.glob("models--*")):
                return repo_models
    return primary

MODELS_DIR = get_models_dir()
DB_PATH = STORAGE_DIR / "indocaption.db"

# Ensure all storage folders exist
for folder in [STORAGE_DIR, UPLOAD_DIR, TEMP_AUDIO_DIR, EXPORT_DIR, MODELS_DIR, USER_MODELS_DIR]:
    folder.mkdir(parents=True, exist_ok=True)

def resolve_model_dir(model_size: str) -> Path:
    """
    Finds an already-downloaded model across local/repo/user cache directories,
    or chooses a destination directory with sufficient free disk space.
    """
    from faster_whisper.utils import _MODELS

    repo_id = _MODELS.get(model_size, "")
    folder_name = f"models--{repo_id.replace('/', '--')}" if repo_id else f"*{model_size}*"

    candidates = [USER_MODELS_DIR, STORAGE_DIR / "models"]
    if getattr(sys, "frozen", False):
        candidates.append(BASE_DIR.parent.parent / "storage" / "models")

    # 1. Reuse already-complete cached model if present anywhere
    for cdir in candidates:
        if cdir.exists():
            matches = list(cdir.glob(f"{folder_name}/snapshots/*/model.bin"))
            if matches and matches[0].stat().st_size > 0:
                return cdir

    # 2. Not cached yet: check if local STORAGE_DIR has at least 3.5 GB free, otherwise use USER_MODELS_DIR (Drive C)
    min_required = 3.5 * 1024 * 1024 * 1024
    local_models = STORAGE_DIR / "models"
    try:
        local_free = shutil.disk_usage(local_models).free
        if local_free >= min_required:
            return local_models
    except Exception:
        pass

    return USER_MODELS_DIR

# App Settings
DATABASE_URL = f"sqlite:///{DB_PATH}"
DEFAULT_WHISPER_MODEL = "small"
DEFAULT_LANGUAGE = "id"
