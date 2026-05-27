/** @type {import('next').NextConfig} */
// In dev, proxy /api/* to the local backend so the browser stays same-origin
// (avoids the CORS preflight that fails when NEXT_PUBLIC_API_URL points cross-origin).
// In prod, NEXT_PUBLIC_API_URL is set at build time and fetched directly.
const isDev = process.env.NODE_ENV === 'development'

const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,
  ...(isDev && {
    async rewrites() {
      return [
        {
          source: '/api/:path*',
          destination: 'http://localhost:8000/api/:path*',
        },
      ]
    },
  }),
}

module.exports = nextConfig
