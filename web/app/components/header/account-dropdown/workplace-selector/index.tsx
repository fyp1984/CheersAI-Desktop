import type { Plan } from '@/app/components/billing/type'
import { Menu, MenuButton, MenuItem, MenuItems, Transition } from '@headlessui/react'
import { RiArrowDownSLine, RiCheckLine } from '@remixicon/react'
import { Fragment } from 'react'
import { useTranslation } from 'react-i18next'
import { useContext } from 'use-context-selector'
import { ToastContext } from '@/app/components/base/toast'
import PlanBadge from '@/app/components/header/plan-badge'
import { useAppContext } from '@/context/app-context'
import { useWorkspacesContext } from '@/context/workspace-context'
import { switchWorkspace } from '@/service/common'
import { cn } from '@/utils/classnames'
import { basePath } from '@/utils/var'

type WorkplaceSelectorProps = {
  compact?: boolean
}

const WorkplaceSelector = ({ compact = false }: WorkplaceSelectorProps) => {
  const { t } = useTranslation()
  const { notify } = useContext(ToastContext)
  const { currentWorkspace } = useAppContext()
  const { workspaces } = useWorkspacesContext()
  const workspaceOptions = workspaces.length
    ? workspaces
    : currentWorkspace.id
      ? [{
          id: currentWorkspace.id,
          name: currentWorkspace.name,
          plan: currentWorkspace.plan,
          status: currentWorkspace.status,
          created_at: currentWorkspace.created_at,
          current: true,
        }]
      : []
  const activeWorkspace = workspaceOptions.find(v => v.current) || workspaceOptions.find(v => v.id === currentWorkspace.id)

  if (!activeWorkspace)
    return null

  const handleSwitchWorkspace = async (tenant_id: string) => {
    try {
      if (activeWorkspace.id === tenant_id)
        return
      await switchWorkspace({ url: '/workspaces/switch', body: { tenant_id } })
      notify({ type: 'success', message: t('actionMsg.modifiedSuccessfully', { ns: 'common' }) })
      location.assign(`${location.origin}${basePath}`)
    }
    catch {
      notify({ type: 'error', message: t('provider.saveFailed', { ns: 'common' }) })
    }
  }

  return (
    <Menu as="div" className="min-w-0">
      {
        ({ open }) => (
          <>
            {compact ? (
              <MenuButton
                className={cn(
                  'flex w-full items-center gap-2 rounded-lg px-3 py-2 text-left transition',
                  open ? 'bg-state-base-hover' : 'hover:bg-state-base-hover',
                )}
                aria-label={t('userProfile.workspace', { ns: 'common' })}
              >
                <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-components-icon-bg-blue-solid text-[13px]">
                  <span className="h-6 bg-gradient-to-r from-components-avatar-shape-fill-stop-0 to-components-avatar-shape-fill-stop-100 bg-clip-text align-middle font-semibold uppercase leading-6 text-shadow-shadow-1 opacity-90">{activeWorkspace.name[0]?.toLocaleUpperCase()}</span>
                </div>
                <div className="min-w-0 grow">
                  <div className="system-xs-medium-uppercase text-text-tertiary">{t('userProfile.workspace', { ns: 'common' })}</div>
                  <div className="truncate system-sm-medium text-text-primary">{activeWorkspace.name}</div>
                </div>
                <RiArrowDownSLine className={cn('h-4 w-4 shrink-0 text-text-tertiary transition-transform', open && 'rotate-180')} />
              </MenuButton>
            ) : (
              <MenuButton className={cn(
                `
                  group flex w-full cursor-pointer items-center
                  rounded-[10px] p-0.5 hover:bg-state-base-hover ${open && 'bg-state-base-hover'}
                `,
              )}
                aria-label={t('userProfile.workspace', { ns: 'common' })}
              >
                <div className="mr-1.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-md bg-components-icon-bg-blue-solid text-[13px] max-[800px]:mr-0">
                  <span className="h-6 bg-gradient-to-r from-components-avatar-shape-fill-stop-0 to-components-avatar-shape-fill-stop-100 bg-clip-text align-middle font-semibold uppercase leading-6 text-shadow-shadow-1 opacity-90">{activeWorkspace.name[0]?.toLocaleUpperCase()}</span>
                </div>
                <div className="flex min-w-0 items-center">
                  <div className="system-sm-medium min-w-0 max-w-[149px] truncate text-text-secondary max-[800px]:hidden">{activeWorkspace.name}</div>
                  <RiArrowDownSLine className="h-4 w-4 shrink-0 text-text-secondary" />
                </div>
              </MenuButton>
            )}
            <Transition
              as={Fragment}
              enter="transition ease-out duration-100"
              enterFrom="transform opacity-0 scale-95"
              enterTo="transform opacity-100 scale-100"
              leave="transition ease-in duration-75"
              leaveFrom="transform opacity-100 scale-100"
              leaveTo="transform opacity-0 scale-95"
            >
              <MenuItems
                anchor="bottom start"
                className={cn(
                  `
                    shadows-shadow-lg absolute left-[-15px] z-[1000] mt-1 flex max-h-[400px] w-[280px] flex-col items-start overflow-y-auto
                    rounded-xl bg-components-panel-bg-blur backdrop-blur-[5px]
                  `,
                  compact && 'left-0 mt-2 w-[320px]',
                )}
              >
                <div className="flex w-full flex-col items-start self-stretch rounded-xl border-[0.5px] border-components-panel-border p-1 pb-2 shadow-lg ">
                  <div className="flex items-start self-stretch px-3 pb-0.5 pt-1">
                    <span className="system-xs-medium-uppercase flex-1 text-text-tertiary">{t('userProfile.workspace', { ns: 'common' })}</span>
                  </div>
                  {workspaceOptions.map(workspace => (
                    <MenuItem key={workspace.id}>
                      {({ focus }) => (
                        <button
                          type="button"
                          className={cn(
                            'flex w-full items-center gap-2 self-stretch rounded-lg py-1 pl-3 pr-2 text-left',
                            focus || workspace.id === activeWorkspace.id
                              ? 'bg-state-base-hover'
                              : 'bg-transparent',
                          )}
                          onClick={() => handleSwitchWorkspace(workspace.id)}
                        >
                          <div className="flex h-6 w-6 shrink-0 items-center justify-center rounded-md bg-components-icon-bg-blue-solid text-[13px]">
                            <span className="h-6 bg-gradient-to-r from-components-avatar-shape-fill-stop-0 to-components-avatar-shape-fill-stop-100 bg-clip-text align-middle font-semibold uppercase leading-6 text-shadow-shadow-1 opacity-90">{workspace.name[0]?.toLocaleUpperCase()}</span>
                          </div>
                          <div className="system-md-regular line-clamp-1 grow overflow-hidden text-ellipsis text-text-secondary">{workspace.name}</div>
                          {workspace.id === activeWorkspace.id && <RiCheckLine className="h-4 w-4 shrink-0 text-text-accent" />}
                          <PlanBadge plan={workspace.plan as Plan} />
                        </button>
                      )}
                    </MenuItem>
                  ))}
                </div>
              </MenuItems>
            </Transition>
          </>
        )
      }
    </Menu>
  )
}

export default WorkplaceSelector
