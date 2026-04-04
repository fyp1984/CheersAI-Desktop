'use client'

import {
  RiApps2Line,
  RiDatabase2Fill,
  RiDatabase2Line,
  RiExchange2Line,
  RiFileShield2Line,
  RiArrowDownSLine,
  RiArrowRightSLine,
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
import { useRouter } from 'next/navigation'
import { useSearchParams, useSelectedLayoutSegment } from 'next/navigation'
import { useEffect, useMemo, useState } from 'react'
import { useAppContext } from '@/context/app-context'
import { cn } from '@/utils/classnames'
import AccountDropdown from '../account-dropdown'
import EnvNav from '../env-nav'
import { useLogout } from '@/service/use-common'

interface SubItemConfig {
  id: string
  href: string
  icon: React.ReactNode
  label: string
}

interface NavItemConfig {
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
  const { isCurrentWorkspaceDatasetOperator, userProfile, currentWorkspace } = useAppContext()
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

  const [expandedItems, setExpandedItems] = useState<Set<string>>(new Set())

  // 角色权限判断
  const isAdmin = useMemo(() => ['owner', 'admin'].includes(currentWorkspace.role), [currentWorkspace.role])
  const isEditor = useMemo(() => ['owner', 'admin', 'editor'].includes(currentWorkspace.role), [currentWorkspace.role])

  const navItems: NavItemConfig[] = []

  // 1. 我的 Agent（所有角色可见）
  if (!isCurrentWorkspaceDatasetOperator) {
    navItems.push({
      id: 'apps',
      href: '/apps',
      icon: <RiRobot3Line className="h-5 w-5" />,
      activeIcon: <RiRobot3Line className="h-5 w-5" />,
      label: '我的 Agent',
      segments: ['apps', 'app'],
    })
  }

  // 2. 对话（所有角色可见）
  if (!isCurrentWorkspaceDatasetOperator) {
    navItems.push({
      id: 'chat',
      href: '/chat',
      icon: <RiMessage3Line className="h-5 w-5" />,
      activeIcon: <RiMessage3Line className="h-5 w-5" />,
      label: '对话',
      segments: ['chat'],
    })
  }

  // 3. 知识库（所有角色可见，但普通用户只读）
  if (!isCurrentWorkspaceDatasetOperator) {
    navItems.push({
      id: 'datasets',
      href: '/datasets',
      icon: <RiDatabase2Line className="h-5 w-5" />,
      activeIcon: <RiDatabase2Fill className="h-5 w-5" />,
      label: '知识库',
      segments: ['datasets'],
    })
  }

  // 4. 智能体管理（技术员和管理员可见）
  if (isEditor) {
    navItems.push({
      id: 'plugins',
      href: '/plugins',
      icon: <RiPuzzle2Line className="h-5 w-5" />,
      activeIcon: <RiPuzzle2Fill className="h-5 w-5" />,
      label: '智能体管理',
      segments: ['plugins'],
    })
  }

  // 5. 工作流（技术员和管理员可见）
  if (isEditor) {
    navItems.push({
      id: 'workflow',
      href: '/apps?category=workflow',
      icon: <RiExchange2Line className="h-5 w-5" />,
      activeIcon: <RiExchange2Line className="h-5 w-5" />,
      label: '工作流',
      segments: [],  // 不设置 segments，避免与 apps 冲突
    })
  }

  // 6. 应用中心（所有角色可见，但普通用户只读）
  if (!isCurrentWorkspaceDatasetOperator) {
    navItems.push({
      id: 'tools',
      href: '/tools',
      icon: <RiApps2Line className="h-5 w-5" />,
      activeIcon: <RiApps2Line className="h-5 w-5" />,
      label: '应用中心',
      segments: ['tools'],
    })
  }

  // 7. 探索（所有角色可见）
  if (!isCurrentWorkspaceDatasetOperator) {
    navItems.push({
      id: 'explore',
      href: '/explore/apps',
      icon: <RiPlanetLine className="h-5 w-5" />,
      activeIcon: <RiPlanetFill className="h-5 w-5" />,
      label: '探索',
      segments: ['explore'],
    })
  }

  // 8. 审计日志（仅管理员可见）
  if (isAdmin) {
    navItems.push({
      id: 'audit-logs',
      href: '/audit-logs',
      icon: <RiFileShield2Line className="h-5 w-5" />,
      activeIcon: <RiFileShield2Line className="h-5 w-5" />,
      label: '审计日志',
      segments: ['audit-logs'],
    })
  }

  // Auto-expand the active nav item on mount / segment change
  useEffect(() => {
    const activeItem = navItems.find(item => item.segments.includes(segment ?? ''))
    if (activeItem?.children?.length) {
      setExpandedItems((prev) => {
        if (prev.has(activeItem.id)) return prev
        const next = new Set(prev)
        next.add(activeItem.id)
        return next
      })
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [segment])

  return (
    <div
      className={cn(
        'flex h-full flex-col shrink-0 bg-[#1a1f2e] transition-all duration-200',
        collapsed ? 'w-[60px]' : 'w-[240px]',
      )}
    >
      {/* Logo + tagline + collapse */}
      <div className={cn(
        'flex items-center shrink-0 border-b border-white/10',
        collapsed ? 'flex-col gap-1 px-2 py-4' : 'justify-between px-4 py-4',
      )}>
        <Link href="/apps" className="flex items-center gap-4 shrink-0">
          <div className={cn(
            'rounded-xl border border-white/20 overflow-hidden shrink-0',
            collapsed ? 'w-8 h-8' : 'w-12 h-12',
          )}>
            <img
              src={`${process.env.NEXT_PUBLIC_BASE_PATH || ''}/logo/CheersAI.png`}
              alt="CheersAI"
              className="w-full h-full object-cover scale-125"
            />
          </div>
          {!collapsed && (
            <div className="flex flex-col leading-tight">
              <span className="text-white/90 text-xs font-medium">省心用</span>
              <span className="text-white/90 text-xs font-medium">安心用</span>
              <span className="text-white/90 text-xs font-medium">领先用</span>
            </div>
          )}
        </Link>
        <button
          onClick={toggleCollapsed}
          className="p-1 rounded text-white/40 hover:text-white/80 hover:bg-white/5"
          title={collapsed ? '展开导航' : '收起导航'}
        >
          {collapsed
            ? <RiMenuUnfoldLine className="w-4 h-4" />
            : <RiMenuFoldLine className="w-4 h-4" />}
        </button>
      </div>

      {/* Nav items */}
      <nav className="flex-1 flex flex-col gap-0.5 px-3 py-2 overflow-y-auto scrollbar-hide">
        {navItems.map((item) => {
          // 特殊处理：工作流菜单在访问 /apps?category=workflow 时高亮
          const isWorkflowActive = item.id === 'workflow' && segment === 'apps' && searchParams.get('category') === 'workflow'
          // 如果是工作流页面，我的 Agent 不应该高亮
          const isWorkflowPage = segment === 'apps' && searchParams.get('category') === 'workflow'
          const isActive = item.segments.includes(segment ?? '') && !(item.id === 'apps' && isWorkflowPage)
          const shouldHighlight = isActive || isWorkflowActive
          const hasChildren = item.children && item.children.length > 0
          const isExpanded = expandedItems.has(item.id)
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
                  'flex items-center gap-3 rounded-xl transition-colors w-full',
                  collapsed ? 'justify-center px-0 py-3' : 'px-4 py-3',
                  shouldHighlight && !showChildren
                    ? 'bg-[#2563eb] text-white font-medium'
                    : shouldHighlight
                      ? 'bg-white/10 text-white font-medium'
                      : 'text-white/70 hover:bg-white/5 hover:text-white',
                )}
              >
                <span className="shrink-0">
                  {shouldHighlight ? item.activeIcon : item.icon}
                </span>
                {!collapsed && (
                  <>
                    <span className="text-sm truncate flex-1">
                      {item.label}
                    </span>
                    {hasChildren && (
                      <span className="shrink-0 text-white/40">
                        {isExpanded
                          ? <RiArrowDownSLine className="w-4 h-4" />
                          : <RiArrowRightSLine className="w-4 h-4" />}
                      </span>
                    )}
                  </>
                )}
              </Link>
              {/* Sub-items */}
              {showChildren && (
                <div className="mt-0.5 ml-4 flex flex-col gap-0.5">
                  {item.children!.map((child) => {
                    const paramValue = item.childParam ? (searchParams.get(item.childParam) || item.childDefault) : ''
                    const isChildActive = shouldHighlight && paramValue === child.id
                    return (
                      <Link
                        key={child.id}
                        href={child.href}
                        className={cn(
                          'flex items-center gap-2.5 rounded-lg px-3 py-2 transition-colors text-[13px]',
                          isChildActive
                            ? 'bg-[#2563eb] text-white font-medium'
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
      <div className="shrink-0 border-t border-white/5 px-3 py-3 flex flex-col gap-2">
        {!collapsed
          ? (
            <>
              <EnvNav />
              <div className="flex items-center gap-3 px-2 py-1.5 rounded-lg hover:bg-white/5 transition-colors">
                <AccountDropdown />
                <div className="flex flex-col min-w-0 flex-1">
                  <span className="text-white/90 text-sm font-medium truncate">{userProfile.name}</span>
                  <span className="text-white/50 text-xs truncate">{userProfile.email}</span>
                </div>
                <button
                  onClick={handleLogout}
                  className="shrink-0 p-1.5 rounded-md text-white/30 hover:text-white/80 hover:bg-white/10 transition-colors"
                  title="退出登录"
                >
                  <RiLogoutBoxRLine className="w-4 h-4" />
                </button>
              </div>
            </>
          )
          : (
            <div className="flex justify-center w-full">
              <AccountDropdown />
            </div>
          )}
      </div>
      <style jsx global>{`
        .scrollbar-hide {
          -ms-overflow-style: none;
          scrollbar-width: none;
        }
        .scrollbar-hide::-webkit-scrollbar {
          display: none;
        }
      `}</style>
    </div>
  )
}

export default SideNav
