# Agentic API Conformance Checker

The Agentic API Conformance Checker is an intelligent, automated testing framework designed to analyze, ingest, and verify API implementations against formal specifications. By leveraging agentic AI workflows, semantic search, and vector databases, it automatically checks conformance, identifies discrepancies, and ensures robust compliance with security and design standards.

## 🚀 Architecture & Strategy

This project implements a **decoupled LLM client strategy** inside `llm_client.py`. Instead of tightly coupling the agentic engine to a specific provider, the LLM is treated as an abstracted infrastructure service. 

While the system is natively designed to integrate open-weight models, we route reasoning workloads through the high-performance **Groq API** (`llama-3.3-70b-versatile`). This design choice isolates the core application code from upstream API variations, provides error isolation, and allows seamless, single-variable model swapping without modifications to the codebase.

---

## 📊 Project Status & Roadmap

- [x] **Phases 1–3: Core Infrastructure Setup**
  - Provisioned and configured a persistent AWS EC2 deployment server.
  - Initialized Docker environment housing active, healthy Qdrant and PostgreSQL containers.
  - Finalized production-grade GitHub repository sync with strict secret protection (`.gitignore` rules for `.env`).
- [x] **System Integration: Decoupled LLM Gateway**
  - Engineered a production-ready `llm_client.py` client using standard environment configuration.
  - Integrated Groq cloud engine utilizing the optimized `llama-3.3-70b-versatile` model.
  - Validated upstream network access and interface connectivity directly through the module.
- [ ] **Phase 4: Corpus — Download and Verify** 🔄 *[Next Step]*
  - Execute automated shell utilities (`corpus/download.sh`) to retrieve raw policy markdown and HTML components (OWASP ASVS, OWASP API Top 10, and Zalando Guidelines).
  - Verify data ingestion limits via line-count profiling (`wc -l`).
- [ ] **Phase 5: Postgres — Schema Configuration**
  - Run local relational database migration to execute the structured layout for the tracking engines (`checks` and `findings` tables).
- [ ] **Phase 6: Pre-Coding Verification & Tool Building**
  - Complete the exhaustive environment health checklist.
  - Code the core Model Context Protocol (MCP) server routing capabilities.

---

## 🛠 Tech Stack

| Component | Technology | Role in System |
| :--- | :--- | :--- |
| **Orchestration/Engine** | Python 3.11 / `uv` | Dependency isolation and core logic runtime. |
| **AI inference Gateway** | Groq (`llama-3.3-70b-versatile`) | Cloud reasoning brain for artifact analysis. |
| **Vector Database** | Qdrant | Semantic storage and snippet contextual retrieval. |
| **Relational Database** | PostgreSQL | Multi-table operational logging and persistence. |
| **Protocol Layer** | Model Context Protocol (MCP) | Secure communication channel for agent tool interaction. |
| **Deployment Layer** | Docker & AWS EC2 | High-availability hosting platform. |

---

## ⚙️ Quick Start

### 1. Configuration
Establish local secrets by modifying the key distribution manifest:
```bash
cp .env.example .env
```
Ensure your configuration keys match your environment variables in `.env`:
```plaintext
LLM_PROVIDER=groq
LLM_API_KEY=gsk_your_secret_production_key
```

### 2. Service Orchestration
Bring up the multi-container data layer in background daemon mode:
```bash
docker compose up -d
```

### 3. Dependency Synchronization
Sync and resolve the project-wide lock file requirements natively with uv:
```bash
uv sync
```

### 4. Core Connectivity Validation
Assert live communication with the Groq inference cloud inline using an on-the-fly execution command (no test files required):
```bash
uv run python -c "from llm_client import AgentBrain; print('Brain Response:', AgentBrain().generate('Say connection verified'))"
```

---

## 📁 Repository Structure
```plaintext
.
├── corpus/                 # Compliance guidelines and raw text documents
│   └── raw/                # Targeted ingestion home for OWASP/Zalando definitions
├── docs/                   # Project design documentation and assignment specifications
├── qdrant/                 # Vector store volume persistence and configurations
├── scripts/                # Operational scripts (setup, restart, ingestion)
├── src/                    # Core codebase for the agent and tool definitions
├── .env.example            # Blueprint for environment variables (not committed)
├── .gitignore              # Protects secrets (.env) and caches from reaching GitHub
├── .python-version         # Pinpoints the exact Python runtime version for uv
├── docker-compose.yml      # Defines database containers (PostgreSQL + Qdrant)
├── llm_client.py           # Decoupled interface for the Groq inference engine
├── main.py                 # Primary entrypoint for application execution
├── pyproject.toml          # Project configuration and package requirements
├── README.md               # Current documentation, roadmap, and quick-start guide
└── uv.lock                 # Deterministic locked dependency graph for reproducibility
```