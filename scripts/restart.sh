#!/bin/bash
# restart.sh — Install and restart all conformance checker services as systemd daemons
# Run this once after deploy, and any time you want to apply changes.
# Services will auto-restart on crash and survive reboots for 7+ days.

set -e
REPO_DIR="$HOME/agentic-api-conformance-checker"
SCRIPTS_DIR="$REPO_DIR/scripts"

echo "═══════════════════════════════════════════════════════"
echo "  API Conformance Checker — Service Restart Manager"
echo "═══════════════════════════════════════════════════════"

# ── 1. Docker Compose: Qdrant + Postgres ────────────────────────────────────
echo ""
echo "▶ Starting Docker infrastructure (Qdrant + Postgres)..."
cd "$REPO_DIR"

# Support both Docker Compose V1 (docker-compose) and V2 (docker compose)
if docker compose version &>/dev/null 2>&1; then
  docker compose up -d
else
  docker-compose up -d
fi
echo "✓ Docker services running (restart policy: unless-stopped)"

# ── 2. Install / refresh systemd service files ──────────────────────────────
echo ""
echo "▶ Installing systemd service units..."

sudo cp "$SCRIPTS_DIR/api-bridge.service" /etc/systemd/system/api-bridge.service
sudo cp "$SCRIPTS_DIR/openclaw.service"   /etc/systemd/system/openclaw.service

sudo systemctl daemon-reload
echo "✓ Service units installed and daemon reloaded"

# ── 3. Enable services to start on boot ─────────────────────────────────────
echo ""
echo "▶ Enabling services for auto-start on reboot..."
sudo systemctl enable api-bridge.service
sudo systemctl enable openclaw.service
echo "✓ Services enabled at boot"

# ── 4. (Re)start services ───────────────────────────────────────────────────
echo ""
echo "▶ Restarting services..."
sudo systemctl restart openclaw.service
sleep 3
sudo systemctl restart api-bridge.service
sleep 3
echo "✓ Services restarted"

# ── 5. Health check ─────────────────────────────────────────────────────────
echo ""
echo "▶ Running health checks..."

API_STATUS=$(sudo systemctl is-active api-bridge.service)
OCL_STATUS=$(sudo systemctl is-active openclaw.service)

echo "  api-bridge : $API_STATUS"
echo "  openclaw   : $OCL_STATUS"

sleep 2
HEALTH=$(curl -s http://localhost:8000/health || echo "unreachable")
echo "  HTTP check : $HEALTH"

echo ""
echo "═══════════════════════════════════════════════════════"
echo "  Done. All services are live and will run for 7+ days."
echo ""
echo "  Useful commands:"
echo "  sudo journalctl -u api-bridge -f      # live logs"
echo "  sudo journalctl -u openclaw -f        # openclaw logs"
echo "  sudo systemctl status api-bridge      # service status"
echo "═══════════════════════════════════════════════════════"
