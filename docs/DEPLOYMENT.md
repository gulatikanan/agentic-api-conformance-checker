# Deployment and Redeploy Guide

This guide provides instructions for deploying, configuring, verifying, and troubleshooting the Agentic API Conformance Checker on an optimized production server environment.

## 1. Prerequisites
Before deploying, ensure the target host environment matches the verified low-resource execution footprint:
- **Host System**: AWS EC2 instance (t3.micro baseline partition running Ubuntu 24.04 LTS).
- **Physical Storage Volume**: 20GB EBS Volume minimum (Allocated to avoid 8GB system defaults).
- **Virtual Memory Allocation**: 2GB Linux Swap Space file configured on the host disk to absorb compilation spikes.
- **Docker**: Docker Engine and Docker Compose v2 (to run containerized PostgreSQL and Qdrant database layers).
- **Python**: Version 3.11.x or higher.
- **Python Package Manager**: `uv` (required for lightning-fast workspace resolution and deterministic tracking locks).

## 2. Environment Variables
Copy `.env.example` to `.env` and configure your target keys. The system uses a centralized workspace config shared by both the OpenClaw orchestration engine and background diagnostic scripts:

| Variable | Description | Example / Recommended Value |
| :--- | :--- | :--- |
| `LLM_PROVIDER` | Selection flag for the inference gateway network | `groq` |
| `LLM_API_KEY` | Upstream cloud reasoning verification token | `gsk_your_secret_production_key` |
| `LLM_MODEL` | Targeting deployment model identifier for checks | `llama-3.3-70b-versatile` |
| `QDRANT_URL` | Interface address of the containerized vector engine | `http://localhost:6333` |
| `QDRANT_COLLECTION` | Active target namespace collection name | `compliance_rules` |
| `POSTGRES_URL` | Private network interaction string for PostgreSQL database | `postgresql://postgres:postgrespassword@localhost:5432/conformance_checker` |
| `POSTGRES_PASSWORD` | Security passphrase credential mapping for relational data | `postgrespassword` |

## 3. Step-by-Step Fresh Deploy Instructions
Follow these sequential blocks to stand up a pristine server from complete scratch:

### Step 3.1: Host RAM and Storage Optimization
Run these commands first on your raw Ubuntu server to expand the storage layout and protect the machine against Out-Of-Memory (Killed) process terminations:
```bash
# 1. Claim expanded cloud disk capacity allocation
sudo growpart /dev/nvme0n1 1
sudo resize2fs /dev/root

# 2. Configure 2GB virtual memory emergency buffer file
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

### Step 3.2: Clone the Workspace Repository
```bash
git clone https://github.com/gulatikanan/agentic-api-conformance-checker.git
cd agentic-api-conformance-checker
```

### Step 3.3: Set Local Environment Secrets
```bash
cp .env.example .env
nano .env
chmod 600 .env
```
> [!IMPORTANT]
> Changing access boundaries via `chmod 600` ensures your Groq keys and DB passwords cannot be scanned or read by other background users on the system.

### Step 3.4: Spin Up Background Data Layers
Start your microservice architecture maps natively inside background daemon mode:
```bash
docker compose up -d
```

### Step 3.5: Synchronize Virtual Environments & Dependencies
Initialize isolation sandboxes and compile workspace requirements safely via `uv`:
```bash
uv sync
```

### Step 3.6: Run Data Ingestion (Vector Database Seeding)
Execute the data processing block using the unbuffered output flag (`-u`) to process, slice, embed, and deposit the 414 compliance rules directly into Qdrant:
```bash
.venv/bin/python -u src/ingestion/parse_corpus.py
```

### Step 3.7: Launch the Python Model Context Protocol Server
Start your isolated tool boundary execution engine using the protocol module runner:
```bash
uv run python src/mcp-server/tools/server.py
# For headless persistent runtime configurations, wrap execution using systemd or nohup
```

### Step 3.8: Boot the OpenClaw Agent Runtime
Fire up your live evaluation reasoning brain interface loop:
```bash
.venv/bin/python src/agent/main.py
```

### Step 3.9: Connect Your Production Frontend
Link your Next.js project directory block directly into Vercel hosting workflows.
Inject environment pointer coordinates directing Vercel server lines toward your EC2 instance's public IP addresses.

## 4. How to Verify Each Service
Run these checks to assert overall ecosystem integrity.

### 4.1. Qdrant Vector Engine
Validation Command:
```bash
curl http://localhost:6333/health
```
Expected Output Payload:
```json
{"title":"qdrant - vector search engine","version":"1.x.x"}
```

### 4.2. PostgreSQL Data Layer
Validation Command:
```bash
docker exec -it api-conformance-postgres pg_isready -U postgres
```
Expected Output Payload:
```plaintext
/var/run/postgresql:5432 - accepting connections
```

### 4.3. Upstream AI Brain Gateway (Groq)
Validation Command:
```bash
uv run python -c "from src.agent.llm_client import AgentBrain; print('Brain Response:', AgentBrain().generate('Say connection verified'))"
```
Expected Output Payload:
```plaintext
Brain Response: connection verified
```

## 5. Re-Ingesting the Corpus
If compliance rules alter or your seed pipeline experiences file drift, force an isolation sweep and repopulate the vector maps:
```bash
# Deletes the active 'compliance_rules' namespace block and re-compiles data matrix structures
.venv/bin/python -u src/ingestion/parse_corpus.py --force
```

## 6. Estimated Deployment Metrics
- **Total End-to-End Build Window**: ~5 minutes.
- **EBS Cloud Disk Layout Expansion**: 30 seconds
- **Docker Core Image Initialization**: 1 minute
- **Package Workspace Synchronization via uv**: 45 seconds
- **Local Extraction Matrix Computation (414 chunks)**: 2 minutes

## 7. Operational Troubleshooting

### 7.1. Terminal Prints "Killed" Instantly During Script Runs
- **Symptom**: System terminates parsing procedures abruptly without error traces.
- **Root Cause**: Host server lacks virtual swap space configurations, leading the Linux system OOM (Out Of Memory) monitor to assassinate compiling PyTorch modules.
- **Resolution**: Re-execute the Swap Space allocation guidelines outlined in Step 3.1.

### 7.2. Fallocate Error: No Space Left on Device
- **Symptom**: Ubuntu blocks creation of the safety file.
- **Root Cause**: The physical partition is operating at 100% capacity on the default 8GB configuration block.
- **Resolution**: Increase volume footprints to 20GB in the AWS EC2 Management UI, then trigger block updates using `sudo resize2fs /dev/root`.

### 7.3. ModuleNotFoundError Tracking Code Dependencies
- **Symptom**: Python flags missing dependencies during command script calls.
- **Root Cause**: Command maps are routing through the server's global environment instead of targeting your project's local directory sandbox space.
- **Resolution**: Prefix script triggers with your local path directory: `.venv/bin/python -u ...` or invoke setups natively using the `uv run` tracking prefix.
