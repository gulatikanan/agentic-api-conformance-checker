# Agentic API Conformance Checker

The Agentic API Conformance Checker is an intelligent, automated testing framework designed to analyze, ingest, and verify API implementations against formal specifications. By leveraging agentic AI workflows, semantic search, and vector databases, it automatically checks conformance, identifies discrepancies, and ensures robust compliance with security and design standards.

---

## 🚀 Architecture & Strategy

This project implements a **decoupled LLM client strategy** inside `src/agent/llm_client.py`. Instead of tightly coupling the agentic engine to a specific provider, the LLM is treated as an abstracted infrastructure service. 

While the system is natively designed to integrate open-weight models, we route reasoning workloads through the high-performance **Groq API** (`llama-3.3-70b-versatile`). This design choice isolates the core application code from upstream API variations, provides error isolation, and allows seamless, single-variable model swapping without modifications to the codebase.

---

## 📁 Repository Structure
```plaintext
.
├── corpus/                 # Compliance guidelines and raw text documents
│   ├── raw/                # Targeted ingestion home for OWASP/Zalando definitions
│   └── download.sh         # Automated corpus procurement script
├── docs/                   # Project design documentation and assignment specifications
│   ├── ARCHITECTURE.md     # System structural mapping and data flows
│   ├── DEPLOYMENT.md       # Target environment environment properties
│   └── PRD.md              # Product Requirement Documentation
├── qdrant/
│   └── storage/            # Persistent local storage volume mapping for Qdrant
├── scripts/                # Operational lifecycle scripts (setup, restart, initialization)
│   ├── ingest.sh
│   ├── restart.sh
│   └── setup.sh
├── src/                    # Core application layer codebase
│   ├── agent/              # Orchestration brain & OpenClaw engine runtime
│   │   ├── AGENTS.md       # Behavioral context instructions
│   │   ├── IDENTITY.md     # Agent identity persona definitions
│   │   ├── SOUL.md         # Operational constraints and logic bounds
│   │   ├── TOOLS.md        # Declared tool execution schemas
│   │   ├── llm_client.py   # Decoupled interface for the Groq inference gateway
│   │   ├── main.py         # Primary orchestration execution entrypoint
│   │   └── openclaw.config.js # OpenClaw platform parameters
│   ├── frontend/           # Presentation layout files
│   ├── ingestion/          # Core vector extraction utilities
│   │   └── parse_corpus.py # Script mapping raw data into vector spaces
│   └── mcp-server/
│       └── tools/          # Model Context Protocol boundary interface tools
├── .env.example            # Blueprint for environment variables (not committed)
├── .gitignore              # Protects secrets (.env) and caches from reaching GitHub
├── .python-version         # Pinpoints the exact Python runtime version for uv
├── docker-compose.yml      # Defines database containers (PostgreSQL + Qdrant)
├── pyproject.toml          # Project configuration and package requirements
└── uv.lock                 # Deterministic locked dependency graph for reproducibility
```

---

## ⚙️ VPS Resource Optimization & Resiliency (Crucial)

Standard AWS Free Tier instances launch with a baseline default configuration of an 8GB storage drive and 1GB of physical hardware RAM.

Because modern deep-learning libraries (like PyTorch, Hugging Face Hub, and tokenizers) generate high memory matrix peaks during initial script execution, running an ingestion engine on a raw 1GB system will cause the Linux kernel to immediately crash the process with an Out Of Memory: Killed termination.

To secure absolute stability, the target VPS environment has been optimized using the following operations:

### 1. Expanding the Physical Hard Drive (From 8GB to 20GB)
1. Go to the AWS EC2 Console $\rightarrow$ **Instances** $\rightarrow$ Select your instance.
2. Click the **Storage** tab at the bottom $\rightarrow$ click the **Volume ID** link.
3. Select the volume $\rightarrow$ **Actions** $\rightarrow$ **Modify Volume**. Change Size from 8 to 20 and save.
4. Run these terminal commands to force Ubuntu to claim the newly allocated physical cloud space:
   ```bash
   sudo growpart /dev/nvme0n1 1
   sudo resize2fs /dev/root
   ```
5. Confirm expansion success by running `df -h`. Your `/dev/root` partition should now show 12G+ of free space.

### 2. Allocating a 2GB Emergency Virtual RAM Swap File
Run these commands sequentially to use a small fraction of your new disk space as backup memory:
```bash
# Allocate a 2 Gigabyte layout file on disk
sudo fallocate -l 2G /swapfile

# Set restrictive read/write flags for system core safety
sudo chmod 600 /swapfile

# Format the allocated partition space into Linux Swap format
sudo mkswap /swapfile

# Enable the virtual swap memory runtime loop
sudo swapon /swapfile

# Make the configuration permanent across system reboots
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```
Verify activation by running `free -h`. The `Swap:` row will confirm 2.0Gi of active virtual breathing room.

---

## 🛠️ Step-by-Step Configuration Guide

Follow these sequential steps to deploy, configure, sync, and run the entire environment from absolute scratch.

### Step 1: Clone the Codebase
```bash
git clone https://github.com/gulatikanan/agentic-api-conformance-checker.git
cd agentic-api-conformance-checker
```

### Step 2: Set Up Local Secrets Environment
Generate your live runtime configuration mapping profile:
```bash
cp .env.example .env
```
Open the newly generated `.env` file and insert your valid API tokens:
```plaintext
LLM_PROVIDER=groq
LLM_API_KEY=gsk_your_secret_production_key_here
```

### Step 3: Run the Multi-Container Infrastructure
Launch your isolated background services (Qdrant Vector Database + PostgreSQL) in detached background daemon mode:
```bash
docker compose up -d
```
To verify that both engines are running healthily, run `docker ps`. You will see Qdrant serving on port `6333` and PostgreSQL on port `5432`.

### Step 4: Synchronize Python Virtual Environment & Dependencies
Initialize and install the locked project workspace using the fast package sync manager `uv`:
```bash
# Creates the local virtual environment and installs exact deterministic package versions
uv sync
```

### Step 5: Run Ingestion Pipeline (Seeding the Vector DB)
Run the ingestion core framework using unbuffered processing output (`-u`). This script automatically extracts entries from the OWASP API Top 10, OWASP ASVS 4.0.3, and Zalando REST Guidelines, segments them into high-granularity contextual slices, computes dense geometric structures using a local embedding matrix (`all-MiniLM-L6-v2`), and seeds your database:
```bash
.venv/bin/python -u src/ingestion/parse_corpus.py
```
Expected Successful Output Log:
```plaintext
🧠 Loading local sentence-transformers model...
📡 Connecting to Qdrant at http://localhost:6333...
🛠️ Creating/Resetting Qdrant collection: 'compliance_rules'...
📖 Parsing OWASP API Top 10 Markdown files...
📊 Parsing OWASP ASVS 4.0.3 CSV...
📐 Parsing Zalando REST Guidelines AsciiDoc files...
✅ Extraction finished! Total generated rule chunks: 414
🚀 Vectorizing chunks and seeding Qdrant collection 'compliance_rules'...
   📥 Pushed chunks 0 to 50 into Qdrant...
   ...
   📥 Pushed chunks 400 to 414 into Qdrant...

🎯 DATABASE SEEDING COMPLETE! Your Vector Database is fully populated.
```

### Step 6: Verify Upstream AI Inference Brain Access
Confirm that your local system can establish network loops and authentications with the Groq inference endpoint using the diagnostic decoupled module wrapper:
```bash
uv run python -c "from src.agent.llm_client import AgentBrain; print('Brain Response:', AgentBrain().generate('Say connection verified'))"
```
Expected Output:
```plaintext
Brain Response: connection verified
```

---

## 📊 Evaluation Rubric Progress

| Requirement Component | Total Score Weights | Active Status |
| :--- | :--- | :--- |
| **Infrastructure & Deploy** (VPS host config, data persistence, and README replication checks) | 20 Marks | Passed & Completed ✅ |
| **RAG & Retrieval** (Granular corpus chunking, vector embedding generation, database seeding) | 20 Marks | Passed & Completed ✅ (414 Rules Live) |
| **MCP Boundary** (Strict access abstraction layers via custom standalone tools) | 25 Marks | 🔄 In Engineering Phase |