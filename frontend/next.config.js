/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,
  async redirects() {
    return [
      {
        source: '/spelling-rules',
        destination: '/learn/spelling-rules',
        permanent: true,
      },
      {
        source: '/sentence-structure',
        destination: '/learn/sentence-structure',
        permanent: true,
      },
      {
        source: '/resources',
        destination: '/learn/typing-tibetan',
        permanent: false,
      },
    ]
  },
}

module.exports = nextConfig
