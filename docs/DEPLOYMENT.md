# Production Deployment & Lifecycle Management Guide

This guide provides instructions for deploying, configuring, verifying, and managing the Agentic API Conformance Checker platform inside a hardened server workspace.

---

## 1. Baseline System Prerequisites

Before launching deployment sequences, ensure the host environment matches the verified low-resource execution footprint:
* **Host OS Node:** AWS EC2 Instance (Ubuntu 24.04 LTS baseline build partition).
* **Storage Allocation:** 20GB EBS Volume minimum (allocated to bypass default 8GB cloud system limits).
* **Virtual Memory Buffer:** 2GB Linux Swap Space file configured on the host disk to securely absorb embedding generation/PyTorch processing spikes.
* **Container Runtime:** Docker Engine and Docker Compose v2 (managing isolated relational and vector database layers).
* **Python Runtime Environment:** Version 3.11.x or higher.
* **Dependency Manager:** `uv` (required for deterministic tracking locks and rapid synchronization environments).
* **Process Manager:** `systemd` (required to guarantee the 7-day minimum uptime capability).

---

## 2. Global Environment Variables Matrix (`.env`)

Copy `.env.example` to generate your local `.env` profile. The system references a unified environment context shared seamlessly by the OpenClaw orchestration engine, background system services, and dynamic MCP boundaries:

| Variable Name | Context Purpose | Production Template Values |
| :--- | :--- | :--- |
| `LLM_PROVIDER` | Selection flag for the upstream inference engine routing | `google` |
| `GEMINI_MODEL` | Targeting deployment model identifier for reasoning steps | `gemini-2.5-flash` |
| `GEMINI_API_KEY` | Upstream Google Cloud AI platform access authentication credential | `AIzaSy...` |
| `GROQ_API_KEY` | (Optional) Upstream Groq platform credential for 100% free lightning-fast inference | `gsk_...` |
| `QDRANT_URL` | Interface access address of the vector container database | `http://127.0.0.1:6333` |
| `POSTGRES_URL` | Complete interaction connection string for PostgreSQL engine | `postgresql://...` |

---

## 3. Step-by-Step Unified Deployment Guide

### 🛠️ Step 3.1: Host RAM and Storage Optimization
Run these parameters first on a raw Ubuntu node to claim disk limits and insulate the core engine against Out-Of-Memory (`Killed`) process terminations:
```bash
# 1. Expand the baseline file system footprint to fill out cloud storage allocations
sudo growpart /dev/nvme0n1 1
sudo resize2fs /dev/root

# 2. Allocate and mount a 2GB virtual memory emergency swap buffer file
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

### 📂 Step 3.2: Clone and Isolate the Repository
```bash
git clone https://github.com/gulatikanan/agentic-api-conformance-checker.git
cd agentic-api-conformance-checker
```

### 🔑 Step 3.3: Seed Production Environment Configurations
```bash
cp .env.example .env
nano .env
chmod 600 .env
```
> **⚠️ Security Warning:** Restricting read permissions to `chmod 600` guarantees that background OS agents cannot scan your active LLM tokens or database credentials.

### 🚀 Step 3.4: Trigger Automated Orchestration Lifecycles
The application utilizes native DevSecOps wrappers inside the `scripts/` directory to manage system dependencies, container architectures, and systemd daemons:
```bash
# 1. Grant global executable permissions to the script suite
chmod +x scripts/*.sh

# 2. Boot Docker databanks (Postgres/Qdrant) and compile Python packages via uv
./scripts/setup.sh

# 3. Parse compliance files, compute local embeddings, and populate Qdrant
./scripts/ingest.sh

# 4. Install systemd units, flush zombie ports, and start the background daemons
./scripts/restart.sh
```

### 4. Multi-Tiered Infrastructure Verification
Execute these baseline validation checkpoints to verify overall ecosystem communication integrity.

#### 4.1. Systemd Daemons (7-Day Uptime Guarantee)
```bash
sudo systemctl is-active api-bridge
sudo systemctl is-active openclaw
```
*Expected Return:* `active` for both services.

#### 4.2. API Bridge Boundary Health
```bash
curl http://localhost:8000/health
```
*Expected Return Payload:* `{"status": "ok", "agent": "openclaw", "mcp": "conformance-tools"}`

### 5. Live Maintenance: Re-Ingesting the Rule Corpus
If the upstream compliance rulebooks update, or you inject new custom corporate guidelines, execute a data sync hot‑reload. The pipeline cleanly flushes the existing vector namespace and recalculates matrices:
```bash
./scripts/ingest.sh
```

### 6. Real-World Operational Troubleshooting Playbook

#### 🔴 Symptom 6.1: 429 Quota Exceeded or 413 Payload Too Large (LLM APIs)
*Root Cause:* Free tier LLMs (like Google AI Studio or Groq) have strict rate limits or context size limits.
*Remediation:* Switch the OpenClaw configuration to use a `minimal` tools profile to drastically reduce the context window overhead (done automatically in setup), and switch between Groq/Gemini as needed depending on rate limits.

#### 🔴 Symptom 6.2: Terminal Prints "Killed" Instantly During Ingestion
*Root Cause:* The host instance lacks virtual swap allocations, causing the Linux OOM monitor to terminate PyTorch transformer pipelines during embedding calculations.
*Remediation:* Execute the manual swap space configuration instructions outlined in **Step 3.1**.

#### 🔴 Symptom 6.3: Gateway Port Binding Failure / 8000 or 18789 Already in Use
*Root Cause:* A zombie daemon background thread retains ownership of network interface ports, preventing a fresh config reload.
*Remediation:* Run `./scripts/restart.sh`. This process automatically scans for dangling port locks, shuts down orphaned processes via `fuser`, and rebuilding a clean communication stream across `systemd`.
