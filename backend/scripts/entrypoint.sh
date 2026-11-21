#!/bin/sh
# Entrypoint do container da API: popula dados de demo (opcional) e sobe o servidor.
set -e

if [ "${SEED_DEMO:-false}" = "true" ]; then
    python -m scripts.seed
fi

exec uvicorn app.main:app --host 0.0.0.0 --port 8000
