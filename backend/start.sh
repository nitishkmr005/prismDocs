#!/bin/bash
# Startup script for Render deployment

# Use PORT from environment or default to 8000
PORT=${PORT:-8000}

echo "==> Starting DocGen API on port $PORT..."
echo "==> PYTHONPATH: $PYTHONPATH"
echo "==> Working directory: $(pwd)"
echo "==> Python version: $(python --version)"

# Ensure data directories exist
echo "==> Ensuring data directories exist..."
mkdir -p data/cache data/output data/temp data/logging
chmod -R 755 data/

echo "==> Verifying config file..."
if [ -f "/app/config/settings.yaml" ]; then
    echo "==> Config file found at /app/config/settings.yaml"
else
    echo "ERROR: Config file not found!"
    exit 1
fi

echo "==> Testing Python imports..."
python -c "import doc_generator; print('==> doc_generator module OK')" || exit 1
python -c "from doc_generator.infrastructure.api.main import app; print('==> FastAPI app imported OK')" || exit 1

echo "==> Starting uvicorn now..."
# Start uvicorn with explicit error handling
exec python -m uvicorn doc_generator.infrastructure.api.main:app \
    --host 0.0.0.0 \
    --port "$PORT" \
    --log-level debug \
    --access-log
