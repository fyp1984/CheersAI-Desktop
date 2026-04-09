'use client'
import type { FC } from 'react'
import type { CurrentTryAppParams } from '@/context/explore-context'
import type { InstalledApp } from '@/models/explore'
import * as React from 'react'
import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import Sidebar from '@/app/components/explore/sidebar'
import { useAppContext } from '@/context/app-context'
import ExploreContext from '@/context/explore-context'
import useDocumentTitle from '@/hooks/use-document-title'

export type IExploreProps = {
  children: React.ReactNode
}

const Explore: FC<IExploreProps> = ({
  children,
}) => {
  const [controlUpdateInstalledApps, setControlUpdateInstalledApps] = useState(0)
  const { canEditApps } = useAppContext()
  const [hasEditPermission, setHasEditPermission] = useState(false)
  const [installedApps, setInstalledApps] = useState<InstalledApp[]>([])
  const [isFetchingInstalledApps, setIsFetchingInstalledApps] = useState(false)
  const { t } = useTranslation()
  useDocumentTitle(t('menus.explore', { ns: 'common' }))

  useEffect(() => {
    setHasEditPermission(canEditApps)
  }, [canEditApps])

  const [currentTryAppParams, setCurrentTryAppParams] = useState<CurrentTryAppParams | undefined>(undefined)
  const [isShowTryAppPanel, setIsShowTryAppPanel] = useState(false)
  const setShowTryAppPanel = (showTryAppPanel: boolean, params?: CurrentTryAppParams) => {
    if (showTryAppPanel)
      setCurrentTryAppParams(params)
    else
      setCurrentTryAppParams(undefined)
    setIsShowTryAppPanel(showTryAppPanel)
  }

  return (
    <div className="flex h-full overflow-hidden border-t border-divider-regular bg-background-body">
      <ExploreContext.Provider
        value={
          {
            controlUpdateInstalledApps,
            setControlUpdateInstalledApps,
            hasEditPermission,
            installedApps,
            setInstalledApps,
            isFetchingInstalledApps,
            setIsFetchingInstalledApps,
            currentApp: currentTryAppParams,
            isShowTryAppPanel,
            setShowTryAppPanel,
          }
        }
      >
        <Sidebar controlUpdateInstalledApps={controlUpdateInstalledApps} />
        <div className="w-0 grow">
          {children}
        </div>
      </ExploreContext.Provider>
    </div>
  )
}
export default React.memo(Explore)
