import os
import sys
import shutil
from pathlib import Path

# Setup paths
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR / "backend"))

from app.config import USER_MODELS_DIR, STORAGE_DIR, validate_model_bin
from faster_whisper.utils import _MODELS

def export_standalone(model_size: str = "large-v3-turbo", dest_dir: Path = None):
    print(f"=== IndoCaption: Ekspor Model Standalone ({model_size}) ===")
    repo_id = _MODELS.get(model_size)
    if not repo_id:
        print(f"Error: Model {model_size} tidak dikenali.")
        return False

    folder_name = f"models--{repo_id.replace('/', '--')}"
    search_dirs = [
        STORAGE_DIR / "models" / folder_name,
        USER_MODELS_DIR / folder_name,
        BASE_DIR / "dist" / "IndoCaption" / "storage" / "models" / folder_name,
    ]

    source_snapshot = None
    for s_dir in search_dirs:
        if s_dir.is_dir():
            snapshots = list(s_dir.glob("snapshots/*"))
            for snap in snapshots:
                m_bin = snap / "model.bin"
                if validate_model_bin(m_bin):
                    source_snapshot = snap
                    break
        if source_snapshot:
            break

    if not source_snapshot:
        print(f"Error: Model {model_size} belum diunduh lengkap di komputer ini.")
        print("Silakan buka IndoCaption dan jalankan Auto Caption sekali agar model terunduh terlebih dahulu.")
        return False

    if dest_dir is None:
        dest_dir = BASE_DIR / "dist" / "IndoCaption" / "storage" / "models" / model_size

    dest_dir.mkdir(parents=True, exist_ok=True)
    print(f"Sumber model : {source_snapshot}")
    print(f"Tujuan ekspor: {dest_dir}")
    print("\nMenyalin file fisik (bukan symlink)... Mohon tunggu...")

    files_to_copy = ["config.json", "preprocessor_config.json", "tokenizer.json", "vocabulary.json", "model.bin"]
    for fname in files_to_copy:
        src_f = source_snapshot / fname
        if not src_f.exists():
            continue
        dst_f = dest_dir / fname
        size_mb = src_f.stat().st_size / (1024 * 1024)
        print(f" -> Menyalin {fname} ({size_mb:.1f} MB)...", end=" ", flush=True)
        # shutil.copyfile follows symlinks and copies the actual real bytes!
        shutil.copyfile(src_f, dst_f)
        print("Selesai.")

    print(f"\n[SUKSES] Model {model_size} berhasil diekspor ke:")
    print(f"  {dest_dir}")
    print("\nFolder ini berisi file asli (model.bin ukuran penuh ~1.6 GB) dan AMAN")
    print("dipindahkan via Flashdisk / ZIP ke laptop lain tanpa error 'v774843950'.")
    return True

if __name__ == "__main__":
    m_size = sys.argv[1] if len(sys.argv) > 1 else "large-v3-turbo"
    export_standalone(m_size)
