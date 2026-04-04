'use client'
import Link from 'next/link'
import { useGlobalPublicStore } from '@/context/global-public-context'
import useDocumentTitle from '@/hooks/use-document-title'

export default function SignInLayout({ children }: any) {
  const { systemFeatures } = useGlobalPublicStore()
  useDocumentTitle('')
  return (
    <>
      <div className="flex min-h-screen w-full items-center justify-center bg-gradient-to-br from-gray-50 to-gray-100 p-4">
        {/* 居中的登录区域 */}
        <div className="relative w-full max-w-md">
          {/* Logo - 顶部居中，圆角 */}
          <div className="mb-8 flex justify-center">
            <div className="flex h-20 w-20 items-center justify-center overflow-hidden rounded-2xl bg-blue-600 shadow-lg">
              <img
                src={`${process.env.NEXT_PUBLIC_BASE_PATH || ''}/logo/CheersAI.png`}
                alt="CheersAI Logo"
                className="h-full w-full object-cover"
              />
            </div>
          </div>

          {/* 登录内容区域 - 无边框 */}
          <div className="w-full">
            {children}
          </div>

          {/* 底部版权 */}
          {systemFeatures.branding.enabled === false && (
            <div className="mt-8 text-center">
              <p className="text-xs text-gray-400">
                ©
                {' '}
                {new Date().getFullYear()}
                {' '}
                <Link
                  href="https://www.cheersai.cloud"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-blue-600 hover:text-blue-700"
                >
                  CheersAI
                </Link>
                . All rights reserved.
              </p>
            </div>
          )}
        </div>
      </div>
    </>
  )
}
