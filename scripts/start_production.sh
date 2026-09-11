#!/usr/bin/env bash
set -e

exec gunicorn main:app \
  --worker-class uvicorn_worker.UvicornWorker \
  --workers 1 \
  --bind 0.0.0.0:8000 \
  --access-logfile - \
  --error-logfile -