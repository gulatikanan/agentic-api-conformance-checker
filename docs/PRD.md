# Product Requirements Document (PRD)

## Project Title: Agentic API Conformance Checker

---

## 1. Problem Statement
Modern software development heavily relies on APIs, which must conform to security, design, and performance standards. However, manually verifying API specifications (OpenAPI, Swagger, custom JSON/YAML schemas, or Markdown files) against industry-standard guidelines is labor-intensive, error-prone, and slow. Developers need a way to automatically and intelligently verify their API definitions against guidelines like OWASP ASVS, OWASP API Top 10, and Zalando REST Guidelines to catch flaws before code is deployed.

---

## 2. Goals and Non-Goals
### Goals
- Provide an automated, intelligent (agent-driven) conformance checking pipeline for API specifications.
- Leverage Retrieval-Augmented Generation (RAG) to dynamically map submitted API designs to relevant sections of industry-standard security and design guidelines.
- Offer actionable feedback with precise citations (rule passages) and verdicts (Pass, Fail, Warn, Abstain).
- Persist test execution history for audits and team visibility.
- Include a transparency panel (Rule-Retrieval Inspector) in the frontend for developers to see why a decision was reached.

### Non-Goals
- Real-time active scanning/fuzzing of live API endpoints in production (v1 is focused purely on specification and design-level conformance).
- Auto-fixing or refactoring the API specs directly in the source repository (the system only reports findings).
- General-purpose LLM chat interface unrelated to API conformance checking.

---

## 3. Target Users
- **Backend Developers**: Want quick verification that their proposed API spec complies with company and security policies.
- **Security Engineers / Auditors**: Want to verify that third-party or internal API specifications do not violate security principles (e.g., OWASP API Top 10) before approval.
- **API Architects**: Wish to ensure consistent design guidelines (e.g., Zalando REST Guidelines) across various teams.

---

## 4. Core Features

### 4.1. Artifact Submission
- Users can submit API artifacts (OpenAPI specs, JSON schemas, YAML files, or Markdown documentation) via a drag-and-drop or text area input in the frontend interface.

### 4.2. Agentic Inspection via MCP
- The agent utilizes the Model Context Protocol (MCP) tool `inspect_artifact` to parse, dissect, and build an understanding of the uploaded spec.

### 4.3. RAG-Based Rule Retrieval
- The agent queries the vector database using the MCP `find_rules` tool to search for rules and guidelines relevant to the API design (searching across embedded collections of OWASP ASVS, OWASP API Top 10, and Zalando REST Guidelines).

### 4.4. Findings Report & Verdicts
- The agent compiles a comprehensive findings report. Each finding must include:
  - **Verdict**: `Pass`, `Fail`, `Warn`, or `Abstain`.
  - **Cited Rule**: The rule name or ID (e.g., "OWASP API1:2023 Broken Object Level Authorization").
  - **Rule Passage**: The exact text segment retrieved from the reference guidelines.
- If no rule in the database is applicable to the endpoint or pattern under review, the agent must output an `Abstain` verdict with the explanation: `"no rule found — flagged for human review"`.

### 4.5. Rule-Retrieval Inspector Panel
- An inspector interface in the frontend display that shows the retrieved rule passages, reference details, and the similarity scores computed by the vector database for each finding.

### 4.6. Persistent Storage
- All conformance checks, metadata, findings, verdicts, retrieved rule passages, and similarity scores are stored in a PostgreSQL database for historical access and analysis.

---

## 5. Functional Requirements (FR)

1. **FR-1: Upload and Validation**
   - The system must accept YAML, JSON, and Markdown formats up to 2MB in size.
   - The frontend must validate that the submitted text or file is not empty before initiating the check.

2. **FR-2: MCP Artifact Parser**
   - The MCP server must expose an `inspect_artifact(content, type)` tool.
   - The tool must parse the schema to identify endpoints, request/response structures, authorization methods, and parameters.

3. **FR-3: MCP Rule Matcher**
   - The MCP server must expose a `find_rules(topic)` tool.
   - The tool must query Qdrant to retrieve the top $K$ rule passages related to the topic, along with similarity scores.

4. **FR-4: Agent Decision-Making Loop**
   - The OpenClaw agent must coordinate the workflow:
     1. Invoke `inspect_artifact` on the submission.
     2. Identify candidate rule topics (e.g., "rate limiting", "ID format", "authentication").
     3. Invoke `find_rules` for each topic.
     4. Compare the specification structure against the retrieved rules.
     5. Generate the verdict, reasoning, and cited passage.

5. **FR-5: Abstention Threshold**
   - If the vector search returns similarity scores below a configurable threshold (e.g., 0.70), the agent must classify the rule check as an `Abstain` rather than hallucinating a rule.

6. **FR-6: Findings Persistency**
   - The system must save each check with a unique UUID in PostgreSQL.
   - The `findings` table must store `check_id`, `verdict`, `rule_citation`, `rule_passage`, and `similarity_score` in a JSONB format.

7. **FR-7: Frontend Results Display**
   - The user interface must present a dashboard card for each finding, color-coded by verdict (Green for Pass, Red for Fail, Yellow for Warn, Grey for Abstain).
   - An expandable "Inspector Panel" must display the raw retrieval results from the vector store and the exact vector similarity scores.

---

## 6. Non-Functional Requirements (NFR)

1. **NFR-1: Service Longevity**
   - The deployment must be stable enough to remain live and responsive for at least 7 consecutive days without intervention or manual restarts.

2. **NFR-2: Cost Efficiency (Free Tiers Only)**
   - The application stack must run entirely within free tiers or open-source local services (e.g., AWS EC2 free tier, local/self-hosted Ollama for inference and embedding, Docker, and Qdrant). No paid API keys (such as OpenAI or Pinecone) should be strictly required for core functionality.

3. **NFR-3: Quick Redeploy and Re-Ingest**
   - Setup, deployment, and ingestion of the reference corpus must be scriptable and complete in ~10 minutes or less on a fresh AWS EC2 t3.micro instance.

4. **NFR-4: Error Resilience**
   - The system must implement retry-on-rate-limit logic for Ollama Cloud or local Ollama instances to handle concurrency limits gracefully.

---

## 7. Out of Scope for v1
- Integration with CI/CD systems (GitHub Actions, GitLab CI) as a blocker check (can be done manually).
- Automated remediation of spec code.
- Interactive multi-turn chat with the agent regarding the findings (results are read-only once generated).
- Custom guideline ingestion via the frontend (ingestion is done via backend scripts/CLI).

---

## 8. Success Metrics
- **Ingestion Time**: Corpus ingestion (OWASP + Zalando Guidelines) completed within 5 minutes.
- **Checker Latency**: Complete conformance check and report generation finished in under 60 seconds per API spec (assuming average Ollama response times).
- **Zero Hallucination of Citations**: The system never manufactures a rule name or rule ID; all cited rules must match actual entries in the vector database or result in an `Abstain` verdict.
- **Deployment Success Rate**: 100% automated script execution success on a standard Ubuntu 24.04 EC2 instance.
