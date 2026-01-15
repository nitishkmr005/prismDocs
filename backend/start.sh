#!/bin/bash
# Startup script for Render deployment

# Ensure output is not buffered
export PYTHONUNBUFFERED=1

# Use PORT from environment or default to 8000
PORT=${PORT:-8000}

echo "==> Starting DocGen API on port $PORT..."
echo "==> PYTHONPATH: $PYTHONPATH"
echo "==> Working directory: $(pwd)"
echo "==> Python version: $(python --version)"
echo "==> PORT environment variable: $PORT"

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

# Test doc_generator module
python -c "import doc_generator; print('==> doc_generator module OK')"
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to import doc_generator module"
    exit 1
fi

# Test FastAPI app import with detailed error output
echo "==> Testing FastAPI app import (this may take a moment)..."
python << 'EOF'
import sys
import traceback

# Ensure immediate output
sys.stdout.flush()

try:
    print("    Loading FastAPI app...", flush=True)
    from doc_generator.infrastructure.api.main import app
    print("==> FastAPI app imported OK", flush=True)
except Exception as e:
    print(f"ERROR importing FastAPI app: {e}", flush=True)
    traceback.print_exc()
    sys.exit(1)
EOF

if [ $? -ne 0 ]; then
    echo "ERROR: FastAPI import failed"
    exit 1
fi

echo "==> All imports successful!"
echo "==> Starting uvicorn now on port $PORT..."
echo "==> Command: uvicorn doc_generator.infrastructure.api.main:app --host 0.0.0.0 --port $PORT"

# Start uvicorn - exec replaces shell process with uvicorn
exec python -m uvicorn doc_generator.infrastructure.api.main:app \
    --host 0.0.0.0 \
    --port "$PORT" \
    --log-level info \
    --access-log
