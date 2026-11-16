# IndoCaption — Local AI Auto Caption & Word-Level SRT Editor

> **Aplikasi Pembuat Subtitle AI 100% Offline & Word-Level SRT Khusus CapCut untuk Video Kreator Indonesia**

IndoCaption adalah aplikasi desktop mandiri untuk menghasilkan caption otomatis dari video dengan akurasi tinggi menggunakan model **Faster-Whisper (CTranslate2)** dan **FFmpeg**. Seluruh proses berjalan di perangkat lokal Anda tanpa mengirim data ke internet dan tanpa biaya API.

---

## 🌟 Fitur Utama

1. **100% Offline & Privasi Terjaga**:
   - File video dan audio tidak pernah dikirim ke cloud atau pihak ketiga.
   - Tidak memerlukan kuota token atau API key berbayar.

2. **Dukungan Bahasa Indonesia & Campuran (Indo + English)**:
   - **Mode Khusus Bahasa Indonesia**: Dioptimalkan untuk tata bahasa dan tanda baca Indonesia.
   - **Mode Campuran (Indo + English)**: Tetap akurat mengenali istilah asing/teknis (misal: *"subscribe"*, *"duck"*, *"workflow"*) di tengah percakapan bahasa Indonesia.

3. **Pilihan Model AI Faster-Whisper Ringan & Cepat**:
   - Pilihan model: `tiny`, `base`, `small` (rekomendasi terbaik CPU), `medium`, hingga `large-v3-turbo`.
   - Dilengkapi optimasi memori MKL multi-threading hemat RAM untuk laptop dan PC standar.

4. **Presisi Kata Word-Level SRT (Khusus CapCut)**:
   - Menghasilkan file SRT per kata dengan timestamp presisi milidetik.
   - Impor langsung ke **CapCut** untuk mengaktifkan animasi teks pop-up kata per kata secara dinamis.
   - Tersedia juga format: **Standard SRT (.srt)**, **WebVTT (.vtt)**, **Styled ASS (.ass)**, dan **Transkrip TXT (.txt)**.

5. **Subtitle Studio Editor & Reorder Interaktif**:
   - **Smart Chronological Insertion**: Menambah subtitle baru otomatis disisipkan tepat di posisi playhead waktu video saat ini.
   - **Sisipkan Klip Baru**: Tombol `+` di setiap kartu untuk menyisipkan baris tepat setelah klip yang dipilih.
   - **Drag & Drop & Quick Move**: Geser urutan baris subtitle dengan mudah via drag handle (`⠿`) atau tombol panah (▲ / ▼).
   - **Urutkan Waktu Otomatis**: 1 klik untuk merapikan kembali urutan subtitle berdasarkan kronologi waktu.
   - **Potong Ulang Viral (TikTok/Reels)**: Membagi kalimat panjang menjadi baris pendek 3–5 kata per baris secara otomatis.
   - **Split & Merge**: Memotong atau menggabungkan baris klip beserta data kata-katanya.

6. **Desain NLE Studio Modern ("Obsidian & Amber Reel")**:
   - Antarmuka bertema editing studio gelap dengan aksen Amber Gold & Cyan Timecode.

---

## 🚀 Cara Menjalankan

### Cara 1: Mode Aplikasi Desktop Standalone (Paling Praktis) ⚡
Jalankan file batch:
```cmd
start-desktop.bat
```
Aplikasi akan membuka jendela desktop mandiri (**Microsoft Edge WebView2 Native**) dengan penggunaan RAM sangat hemat (~35 MB) dan integrasi Windows File Dialog native (Zero-Copy instant video load).

---

### Cara 2: Mode Web Browser Lokal
Jalankan file:
```cmd
start.bat
```
Aplikasi akan menjalankan backend FastAPI di port 8000 dan membuka antarmuka web di browser.

---

### Cara 3: Menjalankan Manual dari Source Code

#### 1. Persyaratan Sistem
- Python 3.10 – 3.12
- Node.js 18+ (untuk frontend)
- FFmpeg (dapat diinstal melalui Windows Terminal: `winget install Gyan.FFmpeg`)

#### 2. Setup Backend:
```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python run.py
```

#### 3. Setup Frontend:
```bash
cd frontend
npm install
npm run dev
```

---

## 📦 Build Standalone Executable (.exe)

Untuk mengompilasi IndoCaption menjadi satu file `.exe` yang siap dibagikan tanpa perlu instalasi Python atau Node.js:

```bash
# 1. Build frontend terlebih dahulu
cd frontend
npm run build
cd ..

# 2. Build executable menggunakan PyInstaller
pyinstaller IndoCaption.spec -y
```

Hasil file executable akan berada di folder:
```cmd
dist\IndoCaption\IndoCaption.exe
```

---

## 🎬 Alur Kerja dengan CapCut (CapCut Workflow)

1. Buka IndoCaption dan pilih video Anda (MP4 / MOV / MKV).
2. Klik tombol **"Auto Caption"** (Pilih model `small` atau `large-v3-turbo`).
3. Gunakan tombol **"Potong Ulang"** jika ingin kalimat dipotong pendek ala TikTok (misal maks 4 kata).
4. Klik **"Export"** $\rightarrow$ Unduh **"Word-Level SRT (Khusus CapCut)"**.
5. Buka **CapCut Desktop / Mobile**:
   - Masukkan video asli Anda ke timeline.
   - Buka tab **Teks** $\rightarrow$ **Impor Subtitle** $\rightarrow$ Masukkan file `.srt` yang baru diunduh.
   - Setiap kata otomatis sinkron dengan audio dan siap diberi animasi pop-up kata!

---

## 📄 Lisensi
MIT License. Bebas digunakan untuk keperluan personal maupun komersial.
