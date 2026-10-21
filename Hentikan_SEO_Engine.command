#!/bin/bash
# ==============================================================================
# UNICAM SEO & GEO ENGINE - STOP LAUNCHER
# Cukup klik ganda file ini untuk menghentikan server dan sesi yang berjalan!
# ==============================================================================

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

echo "======================================================================"
echo " 🛑 MENGHENTIKAN SESI UNICAM SEO & GEO ENGINE"
echo "======================================================================"

if [ -f "$DIR/seo-engine" ]; then
    "$DIR/seo-engine" stop
else
    # Fallback to kill port
    PORT=28420
    echo "Mencari proses pada port $PORT..."
    PID=$(lsof -ti :$PORT 2>/dev/null)
    if [ -n "$PID" ]; then
        kill -9 $PID
        echo "✅ Proses PID $PID pada port $PORT berhasil dihentikan."
    else
        echo "ℹ️  Tidak ada server yang sedang berjalan."
    fi
    rm -f "$DIR/.server.pid"
fi

echo ""
echo "Sesi telah ditutup."
sleep 1.5
