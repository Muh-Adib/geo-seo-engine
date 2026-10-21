#!/bin/bash
# ==============================================================================
# UNICAM SEO & GEO ENGINE - LAUNCHER MACOS (INTEL & APPLE SILICON)
# Cukup klik ganda (double-click) file ini dari Finder untuk menjalankan aplikasi!
# ==============================================================================

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

echo "======================================================================"
echo " ⚡ MEMULAI UNICAM PROGRAMMATIC SEO & GEO ENGINE"
echo " 💻 Kompatibilitas: Mac OS Intel (x86_64) & Apple Silicon (M1/M2/M3/M4)"
echo "======================================================================"

# 1. Cek Python 3
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 tidak ditemukan. Silakan pasang Python 3 terlebih dahulu dari python.org."
    read -p "Tekan [Enter] untuk keluar..."
    exit 1
fi

# 2. Siapkan Virtual Environment jika belum ada
if [ ! -d ".venv" ]; then
    echo "📦 Membuat virtual environment Python lokal..."
    python3 -m venv .venv
    echo "📥 Menginstal modul yang diperlukan..."
    .venv/bin/pip install --upgrade pip
    .venv/bin/pip install -r requirements.txt
fi

# 3. Jalankan Server Web Dashboard via CLI
PORT=28420
echo "🚀 Menjalankan Server di http://localhost:$PORT ..."
exec "$DIR/seo-engine" start --port "$PORT"
