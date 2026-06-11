# 🛡️ Agentic API Conformance Checker (OpenClaw + FastMCP Architecture)

An enterprise-grade, automated security and architecture compliance compliance-auditing framework. This platform ingests raw OpenAPI/Swagger schemas or custom API markdown document specifications, routes them through a specialized AI reasoning core governed by rigorous local guardrails, validates endpoint structural signatures against vector-embedded compliance engines (OWASP API Top 10, OWASP ASVS 4.0.3, and Zalando REST Guidelines), and logs multi-dimensional telemetry reports to a localized PostgreSQL data warehouse for visualization.

## 🏗️ Core System Architecture

The application decouples ingestion, real-time agentic reasoning, tool orchestration, and analytical storage into isolated, modular boundaries:
* **Cognitive Controller Layer:** Managed via OpenClaw Gateway Daemon. It isolates the LLM's behavioral prompt configurations into declarative state files (`IDENTITY.md`, `SOUL.md`, `AGENTS.md`).
* **Tool & Context Discovery Layer:** Formulated over the Model Context Protocol (MCP) using a high-performance Python FastMCP server communicating via standard I/O pipes.
* **Vector Space (RAG Engine):** Powered by an offline Qdrant instance. Text blocks are mapped into 384-dimensional mathematical arrays via local CPU sentence-transformers (`all-MiniLM-L6-v2`).
* **Relational Storage Matrix:** PostgreSQL stores final audit verdicts (PASS, FAIL, ABSTAIN) and exact semantic distance parameters for frontend rendering.

## 🛠️ Senior Architecture & Protocol Engineering Decisions

To stabilize execution loops on resource-constrained host infrastructure (e.g., 1GB RAM cloud nodes), the following production‑grade optimization layers were implemented:
* **Lazy Module Importing & Loading:** Massive ML frameworks (`torch`, `sentence_transformers`) are completely deferred and imported *locally inside the tool boundary function* rather than at the global file scope. This minimizes base process initialization latency from >30 seconds down to **under 50 milliseconds**, cleanly passing strict MCP client handshake timeout gates.
* **Standard I/O Stream Isolation:** Framework output streams, Hugging Face download telemetry, and HTTPX logs are trapped and explicitly redirected to `sys.stderr`. This leaves the primary data channel (`sys.stdout`) 100% pristine for structured JSON‑RPC data packets, preventing protocol pollution.
* **Modernized Vector Querying:** Migrated from legacy, deprecated client search methods to Qdrant's atomic `.query_points()` client API layer to guarantee long‑term dependency stability and prevent attribute runtime execution faults.

## ⚡ Quick Deployment & Data Ingestion (One‑Click)

The codebase ships with native DevSecOps automation wrappers inside the `scripts/` directory to guarantee deterministic deployment stabilization and repeatable ingestion lifecycles.

### 1️⃣ Clone and Environment Initialization

Clone the repository to your host VPS or local machine and configure your structural credentials within the environment context:
```bash
# Clone the workspace repository
git clone https://github.com/gulatikanan/agentic-api-conformance-checker.git
cd agentic-api-conformance-checker

# Initialize your environment secrets mapping
cp .env.example .env

# Edit .env to populate your GEMINI_API_KEY, POSTGRES_URL, and QDRANT_URL
nano .env
```

### 2️⃣ Infrastructure Redeployment
Run the unified setup script. This script automatically provisions your background database containers (PostgreSQL and Qdrant) via Docker Compose, validates package managers, and hooks into uv to cleanly compile and synchronize the virtual runtime dependencies:
```bash
chmod +x scripts/*.sh
./scripts/setup.sh
```

### 3️⃣ Knowledge Base Re‑Ingestion (RAG Seeding)
To rebuild or refresh the vector database knowledge collections, trigger the specialized parsing runner. This engine completely wipes the target Qdrant collection, parses the raw text corpus, computes local structural embeddings, and stream‑pushes the points into your vector engine:
```bash
./scripts/ingest.sh
```

### 4️⃣ Daemon Cycle & Verification
Initialize or hot‑reload your active OpenClaw Systemd service background daemon process to lock in configuration streams and verify network service port availability (18789):
```bash
./scripts/restart.sh
```

🛡️ **Critical Guardrails & Behavioral Compliance**
The core engine is bound to a strict mathematical threshold gate defined inside the immutable operational context boundaries (`src/agent/SOUL.md`):

*The 0.45 Similarity Threshold Gate:* The `find_rules` MCP search pipeline dynamically compares vector cosine values. If the dense distance metric falls below 0.45, the system intercepts execution loops and issues a definitive **ABSTAIN** verdict labeled *no rule found* — flagged for human review to block artificial hallucinations.

*Verbatim Citations:* For all PASS or FAIL verdicts, the engine requires verbatim text extractions and source records from the vector payloads to prove compliance claims.

## 📋 Environment Configuration Reference (.env)
Ensure the following system variables are exported within your local host runtime configuration:
```dotenv
# Core AI Inference Secrets
LLM_PROVIDER=gemini
GEMINI_MODEL="gemini-1.5-flash"  # Flash is highly recommended to handle high‑throughput, free‑tier rate limits
GEMINI_API_KEY=AIzaSy...

# Operational Infrastructure Ports & Coordinates
QDRANT_URL=http://localhost:6333
QDRANT_COLLECTION=compliance_rules
POSTGRES_URL=postgresql://postgres:postgrespassword@localhost:5432/conformance_checker

# Algorithmic Safety Rails
SIMILARITY_THRESHOLD=0.45
```

## 📈 System Health & Maintenance Commands
```bash
# View live output logs of the background OpenClaw service
sudo journalctl -u openclaw.service -f -n 100

# Inspect local database tables structure directly within the container
docker exec -it agentic-api-conformance-checker-db-1 psql -U postgres -d conformance_checker -c "\dt"

# Manually trigger an audit run via the OpenClaw Agent CLI
openclaw agent --agent main --prompt "Analyze standard security posture for specifications inside data/target_spec.json"
```