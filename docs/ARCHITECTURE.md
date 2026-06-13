# System Architecture - Agentic API Conformance Checker

This document describes the high-level architecture, primary data flows, components, and key design decisions of the Agentic API Conformance Checker.

## 1. High-Level System Diagram

Below is the architectural mapping of the core components and their protocol interactions:

```plaintext
                  +-----------------------------------------------+
                  |                   Frontend                    |
                  |        (Next.js + shadcn/ui App Router)       |
                  +-------+-------------------------------^-------+
                          |                               |
                1. Submit |                               | 6. Read Results
                Artifact  |                               |    & Passages
                          v                               |
                  +-------+-------------------------------+-------+
                  |               OpenClaw Agent                  |
                  |                (AWS EC2 VM)                   |
                  +-------+-------------------------------+-------+
                          |                               |
             2. Inspect   |                               | 5. Persist
                Artifact  |                               |    Findings
             3. Find      v                               |
                Rules   +---------------------------------+-------+
                        |               MCP Server                |
                        |            (Python / FastMCP)           |
                        +---+-------------------------+-----------+
                            |                         |
                 Vector DB  |                         | Parse
                 Queries    v                         v Artifacts
                 +----------+----------+        +-----+-----------+
                 |  Vector Store (MCP) |        | Artifact Parser |
                 +----------+----------+        +-----------------+
                            |
                 Requires   |
                 Embeddings v
                 +----------+----------+        +-----------------+
                 |  Local Transformer  |        |Google Gemini API|
                 | (all-MiniLM-L6-v2)  |        |   (Inference)   |
                 +---------------------+        +-----------------+

       ================== DOCKER COMPOSE INFRASTRUCTURE ==================
       =  Both services run on a shared network ('backend-network')      =
       =                                                                 =
       =   +-----------------------+           +---------------------+   =
       =   |       Qdrant DB       |           |     PostgreSQL      |   =
       =   |    (Vector Store)     |           |    (Relational)     |   =
       =   +-----------------------+           +---------------------+   =
       ===================================================================
```

## 2. Primary Flows

### 2.1. Ingestion Flow
The ingestion flow is responsible for preparing, chunking, and seeding the security and compliance guidelines into the vector database.

```
+--------------+     +-------------+     +--------------------+     +-------------+
| Corpus Files | --> |   Chunker   | --> | Local Embeddings   | --> |  Qdrant DB  |
| (OWASP, etc) |     | (Markdown)  |     | (all-MiniLM-L6-v2) |     | (Vector-DB) |
+--------------+     +-------------+     +--------------------+     +-------------+
```
Corpus Source: Markdown, CSV, and AsciiDoc guideline files (OWASP ASVS 4.0.3, OWASP API Top 10, Zalando REST Guidelines) are pulled natively from `corpus/raw/`.

- **Chunker**: Files are parsed and split into highly granular, semantic chunks to preserve contextual metadata.
- **Embedding Generation**: Vectors are computed locally on the host CPU using the native Python `sentence-transformers` framework running the `all-MiniLM-L6-v2` topology (generating highly efficient 384-dimensional dense vectors).
- **Vector Storage**: The resulting vector matrices, along with raw payload strings and contextual titles, are written over standard connections directly into the Qdrant `compliance_rules` collection.

### 2.2. Conformance Check Flow
The verification execution pipeline operates in a live loop when an API specification asset is submitted.

1. **Submission**: The user uploads an API artifact (OpenAPI JSON/YAML spec) through the Next.js frontend web interface.
2. **Orchestration Lifecycle**: The frontend initiates a live analysis process inside the OpenClaw agent runtime and instantiates a state record inside the PostgreSQL database.
3. **Artifact Inspection**: The OpenClaw agent invokes the MCP server's `inspect_artifact` tool boundary to flatten the endpoint schemas, parameters, and structural design signatures.
4. **Rule Matching**: The agent identifies structural security topics and requests compliance context by calling the MCP server's `find_rules` tool.
5. **RAG Retrieval**: The MCP server computes vector dimensions of the search query locally, runs a cosine distance lookup against Qdrant, and relays matching clauses and similarity scores back across the protocol boundary to OpenClaw.
6. **Verdict Formulation**: The OpenClaw engine weighs the custom system instructions (`SOUL.md`) alongside the rules using the native Google Gemini API (`gemini-3.1-pro-preview`).
7. **Report Persistence**: The agent compiles audit assertions into a structured findings object, writes outcomes to the PostgreSQL relational database via the `save_conformance_check` tool, and flushes real-time data straight to the web interface.

## 3. Component Descriptions

### 3.1. Frontend
**Technology Stack**: Next.js (App Router), Tailwind CSS, shadcn/ui.
**Responsibilities**: Renders visual file interfaces and houses the reporting layout to expose real-time similarity metrics and exact clause citations transparently.

### 3.2. Agent (OpenClaw Engine)
**Technology Stack**: OpenClaw platform orchestration framework.
**Hosting**: AWS EC2 Virtual Memory Workspace.
**Responsibilities**: Holds behavioral rules (`IDENTITY.md`, `SOUL.md`, `AGENTS.md`), manages reasoning contexts, and makes final compliance evaluations without ever possessing direct access to database configurations or raw data blocks.

### 3.3. Model Context Protocol (MCP) Server
**Technology Stack**: Python / FastMCP.
**Hosting**: Co‑located natively within the EC2 application runtime layer, communicating via standard I/O pipes.
**Exposed Tools**:
- `inspect_artifact(content, artifact_type)`: Standardizes various API formats into a unified syntax layout representation for the agent.
- `find_rules(topic)`: Abstracts vector lookups, computing local embeddings on the fly and querying the Qdrant instance.
- `save_conformance_check(artifact_name, summary_json, findings_json)`: Persists high‑level master logs and granular violation rows directly to the SQL backend.

### 3.4. Vector Store (Qdrant)
**Technology Stack**: Qdrant Vector Database engine running inside an isolated Docker container.
**Storage**: Mapped to a local host directory volume (`./qdrant/storage/`) to ensure persistence.

### 3.5. Embeddings & Inference Brain
- **Embedding Matrix**: Local host computation running `all-MiniLM-L6-v2` (384 dimensions).
- **LLM Reasoning Brain**: Google Gemini API Core executing `gemini-1.5-pro` processing loops under low temperature (`0.1`) configurations.

### 3.6. Relational Database (PostgreSQL)
**Technology Stack**: PostgreSQL 15 running inside an isolated Docker container.
**Storage**: Persistent host mapping directory (`./postgres/data/`).
**Responsibilities**: Tracks session run metrics, metadata indexes, and audit logs.

## 4. Key Architectural Decisions

### 4.1. Strict Tool Boundaries (MCP‑Only Access)
The OpenClaw agent has zero direct interaction or drivers connected to the underlying databases or vector engines. By forcing all interaction through the Model Context Protocol (MCP), the agent stays decoupled from infrastructure specifications.

### 4.2. Low‑Resource Optimization (Swap Space Resiliency)
To prevent Out‑Of‑Memory (OOM) kernel crashes during vector extraction on limited hardware allocations, a 2 GB Virtual Memory Swap File is configured on the host server disk. This absorbs high execution compilation spikes securely.

### 4.3. Abstention Logic Threshold
Any retrieval results producing similarity scores below a strict **0.45** threshold force an automatic **ABSTAIN** verdict. This restricts the LLM from inventing or guessing policy constraints, defaulting the asset directly to human reviewer flags.

## 5. Live Data Models
The following relational PostgreSQL schemas are automatically initialized by the MCP tool layer at runtime to track audit metrics.

### 5.1. `compliance_checks` Table
Stores high‑level tracking data about a master conformance scan session execution.

| Column Name | Data Type | Constraints |
|-------------|-----------|-------------|
| `id` | SERIAL | PRIMARY KEY |
| `artifact_name` | VARCHAR(255) | NOT NULL |
| `created_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP |
| `summary` | JSONB | NULLABLE |

### 5.2. `check_findings` Table
Stores individual granular compliance endpoints and matching RAG scores linked directly to a parent check record.

| Column Name | Data Type | Constraints |
|-------------|-----------|-------------|
| `id` | SERIAL | PRIMARY KEY |
| `check_id` | INTEGER | REFERENCES `compliance_checks(id)` ON DELETE CASCADE |
| `rule_title` | VARCHAR(255) | NULLABLE |
| `verdict` | VARCHAR(50) | NULLABLE |
| `score` | NUMERIC(5,4) | NULLABLE |
| `details` | TEXT | NULLABLE |
| `rule_passage` | TEXT | NULLABLE |
