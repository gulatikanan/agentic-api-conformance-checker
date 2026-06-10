# Agentic API Conformance Checker

The Agentic API Conformance Checker is an intelligent, automated testing framework designed to analyze, ingest, and verify API implementations against their specifications. By leveraging agentic AI workflows, semantic search, and vector databases, it automatically checks conformance, identifies discrepancies, and ensures robust compliance with API standards.

## Overview
This tool performs deep conformance checking on API endpoints by analyzing their behavior and comparing them to formal specifications. It uses an AI-driven agent to construct test scenarios, generate test requests, execute them, and evaluate the responses against the expected schemas and business logic.

## Stack
- **AI/LLM**: Ollama (for local LLM and embedding generation)
- **Vector DB**: Qdrant (for semantic indexing and retrieval of API specs)
- **Relational DB**: PostgreSQL (for storing test logs, results, and system state)
- **Server Protocol**: Model Context Protocol (MCP) server for tool access
- **Containerization**: Docker & Docker Compose

## Setup
1. Copy `.env.example` to `.env` and configure the environment variables:
   ```bash
   cp .env.example .env
   ```
2. Start the database and vector store services:
   ```bash
   docker compose up -d
   ```
3. Run the setup script to initialize dependencies:
   ```bash
   bash scripts/setup.sh
   ```

## Ingestion
To ingest new API specifications or documentation:
1. Place raw spec files (OpenAPI/Swagger, etc.) into the `corpus/raw/` directory.
2. Run the ingestion script:
   ```bash
   bash scripts/ingest.sh
   ```

## Redeploy
To restart the services or apply updates:
```bash
bash scripts/restart.sh
```