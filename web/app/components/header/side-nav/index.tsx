'use client'

import {
  RiApps2Line,
  RiArrowDownSLine,
  RiArrowRightSLine,
  RiDatabase2Fill,
  RiDatabase2Line,
  RiExchange2Line,
  RiFileShield2Line,
  RiLogoutBoxRLine,
  RiMenuFoldLine,
  RiMenuUnfoldLine,
  RiMessage3Line,
  RiPlanetFill,
  RiPlanetLine,
  RiPuzzle2Fill,
  RiPuzzle2Line,
  RiRobot3Line,
} from '@remixicon/react'
import Link from 'next/link'
import { useRouter, useSearchParams, useSelectedLayoutSegment } from 'next/navigation'
import { useMemo, useState } from 'react'
import { useAppContext } from '@/context/app-context'
import { useLogout } from '@/service/use-common'
import { cn } from '@/utils/classnames'
import { hasPluginManageWorkspaceCapability, hasWorkspaceCapability, WORKSPACE_CAPABILITIES } from '@/utils/workspace-capabilities'
import AccountDropdown from '../account-dropdown'
import EnvNav from '../env-nav'

type SubItemConfig = {
  id: string
  href: string
  icon: React.ReactNode
  label: string
}

type NavItemConfig = {
  id: string
  href: string
  icon: React.ReactNode
  activeIcon: React.ReactNode
  label: string
  segments: string[]
  children?: SubItemConfig[]
  /** query param name used for child active detection */
  childParam?: string
  /** default child id when no param is set */
  childDefault?: string
}

const SideNav = () => {
  const segment = useSelectedLayoutSegment()
  const searchParams = useSearchParams()
  const { userProfile, currentWorkspace } = useAppContext()
  const router = useRouter()
  const { mutateAsync: logout } = useLogout()

  const handleLogout = async () => {
    await logout()
    localStorage.removeItem('setup_status')
    router.push('/signin')
  }
  const [collapsed, setCollapsed] = useState(() => {
    if (typeof window !== 'undefined')
      return localStorage.getItem('side_nav_collapsed') === 'true'
    return false
  })

  const toggleCollapsed = () => {
    setCollapsed((prev) => {
      const next = !prev
      localStorage.setItem('side_nav_collapsed', String(next))
      return next
    })
  }

  const [expandedItems, setExpandedItems] = useState<Set<string>>(() => new Set())

  const canUseAgent = useMemo(() => hasWorkspaceCapability(currentWorkspace, WORKSPACE_CAPABILITIES.agentUse), [currentWorkspace])
  const canUseChat = useMemo(() => hasWorkspaceCapability(currentWorkspace, WORKSPACE_CAPABILITIES.chatUse), [currentWorkspace])
  const canViewKnowledge = useMemo(() => hasWorkspaceCapability(currentWorkspace, WORKSPACE_CAPABILITIES.knowledgeView), [currentWorkspace])
  const canManagePlugin = useMemo(() => hasPluginManageWorkspaceCapability(currentWorkspace), [currentWorkspace])
  const canViewWorkflow = useMemo(() => hasWorkspaceCapability(currentWorkspace, WORKSPACE_CAPABILITIES.workflowView), [currentWorkspace])
  const canViewAppCenter = useMemo(() => hasWorkspaceCapability(currentWorkspace, WORKSPACE_CAPABILITIES.appView), [currentWorkspace])
  const canViewExplore = useMemo(() => hasWorkspaceCapability(currentWorkspace, WORKSPACE_CAPABILITIES.exploreView), [currentWorkspace])
  const canViewAudit = useMemo(() => hasWorkspaceCapability(currentWorkspace, WORKSPACE_CAPABILITIES.auditView), [currentWorkspace])

  const navItems: NavItemConfig[] = []

  if (canUseAgent) {
    navItems.push({
      id: 'apps',
      href: '/apps',
      icon: <RiRobot3Line className="h-5 w-5" />,
      activeIcon: <RiRobot3Line className="h-5 w-5" />,
      label: '我的 Agent',
      segments: ['apps', 'app'],
    })
  }

  if (canUseChat) {
    navItems.push({
      id: 'chat',
      href: '/chat',
      icon: <RiMessage3Line className="h-5 w-5" />,
      activeIcon: <RiMessage3Line className="h-5 w-5" />,
      label: '对话',
      segments: ['chat'],
    })
  }

  if (canViewKnowledge) {
    navItems.push({
      id: 'datasets',
      href: '/datasets',
      icon: <RiDatabase2Line className="h-5 w-5" />,
      activeIcon: <RiDatabase2Fill className="h-5 w-5" />,
      label: '知识库',
      segments: ['datasets'],
    })
  }

  if (canManagePlugin) {
    navItems.push({
      id: 'plugins',
      href: '/plugins',
      icon: <RiPuzzle2Line className="h-5 w-5" />,
      activeIcon: <RiPuzzle2Fill className="h-5 w-5" />,
      label: '工具插件',
      segments: ['plugins'],
    })
  }

  if (canViewWorkflow) {
    navItems.push({
      id: 'workflow',
      href: '/apps?category=workflow',
      icon: <RiExchange2Line className="h-5 w-5" />,
      activeIcon: <RiExchange2Line className="h-5 w-5" />,
      label: '工作流',
      segments: [],
    })
  }

  if (canViewAppCenter) {
    navItems.push({
      id: 'tools',
      href: '/tools',
      icon: <RiApps2Line className="h-5 w-5" />,
      activeIcon: <RiApps2Line className="h-5 w-5" />,
      label: '应用中心',
      segments: ['tools'],
    })
  }

  if (canViewExplore) {
    navItems.push({
      id: 'explore',
      href: '/explore/apps',
      icon: <RiPlanetLine className="h-5 w-5" />,
      activeIcon: <RiPlanetFill className="h-5 w-5" />,
      label: '探索',
      segments: ['explore'],
    })
  }

  if (canViewAudit) {
    navItems.push({
      id: 'audit-logs',
      href: '/audit-logs',
      icon: <RiFileShield2Line className="h-5 w-5" />,
      activeIcon: <RiFileShield2Line className="h-5 w-5" />,
      label: '审计日志',
      segments: ['audit-logs'],
    })
  }

  const activeExpandableItemId = navItems.find(item => item.children?.length && item.segments.includes(segment ?? ''))?.id

  return (
    <div
      className={cn(
        'flex h-full shrink-0 flex-col bg-[#1a1f2e] transition-all duration-200',
        collapsed ? 'w-[60px]' : 'w-[240px]',
      )}
    >
      {/* Logo + tagline + collapse */}
      <div className={cn(
        'flex shrink-0 items-center border-b border-white/10',
        collapsed ? 'flex-col gap-1 px-2 py-4' : 'justify-between px-4 py-4',
      )}
      >
        <Link href="/apps" className="flex shrink-0 items-center gap-4">
          <div className={cn(
            'shrink-0 overflow-hidden rounded-xl border border-white/20',
            collapsed ? 'h-8 w-8' : 'h-12 w-12',
          )}
          >
            <img
              src={`${process.env.NEXT_PUBLIC_BASE_PATH || ''}/logo/CheersAI.png`}
              alt="CheersAI"
              className="h-full w-full scale-125 object-cover"
            />
          </div>
          {!collapsed && (
            <div className="flex flex-col leading-tight">
              <span className="text-xs font-medium text-white/90">省心用</span>
              <span className="text-xs font-medium text-white/90">安心用</span>
              <span className="text-xs font-medium text-white/90">领先用</span>
            </div>
          )}
        </Link>
        <button
          onClick={toggleCollapsed}
          className="rounded p-1 text-white/40 hover:bg-white/5 hover:text-white/80"
          title={collapsed ? '展开导航' : '收起导航'}
        >
          {collapsed
            ? <RiMenuUnfoldLine className="h-4 w-4" />
            : <RiMenuFoldLine className="h-4 w-4" />}
        </button>
      </div>

      {/* Nav items */}
      <nav className="scrollbar-hide flex flex-1 flex-col gap-0.5 overflow-y-auto px-3 py-2">
        {navItems.map((item) => {
          // 特殊处理：工作流菜单在访问 /apps?category=workflow 时高亮
          const isWorkflowActive = item.id === 'workflow' && segment === 'apps' && searchParams.get('category') === 'workflow'
          // 如果是工作流页面，我的 Agent 不应该高亮
          const isWorkflowPage = segment === 'apps' && searchParams.get('category') === 'workflow'
          const isActive = item.segments.includes(segment ?? '') && !(item.id === 'apps' && isWorkflowPage)
          const shouldHighlight = isActive || isWorkflowActive
          const hasChildren = item.children && item.children.length > 0
          const isExpanded = expandedItems.has(item.id) || activeExpandableItemId === item.id
          const showChildren = isExpanded && hasChildren && !collapsed

          const handleItemClick = (e: React.MouseEvent) => {
            if (hasChildren && !collapsed) {
              e.preventDefault()
              setExpandedItems((prev) => {
                const next = new Set(prev)
                if (next.has(item.id))
                  next.delete(item.id)
                else
                  next.add(item.id)
                return next
              })
              // Navigate if not already on this section
              if (!shouldHighlight)
                router.push(item.href)
            }
          }

          return (
            <div key={item.id}>
              <Link
                href={item.href}
                onClick={handleItemClick}
                title={collapsed ? item.label : undefined}
                className={cn(
                  'flex w-full items-center gap-3 rounded-xl transition-colors',
                  collapsed ? 'justify-center px-0 py-3' : 'px-4 py-3',
                  shouldHighlight && !showChildren
                    ? 'bg-[#2563eb] font-medium text-white'
                    : shouldHighlight
                      ? 'bg-white/10 font-medium text-white'
                      : 'text-white/70 hover:bg-white/5 hover:text-white',
                )}
              >
                <span className="shrink-0">
                  {shouldHighlight ? item.activeIcon : item.icon}
                </span>
                {!collapsed && (
                  <>
                    <span className="flex-1 truncate text-sm">
                      {item.label}
                    </span>
                    {hasChildren && (
                      <span className="shrink-0 text-white/40">
                        {isExpanded
                          ? <RiArrowDownSLine className="h-4 w-4" />
                          : <RiArrowRightSLine className="h-4 w-4" />}
                      </span>
                    )}
                  </>
                )}
              </Link>
              {/* Sub-items */}
              {showChildren && (
                <div className="ml-4 mt-0.5 flex flex-col gap-0.5">
                  {item.children!.map((child) => {
                    const paramValue = item.childParam ? (searchParams.get(item.childParam) || item.childDefault) : ''
                    const isChildActive = shouldHighlight && paramValue === child.id
                    return (
                      <Link
                        key={child.id}
                        href={child.href}
                        className={cn(
                          'flex items-center gap-2.5 rounded-lg px-3 py-2 text-[13px] transition-colors',
                          isChildActive
                            ? 'bg-[#2563eb] font-medium text-white'
                            : 'text-white/60 hover:bg-white/5 hover:text-white/90',
                        )}
                      >
                        <span className="shrink-0">{child.icon}</span>
                        <span className="truncate">{child.label}</span>
                      </Link>
                    )
                  })}
                </div>
              )}
            </div>
          )
        })}
      </nav>

      {/* Bottom: env, account */}
      <div className="flex shrink-0 flex-col gap-2 border-t border-white/5 px-3 py-3">
        {!collapsed
          ? (
              <>
                <EnvNav />
                <div className="flex items-center gap-3 rounded-lg px-2 py-1.5 transition-colors hover:bg-white/5">
                  <AccountDropdown />
                  <div className="flex min-w-0 flex-1 flex-col">
                    <span className="truncate text-sm font-medium text-white/90">{userProfile.name}</span>
                    <span className="truncate text-xs text-white/50">{userProfile.email}</span>
                  </div>
                  <button
                    onClick={handleLogout}
                    className="shrink-0 rounded-md p-1.5 text-white/30 transition-colors hover:bg-white/10 hover:text-white/80"
                    title="退出登录"
                  >
                    <RiLogoutBoxRLine className="h-4 w-4" />
                  </button>
                </div>
              </>
            )
          : (
              <div className="flex w-full justify-center">
                <AccountDropdown />
              </div>
            )}
      </div>
      <style jsx global>
        {`
        .scrollbar-hide {
          -ms-overflow-style: none;
          scrollbar-width: none;
        }
        .scrollbar-hide::-webkit-scrollbar {
          display: none;
        }
      `}
      </style>
    </div>
  )
}

export default SideNav
