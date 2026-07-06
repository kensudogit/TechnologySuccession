/** @type {import('next').NextConfig} */
function resolveBackendUrlForRewrites() {
  const explicit = process.env.BACKEND_URL?.trim();
  if (explicit) {
    return explicit.replace(/\/$/, "");
  }

  const candidates = [
    process.env.RAILWAY_BACKEND_URL,
    process.env.BACKEND_INTERNAL_URL,
    process.env.NEXT_PUBLIC_API_BASE_URL,
  ];

  for (const raw of candidates) {
    const url = raw?.trim();
    if (!url) continue;
    if (url.includes("localhost") || url.includes("127.0.0.1")) continue;
    return url.replace(/\/$/, "");
  }

  return "http://127.0.0.1:8080";
}

const nextConfig = {
  reactStrictMode: true,
  async rewrites() {
    const backend = resolveBackendUrlForRewrites();
    return [
      {
        source: "/api/proxy/:path*",
        destination: `${backend}/:path*`,
      },
    ];
  },
};

module.exports = nextConfig;
