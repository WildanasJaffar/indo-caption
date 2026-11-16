# 🚀 IndoCaption v1.1.0 – Global Time Shift & Quick Clipboard Export

Release ini membawa dua fitur produktivitas utama untuk mempercepat proses penyuntingan dan ekspor subtitle video kreator.

---

### ✨ Apa yang Baru? (What's New)

#### 1. ⏱️ Geser Waktu Massal (Global Time Offset / Time Shift)
Sering kali hasil transkripsi AI sedikit mendahului atau terlambat beberapa milidetik dari suara aslinya. Sekarang Anda tidak perlu lagi menggeser satu per satu baris subtitle:
* **Toolbar Geser Waktu**: Klik tombol berikon jam di atas daftar subtitle untuk membuka panel geser waktu.
* **Pintasan Cepat (Quick Presets)**: Tersedia tombol instan `[-0.5s]`, `[-0.2s]`, `[+0.2s]`, dan `[+0.5s]`.
* **Kustomisasi Presisi**: Masukkan angka desimal positif atau negatif (misal: `+0.15s` atau `-0.3s`) lalu klik **Terapkan**.
* **Presisi Kata Terjaga (Word-Level Sync)**: Waktu mulai, waktu selesai, serta seluruh timestamp per kata (`words_json`) otomatis ikut bergeser secara akurat sehingga efek animasi kata CapCut tetap sinkron.
* **Pengaman Waktu Negatif**: Waktu awal subtitle diproteksi agar tidak pernah minus (`clamp >= 0.0s`).

#### 2. 📋 Tombol "Salin ke Clipboard" pada Modal Export
Kini Anda bisa menyalin teks subtitle langsung ke clipboard tanpa harus mendownload file fisiknya ke komputer terlebih dahulu:
* Tersedia tombol **"Salin"** untuk semua format ekspor:
  * 🎯 **Word-Level SRT** (Khusus CapCut kata per kata)
  * 📄 **Standard SRT (.srt)**
  * 🌐 **WebVTT (.vtt)**
  * 🎨 **Styled ASS (.ass)**
  * 📝 **Transkrip TXT (.txt)**
* Dilengkapi umpan balik visual instan: tombol berubah hijau bertuliskan **"Tersalin! ✓"** dan banner notifikasi konfirmasi.

---

### 🛠️ Rincian Perubahan Teknis (Under the Hood)
* **Backend**:
  * Menambahkan endpoint baru `POST /api/subtitles/{project_id}/time-shift` pada `backend/app/routers/subtitles.py`.
  * Penyesuaian skema request `TimeShiftRequest` dengan validasi offset.
* **Frontend**:
  * Menambahkan metode `subtitleApi.timeShift` di `frontend/src/api/client.js`.
  * Integrasi panel kontrol waktu di `frontend/src/components/editor/SubtitleList.vue`.
  * Pembaruan komponen `frontend/src/components/export/ExportModal.vue` dengan integrasi Web Clipboard API (`navigator.clipboard.writeText`).

---

### 📦 Cara Menjalankan
Bagi pengguna desktop Windows, jalankan file executable di:
```text
dist/IndoCaption/IndoCaption.exe
```
