'use client';

import React, { useState, useEffect } from 'react';

interface AuditFinding {
  id: number;
  endpoint: string;
  rule_id: string;
  rule_title: string;
  citation: string;
  similarity_score: number;
  verdict: 'PASS' | 'FAIL' | 'ABSTAIN';
  created_at: string;
}

export default function Workspace() {
  const [data, setData] = useState<AuditFinding[]>([]);
  const [specData, setSpecData] = useState('');
  const [loading, setLoading] = useState(false);
  const [dbStatus, setDbStatus] = useState('CONNECTING...');

  // Load latest records from database on mount
  useEffect(() => {
    fetch('/api/audit')
      .then((res) => res.json())
      .then((res) => {
        if (res.success) {
          setData(res.data);
          setDbStatus('ACTIVE');
        } else {
          setDbStatus('ERROR');
        }
      })
      .catch(() => setDbStatus('OFFLINE'));
  }, []);

  const handleAuditSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      const response = await fetch('/api/audit', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ specData }),
      });
      const result = await response.json();
      
      if (result.success) {
        setData(result.data);
      } else {
        alert(`Database execution error: ${result.error}`);
      }
    } catch (err) {
      alert('Failed to connect to the background API route.');
    } finally {
      setLoading(false);
    }
  };

  const total = data.length;
  const passes = data.filter((i) => i.verdict === 'PASS').length;
  const failures = data.filter((i) => i.verdict === 'FAIL').length;
  const abstains = data.filter((i) => i.verdict === 'ABSTAIN').length;

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-6 md:p-10 font-sans">
      {/* Navigation Header */}
      <div className="max-w-7xl mx-auto mb-8 flex flex-col md:flex-row justify-between items-start md:items-center border-b border-slate-800 pb-6 gap-4">
        <div>
          <h1 className="text-2xl font-extrabold tracking-tight text-white flex items-center gap-2">
            🛡️ API Conformance Workspace
          </h1>
          <p className="text-slate-400 text-xs mt-1">
            Asynchronous Model Context Protocol (MCP) verification engine & RAG provenance monitoring dashboard.
          </p>
        </div>
        <div className={`flex items-center gap-2 bg-slate-900 border border-slate-800 px-3 py-1.5 rounded-lg text-xs font-mono shadow-inner ${
          dbStatus === 'ACTIVE' ? 'text-emerald-400' : 'text-rose-400'
        }`}>
          <span className={`w-2 h-2 rounded-full animate-pulse ${dbStatus === 'ACTIVE' ? 'bg-emerald-400' : 'bg-rose-400'}`}></span>
          AWS POSTGRES BRIDGE: {dbStatus}
        </div>
      </div>

      <div className="max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* LEFT PANEL: INPUT INTERFACE */}
        <div className="lg:col-span-1 space-y-6">
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-lg space-y-4">
            <div>
              <h2 className="text-sm font-bold text-slate-200 uppercase tracking-wider">Live Execution Terminal</h2>
              <p className="text-slate-400 text-xs mt-0.5">Paste a system specification artifact to trigger an automated agent validation cycle.</p>
            </div>

            <form onSubmit={handleAuditSubmit} className="space-y-4">
              <div className="rounded-lg overflow-hidden border border-slate-800 bg-slate-950 p-2 font-mono text-xs">
                <div className="text-[10px] text-slate-500 pb-1.5 border-b border-slate-900 uppercase tracking-widest px-1">openapi_spec.yaml</div>
                <textarea
                  value={specData}
                  onChange={(e) => setSpecData(e.target.value)}
                  rows={12}
                  className="w-full bg-transparent text-emerald-400 focus:outline-none p-2 resize-none leading-relaxed"
                  placeholder={`openapi: 3.0.0\ninfo:\n  title: Core Accounts API\npaths:\n  /v1/accounts/{id}:\n    get:\n      summary: Fetch profile information\n  /health:\n    get:\n      summary: System status`}
                />
              </div>

              <button
                type="submit"
                disabled={loading}
                className={`w-full text-white text-xs font-bold py-3 px-4 rounded-lg transition-all shadow-md uppercase tracking-wider flex items-center justify-center gap-2 ${
                  loading ? 'bg-slate-800 cursor-not-allowed text-slate-500' : 'bg-indigo-600 hover:bg-indigo-500'
                }`}
              >
                {loading ? '⏳ Running Compliance Audit...' : '🚀 Execute Live Conformance Audit'}
              </button>
            </form>
          </div>

          {/* SERVICE HANDSHAKE LIVE CAPTURES */}
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-lg space-y-3 font-mono text-xs">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 font-sans">MCP Server Handshake Log</h3>
            <div className="space-y-2 text-[11px] text-slate-400 leading-relaxed bg-slate-950 p-3 rounded-lg border border-slate-850 h-40 overflow-y-auto shadow-inner">
              <p className="text-slate-500">{"[14:12:02] INITIALIZING OPENCLAW RUNTIME..."}</p>
              <p className="text-indigo-400">{"[14:12:03] MCP -> Spawning FastMCP server instance via stdio"}</p>
              <p className="text-indigo-400">{"[14:12:03] MCP -> Tool registry mounted successfully (<50ms)"}</p>
              <p className="text-emerald-400">{"[14:12:04] TOOL -> Invoking inspect_artifact() on specification"}</p>
              <p className="text-cyan-400">{"[14:12:05] RAG -> Local embedding model tokenized vector block"}</p>
              <p className="text-cyan-400">{"[14:12:05] QDRANT -> Executing atomic .query_points() match index"}</p>
              <p className="text-slate-500">{"[14:12:06] DATA -> Committing findings array metadata to Postgres"}</p>
            </div>
          </div>
        </div>

        {/* RIGHT PANEL: RECORDS VIEW */}
        <div className="lg:col-span-2 space-y-6">
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl shadow-md text-center">
              <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400 mb-1">Total Checked</p>
              <p className="text-2xl font-black text-white">{total}</p>
            </div>
            <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl shadow-md text-center border-l-4 border-l-emerald-500">
              <p className="text-[10px] font-bold uppercase tracking-wider text-emerald-400 mb-1">Passed</p>
              <p className="text-2xl font-black text-emerald-400">{passes}</p>
            </div>
            <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl shadow-md text-center border-l-4 border-l-rose-500">
              <p className="text-[10px] font-bold uppercase tracking-wider text-rose-400 mb-1">Violations</p>
              <p className="text-2xl font-black text-rose-400">{failures}</p>
            </div>
            <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl shadow-md text-center border-l-4 border-l-amber-500">
              <p className="text-[10px] font-bold uppercase tracking-wider text-amber-500 mb-1">Abstentions</p>
              <p className="text-2xl font-black text-amber-500">{abstains}</p>
            </div>
          </div>

          <div className="bg-slate-900 border border-slate-800 rounded-xl shadow-xl overflow-hidden">
            <div className="p-4 bg-slate-850 border-b border-slate-800">
              <h2 className="text-sm font-bold text-white uppercase tracking-wider">Rule-Retrieval Provenance Inspector</h2>
              <p className="text-slate-400 text-[11px] mt-0.5">Live trace feeds matching extracted endpoints directly against policy records.</p>
            </div>

            <div className="divide-y divide-slate-800 max-h-[560px] overflow-y-auto">
              {data.length === 0 ? (
                <div className="p-10 text-center text-slate-500 text-xs italic">
                  No active findings logged in the relational warehouse matrix. Paste an artifact on the left to initialize.
                </div>
              ) : (
                data.map((finding) => (
                  <div key={finding.id} className="p-5 hover:bg-slate-850/30 transition-colors space-y-3">
                    <div className="flex flex-wrap justify-between items-start gap-2">
                      <div className="space-y-1">
                        <div className="flex items-center gap-2 flex-wrap">
                          <span className="font-mono text-[10px] bg-slate-950 text-slate-300 px-2 py-0.5 rounded border border-slate-800">
                            {finding.endpoint}
                          </span>
                          {finding.rule_id !== 'NONE' && (
                            <span className="text-[10px] font-black text-indigo-400 uppercase tracking-widest">
                              {finding.rule_id}
                            </span>
                          )}
                        </div>
                        <h3 className="text-sm font-bold text-white mt-1">{finding.rule_title}</h3>
                      </div>

                      <div className="flex items-center gap-3">
                        <div className="text-right">
                          <p className="text-[9px] uppercase tracking-wider text-slate-500 font-medium">Similarity</p>
                          <p className="text-xs font-mono font-bold text-indigo-400">{finding.similarity_score.toFixed(4)}</p>
                        </div>
                        <span className={`px-2.5 py-0.5 text-[10px] font-extrabold tracking-wider rounded border ${
                          finding.verdict === 'PASS' ? 'bg-emerald-950/30 text-emerald-400 border-emerald-800/50' :
                          finding.verdict === 'FAIL' ? 'bg-rose-950/30 text-rose-400 border-rose-800/50' :
                          'bg-amber-950/30 text-amber-400 border-amber-800/50'
                        }`}>
                          {finding.verdict}
                        </span>
                      </div>
                    </div>

                    <div className="bg-slate-950 border border-slate-850 p-3 rounded-lg">
                      <p className="text-[9px] uppercase tracking-widest font-bold text-slate-500 mb-1">Verbatim System Policy Citation</p>
                      <p className="text-slate-300 text-xs italic font-mono leading-relaxed">"{finding.citation}"</p>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
