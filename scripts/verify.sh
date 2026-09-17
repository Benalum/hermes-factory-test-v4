#!/usr/bin/env bash
set -euo pipefail

# Activate venv
if [ -d "venv" ]; then
    source venv/bin/activate
else
    echo "ERROR: venv not found. Please run 'python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt' first." >&2
    exit 1
fi

export PYTHONPATH=${PYTHONPATH:-}:$(pwd)

# Run pytest
echo "Running pytest..."
pytest

# Verify /health endpoint with a live process
echo "Verifying /health endpoint..."

# Check if curl is installed
if ! command -v curl >/dev/null 2>&1; then
    echo "ERROR: curl not found. Please install curl." >&2
    exit 1
fi

# Start server using python -m uvicorn for better compatibility with venvs
# Redirect output to a log file for debugging
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 > server.log 2>&1 &
PID=$!

# Ensure cleanup on exit
trap "kill $PID 2>/dev/null || true" EXIT

# Wait for app to start and check health
MAX_TRIES=30
COUNT=0
until curl -s 127.0.0.1:8000/health | grep -q '"status":"ok"'; do
    ((COUNT++))
    if [ $COUNT -ge $MAX_TRIES ]; then
        echo "ERROR: Health check timed out after $MAX_TRIES seconds" >&2
        echo "--- Server Log ---"
        cat server.log
        exit 1
    fi
    sleep 1
done

echo "Health check passed!"
