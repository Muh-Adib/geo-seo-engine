#!/usr/bin/env bash
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

echo "=========================================================="
echo " Starting Unicam Programmatic SEO & GEO Engine Dashboard"
echo " Multi-Tenant Network: WordPress Bridge & GEO Optimization"
echo " Dashboard URL: http://localhost:28420"
echo "=========================================================="

"$DIR/.venv/bin/uvicorn" web.app:app --host 0.0.0.0 --port 28420 --reload
