import { Client } from 'pg'

export const dynamic = 'force-dynamic'

async function getAuditData() {
  const connectionString = process.env.POSTGRES_URL || 'postgresql://postgres:postgrespassword@localhost:5432/conformance_checker'
  const client = new Client({ connectionString })
  
  try {
    await client.connect()
    const checksRes = await client.query('SELECT * FROM compliance_checks ORDER BY created_at DESC;')
    const findingsRes = await client.query('SELECT * FROM check_findings ORDER BY id ASC;')
    await client.end()
    
    return {
      checks: checksRes.rows,
      findings: findingsRes.rows,
    }
  } catch (error) {
    console.error('Database connection error:', error)
    return { checks: [], findings: [] }
  }
}

export default async function DashboardPage() {
  const { checks, findings } = await getAuditData()

  return (
    <main className="min-h-screen p-8 max-w-7xl mx-auto">
      <header className="border-b border-slate-800 pb-6 mb-8 flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-white flex items-center gap-2">
            🛡️ API Conformance Workspace
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Real-time compliance validation telemetry via OpenClaw + FastMCP Engine
          </p>
        </div>
        <div className="bg-slate-900 border border-slate-800 px-4 py-2 rounded-lg text-xs text-slate-300">
          Database Nodes: <span className="text-emerald-400 font-mono font-bold">ONLINE</span>
        </div>
      </header>

      {checks.length === 0 ? (
        <section className="bg-slate-900 border border-slate-800 rounded-xl p-12 text-center text-slate-400">
          <p className="text-lg">No conformance test telemetry logged inside the data warehouse yet.</p>
          <p className="text-xs text-slate-500 mt-2 font-mono">Run your OpenClaw agent scanner CLI to populate tables.</p>
        </section>
      ) : (
        <div className="space-y-10">
          {checks.map((check) => {
            const currentFindings = findings.filter(f => f.check_id === check.id)
            
            return (
              <section key={check.id} className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-xl">
                <div className="bg-slate-900 border-b border-slate-800 p-6 flex flex-col md:flex-row md:items-center justify-between gap-4">
                  <div>
                    <h2 className="text-xl font-bold text-slate-200 font-mono">{check.artifact_name}</h2>
                    <p className="text-xs text-slate-500 mt-1">
                      Scan Token: Check #{check.id} • Processed: {new Date(check.created_at).toLocaleString()}
                    </p>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="text-xs bg-slate-800 text-slate-300 px-3 py-1 rounded-full border border-slate-700">
                      Total Findings: {currentFindings.length}
                    </span>
                  </div>
                </div>

                <div className="p-6 space-y-4">
                  {currentFindings.length === 0 ? (
                    <p className="text-sm text-slate-500 font-mono">No endpoint clauses analyzed inside this session.</p>
                  ) : (
                    <div className="grid grid-cols-1 gap-4">
                      {currentFindings.map((finding) => {
                        const verdict = (finding.verdict || 'ABSTAIN').toUpperCase()
                        
                        let badgeColor = 'bg-slate-950 text-slate-400 border-slate-700'
                        if (verdict === 'PASS') badgeColor = 'bg-emerald-950/40 text-emerald-400 border-emerald-800'
                        if (verdict === 'FAIL') badgeColor = 'bg-rose-950/40 text-rose-400 border-rose-800'
                        if (verdict === 'ABSTAIN') badgeColor = 'bg-amber-950/30 text-amber-500 border-amber-800'

                        return (
                          <div key={finding.id} className="bg-slate-950 border border-slate-800 rounded-lg p-5 space-y-3">
                            <div className="flex justify-between items-start gap-4">
                              <div>
                                <h3 className="font-bold text-slate-200 text-sm font-mono">{finding.rule_title}</h3>
                                {finding.score && (
                                  <span className="text-xs text-slate-500 font-mono">
                                    Vector Metric: Cosine {(parseFloat(finding.score)).toFixed(4)}
                                  </span>
                                )}
                              </div>
                              <span className={`text-xs font-bold font-mono px-2.5 py-1 rounded border tracking-wider ${badgeColor}`}>{{verdict}}</span>
                            </div>

                            <p className="text-sm text-slate-300 leading-relaxed bg-slate-900/50 p-3 rounded border border-slate-900">
                              {finding.details}
                            </p>

                            {finding.rule_passage && (
                              <div className="bg-slate-900/30 border-l-2 border-slate-700 pl-4 py-1 mt-2">
                                <span className="text-[11px] uppercase tracking-wider text-slate-500 font-bold block mb-1">
                                  Verbatim Cited Knowledge Passage Base
                                </span>
                                <p className="text-xs italic text-slate-400 leading-relaxed font-mono">
                                  {finding.rule_passage}
                                </p>
                              </div>
                            )}
                          </div>
                        )
                      })}
                    </div>
                  )}
                </div>
              </section>
            )
          })}
        </div>
      )}
    </main>
  )
}
