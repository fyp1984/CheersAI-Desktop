'use client'

import { useRouter } from 'next/navigation'
import { useEffect } from 'react'
import Loading from '@/app/components/base/loading'
import { useAppContext } from '@/context/app-context'
import { ExternalApiPanelProvider } from '@/context/external-api-panel-context'
import { ExternalKnowledgeApiProvider } from '@/context/external-knowledge-api-context'
import { hasWorkspaceCapability, WORKSPACE_CAPABILITIES } from '@/utils/workspace-capabilities'

export default function DatasetsLayout({ children }: { children: React.ReactNode }) {
  const { currentWorkspace, isLoadingCurrentWorkspace } = useAppContext()
  const router = useRouter()
  const canViewKnowledge = hasWorkspaceCapability(currentWorkspace, WORKSPACE_CAPABILITIES.knowledgeView)

  useEffect(() => {
    if (isLoadingCurrentWorkspace || !currentWorkspace.id)
      return
    if (!canViewKnowledge)
      router.replace('/apps')
  }, [canViewKnowledge, isLoadingCurrentWorkspace, currentWorkspace, router])

  if (isLoadingCurrentWorkspace || !canViewKnowledge)
    return <Loading type="app" />
  return (
    <ExternalKnowledgeApiProvider>
      <ExternalApiPanelProvider>
        {children}
      </ExternalApiPanelProvider>
    </ExternalKnowledgeApiProvider>
  )
}
