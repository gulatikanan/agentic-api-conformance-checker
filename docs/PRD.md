# Product Requirements Document (PRD)

## Project Title: Agentic API Conformance Checker
**Version:** 1.2 (Aligned with OpenClaw Core, Google Gemini, and FastMCP Infrastructure)

---

## 1. Problem Statement

Modern software development heavily relies on APIs, which must conform to strict security, design, and performance standards. However, manually verifying API specifications (OpenAPI, Swagger, custom JSON/YAML schemas, or Markdown files) against industry‑standard guidelines is labor‑intensive, error‑prone, and slow.

Developers and security engineers need an automated, intelligent way to evaluate their API design definitions against complex regulatory frameworks like OWASP ASVS, OWASP API Top 10, and Zalando REST Guidelines to discover structural design flaws and vulnerabilities before code ever hits production.

---

## 2. Goals and Non‑Goals

### Goals
- Provide an automated, agent‑driven conformance‑checking pipeline for uploaded API specifications.
- Leverage Retrieval‑Augmented Generation (RAG) to dynamically extract and cross‑reference submitted API designs against sections of security and compliance guideline books.
- Offer granular, actionable audit feedback with exact verbatim citations and structural verdicts (`PASS`, `FAIL`, `ABSTAIN`).
- Persist complete test execution histories and metrics natively in a relational database for auditing and team dashboard tracking.
- Eliminate model guessing and hallucinations by implementing an exact mathematical similarity‑threshold boundary mechanism.

### Non‑Goals
- Real‑time active dynamic fuzzing or network‑level scanning of live API endpoints in production (the platform focuses strictly on design and specification‑level security compliance checks).
- Automated code refactoring or rewriting of the specification files directly in source control (the framework reports findings but does not alter source files).
- Multi‑turn conversational chat interfaces unrelated to explicit compliance validation.

---

## 3. Target Users
- **Backend Developers:** Want rapid verification that their proposed API routes conform to organizational security policies before opening pull requests.
- **Security Engineers & Auditors:** Need to verify that internal or third‑party vendor API schemas do not violate structural safety foundations before authorizing deployments.
- **API Architects:** Wish to guarantee design uniformity (e.g., standard path formatting, encrypted parameter structures) across multiple distributed product teams.

---

## 4. Core Features

### 4.1. Asset Submission Interface
Users can submit API specification artifacts (OpenAPI JSON/YAML objects or text‑based Markdown route documentation) via the web‑based frontend application interface.

### 4.2. Declarative Prompt Configuration Matrix
The agent’s cognitive persona and operational constraints are managed via a clean, declarative text system using individual markdown documents read natively by the execution core:
- **IDENTITY.md:** Establishes the elite security compliance auditor persona.
- **SOUL.md:** Implements rigid operational guardrails, watches for specific flaws (BOLA, unencrypted parameters), and defines the similarity fallback boundaries.
- **AGENTS.md:** Outlines the sequential orchestration loop mapping (Extract → Retrieve → Evaluate → Save).

### 4.3. Dynamic MCP Tool Discovery Layer
The system couples the reasoning brain to local host infrastructure tools using the Model Context Protocol (MCP) driven by a standard Python FastMCP server communicating over standard I/O pipes.

### 4.4. Algorithmic Abstention Gate
The system enforces a hard **0.45** Cosine Similarity safety rail. If a vector search query against the knowledge base fails to produce any compliance rules with a score greater than or equal to **0.45**, the system blocks the LLM from inventing policies and mandates a strict **ABSTAIN** verdict with the reason: `no rule found — flagged for human review`.

### 4.5. Telemetry Tracking & Relational Storage
All execution metrics, overall file summary stats, and endpoint‑level findings are captured natively via relational SQL storage configurations to power long‑term analytics dashboards.

### 4.6. DevSecOps One‑Click Automation
The workspace implements a structured Bash automation suite inside the `scripts/` folder to enable seamless environment synchronization and database lifecycle caching:
- **setup.sh:** Builds databases and syncs Python dependencies via `uv`.
- **ingest.sh:** Re‑calculates local rule text vectors and populates the database.
- **restart.sh:** Frees orphaned network process blocks and cycles the background system daemons.

---

## 5. Functional Requirements (FR)

- **FR‑1:** Upload Handling & Content Validation – The system must accept raw input text string objects up to **2 MB** in size and validate that submissions are structurally populated before dispatching requests to the background orchestration loops.
- **FR‑2:** FastMCP Structure Parsing Engine (`inspect_artifact`) – Must ingest raw specification content strings, evaluate syntax patterns, and discover paths, routes, parameters, and active authentication protocols.
- **FR‑3:** FastMCP Vector RAG Matcher (`find_rules`) – Must compute local embeddings using **all‑MiniLM‑L6‑v2** (384‑dimensional), execute cosine‑similarity lookups across the seeded `compliance_rules` collection, and filter out results below the global **0.45** threshold.
- **FR‑4:** Agent Orchestration Execution Loop – OpenClaw daemon (`openclaw.service`) must coordinate the flow: extract via `inspect_artifact` → map to semantic search blocks → query RAG via `find_rules` → pass context to Google Gemini (`gemini-3.1-pro-preview`, temperature 0.1) → compute verdicts → store via `save_conformance_check`.
- **FR‑5:** Robust Data Ingestion and Normalization – `save_conformance_check` must implement defensive parsing; if the reasoning core updates output payload formats, the ingestion loop must intercept and normalize variations (e.g., cross‑mapping `endpoint` to `rule_title`, `reason` to `details`) to guarantee that database cells never receive broken NULL keys.

---

## 6. Non‑Functional Requirements (NFR)

- **NFR‑1:** Service Continuity & Longevity – Background OpenClaw daemon and container dependencies must remain live, responsive, and leak‑free for a minimum of **7 days** of deployment without human intervention or server restarts.
- **NFR‑2:** Efficient Resource Footprint – Prioritize highly scalable open‑source modules over costly cloud endpoints where possible. Vector extractions and text chunking loops must run locally on the host CPU. Deploy on a **20 GB** EBS volume with a **2 GB** Linux Swap file to prevent OOM termination.
- **NFR‑3:** Quick Redeployment Bounds – Complete infrastructure setup, dependency compilation via `uv`, and dense embedding parsing of the full **414‑chunk** compliance corpus must execute in **≤ 5 minutes** on a fresh host using the automation scripts.

---

## 7. Out of Scope for v1
- Live integration into automated CI/CD pipeline blocking gates (e.g., active GitHub Actions blocker checks).
- Direct automated write‑back corrections to alter specification source code files natively inside active user repositories.
- Multi‑user, multi‑tenant access control logic or organization‑space separations inside the database models.

---

## 8. Performance & Success Metrics

| Evaluation Metric                     | Target Threshold | Boundary Validation Method |
|--------------------------------------|------------------|----------------------------|
| **Ingestion Pipeline Efficiency**    | ≤ 5 minutes      | Measure total parsing, embedding generation, and vector seeding time via `ingest.sh`.
| **Audit Execution Latency**          | ≤ 20 seconds     | End‑to‑end conformance check timing from upload to report generation.
| **Data Contract Ingestion Accuracy** | 100 %            | Verify that database tables receive fully populated rows with no broken NULL values.
| **Citation Soundness**               | 100 %            | Ensure every PASS/FAIL finding links to a verbatim guideline string; otherwise, ABSTAIN.
| **Deployment Automation Success**    | 100 %            | Unattended execution of deployment scripts across identical Ubuntu targets.
