import { NextResponse } from 'next/server';
import { Pool } from 'pg';

const pool = new Pool({
  connectionString: process.env.POSTGRES_URL,
  ssl: false,
});

export async function GET() {
  try {
    const res = await pool.query(
      'SELECT id, endpoint, rule_id, rule_title, citation, similarity_score, verdict, created_at FROM compliance_findings ORDER BY created_at DESC LIMIT 50'
    );
    return NextResponse.json({ success: true, data: res.rows });
  } catch (error: any) {
    return NextResponse.json({ success: false, error: error.message, data: [] });
  }
}

export async function POST(request: Request) {
  try {
    const body = await request.json();

    const pythonEngineResponse = await fetch('http://13.60.45.176:8000/api/live-audit', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ specData: body.specData }),
    });

    const auditResult = await pythonEngineResponse.json();

    if (!auditResult.success) {
      return NextResponse.json({ success: false, error: auditResult.error });
    }

    return NextResponse.json({ success: true, data: auditResult.data });

  } catch (error: any) {
    return NextResponse.json({ success: false, error: error.message });
  }
}
