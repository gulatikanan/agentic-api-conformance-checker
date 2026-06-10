# Agentic API Conformance Checker

The Agentic API Conformance Checker is an intelligent, automated testing framework designed to analyze, ingest, and verify API implementations against formal specifications. By leveraging agentic AI workflows, semantic search, and vector databases, it automatically identifies discrepancies and ensures compliance with industry API standards.

## Project Progress & Milestones

- [x] **Infrastructure Setup**: Initialized environment, AWS EC2, Docker (Qdrant & PostgreSQL).
- [x] **Decoupled Architecture**: Implemented `llm_client.py` with Groq API integration (Llama 3.3).
- [ ] **Phase 4: Corpus Ingestion**: Downloading and indexing OWASP/Zalando guidelines.
- [ ] **Phase 5: Schema Migration**: Configuring PostgreSQL findings and check tables.
- [ ] **Phase 6: Agent Logic**: Developing MCP tool-calling capabilities.

## Stack
- **AI/LLM**: Groq (Llama 3.3 70B for high-speed inference)
- **Vector DB**: Qdrant (Semantic indexing of API rules)
- **Relational DB**: PostgreSQL (Storing test logs, findings, and system state)
- **Server Protocol**: Model Context Protocol (MCP) for tool interaction
- **Containerization**: Docker & Docker Compose

## Setup
1. Copy `.env.example` to `.env` and configure your credentials:
   ```bash
   cp .env.example .env
   ```
   *Required*: `LLM_PROVIDER`, `LLM_API_KEY` (Groq), and DB connection strings.

2. Start the database and vector store services:
   ```bash
   docker compose up -d
   ```

3. Install dependencies using uv:
   ```bash
   uv sync
   ```

## Ingestion
To ingest API specifications and guidelines (OWASP/Zalando):

1. Place raw markdown/html files into `corpus/raw/`.
2. Execute the ingestion workflow:
   ```bash
   bash corpus/download.sh
   # (Followed by vectorization scripts)
   ```

## Architecture
This project utilizes a decoupled LLM client strategy, allowing for seamless provider switching (e.g., Groq to Gemini) without modifying core agent logic. All reasoning passes through `llm_client.py`, ensuring consistent error handling and token management.

## License
MIT