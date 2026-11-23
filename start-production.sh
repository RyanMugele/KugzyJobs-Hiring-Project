#!/bin/sh
set -eu
export FLASK_CONFIG=production
python -m flask --app flasky init-db
exec gunicorn --config gunicorn.conf.py flasky:app
