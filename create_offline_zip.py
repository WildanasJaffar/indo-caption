import os
import sys
import shutil
import zipfile
import time
from pathlib import Path

def create_offline_zip():
    t0 = time.time()
    desktop = Path(os.environ.get("USERPROFILE", "C:/Users/ASUS")) / "Desktop"
    zip_path = desktop / "IndoCaption_Portable_Offline.zip"
    staging = Path(os.environ.get("LOCALAPPDATA", "C:/Users/ASUS/AppData/Local")) / "Temp" / "IndoCaption_Portable"
    
    dist_dir = Path("dist/IndoCaption").resolve()
    if not dist_dir.exists():
        print(f"Error: Folder {dist_dir} tidak ditemukan.")
        return False
        
    print(f"=== Mempersiapkan Staging di {staging} ===")
    if staging.exists():
        shutil.rmtree(staging, ignore_errors=True)
    staging.mkdir(parents=True, exist_ok=True)
    
    app_root = staging / "IndoCaption"
    app_root.mkdir(parents=True, exist_ok=True)
    
    # 1. Copy IndoCaption.exe
    print("1/4 Menyalin IndoCaption.exe...")
    shutil.copyfile(dist_dir / "IndoCaption.exe", app_root / "IndoCaption.exe")
    
    # 2. Copy _internal folder
    print("2/4 Menyalin folder runtime _internal (dependensi, python runtime, dll)...")
    shutil.copytree(dist_dir / "_internal", app_root / "_internal", symlinks=False)
    
    # 3. Setup storage and model
    print("3/4 Mempersiapkan folder model offline (Large-v3-Turbo)...")
    model_dest = app_root / "storage" / "models" / "large-v3-turbo"
    model_dest.mkdir(parents=True, exist_ok=True)
    (app_root / "storage" / "uploads").mkdir(parents=True, exist_ok=True)
    (app_root / "storage" / "temp_audio").mkdir(parents=True, exist_ok=True)
    (app_root / "storage" / "exports").mkdir(parents=True, exist_ok=True)
    
    # Model sources
    user_models = Path(os.environ.get("LOCALAPPDATA", "C:/Users/ASUS/AppData/Local")) / "IndoCaption" / "models" / "models--mobiuslabsgmbh--faster-whisper-large-v3-turbo"
    snap_dir = user_models / "snapshots" / "0a363e9161cbc7ed1431c9597a8ceaf0c4f78fcf"
    blob_file = user_models / "blobs" / "e76620f83d5f5b69efd3d87e3dc180c1bd21df9fbebacfd4335e5e1efcc018da"
    
    if not blob_file.exists():
        print(f"Error: Blob model tidak ditemukan di {blob_file}")
        return False
        
    for fname in ["config.json", "preprocessor_config.json", "tokenizer.json", "vocabulary.json"]:
        src_f = snap_dir / fname
        if src_f.exists():
            shutil.copyfile(src_f, model_dest / fname)
            
    print(f" -> Menyalin file bobot model.bin asli (1.61 GB)...")
    shutil.copyfile(blob_file, model_dest / "model.bin")
    print(" -> File model.bin berhasil disalin utuh!")
    
    # 4. Create ZIP
    print(f"4/4 Mengompresi menjadi ZIP di {zip_path}...")
    if zip_path.exists():
        zip_path.unlink()
        
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=1) as zf:
        for root, dirs, files in os.walk(staging):
            for file in files:
                full_path = Path(root) / file
                rel_path = full_path.relative_to(staging)
                zf.write(full_path, rel_path)
                
    # Clean up staging
    print("Membersihkan temporary build staging...")
    shutil.rmtree(staging, ignore_errors=True)
    
    elapsed = time.time() - t0
    size_gb = zip_path.stat().st_size / (1024 * 1024 * 1024)
    print(f"\n[SUKSES] File ZIP siap pakai berhasil dibuat!")
    print(f"Lokasi: {zip_path}")
    print(f"Ukuran: {size_gb:.2f} GB")
    print(f"Waktu : {elapsed:.1f} detik")
    return True

if __name__ == "__main__":
    create_offline_zip()
