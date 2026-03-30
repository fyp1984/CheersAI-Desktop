'use client'
import Link from 'next/link'
import { useGlobalPublicStore } from '@/context/global-public-context'

import useDocumentTitle from '@/hooks/use-document-title'

export default function SignInLayout({ children }: any) {
  const { systemFeatures } = useGlobalPublicStore()
  useDocumentTitle('')
  return (
    <>
      <div className="flex min-h-screen w-full items-center justify-center bg-white p-4">
        {/* 居中的登录卡片 */}
        <div className="relative w-full max-w-4xl overflow-hidden rounded-2xl bg-white shadow-2xl">
          {/* Logo区域 - 左上角 */}
          <div className="absolute left-6 top-6 z-20 flex items-center gap-3">
            <img
              src={`${process.env.NEXT_PUBLIC_BASE_PATH || ''}/logo/logo-monochrome-white.png`}
              alt="CheersAI Logo"
              className="h-10 w-10 rounded-xl"
            />
            <span className="text-xl font-bold text-white">CheersAI企业版</span>
          </div>

          <div className="flex min-h-[600px]">
            {/* 左侧宣传区域 */}
            <div className="relative hidden overflow-hidden bg-gradient-to-br from-blue-500 via-blue-600 to-blue-700 md:flex md:w-1/2">
              {/* 背景装饰 */}
              <div className="absolute inset-0 bg-gradient-to-br from-blue-400/20 to-transparent"></div>

              <div className="relative z-10 flex flex-col justify-center px-8 py-8 pt-20 text-white">
                {/* 主标题 */}
                <h1 className="mb-6 text-3xl font-bold leading-tight">
                  开启智能办公新体验
                </h1>

                {/* 副标题 */}
                <p className="mb-8 text-lg text-blue-100">
                  企业级AI助手平台，提升团队协作效率
                </p>

                {/* 特性列表 */}
                <div className="mb-8 space-y-4">
                  <div className="flex items-center gap-3">
                    <div className="h-2 w-2 rounded-full bg-white"></div>
                    <span className="text-blue-100">【智能对话】多模态AI交互体验</span>
                  </div>
                  <div className="flex items-center gap-3">
                    <div className="h-2 w-2 rounded-full bg-white"></div>
                    <span className="text-blue-100">【数据安全】企业级安全防护</span>
                  </div>
                  <div className="flex items-center gap-3">
                    <div className="h-2 w-2 rounded-full bg-white"></div>
                    <span className="text-blue-100">【工作流程】智能化业务流程</span>
                  </div>
                  <div className="flex items-center gap-3">
                    <div className="h-2 w-2 rounded-full bg-white"></div>
                    <span className="text-blue-100">【团队协作】高效协同办公</span>
                  </div>
                </div>

                {/* 底部插图区域 */}
                <div className="mt-auto flex justify-center">
                  <div className="flex h-36 w-56 items-center justify-center rounded-xl bg-white/10 backdrop-blur-sm">
                    <div className="text-center">
                      <div className="mx-auto mb-3 flex h-16 w-16 items-center justify-center rounded-full bg-white/20">
                        <span className="text-2xl">🤖</span>
                      </div>
                      <p className="text-sm text-blue-100">智能AI助手</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* 右侧登录区域 */}
            <div className="flex w-full flex-col bg-gray-50 md:w-1/2">
              {/* 头部 */}
              <div className="flex items-center justify-end p-6">
                <div>
                  <span className="text-xs text-gray-500">还没有账号？</span>
                  <Link href="/signup/" className="ml-1 text-xs text-blue-600 hover:text-blue-700">立即注册</Link>
                </div>
              </div>

              {/* 登录表单区域 */}
              <div className="flex flex-1 items-center justify-center px-6">
                <div className="w-full max-w-sm">
                  {children}
                </div>
              </div>

              {/* 底部版权 */}
              {systemFeatures.branding.enabled === false && (
                <div className="p-6 text-center">
                  <p className="text-xs text-gray-400">
                    ©
                    {' '}
                    {new Date().getFullYear()}
                    {' '}
                    CheersAI. All rights reserved.
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </>
  )
}
