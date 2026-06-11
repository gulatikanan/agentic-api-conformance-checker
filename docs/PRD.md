# Product Requirements Document (PRD)
Project Title: Agentic API Conformance Checker
Version: 1.1 (Aligned with Groq + Python FastMCP Infrastructure)

## 1. Problem Statement
Modern software development heavily relies on APIs, which must conform to security, design, and performance standards. However, manually verifying API specifications (OpenAPI, Swagger, custom JSON/YAML schemas, or Markdown files) against industry-standard guidelines is labor-intensive, error-prone, and slow. Developers need a way to automatically and intelligently verify their API definitions against guidelines like OWASP ASVS, OWASP API Top 10, and Zalando REST Guidelines to catch flaws before code is deployed.

## 2. Goals and Non-Goals
### Goals
- Provide an automated, intelligent (agent-driven) conformance checking pipeline for API specifications.
- Leverage Retrieval-Augmented Generation (RAG) to dynamically map submitted API designs to relevant sections of industry-standard security and design guidelines.
- Offer actionable feedback with precise citations (rule passages) and verdicts (Pass, Fail, Warn, Abstain).
- Persist test execution history for audits and team visibility.
- Include a transparency panel (Rule-Retrieval Inspector) in the frontend for developers to see exactly why an operational decision was reached.

### Non-Goals
- Real-time active scanning/fuzzing of live API endpoints in production (v1 is focused purely on specification and design-level conformance checking).
- Auto-fixing or refactoring the API specs directly in the source repository (the system only reports findings).
- General-purpose LLM chat interface unrelated to API conformance checking.

## 3. Target Users
- **Backend Developers**: Want quick verification that their proposed API spec complies with company and security policies.
- **Security Engineers / Auditors**: Want to verify that third-party or internal API specifications do not violate security principles (e.g., OWASP API Top 10) before approval.
- **API Architects**: Wish to ensure consistent design guidelines (e.g., Zalando REST Guidelines) across various teams.

## 4. Core Features
### 4.1. Artifact Submission
Users can submit API artifacts (OpenAPI specs, JSON schemas, YAML files, or Markdown documentation) via a drag-and-drop or text area input in the frontend interface.

### 4.2. Agentic Inspection via MCP
The agent utilizes the Model Context Protocol (MCP) tool `inspect_artifact` to parse, dissect, and build an abstract semantic understanding of the uploaded specification.

### 4.3. RAG-Based Rule Retrieval
The agent queries the vector database using the MCP `find_rules` tool to search for rules and guidelines relevant to the API design. The lookup runs across local embedded collections of OWASP ASVS 4.0.3, OWASP API Top 10, and Zalando REST Guidelines.

### 4.4. Findings Report & Verdicts
The agent compiles a comprehensive findings report. Each finding must include:
- **Verdict**: Pass, Fail, Warn, or Abstain.
- **Cited Rule**: The rule name or ID (e.g., OWASP API1:2023 Broken Object Level Authorization).
- **Rule Passage**: The exact text segment retrieved from the reference guidelines.
- **Abstention Constraint**: If no rule in the database is applicable to the endpoint or pattern under review, the agent must output an `Abstain` verdict with the explanation: `"no rule found — flagged for human review"`.

### 4.5. Rule-Retrieval Inspector Panel
An inspector interface in the frontend display that shows the retrieved rule passages, reference details, and the exact cosine similarity scores computed by the vector database for each finding.

### 4.6. Persistent Storage
All conformance checks, metadata, findings, verdicts, retrieved rule passages, and similarity scores are stored in a PostgreSQL database for historical access and analysis.

## 5. Functional Requirements (FR)
- **FR-1: Upload and Validation**
  - The system must accept YAML, JSON, and Markdown formats up to 2MB in size.
  - The frontend must validate that the submitted text or file is not empty before initiating the check.
- **FR-2: MCP Artifact Parser**
  - The Python-based MCP server must expose an `inspect_artifact(content, type)` tool.
  - The tool must parse the schema to identify endpoints, request/response structures, authorization methods, and parameters.
- **FR-3: MCP Rule Matcher**
  - The Python-based MCP server must expose a `find_rules(topic)` tool.
  - The tool must query Qdrant to retrieve the top $K$ rule passages related to the topic, automatically computing 384-dimensional dense vectors on the fly using local `all-MiniLM-L6-v2` matrices.
- **FR-4: Agent Decision-Making Loop**
  - The OpenClaw agent must coordinate the workflow:
    - Invoke `inspect_artifact` on the submission.
    - Identify candidate rule topics (e.g., "rate limiting", "ID format", "authentication").
    - Invoke `find_rules` for each topic.
    - Compare the specification structure against the retrieved rules.
    - Generate the verdict, reasoning, and cited passage.
- **FR-5: Abstention Threshold**
  - If the vector search returns similarity scores below a configurable threshold (e.g., 0.70), the agent must classify the rule check as an `Abstain` rather than hallucinating a compliance rule.
- **FR-6: Findings Persistency**
  - The system must save each check with a unique UUID in PostgreSQL.
  - The findings table must store `check_id`, `verdict`, `rule_citation`, `rule_passage`, and `similarity_score` in a relational layout containing JSONB arrays for alternative evaluations.
- **FR-7: Frontend Results Display**
  - The user interface must present a dashboard card for each finding, color-coded by verdict (Green for Pass, Red for Fail, Yellow for Warn, Grey for Abstain).
  - An expandable "Inspector Panel" must display the raw retrieval results from the vector store and the exact vector similarity scores.

## 6. Non-Functional Requirements (NFR)
- **NFR-1: Service Longevity**
  - The deployment must be stable enough to remain live and responsive for at least 7 consecutive days without intervention or manual restarts.
- **NFR-2: Cost Efficiency & Resource Resilience**
  - The application stack must run within free-tier bounds or open-source local services.
  - Reasoning workloads must be routed through the Groq API Cloud Gateway using the optimized, free-credit model `llama-3.3-70b-versatile`.
  - Ingestion and local embedding computation must execute on the host CPU. To guarantee absolute runtime stability within a 1GB hardware memory ceiling, the host VPS must be provisioned with a 20GB EBS Volume and an active 2GB Linux Swap Space file to prevent Out-Of-Memory (OOM) termination.
- **NFR-3: Quick Redeploy and Re-Ingest**
  - Setup, deployment, and ingestion of the reference corpus must be fully scriptable and complete in ~10 minutes or less on a fresh AWS EC2 instance.
- **NFR-4: Error Resilience**
  - The system must implement retry-on-rate-limit logic using jittered exponential backoff for the Groq API gateway to handle upstream network throttling gracefully.

## 7. Out of Scope for v1
- Integration with CI/CD systems (GitHub Actions, GitLab CI) as a blocking gate check.
- Automated remediation or rewriting of the specification code.
- Interactive multi-turn chat with the agent regarding the findings (results are static once generated).
- Custom guideline ingestion via the frontend UI (ingestion remains dedicated to backend scripts).

## 8. Success Metrics

| Metric | Target Boundary | Implementation Validation |
| :--- | :--- | :--- |
| **Ingestion Efficiency** | $\le$ 5 minutes | Complete parsing and vector initialization of all 414 chunks. |
| **Checker Latency** | $\le$ 20 seconds | Full conformance check and report delivery via Groq cloud execution speeds. |
| **Citation Accuracy** | 100% | Zero hallucination of citations; all findings link to real vector entries or yield an Abstain verdict. |
| **Script Automation** | 100% Success | Unattended execution of deployment parameters on standard Ubuntu environments. |
