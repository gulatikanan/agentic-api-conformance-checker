import os
import re
import sys
import json
import uuid
import time
import subprocess
import psycopg2
from datetime import datetime, timezone
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env'))

app = FastAPI(title="API Conformance Bridge", version="2.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

POSTGRES_URL  = os.getenv("POSTGRES_URL")
OPENCLAW_BIN  = "/home/ubuntu/.npm-global/bin/openclaw"

class AuditRequest(BaseModel):
    specData: str

def call_openclaw(spec_data: str) -> dict:
    prompt = f"""You are a strict API conformance checker. Follow these steps exactly:
1. Call conformance-tools__inspect_artifact with the spec below as the `content` parameter and "openapi" as `artifact_type`.
2. For each endpoint found, call conformance-tools__find_rules with topic describing that endpoint's security concerns.
3. Return ONLY a raw JSON array — no markdown, no explanation:
[{{"endpoint": "/path", "verdict": "PASS or FAIL or ABSTAIN", "rule_id": "rule id or NONE", "rule_title": "rule title or No rule found", "citation": "exact verbatim quote or no rule found flagged for human review", "similarity_score": 0.0}}]

API Spec to check:
{spec_data}"""

    try:
        os.system("rm -rf /home/ubuntu/.openclaw/agents/main/sessions/*")
        os.system("rm -rf /home/ubuntu/.openclaw/sessions/*")
        session_id = f"audit_{uuid.uuid4().hex[:8]}"
        custom_env = os.environ.copy()

        # Invokes OpenClaw using global settings
        result = subprocess.run(
            [OPENCLAW_BIN, "agent", "--agent", "main", "--local",
             "--session-id", session_id,
             "--message", prompt, "--json"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=180,
            env=custom_env,
        )
        combined = result.stdout.strip()

        json_start = combined.find('{"payloads"')
        if json_start == -1: json_start = combined.find('{')
        json_end = combined.rfind('}') + 1

        if json_start == -1 or json_end <= json_start:
            return {"success": False, "error": f"OpenClaw execution failed:\n{combined}"}

        parsed = json.loads(combined[json_start:json_end])
        payloads = parsed.get("payloads", [])
        reply = payloads[0].get("text", "") if payloads else ""
        
        start = reply.find('[')
        end = reply.rfind(']') + 1
        if start != -1 and end > start:
            return {"success": True, "findings": json.loads(reply[start:end])}
        
        return {"success": True, "findings": _parse_text_response(reply)}

    except Exception as exc:
        return {"success": False, "error": str(exc)}

def _parse_text_response(text: str) -> list:
    findings = []
    for line in text.split('\n'):
        line = line.strip()
        ep_match = re.search(r'`?(/[a-zA-Z0-9_\-/{}/]+)`?', line)
        if not ep_match: continue
        verdict = "ABSTAIN"
        if 'PASS' in line.upper(): verdict = 'PASS'
        elif 'FAIL' in line.upper(): verdict = 'FAIL'
        findings.append({
            "endpoint": ep_match.group(1), "verdict": verdict, "rule_id": "NONE",
            "rule_title": "Processed", "citation": "", "similarity_score": 0.0,
        })
    return findings

def _save_findings(findings: list) -> list:
    if not POSTGRES_URL or not findings: return []
    rows = []
    try:
        conn = psycopg2.connect(POSTGRES_URL)
        cur  = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS compliance_findings (
                id VARCHAR(36) PRIMARY KEY, endpoint VARCHAR(500), rule_id VARCHAR(100),
                rule_title VARCHAR(500), citation TEXT, similarity_score NUMERIC(6,4),
                verdict VARCHAR(20), created_at TIMESTAMP
            );
        """)
        now = datetime.now(timezone.utc)
        for f in findings:
            row_id = str(uuid.uuid4())
            cur.execute(
                "INSERT INTO compliance_findings VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
                (row_id, f.get("endpoint",""), f.get("rule_id","NONE"), f.get("rule_title",""),
                 f.get("citation",""), float(f.get("similarity_score",0.0)), f.get("verdict","ABSTAIN"), now)
            )
            rows.append({
                "id": row_id, "endpoint": f.get("endpoint",""), "rule_id": f.get("rule_id","NONE"),
                "rule_title": f.get("rule_title",""), "citation": f.get("citation",""),
                "similarity_score": float(f.get("similarity_score",0.0)), "verdict": f.get("verdict","ABSTAIN"),
                "created_at": now.isoformat()
            })
        conn.commit()
        cur.close()
        conn.close()
    except Exception as exc: print(f"[DB ERROR] {exc}")
    return rows

@app.get("/health")
def health(): return {"status": "ok"}

@app.post("/api/live-audit")
async def live_audit(req: AuditRequest):
    result = call_openclaw(req.specData)
    if not result["success"]:
        return JSONResponse({"success": False, "error": result.get("error"), "data": []}, status_code=500)
    rows = _save_findings(result.get("findings", []))
    return JSONResponse({"success": True, "data": rows})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
