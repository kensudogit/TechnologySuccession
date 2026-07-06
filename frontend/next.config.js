/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  async rewrites() {
    // 一体デプロイ時は Next.js 内蔵プロキシで FastAPI へ転送（custom server 非依存）
    if (process.env.COMBINED_DEPLOY === "1") {
      return [
        {
          source: "/api/backend/:path*",
          destination: "http://127.0.0.1:8080/:path*",
        },
        {
          source: "/api/proxy/:path*",
          destination: "http://127.0.0.1:8080/:path*",
        },
        {
          source: "/backend/:path*",
          destination: "http://127.0.0.1:8080/:path*",
        },
      ];
    }
    return [];
  },
};

module.exports = nextConfig;
