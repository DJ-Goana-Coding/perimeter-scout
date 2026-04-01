#!/bin/bash
# Startup script for Hugging Face Spaces and production deployments.
# Runs the FastAPI backend on PORT (default 7860).
# The Streamlit frontend is optional — set STREAMLIT=1 to enable it.

set -e

export PORT=${PORT:-7860}
export API_BASE_URL=${API_BASE_URL:-http://localhost:${PORT}/api/v1}

echo "🛡️ Starting Perimeter Scout backend on port ${PORT}..."
uvicorn backend.main:app --host 0.0.0.0 --port "${PORT}"
