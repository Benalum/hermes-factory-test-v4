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
uvicorn app.main:app --host 0.0.0.0 --port 8000 &
PID=$!

# Ensure cleanup on exit
trap "kill $PID 2>/dev/null || true" EXIT

# Wait for app to start and check health
# We use a loop with a timeout to avoid hanging indefinitely
MAX_TRIES=10
COUNT=0
until curl -s localhost:8000/health | grep -q '"status":"ok"'; do
    ((COUNT++))
    if [ $COUNT -ge $MAX_TRIES ]; then
        echo "ERROR: Health check timed out after $MAX_TRIES seconds" >&2
        exit 1
    fi
    sleep 1
done

echo "Health check passed!"
