import type { Metadata } from 'next'
import SignInPageClient from './page-client'

export const metadata: Metadata = {
  title: '登录CheersAI-Desktop',
  description: '使用企业单点登录进入 CheersAI Desktop 工作区，获得安全、可审计、可扩展的 AI 协作体验。',
}

export default function SignInPage() {
  return <SignInPageClient />
}
