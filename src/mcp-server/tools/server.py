import os
import json
import re
import yaml
from mcp.server.fastmcp import FastMCP
from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

# Load workspace configurations (.env)
load_dotenv()

# 1. Initialize the official FastMCP context block
mcp = FastMCP("API Conformance Checker Backend")

# 2. Establish connections to the local storage infrastructure layers
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
COLLECTION_NAME = os.getenv("QDRANT_COLLECTION", "compliance_rules")

qdrant_client = QdrantClient(url=QDRANT_URL)
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")


@mcp.tool()
def find_rules(topic: str) -> str:
    """
    Queries the Qdrant vector database using local semantic search embeddings 
    to retrieve compliance, security, and design guidelines matching the topic.
    Enforces a strict similarity threshold to prevent hallucinations.
    """
    try:
        # Fetch configurable similarity threshold dynamically from environment
        SIMILARITY_THRESHOLD = float(os.getenv("SIMILARITY_THRESHOLD", "0.65"))

        # Compute dense vector dimensions locally on the host CPU (384-dimensions)
        query_vector = embedding_model.encode(topic).tolist()
        
        # Execute cosine distance search over the seeded compliance collection
        raw_results = qdrant_client.search(
            collection_name=COLLECTION_NAME,
            query_vector=query_vector,
            limit=3
        )
        
        # Filter out low-confidence results below the strict threshold
        results = [r for r in raw_results if r.score >= SIMILARITY_THRESHOLD]
        
        # Handle Abstention Gate with structured JSON
        if not results:
            return json.dumps({
                "status": "abstain",
                "topic": topic,
                "reason": f"No rules found above similarity threshold {SIMILARITY_THRESHOLD} — flagged for human review",
                "retrieved_passages": []
            })
            
        # Compile structured passages for frontend inspector ingestion
        passages = []
        for res in results:
            passages.append({
                "title": res.payload.get("title", "Unknown Guideline Clause"),
                "text": res.payload.get("text", ""),
                "score": round(res.score, 4),
                "source": res.payload.get("source", "")
            })
            
        return json.dumps({
            "status": "found",
            "topic": topic,
            "retrieved_passages": passages
        })
        
    except Exception as e:
        return json.dumps({
            "status": "error",
            "topic": topic,
            "reason": f"Error executing vector tool boundary: {str(e)}",
            "retrieved_passages": []
        })


@mcp.tool()
def inspect_artifact(content: str, artifact_type: str = "openapi") -> str:
    """
    Parses and standardizes raw API specifications (YAML/JSON/Markdown) into a 
    structured JSON layout highlighting endpoints, parameters, and auth schemes.
    """
    try:
        summary = {
            "status": "success",
            "content_type_inferred": artifact_type,
            "detected_endpoints": [],
            "auth_mechanisms": []
        }
        
        # Scenario A: Handle JSON or YAML OpenAPI Specifications
        if "paths" in content or "openapi" in content or "swagger" in content:
            try:
                data = json.loads(content) if content.strip().startswith("{") else yaml.safe_load(content)
                if isinstance(data, dict):
                    paths_dict = data.get("paths", {})
                    summary["detected_endpoints"] = list(paths_dict.keys())
                    
                    components = data.get("components", {})
                    if "securitySchemes" in components:
                        summary["auth_mechanisms"] = list(components["securitySchemes"].keys())
            except Exception:
                summary["detected_endpoints"] = re.findall(r'(?:^\s*[\'"]?\/[a-zA-Z0-9_\-\/]+[\'"]?:)', content, re.MULTILINE)
        
        # Scenario B: Handle raw Markdown documentation submissions
        else:
            summary["content_type_inferred"] = "markdown_documentation"
            summary["detected_endpoints"] = re.findall(r'(?:GET|POST|PUT|DELETE|PATCH)\s+(\/[a-zA-Z0-9_\-\/]+)', content, re.IGNORECASE)
            if any(k in content.lower() for k in ["auth", "token", "api-key"]):
                summary["auth_mechanisms"].append("Inferred Token/Key Reference")

        # Return a clean structured JSON dump string
        return json.dumps(summary)
        
    except Exception as e:
        return json.dumps({
            "status": "error",
            "reason": f"Error executing artifact analysis parser: {str(e)}"
        })


@mcp.tool()
def save_conformance_check(artifact_name: str, summary_json: str, findings_json: str) -> str:
    """
    Saves the finalized API conformance check metrics and granular cited findings 
    directly into the persistent relational PostgreSQL database.
    """
    try:
        import psycopg2
        db_url = os.getenv("POSTGRES_URL", "postgresql://postgres:postgrespassword@localhost:5432/conformance_checker")
        conn = psycopg2.connect(db_url)
        
        with conn.cursor() as cur:
            # 1. Initialize data tables if missing
            cur.execute("""
                CREATE TABLE IF NOT EXISTS compliance_checks (
                    id SERIAL PRIMARY KEY,
                    artifact_name VARCHAR(255) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    summary JSONB
                );
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS check_findings (
                    id SERIAL PRIMARY KEY,
                    check_id INTEGER REFERENCES compliance_checks(id) ON DELETE CASCADE,
                    rule_title VARCHAR(255),
                    verdict VARCHAR(50),
                    score NUMERIC(5,4),
                    details TEXT,
                    rule_passage TEXT
                );
            """)
            
            # 2. Insert master session tracking entry
            cur.execute(
                "INSERT INTO compliance_checks (artifact_name, summary) VALUES (%s, %s) RETURNING id;",
                (artifact_name, summary_json)
            )
            check_id = cur.fetchone()[0]
            
            # 3. Insert individual cited rule logs
            findings = json.loads(findings_json)
            for f in findings:
                cur.execute("""
                    INSERT INTO check_findings (check_id, rule_title, verdict, score, details, rule_passage)
                    VALUES (%s, %s, %s, %s, %s, %s);
                """, (check_id, f.get("rule_title"), f.get("verdict"), f.get("score"), f.get("details"), f.get("rule_passage")))
                
            conn.commit()
            conn.close()
            
        return json.dumps({"status": "success", "check_id": check_id, "message": "Telemetry logged to Postgres successfully."})
    except Exception as e:
        return json.dumps({"status": "error", "reason": f"Database persistence failure: {str(e)}"})


if __name__ == "__main__":
    mcp.run()
