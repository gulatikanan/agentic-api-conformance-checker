#!/bin/bash
set -e

echo "🧠 Initializing data ingestion pipeline..."

# Ensure python binary exists
if [ -f ".venv/bin/python" ]; then
    .venv/bin/python -u src/ingestion/parse_corpus.py
else
    echo "❌ Error: Virtual environment python not found. Run setup.sh first."
    exit 1
fi

echo "🎯 Knowledge base population completed successfully!"
