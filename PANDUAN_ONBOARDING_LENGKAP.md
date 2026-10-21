# 📘 Panduan Lengkap Onboarding & Penggunaan (Untuk Orang Awam)
### Programmatic Local SEO & Generative Engine Optimization (GEO) Engine

Selamat datang! Panduan ini dirancang khusus dengan langkah-langkah praktis dan ramah pemula (*orang awam friendly*) agar Anda dapat menjalankan dan mengoperasikan mesin SEO otomatis ini dengan mudah di **Mac OS Intel** maupun **Apple Silicon (M1/M2/M3/M4)**.

---

## 🌟 Keunggulan Utama Sistem Ini

1. **Langsung Menggunakan Akun Google Gemini User**:
   - Tidak lagi memerlukan pihak ketiga seperti OpenRouter.
   - Otomatis mendeteksi login **Antigravity Desktop** yang sudah aktif di Mac Anda.
   - Mendukung **Multi-Akun Google Gemini**: Anda dapat memasukkan beberapa akun Google sekaligus. Jika kuota gratis akun pertama habis, sistem otomatis beralih ke akun kedua (*auto-rotation*).
2. **Thumbnail 16:9 Otomatis dari Gemini**:
   - Setiap artikel langsung dibuatkan gambar unggulan (*Featured Image*) berasio 16:9 (1200x675) berstandar studio dan terpasang otomatis di WordPress.
3. **50 Tag Masuk ke Tag WordPress (Bukan di Badan Teks)**:
   - 50 kata kunci turunan langsung disuntikkan ke taxonomy Tag WordPress via REST API dalam 1 milidetik, menjaga artikel tetap rapi dan bebas penalti Google.
4. **Mulai dari Nol (Brand Disetup Satu per Satu)**:
   - Anda dapat mendaftarkan website brand Anda secara bertahap dengan memasang plugin WordPress yang kami sediakan.
5. **Bank Data dari Spreadsheet**:
   - Cukup masukkan link Google Sheets Anda atau upload CSV untuk mengisi daftar kota, layanan, dan kata kunci secara massal.

---

## 💻 Langkah 1: Menjalankan Aplikasi di Mac OS Intel (Cukup 1 Klik!)

Anda **tidak perlu** mengetik perintah rumit di Terminal.

1. Buka folder proyek di Finder:
   ```
   /Users/macprom12020/Code/geo-seo-engine
   ```
2. Temukan file bernama:
   **`Jalankan_SEO_Engine.command`**
3. **Klik ganda (*double-click*)** file tersebut.
4. Jendela terminal akan terbuka sebentar, dan browser Google Chrome atau Safari Anda akan otomatis membuka halaman Dashboard di:
   👉 **`http://127.0.0.1:28420`**

*(Catatan: Launcher ini kompatibel 100% untuk Mac dengan prosesor Intel x86_64 maupun Mac M-Series Apple Silicon).*

---

## 🧠 Langkah 2: Menggunakan Router & Dynamic Model Discovery (9router)

Sistem ini menggunakan integrasi LLM Router nyata (**9router**) pada port `20128`:

1. Buka tab **"Router & Model LLM"** di Dashboard.
2. Anda akan melihat status router secara real-time (`Online` dengan 113+ model terdeteksi).
3. Klik tombol **`🔄 Fetch Live Models`** untuk menyegarkan daftar model langsung dari router.
4. Pilih model yang Anda inginkan (misalnya `ox-alpha`, `kr/auto`, `kr/claude-sonnet-4.5`, atau `GK/gk/deepseek-v4-flash`).
5. Model akan langsung dipakai untuk produksi artikel GEO tanpa menggunakan model hardcoded atau fiktif.
6. Anda juga dapat mengetik pesan singkat di kotak **Uji Respons Model** untuk memverifikasi model menjawab secara instan.

---

## 🎨 Langkah 3: Studio Generator Gambar AI & Visual Assets

Anda dapat membuat gambar visual kapan saja secara interaktif:

1. Klik tab **"Studio Generator Gambar"** di Dashboard.
2. Masukkan deskripsi visual atau klik salah satu **Contoh Cepat** (misalnya *Commercial Video Production Studio with 4K Cine Camera*).
3. Pilih rasio gambar yang Anda butuhkan:
   - **16:9:** Khusus thumbnail artikel WordPress (1200x675).
   - **1:1:** Khusus feed Instagram atau foto profil bisnis (1000x1000).
   - **9:16:** Khusus video vertikal Stories, Shorts, atau Reels (720x1280).
4. Pilih gaya visual: *Photorealistic*, *Cyberpunk*, atau *Minimalist*.
5. Klik **`✨ Generate Visual AI Sekarang`**.
6. Gambar akan langsung muncul di panel pratinjau dan dapat diunduh (JPG) atau disalin URL-nya. Seluruh gambar tersimpan otomatis di **Galeri Asset Visual**.

---

## 🔑 Langkah 4: Menghubungkan Akun Google Gemini (Opsional / Multi-Akun)

Sistem ini mendukung login langsung seperti Antigravity Desktop:

### Opsi A (Paling Cepat - 1 Tombol): Gunakan Sesi Antigravity yang Sudah Ada
1. Di Dashboard, klik tab **"Akun Gemini (Multi-Akun)"**.
2. Anda akan melihat kotak hijau bertuliskan:
   *"Sesi Antigravity / Gemini Desktop Terdeteksi: `proofingunipics@gmail.com`"*.
3. Klik tombol hijau **"Sinkronkan Sesi Antigravity"**.
4. Selesai! Sistem sudah langsung siap membuat artikel dan gambar thumbnail menggunakan akun Gemini Anda.

### Opsi B (Multi-Akun): Tambahkan Akun Google Gemini Tambahan
Untuk memperbesar kuota harian gratis:
1. Buka [https://aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey) dengan akun Google Anda yang lain.
2. Klik **"Create API key"** dan salin kuncinya (berawalan `AIzaSy...`).
3. Di Dashboard tab "Akun Gemini", masukkan email dan API Key tersebut pada form **"Tambah Akun Google Lain"**, lalu klik **Simpan & Hubungkan**.
4. Sistem sekarang memiliki 2 atau lebih akun yang akan bergantian dipakai secara otomatis.

---

## 🏢 Langkah 3: Setup Website Brand Anda (Satu per Satu)

1. Di Dashboard, klik tab **"Brand Network"**.
2. Klik tombol **"+ Tambah Brand Baru"**.
3. Isi data sederhana website Anda:
   - **Nama Brand**: Contoh `UNIMASI Studio` atau `SEGIA Tech`
   - **URL Domain WordPress**: Contoh `https://unimasi.com`
   - **Lokasi Kantor Pusat**: `Yogyakarta, Indonesia` (atau kota Anda)
   - **Bahasa Utama**: Pilih `Bahasa Indonesia` atau `English (Global/Australia)`
   - **Layanan Utama**: Contoh `3D Safety Induction Video` atau `Jasa Video Mapping`
   - **Wilayah Target**: Contoh `Australia` atau `Indonesia`
4. Klik **"Simpan & Daftarkan Brand"**.
5. Brand Anda kini aktif dan siap menerima postingan!

---

## 🔌 Langkah 4: Memasang Plugin di Website WordPress Target

Agar WordPress Anda dapat menerima artikel, 50 tag, dan thumbnail secara aman tanpa terblokir Wordfence:

1. Unduh file plugin zip yang sudah kami paketkan di:
   [`/Users/macprom12020/Code/wise-hertz/wordpress-plugin/unicam-seo-bridge.zip`](file:///Users/macprom12020/Code/wise-hertz/wordpress-plugin/unicam-seo-bridge.zip)
2. Masuk ke **WP Admin** website Anda (`https://namadomain.com/wp-admin/` atau `/pawon/`).
3. Buka menu **Plugins** -> **Add New** (Tambah Baru) -> **Upload Plugin**.
4. Pilih file `unicam-seo-bridge.zip`, lalu klik **Install Now** -> **Activate Plugin**.
5. Menu baru bernama **"SEO Engine"** akan muncul di sidebar kiri WordPress Anda!
6. Buka menu **SEO Engine** di WordPress untuk melihat progres artikel yang diproduksi, tag yang terpasang, dan status koneksi engine.

---

## 📊 Langkah 5: Mengisi Bank Data dari Google Sheets / CSV

Jika Anda memiliki ratusan kombinasi kota dan layanan di spreadsheet:

1. Di Dashboard lokal, klik tab **"Spreadsheet Bank Data"**.
2. Klik **"Download CSV Template"** untuk melihat contoh format kolom:
   - `brand_id`: ID brand (contoh: `unimasi`)
   - `service_name`: Nama layanan (contoh: `3D Safety Induction Video`)
   - `target_region`: Wilayah/Negara (contoh: `Australia`)
   - `cities`: Daftar kota target dipisah koma (contoh: `Sydney, Melbourne, Brisbane, Perth`)
3. **Menggunakan Google Sheets**:
   - Bagikan Google Sheets Anda dengan setelan: *"Anyone with the link can view"* (Siapa saja yang memiliki link dapat melihat).
   - Tempel link Google Sheets Anda ke kolom input dan klik **"Sync Bank Data from Google Sheet"**.
4. Seluruh layanan dan daftar kota target akan otomatis tersinkronisasi ke sistem!

---

## ✍️ Langkah 6: Menghasilkan & Memublikasikan Artikel Pertama Anda

1. Klik tab **"Matrix Writer & Preview"**.
2. Pilih **Target Brand** dan **Specialized Service**.
3. Pilih **Target Region** (misal: Australia atau Indonesia).
4. Masukkan nama kota (misal: `Sydney` atau `Jakarta`).
5. Klik **"Generate 12-Block Preview"**:
   - Sistem akan menyusun 12 blok artikel secara utuh.
   - Menghasilkan 10 Q&A untuk AI Overviews (GEO).
   - Menyiapkan 50 tag SEO transaksional.
   - Membuat gambar thumbnail 16:9 dengan Google Gemini.
   - Memasukkan internal link alami dan skema JSON-LD.
6. Klik **"Publish Previewed Post to WordPress"**:
   - Artikel langsung terbit atau terjadwal di WordPress Anda lengkap dengan thumbnail dan 50 tag!

---

## 🤖 Langkah 7: Menghubungkan ke Berbagai LLM (ChatGPT / Gemini / Claude)

Mesin ini sudah dilengkapi dua jalur akses aman untuk dioperasikan oleh AI Assistant:

### A. Untuk Antigravity / Gemini CLI / Claude Desktop / Cursor (Protokol MCP)
Buka file konfigurasi MCP Anda (misalnya `claude_desktop_config.json`) dan tambahkan:
```json
{
  "mcpServers": {
    "unicam-seo-engine": {
      "command": "/Users/macprom12020/Code/wise-hertz/.venv/bin/python",
      "args": ["-m", "mcp.server"],
      "cwd": "/Users/macprom12020/Code/wise-hertz"
    }
  }
}
```

### B. Untuk ChatGPT (Custom GPT Actions)
1. Buka ChatGPT -> **Explore GPTs** -> **Create a GPT**.
2. Di bagian **Configure** -> **Actions**, klik **Create new action**.
3. Salin isi file:
   [`/Users/macprom12020/Code/wise-hertz/openapi_chatgpt.json`](file:///Users/macprom12020/Code/wise-hertz/openapi_chatgpt.json)
   lalu tempelkan ke kolom Schema.
4. Di bagian Authentication, pilih **API Key**, masukkan header `X-API-Key` dengan nilai:
   `geo-engine-secret-2026`.
5. ChatGPT kini dapat membuat, menjadwalkan, dan memublikasikan artikel SEO ke WordPress Anda secara langsung!

---

## 🔒 Keamanan & Perlindungan Privasi

- **Tidak Ada Kebocoran Email**: Seluruh konten otomatis dibersihkan dari format email agar tidak menjadi sasaran spam bot.
- **Bypass Wordfence yang Aman**: Plugin menggunakan header token terenkripsi `X-SEO-Engine-Key`, sehingga password administrator WordPress Anda tidak pernah dibagikan kepada LLM mana pun.
- **Anti Tag-Stuffing**: 50 tag diletakkan pada taxonomy WordPress, bukan di dalam badan artikel, menjaga keterbacaan artikel tetap 100% natural di mata pembaca manusia dan Google.
