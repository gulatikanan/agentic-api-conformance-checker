module.exports = {
  // 🌐 Gateway Network Service Core
  gateway: {
    port: 18789,
    host: '127.0.0.1',
    logLevel: 'info',
  },

  // 🧠 Upstream AI Inference Router Configuration
  llm: {
    provider: process.env.LLM_PROVIDER || 'gemini',
    model: process.env.GEMINI_MODEL || 'google/gemini-3.1-pro-preview',
    apiKey: process.env.GEMINI_API_KEY,
    options: {
      temperature: 0.1, // Low temperature ensures strict, objective architectural evaluations
      maxTokens: 4096,
    }
  },

  // 🎭 Cognitive Prompts & Behavioral Rule Injection
  agent: {
    name: 'audit_expert',
    identity: './src/agent/IDENTITY.md',
    soul: './src/agent/SOUL.md',
    strategy: './src/agent/AGENTS.md',
  },

  // 🔌 Model Context Protocol (MCP) Dynamic Tool Bridges
  mcpServers: {
    'compliance-tool-engine': {
      command: 'uv',
      args: ['run', '--project', '/home/ubuntu/agentic-api-conformance-checker', 'python', '-u', '/home/ubuntu/agentic-api-conformance-checker/src/mcp-server/tools/server.py'],
      env: {
        SIMILARITY_THRESHOLD: process.env.SIMILARITY_THRESHOLD || '0.45',
        TRANSFORMERS_OFFLINE: '1',
        HF_HUB_OFFLINE: '1',
      }
    }
  }
};
