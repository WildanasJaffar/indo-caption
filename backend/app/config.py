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

def validate_model_bin(model_bin: Path) -> bool:
    """Verifies that model.bin exists, is at least 10 MB, and has a valid CTranslate2 binary header (v1-v10)."""
    if not model_bin.is_file():
        return False
    try:
        if model_bin.stat().st_size < 10 * 1024 * 1024:
            return False
        with open(model_bin, "rb") as f:
            header = f.read(4)
            if len(header) < 4:
                return False
            v = int.from_bytes(header, "little")
            return 1 <= v <= 10
    except Exception:
        return False

def auto_heal_hf_model(model_dir: Path) -> bool:
    """
    If a model was copied via flash drive or without symlink dereferencing,
    model.bin in snapshots/ might be missing or corrupted (containing only a text pointer '../.').
    This function heals it automatically by linking/copying from blobs/.
    """
    import json
    blobs_dir = model_dir / "blobs"
    snapshots_dir = model_dir / "snapshots"
    if not blobs_dir.is_dir() or not snapshots_dir.is_dir():
        return False

    snapshots = [d for d in snapshots_dir.iterdir() if d.is_dir()]
    if not snapshots:
        return False

    healed_any = False
    for snap in snapshots:
        model_bin = snap / "model.bin"
        if not validate_model_bin(model_bin):
            target_blob = None
            trees_dir = model_dir / "trees"
            tree_file = trees_dir / f"{snap.name}.json"
            if tree_file.is_file():
                try:
                    with open(tree_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    m_info = data.get("files", {}).get("model.bin", {})
                    sha = m_info.get("lfs_sha256") or m_info.get("blob_id")
                    if sha and (blobs_dir / sha).is_file():
                        target_blob = blobs_dir / sha
                except Exception:
                    pass

            if not target_blob or not target_blob.is_file():
                blob_files = [b for b in blobs_dir.iterdir() if b.is_file() and b.stat().st_size > 50 * 1024 * 1024]
                if blob_files:
                    target_blob = max(blob_files, key=lambda b: b.stat().st_size)

            if target_blob and target_blob.is_file():
                if model_bin.is_file() or model_bin.is_symlink():
                    try:
                        model_bin.unlink()
                    except Exception:
                        pass
                try:
                    os.link(target_blob, model_bin)
                except Exception:
                    shutil.copyfile(target_blob, model_bin)
                healed_any = True

        # Check other critical files
        for fname in ["config.json", "tokenizer.json", "vocabulary.json"]:
            target_f = snap / fname
            if not target_f.is_file() or target_f.stat().st_size == 0:
                trees_dir = model_dir / "trees"
                tree_file = trees_dir / f"{snap.name}.json"
                if tree_file.is_file():
                    try:
                        with open(tree_file, "r", encoding="utf-8") as f:
                            data = json.load(f)
                        sha = data.get("files", {}).get(fname, {}).get("blob_id")
                        if sha and (blobs_dir / sha).is_file():
                            shutil.copyfile(blobs_dir / sha, target_f)
                    except Exception:
                        pass
    return healed_any

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
            for mdir in cdir.glob(folder_name):
                if mdir.is_dir():
                    auto_heal_hf_model(mdir)
            matches = list(cdir.glob(f"{folder_name}/snapshots/*/model.bin"))
            valid_matches = [m for m in matches if validate_model_bin(m)]
            if valid_matches:
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
