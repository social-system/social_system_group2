#!/usr/bin/env bash
set -euo pipefail

alembic upgrade head
python -m scripts.seed_master_data
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
