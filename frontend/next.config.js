/** @type {import('next').NextConfig} */
const internalBackendPort = process.env.INTERNAL_BACKEND_PORT || "18080";
const internalBackendBase = `http://127.0.0.1:${internalBackendPort}`;

const nextConfig = {
  reactStrictMode: true,
  async rewrites() {
    // 一体デプロイ時は Next.js 内蔵プロキシで FastAPI へ転送（custom server 非依存）
    if (process.env.COMBINED_DEPLOY === "1") {
      return [
        {
          source: "/api/backend/:path*",
          destination: `${internalBackendBase}/:path*`,
        },
        {
          source: "/api/proxy/:path*",
          destination: `${internalBackendBase}/:path*`,
        },
        {
          source: "/backend/:path*",
          destination: `${internalBackendBase}/:path*`,
        },
      ];
    }
    return [];
  },
};

module.exports = nextConfig;
