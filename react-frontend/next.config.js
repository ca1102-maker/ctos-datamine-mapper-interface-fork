/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  images: {
    domains: [],
  },
  // Turbopack config (Next.js 16+ default bundler)
  turbopack: {
    resolveAlias: {
      // Use plotly.js-basic-dist-min to avoid glslify errors
      'plotly.js': 'plotly.js-basic-dist-min',
    },
  },
}

module.exports = nextConfig

