import { useMemo } from 'react'
import { useTranslation } from 'react-i18next'
import { useAppContext } from '@/context/app-context'
import { useGlobalPublicStore } from '@/context/global-public-context'
import { useInvalidateReferenceSettings, useMutationReferenceSettings, useReferenceSettings } from '@/service/use-plugins'
import { hasBuiltInAdminAccess, hasWorkspaceCapability, WORKSPACE_CAPABILITIES } from '@/utils/workspace-capabilities'
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
  const systemFeatures = useGlobalPublicStore(s => s.systemFeatures)
  const hasBuiltInAdmin = hasBuiltInAdminAccess(currentWorkspace, systemFeatures)
  const { data } = useReferenceSettings(hasBuiltInAdmin)
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

  return {
    referenceSetting: data,
    setReferenceSettings: updateReferenceSetting,
    canManagement: hasBuiltInAdmin && hasPermission(permissions?.install_permission, true),
    canDebugger: hasBuiltInAdmin && hasPermission(permissions?.debug_permission, true),
    canSetPermissions: hasBuiltInAdmin,
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
