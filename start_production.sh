#!/bin/bash
# Production startup script for DovOS RAG API

# Load environment variables
export FLASK_APP=app.py
export FLASK_ENV=production

# Ensure we're in the right directory
cd "$(dirname "$0")"

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Start the application
exec python app.py
