#!/usr/bin/env bash
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

echo "=========================================================="
echo " Starting Unicam Programmatic SEO & GEO Engine Dashboard"
echo " Multi-Tenant Network: 10 Brands Architecture"
echo " Dashboard URL: http://localhost:8000"
echo "=========================================================="

"$DIR/.venv/bin/uvicorn" web.app:app --host 0.0.0.0 --port 8000 --reload
