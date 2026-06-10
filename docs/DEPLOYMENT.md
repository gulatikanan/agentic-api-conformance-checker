# Deployment and Redeploy Guide

This guide provides instructions for deploying, configuring, verifying, and troubleshooting the Agentic API Conformance Checker.

---

## 1. Prerequisites
Before deploying, ensure the target host (e.g., AWS EC2) has the following installed:
- **Host System**: AWS EC2 instance (recommended: `t3.micro` or higher, running **Ubuntu 24.04 LTS**).
- **Docker**: Docker Engine and Docker Compose v2 (to run Postgres and Qdrant).
- **Node.js**: Version 20.x or higher (for the MCP server).
- **Python**: Version 3.11.x (for ingestion scripts and the agent).
- **Python Package Manager**: `uv` (recommended for ultra-fast, clean Python dependency resolution).
- **OpenClaw**: The orchestration framework installed and configured.

---

## 2. Environment Variables
Copy [.env.example](file:///c:/Users/K2/Desktop/assignment-conformance-checker/.env.example) to `.env` and configure the values:

| Variable | Description | Example / Recommended Value |
| :--- | :--- | :--- |
| `OLLAMA_BASE_URL` | Base URL of the running Ollama API | `http://localhost:11434` or Ollama Cloud URL |
| `OLLAMA_MODEL` | LLM model name for reasoning | `llama3` or `mistral` |
| `OLLAMA_EMBED_MODEL` | LLM model name for text embeddings | `nomic-embed-text` |
| `QDRANT_URL` | Address of the Qdrant service | `http://localhost:6333` |
| `QDRANT_COLLECTION` | Vector collection name for storing rule chunks | `api_conformance_rules` |
| `POSTGRES_URL` | Connection string for the PostgreSQL database | `postgresql://postgres:postgrespassword@localhost:5432/conformance_checker` |
| `POSTGRES_PASSWORD` | Password for the postgres database user | `postgrespassword` |
| `MCP_SERVER_PORT` | The port the MCP server daemon listens on | `4000` |

---

## 3. Step-by-Step Fresh Deploy Instructions

Follow these steps for a complete deployment on a clean machine:

### Step 3.1: Clone the Repository
```bash
git clone https://github.com/gulatikanan/agentic-api-conformance-checker.git
cd agentic-api-conformance-checker
```

### Step 3.2: Configure Environment
Copy the example environment template, edit the values inside, and restrict permissions to protect sensitive API keys and database credentials:
```bash
cp .env.example .env
nano .env
chmod 600 .env
```
> [!NOTE]
> Running `chmod 600 .env` restricts file access to the owner only, preventing exposure of database passwords and API tokens on shared hosting environments.


### Step 3.3: Run the Setup Script
Initialize Python virtual environments, install dependency packages (both npm and python), and set executable permissions:
```bash
bash scripts/setup.sh
```

### Step 3.4: Spin Up Databases
Start PostgreSQL and Qdrant in detached mode via Docker Compose:
```bash
docker compose up -d
```

### Step 3.5: Run the Ingestion Script
Download compliance rules and specifications, perform semantic chunking, call Ollama to generate vector embeddings, and load them into Qdrant:
```bash
bash scripts/ingest.sh
```

### Step 3.6: Start the MCP Server
Start the Model Context Protocol server:
```bash
npm run start:mcp
# Alternatively, run using pm2 or systemd to keep it daemonized
```

### Step 3.7: Start the OpenClaw Agent
Execute the agent orchestration loop:
```bash
python src/agent/main.py
# Or run under a background daemon manager
```

### Step 3.8: Deploy Frontend to Vercel
1. Install the Vercel CLI locally or connect your GitHub repository directly to Vercel.
2. Ensure Vercel environment variables point to your EC2 instance's public IP address for the MCP and Database connections if appropriate.
3. Trigger deployment:
   ```bash
   vercel --prod
   ```

---

## 4. How to Verify Each Service

Use these commands to verify that all components are running correctly.

### 4.1. Qdrant Vector DB
* **Command**:
  ```bash
  curl http://localhost:6333/health
  ```
* **Expected Response**:
  ```json
  {"title":"qdrant - vector search engine","version":"1.x.x"}
  ```

### 4.2. PostgreSQL Database
* **Command**:
  ```bash
  docker exec -it api-conformance-postgres pg_isready -U postgres
  ```
* **Expected Response**:
  ```text
  /var/run/postgresql:5432 - accepting connections
  ```

### 4.3. Ollama API
* **Command**:
  ```bash
  curl http://localhost:11434/api/tags
  ```
* **Expected Response**: Contains list of downloaded models, including `nomic-embed-text`.
  ```json
  {
    "models": [
      { "name": "nomic-embed-text:latest", ... },
      { "name": "llama3:latest", ... }
    ]
  }
  ```

### 4.4. MCP Server
* **Command**:
  ```bash
  curl http://localhost:4000/status
  ```
* **Expected Response**:
  ```json
  {"status":"ready","tools":["find_rules","inspect_artifact"]}
  ```

---

## 5. Re-Ingesting the Corpus
If the raw rules change, or you want to wipe the vector store and load the corpus from scratch:
```bash
bash scripts/ingest.sh --force
```
This script will:
1. Re-initialize the Qdrant collection (deleting existing data if `--force` is supplied).
2. Reparse documents inside `corpus/raw/`.
3. Re-embed all passages.
4. Upload them back to Qdrant.

---

## 6. Restarting All Services
To cleanly restart all local backend services (Docker containers, MCP server, and agent), run:
```bash
bash scripts/restart.sh
```

---

## 7. Estimated Deployment Time
* **Fresh Deploy + Ingestion**: ~10 minutes.
  - Docker images pull: ~2 mins
  - NPM & Pip dependencies installation: ~2 mins
  - Rule chunking & Ollama ingestion: ~4 mins
  - Final service check: ~1 min

---

## 8. Troubleshooting

### 8.1. Qdrant Container Fails to Start
- **Symptom**: `docker compose ps` shows Qdrant in `Exit` state.
- **Cause**: Permission denied on the volume directory `./qdrant/storage`.
- **Fix**: Grant Docker permission to write to the folder:
  ```bash
  sudo chmod -R 777 ./qdrant/storage
  ```

### 8.2. Ollama API Rate Limit / Connection Failures
- **Symptom**: "429 Too Many Requests" or socket hangs in logs.
- **Cause**: Shared Ollama server context queues or GPU memory limits reached.
- **Fix**: The client logic automatically retries. If errors persist, decrease concurrent ingestion batch size in `src/ingestion/config.py` or restart the Ollama service.

### 8.3. Postgres Connection Refused
- **Symptom**: Node.js/Python logs show `ECONNREFUSED 127.0.0.1:5432`.
- **Cause**: Postgres container is still initializing or database credentials mismatched in `.env`.
- **Fix**: Wait 15 seconds for DB startup. Verify `.env` values match the credentials in `docker-compose.yml`.

### 8.4. OpenClaw Agent Fails to Boot
- **Symptom**: ModuleNotFoundError or startup crash.
- **Cause**: Virtual environment not active or dependencies outdated.
- **Fix**: Re-run the setup script or verify path resolution:
  ```bash
  source .venv/bin/activate
  pip install -r requirements.txt
  ```
