'use client'
import { Menu, MenuButton, MenuItem, MenuItems, Transition } from '@headlessui/react'
import {
  RiAccountCircleLine,
  RiArrowDownSLine,
  RiArrowRightUpLine,
  RiBookOpenLine,
  RiGithubLine,
  RiGraduationCapFill,
  RiInformation2Line,
  RiLogoutBoxRLine,
  RiMap2Line,
  RiSettings3Line,
  RiStarLine,
  RiTShirt2Line,
} from '@remixicon/react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { Fragment, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { resetUser } from '@/app/components/base/amplitude/utils'
import Avatar from '@/app/components/base/avatar'
import PremiumBadge from '@/app/components/base/premium-badge'
import ThemeSwitcher from '@/app/components/base/theme-switcher'
import { ACCOUNT_SETTING_TAB } from '@/app/components/header/account-setting/constants'
import { IS_CLOUD_EDITION } from '@/config'
import { useAppContext } from '@/context/app-context'
import { useGlobalPublicStore } from '@/context/global-public-context'
import { useDocLink } from '@/context/i18n'
import { useModalContext } from '@/context/modal-context'
import { useProviderContext } from '@/context/provider-context'
import { useLogout } from '@/service/use-common'
import { cn } from '@/utils/classnames'
import { hasWorkspaceCapability, WORKSPACE_CAPABILITIES } from '@/utils/workspace-capabilities'
import AccountAbout from '../account-about'
import GithubStar from '../github-star'
import Indicator from '../indicator'
import Compliance from './compliance'
import Support from './support'
import WorkplaceSelector from './workplace-selector'

type AccountDropdownProps = {
  placement?: 'side' | 'bottom-end'
  showLabel?: boolean
}

export default function AppSelector({ placement = 'side', showLabel = false }: AccountDropdownProps) {
  const itemClassName = `
    flex items-center w-full h-8 pl-3 pr-2 text-text-secondary system-md-regular
    rounded-lg hover:bg-state-base-hover cursor-pointer gap-1
  `
  const router = useRouter()
  const [aboutVisible, setAboutVisible] = useState(false)
  const { systemFeatures } = useGlobalPublicStore()

  const { t } = useTranslation()
  const docLink = useDocLink()
  const { userProfile, langGeniusVersionInfo, isCurrentWorkspaceOwner, isCurrentWorkspaceManager, currentWorkspace } = useAppContext()
  const { isEducationAccount } = useProviderContext()
  const { setShowAccountSettingModal } = useModalContext()
  const canViewAdminOnlyLinks = isCurrentWorkspaceOwner || isCurrentWorkspaceManager
  const isSystemAdmin = hasWorkspaceCapability(currentWorkspace, WORKSPACE_CAPABILITIES.systemAdmin)

  const { mutateAsync: logout } = useLogout()
  const handleLogout = async () => {
    await logout()
    resetUser()
    localStorage.removeItem('setup_status')
    // Tokens are now stored in cookies and cleared by backend

    // To avoid use other account's education notice info
    localStorage.removeItem('education-reverify-prev-expire-at')
    localStorage.removeItem('education-reverify-has-noticed')
    localStorage.removeItem('education-expired-has-noticed')

    router.push('/signin')
  }

  return (
    <div className="">
      <Menu as="div" className="relative inline-block text-left">
        {
          ({ open, close }) => (
            <>
              <MenuButton className={cn('inline-flex items-center rounded-[20px] p-0.5 hover:bg-background-default-dodge', open && 'bg-background-default-dodge')}>
                <div className={cn(
                  'inline-flex items-center gap-2 rounded-2xl px-1 py-1',
                  showLabel && 'pr-3',
                )}
                >
                  <Avatar avatar={userProfile.avatar_url} name={userProfile.name} size={36} />
                  {showLabel && (
                    <div className="flex min-w-0 items-center gap-2">
                      <div className="min-w-0 text-left">
                        <div className="system-sm-medium truncate text-text-primary">{userProfile.name}</div>
                        <div className="system-2xs-regular truncate text-text-tertiary">{userProfile.email}</div>
                      </div>
                      <RiArrowDownSLine className={cn('size-4 shrink-0 text-text-tertiary transition-transform', open && 'rotate-180')} />
                    </div>
                  )}
                </div>
              </MenuButton>
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
                  className={cn(
                    'absolute z-50 w-60 max-w-80 divide-y divide-divider-subtle rounded-xl bg-components-panel-bg-blur shadow-lg backdrop-blur-sm focus:outline-none',
                    placement === 'side'
                      ? 'bottom-0 left-full ml-2 origin-bottom-left'
                      : 'right-0 top-[calc(100%+8px)] origin-top-right',
                  )}
                >
                  <div className="px-1 py-1">
                    <MenuItem disabled>
                      <div className="flex flex-nowrap items-center py-2 pl-3 pr-2">
                        <div className="grow">
                          <div className="system-md-medium break-all text-text-primary">
                            {userProfile.name}
                            {isEducationAccount && (
                              <PremiumBadge size="s" color="blue" className="ml-1 !px-2">
                                <RiGraduationCapFill className="mr-1 h-3 w-3" />
                                <span className="system-2xs-medium">EDU</span>
                              </PremiumBadge>
                            )}
                          </div>
                          <div className="system-xs-regular break-all text-text-tertiary">{userProfile.email}</div>
                        </div>
                        <Avatar avatar={userProfile.avatar_url} name={userProfile.name} size={36} />
                      </div>
                    </MenuItem>
                    <div className="px-1 pb-2">
                      <WorkplaceSelector compact />
                    </div>
                    <MenuItem>
                      <Link
                        className={cn(itemClassName, 'group', 'data-[active]:bg-state-base-hover')}
                        href="/account"
                        target="_self"
                        rel="noopener noreferrer"
                      >
                        <RiAccountCircleLine className="size-4 shrink-0 text-text-tertiary" />
                        <div className="system-md-regular grow px-1 text-text-secondary">{t('account.account', { ns: 'common' })}</div>
                        <RiArrowRightUpLine className="size-[14px] shrink-0 text-text-tertiary" />
                      </Link>
                    </MenuItem>
                    <MenuItem>
                      <div
                        className={cn(itemClassName, 'data-[active]:bg-state-base-hover')}
                        onClick={() => setShowAccountSettingModal({
                          payload: isSystemAdmin ? ACCOUNT_SETTING_TAB.PROVIDER : ACCOUNT_SETTING_TAB.MEMBERS,
                        })}
                      >
                        <RiSettings3Line className="size-4 shrink-0 text-text-tertiary" />
                        <div className="system-md-regular grow px-1 text-text-secondary">{t('userProfile.settings', { ns: 'common' })}</div>
                      </div>
                    </MenuItem>
                  </div>
                  {!systemFeatures.branding.enabled && canViewAdminOnlyLinks && (
                    <>
                      <div className="p-1">
                        <MenuItem>
                          <Link
                            className={cn(itemClassName, 'group justify-between', 'data-[active]:bg-state-base-hover')}
                            href={docLink('/use-dify/getting-started/introduction')}
                            target="_blank"
                            rel="noopener noreferrer"
                          >
                            <RiBookOpenLine className="size-4 shrink-0 text-text-tertiary" />
                            <div className="system-md-regular grow px-1 text-text-secondary">{t('userProfile.helpCenter', { ns: 'common' })}</div>
                            <RiArrowRightUpLine className="size-[14px] shrink-0 text-text-tertiary" />
                          </Link>
                        </MenuItem>
                        <Support closeAccountDropdown={close} />
                        {IS_CLOUD_EDITION && isCurrentWorkspaceOwner && <Compliance />}
                      </div>
                      <div className="p-1">
                        <MenuItem>
                          <Link
                            className={cn(itemClassName, 'group justify-between', 'data-[active]:bg-state-base-hover')}
                            href="https://roadmap.dify.ai"
                            target="_blank"
                            rel="noopener noreferrer"
                          >
                            <RiMap2Line className="size-4 shrink-0 text-text-tertiary" />
                            <div className="system-md-regular grow px-1 text-text-secondary">{t('userProfile.roadmap', { ns: 'common' })}</div>
                            <RiArrowRightUpLine className="size-[14px] shrink-0 text-text-tertiary" />
                          </Link>
                        </MenuItem>
                        <MenuItem>
                          <Link
                            className={cn(itemClassName, 'group justify-between', 'data-[active]:bg-state-base-hover')}
                            href="https://github.com/langgenius/dify"
                            target="_blank"
                            rel="noopener noreferrer"
                          >
                            <RiGithubLine className="size-4 shrink-0 text-text-tertiary" />
                            <div className="system-md-regular grow px-1 text-text-secondary">{t('userProfile.github', { ns: 'common' })}</div>
                            <div className="flex items-center gap-0.5 rounded-[5px] border border-divider-deep bg-components-badge-bg-dimm px-[5px] py-[3px]">
                              <RiStarLine className="size-3 shrink-0 text-text-tertiary" />
                              <GithubStar className="system-2xs-medium-uppercase text-text-tertiary" />
                            </div>
                          </Link>
                        </MenuItem>
                        {
                          document?.body?.getAttribute('data-public-site-about') !== 'hide' && (
                            <MenuItem>
                              <div
                                className={cn(itemClassName, 'justify-between', 'data-[active]:bg-state-base-hover')}
                                onClick={() => setAboutVisible(true)}
                              >
                                <RiInformation2Line className="size-4 shrink-0 text-text-tertiary" />
                                <div className="system-md-regular grow px-1 text-text-secondary">{t('userProfile.about', { ns: 'common' })}</div>
                                <div className="flex shrink-0 items-center">
                                  <div className="system-xs-regular mr-2 text-text-tertiary">{langGeniusVersionInfo.current_version}</div>
                                  <Indicator color={langGeniusVersionInfo.current_version === langGeniusVersionInfo.latest_version ? 'green' : 'orange'} />
                                </div>
                              </div>
                            </MenuItem>
                          )
                        }
                      </div>
                    </>
                  )}
                  <MenuItem disabled>
                    <div className="p-1">
                      <div className={cn(itemClassName, 'hover:bg-transparent')}>
                        <RiTShirt2Line className="size-4 shrink-0 text-text-tertiary" />
                        <div className="system-md-regular grow px-1 text-text-secondary">{t('theme.theme', { ns: 'common' })}</div>
                        <ThemeSwitcher />
                      </div>
                    </div>
                  </MenuItem>
                  <MenuItem>
                    <div className="p-1" onClick={() => handleLogout()}>
                      <div
                        className={cn(itemClassName, 'group justify-between', 'data-[active]:bg-state-base-hover')}
                      >
                        <RiLogoutBoxRLine className="size-4 shrink-0 text-text-tertiary" />
                        <div className="system-md-regular grow px-1 text-text-secondary">{t('userProfile.logout', { ns: 'common' })}</div>
                      </div>
                    </div>
                  </MenuItem>
                </MenuItems>
              </Transition>
            </>
          )
        }
      </Menu>
      {
        aboutVisible && <AccountAbout onCancel={() => setAboutVisible(false)} langGeniusVersionInfo={langGeniusVersionInfo} />
      }
    </div>
  )
}
