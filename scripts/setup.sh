#!/bin/bash
set -e

echo "🚀 Starting environment setup..."

# 1. Start database containers
echo "📦 Initializing Docker containers (PostgreSQL & Qdrant)..."
docker compose up -d

# 2. Sync python dependencies
echo "🔄 Synchronizing project virtual environment via uv..."
if command -v uv &> /dev/null; then
    uv sync
else
    echo "⚠️ 'uv' package manager not found. Falling back to standard pip..."
    python3 -m venv .venv
    .venv/bin/pip install --upgrade pip
    .venv/bin/pip install -e .
fi

echo "✅ Setup complete! System infrastructure is active."
