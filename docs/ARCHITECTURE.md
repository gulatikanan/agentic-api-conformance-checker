# System Architecture

This document describes the high-level architecture, primary data flows, components, and key design decisions of the Agentic API Conformance Checker.

---

## 1. High-Level System Diagram

Below is an ASCII representation of the core components and their interactions:

```
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
                        |             (Node.js on EC2)            |
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
                 +----------+----------+
                 |    Ollama Cloud     |
                 +---------------------+

       ================== DOCKER COMPOSE INFRASTRUCTURE ==================
       =  Both services run on a shared network ('backend-network')      =
       =                                                                 =
       =   +-----------------------+           +---------------------+   =
       =   |       Qdrant DB       |           |     PostgreSQL      |   =
       =   |    (Vector Store)     |           |     (Relational)    |   =
       =   +-----------------------+           +---------------------+   =
       ===================================================================

```

---

## 2. Primary Flows

### 2.1. Ingestion Flow
The ingestion flow is responsible for preparing and loading the security and compliance guidelines into the vector database.

```
+--------------+     +-------------+     +-------------------+     +-------------+
| Corpus Files | --> |   Chunker   | --> | Ollama Embeddings | --> |  Qdrant DB  |
| (OWASP, etc) |     | (Markdown)  |     | (nomic-embed-text)|     | (Vector-DB) |
+--------------+     +-------------+     +-------------------+     +-------------+
```

1. **Corpus Source**: Markdown and YAML guideline files (OWASP ASVS, OWASP API Top 10, Zalando REST Guidelines) are read from `corpus/raw/`.
2. **Chunker**: Files are parsed and split into logical, semantic chunks (paragraphs, headings, or rules).
3. **Embedding Generation**: Chunks are sent to the Ollama API using the `nomic-embed-text` model to generate 768-dimensional vector representations.
4. **Vector Storage**: The resulting embeddings, along with the raw text payload, rule metadata, and identifiers, are written to a Qdrant collection.

---

### 2.2. Conformance Check Flow
The check flow executes when a developer submits an API specification for verification.

1. **Submission**: The developer uploads an API artifact (JSON/YAML spec or Markdown) through the Next.js frontend.
2. **Parsing & Analysis Initiation**: The frontend triggers a background run inside the OpenClaw agent and stores a record of the request in the PostgreSQL `checks` table.
3. **Artifact Inspection**: The OpenClaw agent invokes the MCP server's `inspect_artifact` tool. The MCP server parses the API spec structure (paths, parameters, authentication) and returns a structured summary to the agent.
4. **Rule Matching**: The OpenClaw agent identifies key design and security concepts (e.g. rate-limiting, SQL Injection points, JWT authorization) and invokes the MCP server's `find_rules` tool for each concept.
5. **RAG Retrieval**: The MCP server queries the Qdrant database using vectors generated from the query text. Qdrant returns matching rule passages and similarity scores.
6. **Verdict Formulation**: The agent reviews the retrieved rules against the parsed spec content using the Ollama LLM:
   - For each checked item, the agent assigns a verdict (`Pass`, `Fail`, `Warn`, or `Abstain`).
   - If vector search scores are below the similarity threshold, it yields `Abstain` with a placeholder description.
7. **Report & Persistence**: The agent compiles the results into a findings report and writes the outcomes to the PostgreSQL `findings` table.
8. **Visualization**: The frontend reads the database records and displays the report alongside the **Rule-Retrieval Inspector Panel**, showing similarity scores and citations.

---

## 3. Component Descriptions

### 3.1. Frontend
- **Technology Stack**: Next.js (App Router), Tailwind CSS, and shadcn/ui.
- **Hosting**: Deployed on Vercel.
- **Responsibilities**:
  - Provides drag-and-drop file upload.
  - Renders visual status badges for conformance runs.
  - Houses the **Rule-Retrieval Inspector Panel** which displays retrieval context and cosine similarity scores.

### 3.2. Agent (OpenClaw)
- **Technology Stack**: Python-based OpenClaw framework.
- **Hosting**: AWS EC2 instance (t3.micro).
- **Responsibilities**:
  - Orchestrates reasoning loops.
  - Queries rules and inspects schemas exclusively through MCP tool boundaries.
  - Performs LLM evaluation on rule compliance.

### 3.3. Model Context Protocol (MCP) Server
- **Technology Stack**: Node.js / TypeScript.
- **Hosting**: Colocated on the EC2 instance, running as a persistent daemon.
- **Exposed Tools**:
  - `inspect_artifact(content, type)`: Standardizes various API formats (YAML/JSON/Markdown) into a unified abstract syntax tree representation for the agent.
  - `find_rules(topic)`: Handles vector queries to Qdrant, abstracting embedding generation and vector lookup.

### 3.4. Vector Store (Qdrant)
- **Technology Stack**: Qdrant Vector Database.
- **Hosting**: Self-hosted Docker container on AWS EC2, port `6333` (HTTP) and `6334` (gRPC).
- **Storage**: Mapped volume to `./qdrant/storage` on host for persistence.

### 3.5. Embeddings & LLM (Ollama)
- **Models Used**:
  - Embedding: `nomic-embed-text`
  - LLM Reasoning: `llama3` or `mistral`
- **Hosting**: Ollama Cloud / Local Ollama instance.
- **Resilience**: Integrated retry + exponential backoff logic is applied at the client layer to handle Ollama API rate limits and connection resets.

### 3.6. Database (PostgreSQL)
- **Technology Stack**: PostgreSQL 15.
- **Hosting**: Self-hosted Docker container on AWS EC2, port `5432`.
- **Storage**: Mapped volume to `./postgres/data` on host.
- **Responsibilities**: Stores persistent logs of conformance checks, detailed findings, and retrieval metadata.

---

## 4. Key Architectural Decisions

### 4.1. Strict Tool Boundaries (MCP-Only Access)
* **Decision**: The OpenClaw agent has no direct filesystem access, database drivers, or direct HTTP clients for Qdrant. It is decoupled entirely behind Model Context Protocol (MCP).
* **Rationale**: Decoupling the agent from DB drivers and indexing protocols keeps the agent lightweight and secure. Tool implementation changes (e.g. migrating from Qdrant to PGVector) require zero updates to the core agent logic.

### 4.2. Abstention Logic Threshold
* **Decision**: Any retrieval result returning a cosine similarity score below `0.70` (configurable) triggers an automatic `Abstain` verdict.
* **Rationale**: Prevents LLM hallucinations. If the vector space cannot find a matching regulatory or design passage, the agent must decline to verify and flag it for manual review by a human security engineer.

### 4.3. Retry and Backoff Strategy
* **Decision**: All outbound Ollama API requests must implement jittered exponential backoff retrying up to 5 times.
* **Rationale**: Ollama execution (especially on CPU or shared instances) is highly susceptible to context congestion and transient connection drops.

---

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
| `cited_rule` | `VARCHAR` | Reference guideline key/rule ID. |
| `rule_passage` | `TEXT` | Exact text retrieved from the guideline corpus. |
| `similarity_score`| `REAL` | Vector search similarity score returned by Qdrant. |
| `reasoning` | `TEXT` | Detailed textual explanation of the verdict. |
| `retrieved_passages`| `JSONB` | Array of alternative passages evaluated, with their similarity scores. |
