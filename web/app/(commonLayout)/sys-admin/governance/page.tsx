'use client'

import Link from 'next/link'
import useDocumentTitle from '@/hooks/use-document-title'

const governanceCards = [
  {
    title: '工具插件治理',
    description: '进入工具插件页安装、更新与启停系统级插件；Admin 安装后的模型插件会自动共享给所有团队。',
    href: '/plugins',
    action: '打开工具插件',
  },
  {
    title: '审计日志',
    description: '查看系统级审计记录，核验安装、启停与团队治理过程中的关键操作。',
    href: '/audit-logs',
    action: '查看审计日志',
  },
]

const SysAdminGovernancePage = () => {
  useDocumentTitle('系统治理')

  return (
    <div className="relative flex h-0 shrink-0 grow flex-col overflow-y-auto bg-background-body">
      <div className="sticky top-0 z-10 bg-background-body px-12 pb-4 pt-7">
        <h2 className="text-lg font-semibold text-text-primary">系统治理</h2>
        <div className="mt-1 max-w-3xl text-sm leading-6 text-text-tertiary">
          built-in Admin 在此页面统一进入系统级插件治理与审计入口。模型插件安装完成后，团队管理员可在
          ` /team-admin/model-provider ` 页面为各自团队补齐专属 API Key 与服务参数。
        </div>
      </div>
      <div className="grid gap-4 px-12 pb-8 md:grid-cols-2">
        {governanceCards.map(card => (
          <div key={card.href} className="rounded-2xl border border-divider-regular bg-components-panel-bg p-6 shadow-sm">
            <div className="text-base font-semibold text-text-primary">{card.title}</div>
            <div className="mt-2 text-sm leading-6 text-text-tertiary">{card.description}</div>
            <div className="mt-5">
              <Link
                href={card.href}
                className="inline-flex items-center rounded-lg bg-components-button-primary-bg px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-components-button-primary-hover-bg"
              >
                {card.action}
              </Link>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

export default SysAdminGovernancePage
