'use client'

import type { PropsWithChildren } from 'react'
import { useRouter } from 'next/navigation'
import { useEffect } from 'react'
import Loading from '@/app/components/base/loading'
import { useAppContext } from '@/context/app-context'
import { hasWorkspaceCapability, WORKSPACE_CAPABILITIES } from '@/utils/workspace-capabilities'

type Props = PropsWithChildren<{
  fallbackHref?: string
}>

const RequireKnowledgeEdit = ({
  children,
  fallbackHref = '/datasets',
}: Props) => {
  const { currentWorkspace, isLoadingCurrentWorkspace } = useAppContext()
  const router = useRouter()
  const canEditKnowledge = hasWorkspaceCapability(currentWorkspace, WORKSPACE_CAPABILITIES.knowledgeEdit)

  useEffect(() => {
    if (isLoadingCurrentWorkspace || !currentWorkspace.id)
      return
    if (!canEditKnowledge)
      router.replace(fallbackHref)
  }, [canEditKnowledge, currentWorkspace.id, fallbackHref, isLoadingCurrentWorkspace, router])

  if (isLoadingCurrentWorkspace || !canEditKnowledge)
    return <Loading type="app" />

  return <>{children}</>
}

export default RequireKnowledgeEdit
