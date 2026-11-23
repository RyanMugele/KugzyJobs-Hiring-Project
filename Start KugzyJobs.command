#!/bin/zsh
set -e
cd -- "$(dirname -- "$0")"
if [[ ! -x .venv/bin/python ]]; then
  python3 -m venv .venv
  .venv/bin/python -m pip install -r requirements-lock.txt
fi
if [[ ! -f .env ]]; then
  .venv/bin/python -c 'import secrets; from pathlib import Path; Path(".env").write_text("SECRET_KEY="+secrets.token_hex(32)+"\nFLASK_CONFIG=development\n")'
fi
.venv/bin/python -m flask --app flasky init-db
echo 'KugzyJobs: http://127.0.0.1:5001 — press Control+C to stop.'
.venv/bin/python -m flask --app flasky run --host 127.0.0.1 --port 5001
