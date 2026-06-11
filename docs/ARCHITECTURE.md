# System Architecture - Agentic API Conformance Checker

This document describes the high-level architecture, primary data flows, components, and key design decisions of the Agentic API Conformance Checker.

## 1. High-Level System Diagram

Below is the architectural mapping of the core components and their protocol interactions:

```plaintext
                  +-----------------------------------------------+
                  |                  Frontend                     |
                  |       (Next.js + shadcn/ui on Vercel)         |
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
                 |  Local Transformer  |        |    Groq Cloud   |
                 | (all-MiniLM-L6-v2)  |        |    (Inference)  |
                 +---------------------+        +-----------------+

       ================== DOCKER COMPOSE INFRASTRUCTURE ==================
       =  Both services run on a shared network ('backend-network')      =
       =                                                                 =
       =   +-----------------------+           +---------------------+   =
       =   |       Qdrant DB       |           |     PostgreSQL      |   =
       =   |    (Vector Store)     |           |     (Relational)    |   =
       =   +-----------------------+           +---------------------+   =
       ===================================================================
```

## 2. Primary Flows

### 2.1. Ingestion Flow
The ingestion flow is responsible for preparing, chunking, and seeding the security and compliance guidelines into the vector database.

```plaintext
+--------------+     +-------------+     +--------------------+     +-------------+
| Corpus Files | --> |   Chunker   | --> | Local Embeddings   | --> |  Qdrant DB  |
| (OWASP, etc) |     | (Markdown)  |     | (all-MiniLM-L6-v2) |     | (Vector-DB) |
+--------------+     +-------------+     +--------------------+     +-------------+
```

- **Corpus Source**: Markdown, CSV, and AsciiDoc guideline files (OWASP ASVS 4.0.3, OWASP API Top 10, Zalando REST Guidelines) are pulled natively from `corpus/raw/`.
- **Chunker**: Files are parsed and split into 414 highly granular, semantic chunks to preserve contextual metadata.
- **Embedding Generation**: Vectors are computed locally on the host CPU using the native Python `sentence-transformers` framework running the `all-MiniLM-L6-v2` topology (generating highly efficient 384-dimensional dense vectors).
- **Vector Storage**: The resulting vector matrices, along with raw payload strings and contextual titles, are written over gRPC directly into the Qdrant `compliance_rules` collection.

### 2.2. Conformance Check Flow
The verification execution pipeline operates in a live loop when an API specification asset is submitted.

1. **Submission**: The user uploads an API artifact (OpenAPI JSON/YAML spec) through the Next.js frontend web interface.
2. **Orchestration Lifecycle**: The frontend initiates a live analysis process inside the OpenClaw agent container and instantiates a state record inside the PostgreSQL tracking table.
3. **Artifact Inspection**: The OpenClaw agent invokes the MCP server's `inspect_artifact` tool boundary to flatten the endpoint schemas, parameters, and structural design signatures.
4. **Rule Matching**: The agent identifies structural security topics and requests compliance context by calling the MCP server's `find_rules` tool.
5. **RAG Retrieval**: The MCP server computes vector dimensions of the search query locally, runs a Cosine distance lookup against Qdrant, and relays matching clauses and similarity scores back across the protocol boundary to OpenClaw.
6. **Verdict Formulation**: The OpenClaw engine weighs the custom system instructions (`SOUL.md`) alongside the rules using the cloud-routed Groq API (`llama-3.3-70b-versatile`).
7. **Report Persistence**: The agent compiles audit assertions into a structured findings object, writes outcomes to the PostgreSQL relational database, and flushes real-time logging arrays straight to the web interface.

## 3. Component Descriptions

### 3.1. Frontend
- **Technology Stack**: Next.js (App Router), Tailwind CSS, shadcn/ui.
- **Hosting**: Vercel.
- **Responsibilities**: Renders visual file interfaces and houses the **Rule-Retrieval Inspector Panel** to expose real-time similarity metrics and exact clause citations transparently.

### 3.2. Agent (OpenClaw Engine)
- **Technology Stack**: OpenClaw platform orchestration framework.
- **Hosting**: AWS EC2 Virtual Machine (t3.micro).
- **Responsibilities**: Holds behavioral rules (`IDENTITY.md`, `SOUL.md`), manages reasoning contexts, and makes final compliance evaluations without ever possessing direct access to database configurations or raw data blocks.

### 3.3. Model Context Protocol (MCP) Server
- **Technology Stack**: Python / FastMCP.
- **Hosting**: Colocated natively within the EC2 application runtime layer.
- **Exposed Tools**:
  - `inspect_artifact(content, type)`: Standardizes various API formats into a unified abstract syntax tree representation for the agent.
  - `find_rules(topic)`: Abstracts vector lookups, computing local embeddings on the fly and querying the Qdrant instance.

### 3.4. Vector Store (Qdrant)
- **Technology Stack**: Qdrant Vector Database engine running inside an isolated Docker container.
- **Storage**: Mapped to a local host directory volume (`./qdrant/storage/`) to ensure persistence.

### 3.5. Embeddings & Inference Brain
- **Embedding Matrix**: Local host computation running `all-MiniLM-L6-v2`.
- **LLM Reasoning Brain**: Groq Cloud API Gateway executing `llama-3.3-70b-versatile` processing loops.

### 3.6. Relational Database (PostgreSQL)
- **Technology Stack**: PostgreSQL 15 running inside an isolated Docker container.
- **Storage**: Persistent host mapping directory (`./postgres/data/`).
- **Responsibilities**: Tracks session run metrics, metadata indexes, and audit logs.

## 4. Key Architectural Decisions

### 4.1. Strict Tool Boundaries (MCP-Only Access)
The OpenClaw agent has zero direct interaction or drivers connected to the underlying databases or vector engines. By forcing all interaction through the Model Context Protocol (MCP), the agent stays decoupled from infrastructure specifications.

### 4.2. Low-Resource Optimization (Swap Space Resiliency)
To prevent Out-Of-Memory (OOM) kernel crashes during vector extraction on limited hardware allocations, a 2GB Virtual Memory Swap File is configured on the host server disk. This absorbs high execution compilation spikes securely.

### 4.3. Abstention Logic Threshold
Any retrieval results producing similarity scores below a `0.70` threshold force an automatic `Abstain` verdict. This restricts the LLM from inventing or guessing policy constraints, defaulting the asset directly to a human reviewer flags state.

## 5. Data Models

### 5.1. `checks` Table
Stores high-level metadata about a conformance scan execution.

| Column Name | Type | Description |
| :--- | :--- | :--- |
| `id` | `UUID` (PK) | Unique check execution identifier. |
| `submitted_at` | `TIMESTAMP` | Time when the API spec was submitted. |
| `status` | `VARCHAR` | Current runner status (`pending`, `running`, `completed`, `failed`). |
| `artifact_type` | `VARCHAR` | Type of spec uploaded (`openapi`, `json_schema`, `markdown`). |
| `artifact_hash` | `VARCHAR` | SHA-256 hash of the content to prevent redundant checks. |

### 5.2. `findings` Table
Stores individual compliance findings linked to a parent check.

| Column Name | Type | Description |
| :--- | :--- | :--- |
| `id` | `UUID` (PK) | Unique finding entry identifier. |
| `check_id` | `UUID` (FK) | Reference to `checks.id`. |
| `verdict` | `VARCHAR` | Verdict outcome (`pass`, `fail`, `warn`, `abstain`). |
| `cited_rule` | `VARCHAR` | Reference guideline key / rule ID. |
| `rule_passage` | `TEXT` | Exact text retrieved from the guideline corpus. |
| `similarity_score` | `REAL` | Vector search similarity score returned by Qdrant. |
| `reasoning` | `TEXT` | Detailed textual explanation of the verdict. |
| `retrieved_passages` | `JSONB` | Array of alternative passages evaluated, with their similarity scores. |
