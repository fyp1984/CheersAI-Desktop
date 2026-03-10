import type { NextConfig } from 'next'
import process from 'node:process'
import createMDX from '@next/mdx'

const isDev = process.env.NODE_ENV === 'development'

// 排除不需要静态导出的动态路由（Web 分享页面，Electron 不需要）
const excludedPaths = [
  '/chat/[token]',
  '/chatbot/[token]',
  '/completion/[token]',
  '/workflow/[token]',
]

const withMDX = createMDX({
  extension: /\.mdx?$/,
  options: {
    remarkPlugins: [],
    rehypePlugins: [],
  },
})

const nextConfig: NextConfig = {
  basePath: process.env.NEXT_PUBLIC_BASE_PATH || '',
  output: 'export',
  distDir: 'out',
  images: {
    unoptimized: true,
  },
  pageExtensions: ['ts', 'tsx', 'js', 'jsx', 'md', 'mdx'],
  typescript: {
    ignoreBuildErrors: true,
  },
  reactStrictMode: true,
  compiler: {
    removeConsole: isDev ? false : { exclude: ['warn', 'error'] },
  },
  trailingSlash: true,
}

export default withMDX(nextConfig)
