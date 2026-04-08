'use client'

import { useRouter } from 'next/navigation'
import { useEffect } from 'react'
import Loading from '@/app/components/base/loading'
import Marketplace from '@/app/components/plugins/marketplace'
import PluginPage from '@/app/components/plugins/plugin-page'
import PluginsPanel from '@/app/components/plugins/plugin-page/plugins-panel'
import { useAppContext } from '@/context/app-context'
import { hasPluginManageWorkspaceCapability } from '@/utils/workspace-capabilities'

const PluginList = () => {
  const router = useRouter()
  const { currentWorkspace, isLoadingCurrentWorkspace } = useAppContext()
  const canManagePlugin = hasPluginManageWorkspaceCapability(currentWorkspace)

  useEffect(() => {
    if (isLoadingCurrentWorkspace || !currentWorkspace.id)
      return

    if (!canManagePlugin)
      router.replace('/apps')
  }, [canManagePlugin, currentWorkspace.id, isLoadingCurrentWorkspace, router])

  if (isLoadingCurrentWorkspace || !canManagePlugin)
    return <Loading type="app" />

  return (
    <PluginPage
      plugins={<PluginsPanel />}
      marketplace={<Marketplace pluginTypeSwitchClassName="top-[60px]" />}
    />
  )
}

export default PluginList
