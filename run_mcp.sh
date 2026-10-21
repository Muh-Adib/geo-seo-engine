#!/usr/bin/env bash
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

export PYTHONPATH="$DIR"
exec "$DIR/.venv/bin/python" -m mcp.server
