'use client'
import type { InvitationResult } from '@/models/common'
import { RiArrowRightLine, RiBrainLine, RiPencilLine, RiPuzzle2Line } from '@remixicon/react'
import { useRouter } from 'next/navigation'
import { useMemo, useState } from 'react'
import { useTranslation } from 'react-i18next'
import Avatar from '@/app/components/base/avatar'
import Button from '@/app/components/base/button'
import Tooltip from '@/app/components/base/tooltip'
import { NUM_INFINITE } from '@/app/components/billing/config'
import { Plan } from '@/app/components/billing/type'
import UpgradeBtn from '@/app/components/billing/upgrade-btn'
import { useAppContext } from '@/context/app-context'
import { useGlobalPublicStore } from '@/context/global-public-context'
import { useLocale } from '@/context/i18n'
import { useModalContext } from '@/context/modal-context'
import { useProviderContext } from '@/context/provider-context'
import { useFormatTimeFromNow } from '@/hooks/use-format-time-from-now'
import { LanguagesSupported } from '@/i18n-config/language'
import { useMembers } from '@/service/use-common'
import { useInstalledPluginList } from '@/service/use-plugins'
import { hasAnyWorkspaceCapability, hasBuiltInAdminAccess, WORKSPACE_CAPABILITIES } from '@/utils/workspace-capabilities'
import { ACCOUNT_SETTING_TAB } from '../constants'
import EditWorkspaceModal from './edit-workspace-modal'
import InviteButton from './invite-button'
import InviteModal from './invite-modal'
import InvitedModal from './invited-modal'
import MemberTagOperation from './member-tag-operation'
import Operation from './operation'
import TransferOwnership from './operation/transfer-ownership'
import TransferOwnershipModal from './transfer-ownership-modal'

const MembersPage = () => {
  const { t } = useTranslation()
  const router = useRouter()
  const RoleMap = {
    owner: t('members.owner', { ns: 'common' }),
    admin: t('members.admin', { ns: 'common' }),
    editor: t('members.editor', { ns: 'common' }),
    dataset_operator: t('members.datasetOperator', { ns: 'common' }),
    normal: t('members.normal', { ns: 'common' }),
  }
  const locale = useLocale()

  const { userProfile, currentWorkspace, isCurrentWorkspaceOwner, isCurrentWorkspaceManager } = useAppContext()
  const { data, refetch } = useMembers()
  const systemFeatures = useGlobalPublicStore(s => s.systemFeatures)
  const { setShowAccountSettingModal } = useModalContext()
  const { formatTimeFromNow } = useFormatTimeFromNow()
  const [inviteModalVisible, setInviteModalVisible] = useState(false)
  const [invitationResults, setInvitationResults] = useState<InvitationResult[]>([])
  const [invitedModalVisible, setInvitedModalVisible] = useState(false)
  const accounts = data?.accounts || []
  const { modelProviders, plan, enableBilling, isAllowTransferWorkspace } = useProviderContext()
  const isNotUnlimitedMemberPlan = enableBilling && plan.type !== Plan.team && plan.type !== Plan.enterprise
  const isMemberFull = enableBilling && isNotUnlimitedMemberPlan && accounts.length >= plan.total.teamMembers
  const [editWorkspaceModalVisible, setEditWorkspaceModalVisible] = useState(false)
  const [showTransferOwnershipModal, setShowTransferOwnershipModal] = useState(false)
  const canManageMemberTags = isCurrentWorkspaceManager
    && ['owner', 'admin'].includes(currentWorkspace.role)
    && hasAnyWorkspaceCapability(currentWorkspace, [
      WORKSPACE_CAPABILITIES.settingsTeam,
      WORKSPACE_CAPABILITIES.teamManage,
    ])
  const canManageModelProviders = hasAnyWorkspaceCapability(currentWorkspace, [
    WORKSPACE_CAPABILITIES.modelProviderManage,
    WORKSPACE_CAPABILITIES.modelManage,
  ])
  const canManagePlugins = hasAnyWorkspaceCapability(currentWorkspace, [
    WORKSPACE_CAPABILITIES.pluginManage,
    WORKSPACE_CAPABILITIES.apiExtensionManage,
  ])
  const hasBuiltInAdmin = hasBuiltInAdminAccess(currentWorkspace, systemFeatures)
  const showInstallWorkbench = hasBuiltInAdmin && (canManageModelProviders || canManagePlugins)
  const { data: installedPluginList, isLoading: isInstalledPluginListLoading } = useInstalledPluginList(!canManagePlugins, 20)
  const configuredProviderCount = useMemo(() => {
    return modelProviders.filter(provider =>
      provider.custom_configuration.status === 'active'
      || provider.system_configuration.enabled === true,
    ).length
  }, [modelProviders])

  const openProviderSettings = () => {
    setShowAccountSettingModal({
      payload: ACCOUNT_SETTING_TAB.PROVIDER,
    })
  }

  const openPluginCenter = () => {
    setShowAccountSettingModal(null)
    router.push('/plugins')
  }

  return (
    <>
      <div className="flex flex-col">
        <div className="mb-4 flex items-center gap-3 rounded-xl border-l-[0.5px] border-t-[0.5px] border-divider-subtle bg-gradient-to-r from-background-gradient-bg-fill-chat-bg-2 to-background-gradient-bg-fill-chat-bg-1 p-3 pr-5">
          <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-components-icon-bg-blue-solid text-[20px]">
            <span className="bg-gradient-to-r from-components-avatar-shape-fill-stop-0 to-components-avatar-shape-fill-stop-100 bg-clip-text font-semibold uppercase text-shadow-shadow-1 opacity-90">{currentWorkspace?.name[0]?.toLocaleUpperCase()}</span>
          </div>
          <div className="grow">
            <div className="system-md-semibold flex items-center gap-1 text-text-secondary">
              <span>{currentWorkspace?.name}</span>
              {isCurrentWorkspaceOwner && (
                <span>
                  <Tooltip
                    popupContent={t('account.editWorkspaceInfo', { ns: 'common' })}
                  >
                    <div
                      className="cursor-pointer rounded-md p-1 hover:bg-black/5"
                      onClick={() => {
                        setEditWorkspaceModalVisible(true)
                      }}
                    >
                      <RiPencilLine className="h-4 w-4 text-text-tertiary" />
                    </div>
                  </Tooltip>
                </span>
              )}
            </div>
            <div className="system-xs-medium mt-1 text-text-tertiary">
              {enableBilling && isNotUnlimitedMemberPlan
                ? (
                    <div className="flex space-x-1">
                      <div>
                        {t('plansCommon.member', { ns: 'billing' })}
                        {locale !== LanguagesSupported[1] && accounts.length > 1 && 's'}
                      </div>
                      <div className="">{accounts.length}</div>
                      <div>/</div>
                      <div>{plan.total.teamMembers === NUM_INFINITE ? t('plansCommon.unlimited', { ns: 'billing' }) : plan.total.teamMembers}</div>
                    </div>
                  )
                : (
                    <div className="flex space-x-1">
                      <div>{accounts.length}</div>
                      <div>
                        {t('plansCommon.memberAfter', { ns: 'billing' })}
                        {locale !== LanguagesSupported[1] && accounts.length > 1 && 's'}
                      </div>
                    </div>
                  )}
            </div>

          </div>
          {isMemberFull && (
            <UpgradeBtn className="mr-2" loc="member-invite" />
          )}
          <div className="flex shrink-0 items-center gap-2">
            <InviteButton disabled={!isCurrentWorkspaceManager || isMemberFull} onClick={() => setInviteModalVisible(true)} />
          </div>
        </div>
        {showInstallWorkbench && (
          <div className="mb-5 rounded-xl border border-[#dbeafe] bg-[#f9fbff] p-4 shadow-sm dark:border-blue-400/20 dark:bg-blue-500/10 dark:shadow-black/20">
            <div className="flex flex-col gap-2 border-b border-[#dbeafe] pb-4 sm:flex-row sm:items-end sm:justify-between dark:border-blue-400/20">
              <div>
                <div className="system-md-semibold text-text-primary">
                  {t('members.installWorkbenchTitle', { ns: 'common', defaultValue: '系统安装能力' })}
                </div>
                <div className="system-sm-regular mt-1 text-text-secondary">
                  {t('members.installWorkbenchDescription', {
                    ns: 'common',
                    defaultValue: 'built-in Admin 可在此快速进入模型服务与工具插件安装入口，无需先切换到其他页面。',
                  })}
                </div>
              </div>
              <div className="system-xs-medium rounded-full bg-white px-3 py-1 text-[#2563eb] shadow-sm dark:bg-blue-500/15 dark:text-blue-200 dark:shadow-black/20">
                {t('members.installWorkbenchBadge', {
                  ns: 'common',
                  defaultValue: '系统管理员专属',
                })}
              </div>
            </div>
            <div className="mt-4 grid gap-3 xl:grid-cols-2">
              {canManageModelProviders && (
                <div className="rounded-xl border border-divider-subtle bg-white p-4 shadow-sm transition-all duration-200 hover:translate-y-[-2px] hover:shadow-md dark:border-white/10 dark:bg-[#24252b] dark:shadow-black/20">
                  <div className="flex items-start gap-3">
                    <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-[#eff6ff] text-[#2563eb] dark:bg-blue-500/15 dark:text-blue-300">
                      <RiBrainLine className="h-5 w-5" />
                    </div>
                    <div className="min-w-0 grow">
                      <div className="system-md-semibold text-text-primary">
                        {t('members.modelInstallTitle', { ns: 'common', defaultValue: '模型服务安装' })}
                      </div>
                      <div className="system-xs-regular mt-1 text-text-secondary">
                        {t('members.modelInstallDescription', {
                          ns: 'common',
                          defaultValue: '集中接入并配置当前工作空间可用的模型服务，安装后即可用于对话与应用。',
                        })}
                      </div>
                    </div>
                  </div>
                  <div className="mt-4 flex flex-wrap gap-2">
                    <div className="system-xs-medium rounded-full bg-[#eff6ff] px-3 py-1 text-[#2563eb] dark:bg-blue-500/15 dark:text-blue-200">
                      {t('members.modelInstallCount', {
                        ns: 'common',
                        defaultValue: '已接入 {{count}} 个模型服务',
                        count: configuredProviderCount,
                      })}
                    </div>
                    <div className="system-xs-medium rounded-full bg-components-badge-bg-dimm px-3 py-1 text-text-secondary">
                      {t('members.modelInstallScope', {
                        ns: 'common',
                        defaultValue: '支持系统默认模型设置',
                      })}
                    </div>
                  </div>
                  <div className="mt-4 flex flex-wrap gap-2">
                    <Button variant="primary" onClick={openProviderSettings}>
                      {t('members.modelInstallAction', {
                        ns: 'common',
                        defaultValue: configuredProviderCount > 0 ? '管理模型服务' : '安装模型服务',
                      })}
                    </Button>
                    <Button variant="secondary" onClick={openProviderSettings}>
                      {t('members.modelInstallSecondaryAction', {
                        ns: 'common',
                        defaultValue: '打开系统模型设置',
                      })}
                      <RiArrowRightLine className="ml-1 h-4 w-4" />
                    </Button>
                  </div>
                </div>
              )}
              {canManagePlugins && (
                <div className="rounded-xl border border-divider-subtle bg-white p-4 shadow-sm transition-all duration-200 hover:translate-y-[-2px] hover:shadow-md dark:border-white/10 dark:bg-[#24252b] dark:shadow-black/20">
                  <div className="flex items-start gap-3">
                    <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-[#eef2ff] text-[#4f46e5] dark:bg-indigo-500/15 dark:text-indigo-300">
                      <RiPuzzle2Line className="h-5 w-5" />
                    </div>
                    <div className="min-w-0 grow">
                      <div className="system-md-semibold text-text-primary">
                        {t('members.pluginInstallTitle', { ns: 'common', defaultValue: '工具插件安装' })}
                      </div>
                      <div className="system-xs-regular mt-1 text-text-secondary">
                        {t('members.pluginInstallDescription', {
                          ns: 'common',
                          defaultValue: '前往工具插件页面安装、更新或启停插件，统一管理当前系统可用工具。',
                        })}
                      </div>
                    </div>
                  </div>
                  <div className="mt-4 flex flex-wrap gap-2">
                    <div className="system-xs-medium rounded-full bg-[#eef2ff] px-3 py-1 text-[#4338ca] dark:bg-indigo-500/15 dark:text-indigo-200">
                      {isInstalledPluginListLoading
                        ? '--'
                        : t(
                            'members.pluginInstallCount',
                            '已安装 {{count}} 个插件',
                            {
                              ns: 'common',
                              count: installedPluginList?.total || 0,
                            },
                          )}
                    </div>
                    <div className="system-xs-medium rounded-full bg-components-badge-bg-dimm px-3 py-1 text-text-secondary">
                      {t('members.pluginInstallScope', {
                        ns: 'common',
                        defaultValue: '支持插件安装与启停管理',
                      })}
                    </div>
                  </div>
                  <div className="mt-4 flex flex-wrap gap-2">
                    <Button variant="primary" onClick={openPluginCenter}>
                      {t('members.pluginInstallAction', {
                        ns: 'common',
                        defaultValue: '安装工具插件',
                      })}
                    </Button>
                    <Button variant="secondary" onClick={openPluginCenter}>
                      {t('members.pluginInstallSecondaryAction', {
                        ns: 'common',
                        defaultValue: '打开工具插件页',
                      })}
                      <RiArrowRightLine className="ml-1 h-4 w-4" />
                    </Button>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
        <div className="overflow-visible lg:overflow-visible">
          <div className="flex min-w-[480px] items-center border-b border-divider-regular py-[7px]">
            <div className="system-xs-medium-uppercase grow px-3 text-text-tertiary">{t('members.name', { ns: 'common' })}</div>
            <div className="system-xs-medium-uppercase w-[104px] shrink-0 text-text-tertiary">{t('members.lastActive', { ns: 'common' })}</div>
            <div className="system-xs-medium-uppercase w-[96px] shrink-0 px-3 text-text-tertiary">{t('members.role', { ns: 'common' })}</div>
            {canManageMemberTags && (
              <div className="system-xs-medium-uppercase w-[148px] shrink-0 px-3 text-text-tertiary">成员标签</div>
            )}
          </div>
          <div className="relative min-w-[480px]">
            {
              accounts.map(account => (
                <div key={account.id} className="flex border-b border-divider-subtle">
                  <div className="flex grow items-center px-3 py-2">
                    <Avatar avatar={account.avatar_url} size={24} className="mr-2" name={account.name} />
                    <div className="">
                      <div className="system-sm-medium text-text-secondary">
                        {account.name}
                        {account.status === 'pending' && <span className="system-xs-medium ml-1 text-text-warning">{t('members.pending', { ns: 'common' })}</span>}
                        {userProfile.email === account.email && <span className="system-xs-regular text-text-tertiary">{t('members.you', { ns: 'common' })}</span>}
                      </div>
                      <div className="system-xs-regular text-text-tertiary">{account.email}</div>
                    </div>
                  </div>
                  <div className="system-sm-regular flex w-[104px] shrink-0 items-center py-2 text-text-secondary">{formatTimeFromNow(Number((account.last_active_at || account.created_at)) * 1000)}</div>
                  <div className="flex w-[96px] shrink-0 items-center">
                    {isCurrentWorkspaceOwner && account.role === 'owner' && isAllowTransferWorkspace && (
                      <TransferOwnership onOperate={() => setShowTransferOwnershipModal(true)}></TransferOwnership>
                    )}
                    {isCurrentWorkspaceOwner && account.role === 'owner' && !isAllowTransferWorkspace && (
                      <div className="system-sm-regular px-3 text-text-secondary">{RoleMap[account.role] || RoleMap.normal}</div>
                    )}
                    {isCurrentWorkspaceManager && account.role !== 'owner' && (
                      <Operation member={account} operatorRole={currentWorkspace.role} onOperate={refetch} />
                    )}
                    {!isCurrentWorkspaceManager && (
                      <div className="system-sm-regular px-3 text-text-secondary">{RoleMap[account.role] || RoleMap.normal}</div>
                    )}
                    {isCurrentWorkspaceManager && account.role === 'owner' && !isCurrentWorkspaceOwner && (
                      <div className="system-sm-regular px-3 text-text-secondary">{RoleMap[account.role] || RoleMap.normal}</div>
                    )}
                  </div>
                  {canManageMemberTags && (
                    <div className="flex w-[148px] shrink-0 items-center">
                      <MemberTagOperation
                        member={account}
                        orgId={currentWorkspace.id}
                        onOperate={refetch}
                      />
                    </div>
                  )}
                </div>
              ))
            }
          </div>
        </div>
      </div>
      {
        inviteModalVisible && (
          <InviteModal
            isEmailSetup={systemFeatures.is_email_setup}
            onCancel={() => setInviteModalVisible(false)}
            onSend={(invitationResults) => {
              setInvitedModalVisible(true)
              setInvitationResults(invitationResults)
              refetch()
            }}
          />
        )
      }
      {
        invitedModalVisible && (
          <InvitedModal
            invitationResults={invitationResults}
            onCancel={() => setInvitedModalVisible(false)}
          />
        )
      }
      {
        editWorkspaceModalVisible && (
          <EditWorkspaceModal
            onCancel={() => setEditWorkspaceModalVisible(false)}
          />
        )
      }
      {showTransferOwnershipModal && (
        <TransferOwnershipModal
          show={showTransferOwnershipModal}
          onClose={() => setShowTransferOwnershipModal(false)}
        />
      )}
    </>
  )
}

export default MembersPage
