import os
import re
import yaml
import json
import psycopg2
from mcp.server.fastapi import FastMCP
from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

# Load credentials
load_dotenv(dotenv_path=os.path.expanduser('~/agentic-api-conformance-checker/.env'))

# Initialize FastMCP Server Instance
mcp = FastMCP("API Conformance Checker Rulebook Engine")

# Pre-load shared RAG weights into memory
print("⏳ Loading RAG Transformer layers into RAM...")
encoder = SentenceTransformer('all-MiniLM-L6-v2')
qdrant_client = QdrantClient(url=os.getenv("QDRANT_URL", "http://localhost:6333"))

@mcp.tool()
def inspect_artifact(spec_data: str) -> str:
    """Parses, lints, and extracts structural endpoint routes and methods from a submitted OpenAPI specification text artifact."""
    endpoints = []
    try:
        data = yaml.safe_load(spec_data) or json.loads(spec_data)
        if isinstance(data, dict) and 'paths' in data:
            for path, methods in data['paths'].items():
                for method, details in methods.items():
                    if method.lower() in ['get', 'post', 'put', 'delete', 'patch']:
                        desc = details.get('description', '') if isinstance(details, dict) else ''
                        endpoints.append({"path": path, "method": method.upper(), "description": str(desc)})
    except Exception:
        pass
    
    if not endpoints:
        matches = re.findall(r'(GET|POST|PUT|DELETE)\s+([/a-zA-Z0-9_{}-]+)', spec_data, re.IGNORECASE)
        for m in matches:
            endpoints.append({"path": m[1], "method": m[0].upper(), "description": ""})
            
    return json.dumps(endpoints if endpoints else [{"path": "/unknown", "method": "EVAL", "description": ""}])

@mcp.tool()
def find_rules(topic: str) -> str:
    """Executes semantic vector RAG search over the 414 policy document corpus inside Qdrant and returns the single highest matching clause with its similarity score."""
    vector = encoder.encode(topic).tolist()
    threshold = float(os.getenv("SIMILARITY_THRESHOLD", "0.45"))
    
    collections = ["api_rules", "compliance_rules"]
    for col in collections:
        try:
            results = qdrant_client.query_points(collection_name=col, query=vector, limit=1).points
            if results:
                match = results[0]
                score = match.score
                p_data = match.payload
                
                return json.dumps({
                    "rule_id": p_data.get("rule_id", "GOV-01"),
                    "title": p_data.get("title", "Policy Match"),
                    "citation": p_data.get("text", p_data.get("content", "Policy clause extracted.")),
                    "similarity_score": score,
                    "above_threshold": score >= threshold
                })
        except Exception:
            continue
            
    return json.dumps({"rule_id": "NONE", "similarity_score": 0.0, "above_threshold": False})

if __name__ == "__main__":
    # FastMCP automatically hosts an SSE (Server-Sent Events) web server endpoint on port 8000
    mcp.run(transport="sse", host="0.0.0.0", port=8000)
