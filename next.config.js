/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  async rewrites() {
    return [
      {
        // 🌐 Safely routes all client-side /api/agent calls to your OpenClaw agent
        source: '/api/agent/:path*',
        destination: 'http://13.60.45.176:18789/:path*',
      },
    ];
  },
};

module.exports = nextConfig;
