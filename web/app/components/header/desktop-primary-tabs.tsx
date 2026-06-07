'use client'

import {
  RiApps2Line,
  RiArrowLeftSLine,
  RiArrowRightSLine,
  RiDatabase2Fill,
  RiDatabase2Line,
  RiExchange2Line,
  RiFileShield2Line,
  RiMessage3Line,
  RiPlanetFill,
  RiPlanetLine,
  RiPuzzle2Fill,
  RiPuzzle2Line,
  RiRobot3Line,
} from '@remixicon/react'
import Link from 'next/link'
import { usePathname, useSearchParams } from 'next/navigation'
import { useCallback, useEffect, useMemo, useReducer, useRef, useState } from 'react'
import { useAppContext } from '@/context/app-context'
import { isTauriRuntime } from '@/service/sso-desktop-auth'
import { cn } from '@/utils/classnames'
import { hasPluginReadWorkspaceCapability, hasWorkspaceCapability, WORKSPACE_CAPABILITIES } from '@/utils/workspace-capabilities'
import AccountDropdown from './account-dropdown'
import EnvNav from './env-nav'

type NavItemConfig = {
  id: string
  href: string
  icon: React.ReactNode
  activeIcon: React.ReactNode
  label: string
  segments: string[]
}

const getIsDesktopRuntime = () => {
  if (typeof window === 'undefined')
    return false

  return isTauriRuntime()
}

const getBrowserShowBrand = (searchParams: URLSearchParams) => {
  if (typeof window === 'undefined')
    return false

  const source = searchParams.get('source')
  if (source === 'vault-shell' || source === 'vault')
    sessionStorage.setItem('cheersai_desktop_embedded', '1')

  const embedded = sessionStorage.getItem('cheersai_desktop_embedded') === '1'
  return !embedded && !isTauriRuntime()
}

const DesktopPrimaryTabs = () => {
  const pathname = usePathname()
  const searchParams = useSearchParams()
  const { currentWorkspace } = useAppContext()
  const normalizedPathname = pathname.endsWith('/') && pathname !== '/' ? pathname.slice(0, -1) : pathname
  const pathnameSegments = normalizedPathname.split('/').filter(Boolean)
  const primarySegment = pathnameSegments[0] || ''
  const tabsViewportRef = useRef<HTMLDivElement>(null)
  const [{ canScrollLeft, canScrollRight }, setScrollState] = useReducer((
    state: { canScrollLeft: boolean, canScrollRight: boolean },
    nextState: { canScrollLeft: boolean, canScrollRight: boolean },
  ) => {
    if (state.canScrollLeft === nextState.canScrollLeft && state.canScrollRight === nextState.canScrollRight)
      return state

    return nextState
  }, { canScrollLeft: false, canScrollRight: false })
  const [isDesktopRuntime] = useState(getIsDesktopRuntime)
  const showBrand = useMemo(() => getBrowserShowBrand(searchParams), [searchParams])

  const canUseAgent = useMemo(() => hasWorkspaceCapability(currentWorkspace, WORKSPACE_CAPABILITIES.agentUse), [currentWorkspace])
  const canUseChat = useMemo(() => hasWorkspaceCapability(currentWorkspace, WORKSPACE_CAPABILITIES.chatUse), [currentWorkspace])
  const canViewKnowledge = useMemo(() => hasWorkspaceCapability(currentWorkspace, WORKSPACE_CAPABILITIES.knowledgeView), [currentWorkspace])
  const canReadPlugin = useMemo(() => hasPluginReadWorkspaceCapability(currentWorkspace), [currentWorkspace])
  const canViewWorkflow = useMemo(() => hasWorkspaceCapability(currentWorkspace, WORKSPACE_CAPABILITIES.workflowView), [currentWorkspace])
  const canViewAppCenter = useMemo(() => hasWorkspaceCapability(currentWorkspace, WORKSPACE_CAPABILITIES.appView), [currentWorkspace])
  const canViewExplore = useMemo(() => hasWorkspaceCapability(currentWorkspace, WORKSPACE_CAPABILITIES.exploreView), [currentWorkspace])
  const canViewAudit = useMemo(() => hasWorkspaceCapability(currentWorkspace, WORKSPACE_CAPABILITIES.auditView), [currentWorkspace])

  const navItems = useMemo<NavItemConfig[]>(() => {
    const items: NavItemConfig[] = []

    if (canUseAgent || canViewAppCenter) {
      items.push({
        id: 'apps',
        href: '/apps',
        icon: <RiRobot3Line className="h-4 w-4" />,
        activeIcon: <RiRobot3Line className="h-4 w-4" />,
        label: '我的 Agent',
        segments: ['apps', 'app'],
      })
    }

    if (canUseChat) {
      items.push({
        id: 'chat',
        href: '/chat',
        icon: <RiMessage3Line className="h-4 w-4" />,
        activeIcon: <RiMessage3Line className="h-4 w-4" />,
        label: '对话',
        segments: ['chat'],
      })
    }

    if (canViewKnowledge) {
      items.push({
        id: 'datasets',
        href: '/datasets',
        icon: <RiDatabase2Line className="h-4 w-4" />,
        activeIcon: <RiDatabase2Fill className="h-4 w-4" />,
        label: '知识库',
        segments: ['datasets'],
      })
    }

    if (canReadPlugin) {
      items.push({
        id: 'plugins',
        href: '/plugins',
        icon: <RiPuzzle2Line className="h-4 w-4" />,
        activeIcon: <RiPuzzle2Fill className="h-4 w-4" />,
        label: '工具插件',
        segments: ['plugins'],
      })
    }

    if (canViewWorkflow) {
      items.push({
        id: 'workflow',
        href: '/workflows',
        icon: <RiExchange2Line className="h-4 w-4" />,
        activeIcon: <RiExchange2Line className="h-4 w-4" />,
        label: '工作流',
        segments: ['workflows'],
      })
    }

    if (canViewAppCenter) {
      items.push({
        id: 'tools',
        href: '/tools',
        icon: <RiApps2Line className="h-4 w-4" />,
        activeIcon: <RiApps2Line className="h-4 w-4" />,
        label: '应用中心',
        segments: ['tools'],
      })
    }

    if (canViewExplore) {
      items.push({
        id: 'explore',
        href: '/explore/apps',
        icon: <RiPlanetLine className="h-4 w-4" />,
        activeIcon: <RiPlanetFill className="h-4 w-4" />,
        label: '探索',
        segments: ['explore'],
      })
    }

    if (canViewAudit) {
      items.push({
        id: 'audit-logs',
        href: '/audit-logs',
        icon: <RiFileShield2Line className="h-4 w-4" />,
        activeIcon: <RiFileShield2Line className="h-4 w-4" />,
        label: '审计日志',
        segments: ['audit-logs'],
      })
    }

    return items
  }, [
    canReadPlugin,
    canUseAgent,
    canUseChat,
    canViewAppCenter,
    canViewAudit,
    canViewExplore,
    canViewKnowledge,
    canViewWorkflow,
  ])

  const activeItem = useMemo(() => navItems.find((item) => {
    if (item.id === 'workflow')
      return normalizedPathname === '/workflows' || (normalizedPathname === '/apps' && searchParams.get('category') === 'workflow')
    if (item.id === 'apps')
      return normalizedPathname === '/apps' && searchParams.get('category') !== 'workflow'

    return normalizedPathname === item.href
      || normalizedPathname.startsWith(`${item.href}/`)
      || item.segments.includes(primarySegment)
  }), [navItems, normalizedPathname, primarySegment, searchParams])

  const updateScrollState = useCallback(() => {
    const viewport = tabsViewportRef.current
    if (!viewport)
      return

    setScrollState({
      canScrollLeft: viewport.scrollLeft > 4,
      canScrollRight: viewport.scrollLeft + viewport.clientWidth < viewport.scrollWidth - 4,
    })
  }, [])

  const isBrowserAccess = showBrand && !isDesktopRuntime

  useEffect(() => {
    if (!activeItem)
      return

    const titleMap: Record<string, string> = {
      'apps': '我的 Agent',
      'chat': '对话',
      'datasets': '知识库',
      'plugins': '工具插件',
      'workflow': '工作流',
      'tools': '应用中心',
      'explore': '探索',
      'audit-logs': '审计日志',
    }

    document.title = `${titleMap[activeItem.id] || activeItem.label} - CheersAI`
  }, [activeItem])

  useEffect(() => {
    updateScrollState()

    const viewport = tabsViewportRef.current
    if (!viewport)
      return

    if (!activeItem)
      return

    const activeTab = viewport.querySelector<HTMLElement>(`[data-tab-id="${activeItem.id}"]`)
    activeTab?.scrollIntoView({ behavior: 'smooth', inline: 'center', block: 'nearest' })

    const resizeObserver = new ResizeObserver(() => updateScrollState())
    resizeObserver.observe(viewport)
    window.addEventListener('resize', updateScrollState)
    viewport.addEventListener('scroll', updateScrollState, { passive: true })

    return () => {
      resizeObserver.disconnect()
      window.removeEventListener('resize', updateScrollState)
      viewport.removeEventListener('scroll', updateScrollState)
    }
  }, [activeItem, updateScrollState])

  const scrollTabs = (direction: 'left' | 'right') => {
    const viewport = tabsViewportRef.current
    if (!viewport)
      return

    viewport.scrollBy({
      left: direction === 'left' ? -240 : 240,
      behavior: 'smooth',
    })
  }

  return (
    <div className="flex h-[76px] shrink-0 items-center justify-between border-b border-divider-subtle bg-components-panel-bg px-5">
      <div className="flex min-w-0 flex-1 items-center gap-4 overflow-hidden">
        {isBrowserAccess && (
          <Link href="/apps" className="flex shrink-0 items-center gap-2">
            <div className="h-11 w-11 overflow-hidden rounded-2xl border border-blue-200/40 bg-[#0F172A] shadow-[0_10px_26px_rgba(37,99,235,0.18)]">
              <img
                src={`${process.env.NEXT_PUBLIC_BASE_PATH || ''}/logo/CheersAI.png`}
                alt="CheersAI"
                className="h-full w-full scale-125 object-cover"
              />
            </div>
            <div className="min-w-0 max-w-[96px]">
              <div className="truncate text-sm font-semibold tracking-[0.16em] text-text-primary">DESKTOP</div>
              <div className="truncate text-[10px] leading-3 text-text-tertiary">智享AI，安全随行</div>
            </div>
          </Link>
        )}

        <div className="flex min-w-0 flex-1 items-center gap-2 overflow-hidden">
          <button
            type="button"
            aria-label="左移菜单"
            onClick={() => scrollTabs('left')}
            className={cn(
              'flex h-9 w-9 shrink-0 items-center justify-center rounded-xl border border-divider-subtle bg-components-panel-bg text-text-tertiary transition',
              canScrollLeft ? 'opacity-100 hover:bg-state-base-hover hover:text-text-primary' : 'pointer-events-none opacity-0',
            )}
          >
            <RiArrowLeftSLine className="h-4 w-4" />
          </button>

          <div className="relative min-w-0 flex-1 overflow-hidden">
            <div className={cn(
              'pointer-events-none absolute inset-y-0 left-0 z-10 w-8 bg-gradient-to-r from-components-panel-bg to-transparent transition-opacity',
              canScrollLeft ? 'opacity-100' : 'opacity-0',
            )}
            />
            <div className={cn(
              'pointer-events-none absolute inset-y-0 right-0 z-10 w-8 bg-gradient-to-l from-components-panel-bg to-transparent transition-opacity',
              canScrollRight ? 'opacity-100' : 'opacity-0',
            )}
            />
            <div
              ref={tabsViewportRef}
              className="scrollbar-hide overflow-x-auto scroll-smooth"
            >
              <div className="flex min-w-max items-center gap-2 pr-2">
                {navItems.map((item) => {
                  const isWorkflowActive = item.id === 'workflow'
                    && (normalizedPathname === '/workflows' || (normalizedPathname === '/apps' && searchParams.get('category') === 'workflow'))
                  const isWorkflowPage = normalizedPathname === '/workflows' || (normalizedPathname === '/apps' && searchParams.get('category') === 'workflow')
                  const isActive = item.id === 'apps'
                    ? normalizedPathname === '/apps' && !isWorkflowPage
                    : normalizedPathname === item.href
                      || normalizedPathname.startsWith(`${item.href}/`)
                      || item.segments.includes(primarySegment)
                  const shouldHighlight = isActive || isWorkflowActive

                  return (
                    <Link
                      key={item.id}
                      data-tab-id={item.id}
                      href={item.href}
                      className={cn(
                        'flex h-10 items-center gap-2 rounded-xl px-4 text-sm font-medium transition-colors',
                        shouldHighlight
                          ? 'bg-state-accent-hover text-text-accent shadow-sm ring-1 ring-state-accent-solid/15'
                          : 'text-text-tertiary hover:bg-state-base-hover hover:text-text-primary',
                      )}
                    >
                      <span className="shrink-0">
                        {shouldHighlight ? item.activeIcon : item.icon}
                      </span>
                      <span className="whitespace-nowrap">{item.label}</span>
                    </Link>
                  )
                })}
              </div>
            </div>
          </div>

          <button
            type="button"
            aria-label="右移菜单"
            onClick={() => scrollTabs('right')}
            className={cn(
              'flex h-9 w-9 shrink-0 items-center justify-center rounded-xl border border-divider-subtle bg-components-panel-bg text-text-tertiary transition',
              canScrollRight ? 'opacity-100 hover:bg-state-base-hover hover:text-text-primary' : 'pointer-events-none opacity-0',
            )}
          >
            <RiArrowRightSLine className="h-4 w-4" />
          </button>
        </div>
      </div>

      <div className="ml-3 flex shrink-0 items-center gap-2">
        <EnvNav />
        <AccountDropdown placement="bottom-end" />
      </div>
    </div>
  )
}

export default DesktopPrimaryTabs
