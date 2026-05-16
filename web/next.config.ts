import type { NextConfig } from 'next'
import process from 'node:process'
import withBundleAnalyzerInit from '@next/bundle-analyzer'
import createMDX from '@next/mdx'
import { codeInspectorPlugin } from 'code-inspector-plugin'

const isDev = process.env.NODE_ENV === 'development'
const withMDX = createMDX({
  extension: /\.mdx?$/,
  options: {
    // If you use remark-gfm, you'll need to use next.config.mjs
    // as the package is ESM only
    // https://github.com/remarkjs/remark-gfm#install
    remarkPlugins: [],
    rehypePlugins: [],
    // If you use `MDXProvider`, uncomment the following line.
    // providerImportSource: "@mdx-js/react",
  },
})
const withBundleAnalyzer = withBundleAnalyzerInit({
  enabled: process.env.ANALYZE === 'true',
})

// the default url to prevent parse url error when running jest
const hasSetWebPrefix = process.env.NEXT_PUBLIC_WEB_PREFIX
const port = process.env.PORT || 3000
const locImageURLs = !hasSetWebPrefix ? [new URL(`http://localhost:${port}/**`), new URL(`http://127.0.0.1:${port}/**`)] : []
const remoteImageURLs = ([hasSetWebPrefix ? new URL(`${process.env.NEXT_PUBLIC_WEB_PREFIX}/**`) : '', ...locImageURLs].filter(item => !!item)) as URL[]

const nextConfig: NextConfig = {
  experimental: {
    cpus: 1,
    workerThreads: false,
    memoryBasedWorkersCount: true,
    turbopackFileSystemCacheForDev: false,
  },
  typescript: { ignoreBuildErrors: true },
  basePath: process.env.NEXT_PUBLIC_BASE_PATH || '',
  // 关键配置：强制使用末尾斜杠，避免与 Nginx 子路径部署的重定向死循环
  trailingSlash: true,
  serverExternalPackages: ['esbuild-wasm'],
  transpilePackages: ['echarts', 'zrender'],
  turbopack: {
    rules: codeInspectorPlugin({
      bundler: 'turbopack',
    }),
  },
  productionBrowserSourceMaps: false, // enable browser source map generation during the production build
  // Configure pageExtensions to include md and mdx
  pageExtensions: ['ts', 'tsx', 'js', 'jsx', 'md', 'mdx'],
  // https://nextjs.org/docs/messages/next-image-unconfigured-host
  images: {
    remotePatterns: remoteImageURLs.map(remoteImageURL => ({
      protocol: remoteImageURL.protocol.replace(':', '') as 'http' | 'https',
      hostname: remoteImageURL.hostname,
      port: remoteImageURL.port,
      pathname: remoteImageURL.pathname,
      search: '',
    })),
  },
  reactStrictMode: true,
  async rewrites() {
    return [
      {
        source: '/console/api/:path*/',
        destination: 'http://localhost:9000/console/api/:path*',
      },
      {
        source: '/console/api/:path*',
        destination: 'http://localhost:9000/console/api/:path*',
      },
    ]
  },
  async redirects() {
    return [
      {
        source: '/',
        destination: '/signin',
        permanent: false,
      },
    ]
  },
  // Keep standalone tracing inside `web` so local Docker builds do not scan the repo root.
  outputFileTracingRoot: process.cwd(),
  output: 'standalone',
  compiler: {
    removeConsole: isDev ? false : { exclude: ['warn', 'error'] },
  },
  devIndicators: false,
  allowedDevOrigins: [
    '192.168.0.3',
    'http://192.168.0.3',
    'http://192.168.0.3:3000',
    'localhost',
    'http://localhost',
    'http://localhost:3000',
    '127.0.0.1',
    'http://127.0.0.1',
    'http://127.0.0.1:3000',
    '0.0.0.0',
    'http://0.0.0.0',
    'http://0.0.0.0:3000',
  ],
}

export default withBundleAnalyzer(withMDX(nextConfig))
