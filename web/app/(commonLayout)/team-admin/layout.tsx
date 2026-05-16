'use client'

import type { ReactNode } from 'react'
import Link from 'next/link'
import Loading from '@/app/components/base/loading'
import { useAppContext } from '@/context/app-context'
import { hasWorkspaceCapability, WORKSPACE_CAPABILITIES } from '@/utils/workspace-capabilities'

const TeamAdminLayout = ({ children }: { children: ReactNode }) => {
  const { currentWorkspace, isLoadingCurrentWorkspace } = useAppContext()
  const canManageTeamModels = hasWorkspaceCapability(currentWorkspace, WORKSPACE_CAPABILITIES.modelProviderManage)
  const isSystemAdmin = hasWorkspaceCapability(currentWorkspace, WORKSPACE_CAPABILITIES.systemAdmin)

  if (isLoadingCurrentWorkspace)
    return <Loading type="app" />

  if (!canManageTeamModels || isSystemAdmin) {
    return (
      <div className="relative flex h-0 shrink-0 grow flex-col items-center justify-center overflow-y-auto bg-background-body px-6">
        <div className="max-w-md rounded-2xl border border-divider-regular bg-components-panel-bg p-8 text-center shadow-sm">
          <div className="text-lg font-semibold text-text-primary">无权访问团队模型配置页</div>
          <div className="mt-3 text-sm leading-6 text-text-tertiary">
            该页面仅对团队管理员开放，用于维护当前团队专属的大模型服务凭据与限流参数。
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

export default TeamAdminLayout
