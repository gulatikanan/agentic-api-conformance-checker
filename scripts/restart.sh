#!/bin/bash
set -e

echo "🔄 Re-initializing OpenClaw Systemd Service..."

# 1. Stop service
sudo systemctl stop openclaw.service

# 2. Clear out any potential orphaned network process locks on port 18789
if command -v fuser &> /dev/null; then
    echo "🧹 Cleaning zombie process locks on port 18789..."
    sudo fuser -k 18789/tcp || true
fi

# 3. Reload and restart
sudo systemctl daemon-reload
sudo systemctl start openclaw.service

echo "🟢 Service successfully cycled! Fetch status via: sudo systemctl status openclaw.service"
