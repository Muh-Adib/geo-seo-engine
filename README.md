# 🚀 GEO SEO Engine — Programmatic Local SEO & Generative Engine Optimization Multi-Brand Network

[![Python Version](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/Framework-FastAPI-009688.svg)](https://fastapi.tiangolo.com)
[![Google Gemini](https://img.shields.io/badge/AI-Google%20Gemini%20%7C%20Imagen%203-8E75C2.svg)](https://ai.google.dev)
[![WordPress Bridge](https://img.shields.io/badge/Integration-WordPress%20REST%20API-21759B.svg)](https://wordpress.org)
[![Tests Passing](https://img.shields.io/badge/Tests-18%2F18%20Passed-success.svg)](https://pytest.org)
[![Port](https://img.shields.io/badge/Port-28420-orange.svg)](#port-configuration)
[![Platform](https://img.shields.io/badge/macOS-Apple%20Silicon%20%7C%20Intel%20x86__64-black.svg)](#installation)

An autonomous, multi-tenant **Programmatic Local SEO & Generative Engine Optimization (GEO)** content engine designed to mass-produce high-ranking landing pages targeting `[Service] x [Location]` matrices across multiple brands simultaneously. 

Natively engineered to dominate both traditional Google SERP rankings and modern AI Answer Engines (Google AI Overviews, Gemini, ChatGPT Search, and Perplexity).

---

## 🌟 Fitur Utama (Key Features)

### 1. 🧠 Multi-Akun Google Gemini Otomatis
* **Direct Gemini Engine:** Menggunakan API Google Gemini langsung (bukan OpenRouter pihak ketiga).
* **Auto-Detect Antigravity Desktop Token:** Mendeteksi sesi login aktif Antigravity / Gemini Desktop lokal secara otomatis (`~/.gemini/jetski-standalone-oauth-token`).
* **Multi-Account Rotation & Failover:** Mendukung penambahan banyak akun dan API key. Jika salah satu akun mencapai batas kuota (HTTP 429), sistem otomatis merotasi ke akun berikutnya tanpa menghentikan proses bulk generate.

### 2. 🎨 Generator Gambar Thumbnail 16:9 Otomatis
* Memproduksi featured image lanskap 16:9 (resolusi standar 1200x675) untuk setiap artikel menggunakan **Google Imagen 3**.
* Dilengkapi sistem fallback cerdas **Studio Typography Canvas** (Pillow) dengan tipografi branding mewah beresolusi tinggi jika kuota gambar habis.
* Featured image otomatis di-upload dan dipasang sebagai *Featured Image* WordPress via REST Bridge.

### 3. 📝 Anatomi Konten 12 Blok Standar GEO & SGE
Setiap artikel diproduksi mengikuti standar 12 blok terstruktur:
1. **H1/H2 Title:** `[Keyword Utama] [Target Lokasi] - [Nama Brand]`
2. **Intro (2 Paragraf):** Penyebutan kota-kota tier-1, exact keyword (**bold**), markas HQ (Yogyakarta), dan nilai ROI remote.
3. **Definisi Layanan:** Fitur pipeline + `*Keyword Subjudul*` (*italic*) + 3 bullet points manfaat.
4. **Urgensi Lokal:** Konteks sektor industri spesifik di wilayah target (Mining, Construction, Real Estate, E-Commerce, dll.).
5. **Brand USP:** Storytelling Mastery + Jaminan Revisi 2x Gratis (*Free 2x Revision Guarantee*).
6. **Edukasi Klien:** Panduan brief yang jelas dan komunikasi transparan.
7. **Katalog Solusi:** 4 turunan solusi modular.
8. **Pipeline Studio:** 5 tahapan alur kerja terurut dari audit hingga master 4K.
9. **Nilai Tambah / ROI:** Modulasi aset untuk format vertikal media sosial (9:16) dan web viewer.
10. **Call to Action (CTA):** Paragraf persuasif + Tagline 🎥 (**Ketat: Tanpa alamat email**).
11. **10 GEO Q&A Items:** Tanya-jawab faktual terstruktur yang dioptimasi untuk AI Overviews (harga, timeline 2-5 minggu, lisensi, deliverables, format file).
12. **Metadata & 50 Tag:** Meta deskripsi ringkas (<160 karakter).

### 4. 🏷️ 50 Tag SEO Bersih (Strictly Taxonomy Tags)
* **Bebas Spam:** 50 tag transaksional **TIDAK DICANTUMKAN** di badan artikel HTML untuk menjaga kerapian konten dan menghindari penalti Google.
* **WordPress Post Tags:** Seluruh 50 tag langsung didaftarkan ke taxonomy WordPress (`wp_set_post_tags`) melalui REST API Bridge dalam 1 ms.

### 5. 🔗 Contextual Cluster Siloing & Schema.org
* **Menggantikan Cloaking:** Menghilangkan teknik usang tumpukan tautan tersembunyi (*hidden text cloaking*) yang rentan deindex Google SpamBrain.
* **Internal Linking Natural:** Menyisipkan 3–5 tautan internal secara kontekstual di dalam paragraf `<p>`.
* **Bottom Directory Component:** Menambahkan blok resmi *"Explore Our Other Regional & Specialized Solutions"* di bagian bawah artikel.
* **Structured Data:** Menginjeksi skema Schema.org JSON-LD valid (`FAQPage` + `ProfessionalService`).

### 6. 🔌 WordPress Bridge Plugin v2.0 (`unicam-seo-bridge.zip`)
* Plugin single-file berkecepatan tinggi yang membypass proteksi Cloudflare / Wordfence Application Passwords.
* Dilengkapi menu Admin WordPress terdedikasi (**SEO Engine**) untuk monitoring artikel masuk, pengaturan Secret Key (`X-SEO-Engine-Key`), dan konfigurasi Gemini API Key.

### 7. 📊 Bank Data Importer (Google Sheets & CSV)
* **Google Sheets 1-Click Import:** Masukkan URL publik share Google Sheets Anda (`https://docs.google.com/spreadsheets/d/...`), sistem otomatis mengekstrak data CSV dan meng-upsert brand, layanan, serta kota target.
* **Local CSV Support:** Tersedia template CSV siap pakai di `data/matrix_template.csv`.

### 8. 🕹️ CLI Terpadu Model `9router` & Web Dashboard
* Kendalikan seluruh sesi melalui CLI terminal `./seo-engine` atau melalui antarmuka web modern Tailwind CSS + Alpine.js.
* Berjalan pada port khusus yang aman: **`28420`**.

---

## ⚡ Panduan Cepat (Quick Start)

### Persyaratan Sistem
* macOS (Intel x86_64 maupun Apple Silicon) / Linux / Windows WSL.
* Python 3.10 atau versi lebih baru.

### 1. Clone Repositori
```bash
git clone https://github.com/Muh-Adib/geo-seo-engine.git
cd geo-seo-engine
```

### 2. Jalankan Sesi

#### Opsi A: Klik-Ganda di macOS Finder (Paling Mudah)
* Klik 2x file **`Jalankan_SEO_Engine.command`**. Skrip akan otomatis menginisialisasi lingkungan virtual Python, menginstal dependensi, menjalankan server di background, dan membuka browser ke dashboard.
* Untuk mematikan, cukup klik 2x file **`Hentikan_SEO_Engine.command`**.

#### Opsi B: Menggunakan CLI `./seo-engine` (Mirip `9router`)
```bash
# Menghidupkan sesi di background
./seo-engine start

# Melihat status sesi dan akun Gemini yang aktif
./seo-engine status

# Melihat daftar akun Gemini & rotasi failover
./seo-engine accounts

# Mengimpor bank data dari Google Sheets
./seo-engine import-sheet "https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID/edit"

# Merestart sesi
./seo-engine restart

# Mematikan sesi
./seo-engine stop
```

---

## 🌐 Port Configuration

Secara bawaan server berjalan di:
```text
http://127.0.0.1:28420
```
Port **`28420`** dipilih secara khusus karena:
1. Merupakan port *unassigned* (sangat jarang digunakan oleh aplikasi background).
2. Bebas dari tabrakan port web developer umum (`3000`, `5000`, `8000`, `8080`).
3. Tidak bersinggungan dengan port bawaan `9router` (`20128`).

Untuk mengganti port sesuai preferensi Anda:
```bash
./seo-engine start --port 29000
```
atau edit variabel `PORT=28420` di dalam file `.env`.

---

## 🔌 Instalasi WordPress Bridge Plugin

File zip siap pasang tersedia di direktori:
```text
wordpress-plugin/unicam-seo-bridge.zip
```

1. Masuk ke WP-Admin situs WordPress target: `https://domain-anda.com/wp-admin`.
2. Buka menu **Plugins** -> **Add New Plugin** -> **Upload Plugin**.
3. Pilih file `unicam-seo-bridge.zip`, lalu klik **Install Now** dan **Activate Plugin**.
4. Masuk ke menu baru di sidebar admin: **SEO Engine**.
5. Salin **Secret Bridge Key** (bawaan: `unicam-geo-secret-key-2026`) atau ganti sesuai keamanan Anda.
6. Masukkan Secret Key dan domain situs tersebut ke Web Dashboard SEO Engine Anda.

---

## 📊 Format Bank Data Spreadsheet (CSV / Google Sheets)

Anda dapat mengimpor matriks layanan dan kota dalam jumlah besar menggunakan format CSV berikut:

```csv
brand_name,domain_url,hq_location,service_name,pillar_url,region_name,sub_cities
UNIMASI,https://unimasi.com,"Yogyakarta, Indonesia",3D Safety Induction Video,https://unimasi.com/services/safety,Australia,"Sydney, Melbourne, Brisbane, Perth"
UNICAM STUDIO,https://unicamstudio.com,"Yogyakarta, Indonesia",Jasa Video Mapping,https://unicamstudio.com/services/mapping,Indonesia,"Jakarta, Surabaya, Bandung, Bali"
```

* Kolom `sub_cities` dipisahkan dengan tanda koma di dalam tanda petik.
* Sistem otomatis membuat brand baru, mendaftarkan layanan, serta menyiapkan matriks artikel untuk setiap kota.

---

## 🧪 Pengujian Otomatis (Automated Tests)

Sistem dilengkapi rangkaian pengujian otomatis end-to-end yang menjamin keandalan seluruh modul:

```bash
# Jalankan seluruh test suite (18 tes)
.venv/bin/pytest -v
```

Hasil verifikasi:
```text
tests/test_bridge_plugin.py::test_php_syntax PASSED                      [  5%]
tests/test_bridge_plugin.py::test_plugin_zip_archive PASSED              [ 11%]
tests/test_bridge_plugin.py::test_bridge_client_initialization PASSED    [ 16%]
tests/test_database.py::test_empty_database_initialization PASSED         [ 22%]
tests/test_database.py::test_brand_creation_and_retrieval PASSED         [ 27%]
tests/test_database.py::test_sheet_importer_and_csv PASSED               [ 33%]
tests/test_gemini_auth.py::test_gemini_pool_initialization PASSED         [ 38%]
tests/test_gemini_auth.py::test_gemini_account_rotation PASSED           [ 44%]
tests/test_gemini_auth.py::test_gemini_image_generation_fallback PASSED   [ 50%]
tests/test_geo_generator.py::test_12_block_structure_and_constraints_english PASSED [ 55%]
tests/test_geo_generator.py::test_indonesian_language_adaptation PASSED  [ 61%]
tests/test_geo_generator.py::test_50_tags_not_in_body_content PASSED     [ 66%]
tests/test_link_injector.py::test_link_injection_and_schema PASSED       [ 72%]
tests/test_mcp_server.py::test_mcp_tools PASSED                          [ 77%]
tests/test_web_app.py::test_dashboard_homepage PASSED                    [ 83%]
tests/test_web_app.py::test_api_list_brands PASSED                       [ 88%]
tests/test_web_app.py::test_api_brand_context PASSED                     [ 94%]
tests/test_web_app.py::test_api_system_diagnostics PASSED                [100%]

============================== 18 passed in 2.18s ==============================
```

---

## 👥 Multi-User & Kolaborasi Tim

Repositori ini telah dikonfigurasi agar dapat di-clone dan digunakan oleh banyak orang dengan aman:
1. **Tidak Ada Kredensial Pribadi yang Bocor:** File `.env`, database lokal (`*.db`), token sesi OAuth, dan log telah dikecualikan di `.gitignore`.
2. **Template Konfigurasi:** Disediakan file [.env.example](.env.example) dan [data/gemini_accounts.example.json](data/gemini_accounts.example.json).
3. **Relative Dynamic Paths:** Seluruh resolver file menggunakan Python `pathlib.Path(__file__).resolve()`, sehingga kode dapat berjalan di komputer manapun tanpa konflik path pengguna.
4. **Panduan Lengkap Non-Teknis:** Dokumentasi onboarding lengkap berbahasa Indonesia tersedia di [PANDUAN_ONBOARDING_LENGKAP.md](PANDUAN_ONBOARDING_LENGKAP.md).

---

## 📜 Lisensi & Atribusi
Dibuat dan dikembangkan untuk jaringan **UNICAM STUDIO**, **UNIMASI**, dan multi-brand ecosystem. Didistribusikan di bawah lisensi MIT.
