import { useMemo } from 'react'
import { useTranslation } from 'react-i18next'
import { useAppContext } from '@/context/app-context'
import { useGlobalPublicStore } from '@/context/global-public-context'
import { useInvalidateReferenceSettings, useMutationReferenceSettings, useReferenceSettings } from '@/service/use-plugins'
import { hasWorkspaceCapability, WORKSPACE_CAPABILITIES } from '@/utils/workspace-capabilities'
import Toast from '../../base/toast'
import { PermissionType } from '../types'

const hasPermission = (permission: PermissionType | undefined, isAdmin: boolean) => {
  if (!permission)
    return false

  if (permission === PermissionType.noOne)
    return false

  if (permission === PermissionType.everyone)
    return true

  return isAdmin
}

const useReferenceSetting = () => {
  const { t } = useTranslation()
  const { currentWorkspace } = useAppContext()
  const { data } = useReferenceSettings()
  // console.log(data)
  const { permission: permissions } = data || {}
  const invalidateReferenceSettings = useInvalidateReferenceSettings()
  const { mutate: updateReferenceSetting, isPending: isUpdatePending } = useMutationReferenceSettings({
    onSuccess: () => {
      invalidateReferenceSettings()
      Toast.notify({
        type: 'success',
        message: t('api.actionSuccess', { ns: 'common' }),
      })
    },
  })
  const isSystemAdmin = hasWorkspaceCapability(currentWorkspace, WORKSPACE_CAPABILITIES.systemAdmin)

  return {
    referenceSetting: data,
    setReferenceSettings: updateReferenceSetting,
    canManagement: isSystemAdmin && hasPermission(permissions?.install_permission, true),
    canDebugger: isSystemAdmin && hasPermission(permissions?.debug_permission, true),
    canSetPermissions: isSystemAdmin,
    isUpdatePending,
  }
}

export const useCanInstallPluginFromMarketplace = () => {
  const { enable_marketplace } = useGlobalPublicStore(s => s.systemFeatures)
  const { canManagement } = useReferenceSetting()

  const canInstallPluginFromMarketplace = useMemo(() => {
    return enable_marketplace && canManagement
  }, [enable_marketplace, canManagement])

  return {
    canInstallPluginFromMarketplace,
  }
}

export default useReferenceSetting
