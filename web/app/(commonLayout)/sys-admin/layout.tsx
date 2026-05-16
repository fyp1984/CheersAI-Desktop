'use client'

import type { ReactNode } from 'react'
import Link from 'next/link'
import Loading from '@/app/components/base/loading'
import { useAppContext } from '@/context/app-context'
import { hasWorkspaceCapability, WORKSPACE_CAPABILITIES } from '@/utils/workspace-capabilities'

const SysAdminLayout = ({ children }: { children: ReactNode }) => {
  const { currentWorkspace, isLoadingCurrentWorkspace } = useAppContext()
  const isSystemAdmin = hasWorkspaceCapability(currentWorkspace, WORKSPACE_CAPABILITIES.systemAdmin)

  if (isLoadingCurrentWorkspace)
    return <Loading type="app" />

  if (!isSystemAdmin) {
    return (
      <div className="relative flex h-0 shrink-0 grow flex-col items-center justify-center overflow-y-auto bg-background-body px-6">
        <div className="max-w-md rounded-2xl border border-divider-regular bg-components-panel-bg p-8 text-center shadow-sm">
          <div className="text-lg font-semibold text-text-primary">无权访问系统治理页</div>
          <div className="mt-3 text-sm leading-6 text-text-tertiary">
            `/sys-admin/*` 仅对 built-in Admin 开放，用于系统级插件治理、审计查看与全局运维入口汇总。
          </div>
          <div className="mt-6">
            <Link
              href="/apps"
              className="inline-flex items-center rounded-lg bg-components-button-primary-bg px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-components-button-primary-hover-bg"
            >
              返回我的 Agent
            </Link>
          </div>
        </div>
      </div>
    )
  }

  return <>{children}</>
}

export default SysAdminLayout
