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

---

## 2. Global Environment Variables Matrix (`.env`)

Copy `.env.example` to generate your local `.env` profile. The system references a unified environment context shared seamlessly by the OpenClaw orchestration engine, background system services, and dynamic MCP boundaries:

| Variable Name | Context Purpose | Production Template Values |
| :--- | :--- | :--- |
| `LLM_PROVIDER` | Selection flag for the upstream inference engine routing | `gemini` |
| `GEMINI_MODEL` | Targeting deployment model identifier for reasoning steps | `google/gemini-1.5-pro` |
| `GEMINI_API_KEY` | Upstream Google Cloud AI platform access authentication credential | `AIzaSyYourSecretProductionKey...` |
| `QDRANT_URL` | Interface access address of the vector container database | `http://127.0.0.1:6333` |
| `QDRANT_COLLECTION` | Target collection namespace inside the vector search instance | `compliance_rules` |
| `POSTGRES_URL` | Complete interaction connection string for PostgreSQL engine | `postgresql://postgres:postgrespassword@localhost:5432/conformance_checker` |
| `SIMILARITY_THRESHOLD`| Strict algorithmic guardrail baseline to prevent hallucinations | `0.45` |

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
> **⚠️ Security Warning:** Restricting read permissions to `chmod 600` guarantees that background OS agents cannot scan your active Gemini tokens or database credentials.

### 🚀 Step 3.4: Trigger Automated Orchestration Lifecycles
The application utilizes native DevSecOps wrappers inside the `scripts/` directory to manage system dependencies and container architectures without manual error steps:
```bash
# 1. Grant global executable permissions to the script suite
chmod +x scripts/*.sh

# 2. Boot Docker databanks (Postgres/Qdrant) and compile Python packages via uv
./scripts/setup.sh

# 3. Parse compliance files, compute local embeddings, and populate Qdrant
./scripts/ingest.sh

# 4. Flush zombie process ports, reload configs, and trigger the background daemon
./scripts/restart.sh
```

### 4. Multi-Tiered Infrastructure Verification
Execute these baseline validation checkpoints to verify overall ecosystem communication integrity.

#### 4.1. Qdrant Vector Engine Node
```bash
curl http://localhost:6333/health
```
*Expected Return Payload:* `{"title":"qdrant - vector search engine","version":"1.x.x"}`

#### 4.2. PostgreSQL Persistent Database Layer
```bash
docker exec -it agentic-api-conformance-checker-db-1 pg_isready -U postgres
```
*Expected Return Payload:* `/var/run/postgresql:5432 - accepting connections`

#### 4.3. OpenClaw Background Systemd Daemon Process
```bash
sudo systemctl status openclaw.service
```
*Expected Return Payload:* Verify the active state displays a green **active (running)** status, listening on localized interface port **18789**.

### 5. Live Maintenance: Re-Ingesting the Rule Corpus
If the upstream compliance rulebooks update, or you inject new custom corporate guidelines, execute a data sync hot‑reload. The pipeline cleanly flushes the existing vector namespace and recalculates matrices:
```bash
./scripts/ingest.sh
```

### 6. Real-World Operational Troubleshooting Playbook
#### 🔴 Symptom 6.1: Terminal Prints "Killed" Instantly During Ingestion
*Root Cause:* The host instance lacks virtual swap allocations, causing the Linux OOM monitor to terminate PyTorch transformer pipelines during embedding calculations.
*Remediation:* Execute the manual swap space configuration instructions outlined in **Step 3.1**.

#### 🔴 Symptom 6.2: Gateway Port Binding Failure / 18789 Already in Use
*Root Cause:* A zombie daemon background thread retains ownership of network interface port 18789, preventing a fresh config reload.
*Remediation:* Run `./scripts/restart.sh`. This process automatically scans for dangling port locks, shuts down orphaned processes via `fuser`, and rebuilds a clean communication stream.

#### 🔴 Symptom 6.3: Relational Logs Show Blank Rows (NULL) inside Database UI
*Root Cause:* Misalignment between AI response fields and database ingestion parameters.
*Remediation:* Verify that `src/mcp-server/tools/server.py` implements defensive fallback extractions matching the endpoint and reason response patterns produced by OpenClaw.
