import os
import re
import json
import uuid
import subprocess
import psycopg2
from datetime import datetime, timezone
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env'))

app = FastAPI(title="API Conformance Bridge", version="5.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

POSTGRES_URL = os.getenv("POSTGRES_URL")
OPENCLAW_BIN = "/home/ubuntu/.npm-global/bin/openclaw"
REPO_DIR     = "/home/ubuntu/agentic-api-conformance-checker"

class AuditRequest(BaseModel):
    specData: str

def call_openclaw(spec_data: str) -> dict:
    """
    Single OpenClaw call for the entire spec.
    OpenClaw calls inspect_artifact + find_rules via MCP in one turn.
    Total tokens: ~3720 base + ~500 spec = ~4220 max. Well within limits.
    """
    os.system("rm -rf /home/ubuntu/.openclaw/agents/main/sessions/ && mkdir -p /home/ubuntu/.openclaw/agents/main/sessions/")
    session_id = f"audit_{uuid.uuid4().hex[:8]}"

    # Single compact prompt — entire audit in one LLM call
    prompt = f"""API conformance check. Do exactly:
1. Call inspect_artifact: content=<spec below>, artifact_type="openapi"
2. For ALL endpoints found in one batch, call find_rules once per endpoint
3. Return ONLY this JSON array:
[{{"endpoint":"/path","verdict":"PASS or FAIL or ABSTAIN","rule_id":"id or NONE","rule_title":"title","citation":"quote or no rule found flagged for human review","similarity_score":0.0}}]

Spec (check ALL endpoints):
{spec_data[:1500]}"""

    try:
        result = subprocess.run(
            [OPENCLAW_BIN, "agent", "--agent", "main", "--local",
             "--model", "google/gemini-2.5-flash",
             "--session-id", session_id,
             "--message", prompt, "--json"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=180,
            cwd=REPO_DIR,
        )
        combined = result.stdout.strip()

        # Find JSON envelope
        json_start = combined.find('{"payloads"')
        if json_start == -1:
            json_start = combined.find('{')
        json_end = combined.rfind('}') + 1

        if json_start == -1 or json_end <= json_start:
            return {"success": False, "error": f"OpenClaw failed: {combined[-300:]}"}

        parsed = json.loads(combined[json_start:json_end])

        if parsed.get("isError"):
            return {"success": False, "error": combined[-300:]}

        payloads = parsed.get("payloads", [])
        reply = payloads[0].get("text", "") if payloads else ""

        if not reply:
            return {"success": False, "error": "Empty reply from agent"}

        # Extract JSON array
        start = reply.find('[')
        end = reply.rfind(']') + 1
        if start != -1 and end > start:
            try:
                findings = json.loads(reply[start:end])
                return {"success": True, "findings": findings}
            except Exception:
                pass

        # Fallback text parser
        findings = _parse_text_response(reply)
        return {"success": True, "findings": findings} if findings else \
               {"success": False, "error": f"Could not parse: {reply[:200]}"}

    except subprocess.TimeoutExpired:
        return {"success": False, "error": "Agent timed out"}
    except Exception as exc:
        return {"success": False, "error": str(exc)}

def _parse_text_response(text: str) -> list:
    findings = []
    for line in text.split('\n'):
        line = line.strip()
        ep_match = re.search(r'`?(/[a-zA-Z0-9_\-/{}/]+)`?', line)
        if not ep_match:
            continue
        verdict = "ABSTAIN"
        if 'PASS' in line.upper():
            verdict = 'PASS'
        elif 'FAIL' in line.upper():
            verdict = 'FAIL'
        findings.append({
            "endpoint": ep_match.group(1),
            "verdict": verdict,
            "rule_id": "NONE" if verdict == "ABSTAIN" else "RULE-01",
            "rule_title": "No rule found — flagged for human review" if verdict == "ABSTAIN" else "Policy match",
            "citation": "no rule found — flagged for human review" if verdict == "ABSTAIN" else "",
            "similarity_score": 0.0,
        })
    return findings

def _save_findings(findings: list) -> list:
    if not POSTGRES_URL or not findings:
        return []
    rows = []
    try:
        conn = psycopg2.connect(POSTGRES_URL)
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS compliance_findings (
                id VARCHAR(36) PRIMARY KEY,
                endpoint VARCHAR(500),
                rule_id VARCHAR(100),
                rule_title VARCHAR(500),
                citation TEXT,
                similarity_score NUMERIC(6,4),
                verdict VARCHAR(20),
                created_at TIMESTAMP
            );
        """)
        now = datetime.now(timezone.utc)
        for f in findings:
            row_id = str(uuid.uuid4())
            cur.execute(
                "INSERT INTO compliance_findings VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
                (row_id, f.get("endpoint","unknown"), f.get("rule_id","NONE"),
                 f.get("rule_title",""), f.get("citation",""),
                 float(f.get("similarity_score",0.0)),
                 f.get("verdict","ABSTAIN"), now)
            )
            rows.append({
                "id": row_id,
                "endpoint": f.get("endpoint","unknown"),
                "rule_id": f.get("rule_id","NONE"),
                "rule_title": f.get("rule_title",""),
                "citation": f.get("citation",""),
                "similarity_score": float(f.get("similarity_score",0.0)),
                "verdict": f.get("verdict","ABSTAIN"),
                "created_at": now.isoformat()
            })
        conn.commit()
        cur.close()
        conn.close()
    except Exception as exc:
        print(f"[DB ERROR] {exc}")
    return rows

@app.get("/health")
def health():
    return {"status": "ok", "agent": "openclaw", "mcp": "conformance-tools"}

@app.post("/api/live-audit")
async def live_audit(req: AuditRequest):
    result = call_openclaw(req.specData)
    if not result["success"]:
        return JSONResponse(
            {"success": False, "error": result.get("error"), "data": []},
            status_code=500
        )
    rows = _save_findings(result.get("findings", []))
    return JSONResponse({"success": True, "data": rows})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="warning")
