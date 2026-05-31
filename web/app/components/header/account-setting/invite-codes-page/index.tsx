'use client'

import { RiFileCopyLine } from '@remixicon/react'
import Toast from '@/app/components/base/toast'
import { useAccountInviteCodes } from '@/service/use-common'
import { cn } from '@/utils/classnames'

const getInviteLink = (code: string) => {
  if (typeof window === 'undefined')
    return `/signup?invite_code=${encodeURIComponent(code)}`
  return `${window.location.origin}/signup?invite_code=${encodeURIComponent(code)}`
}

const InviteCodesPage = () => {
  const { data, isLoading } = useAccountInviteCodes()
  const inviteCodes = data?.data || []
  const unusedCount = inviteCodes.filter(item => item.status === 'unused').length

  const handleCopyLink = async (code: string) => {
    await navigator.clipboard.writeText(getInviteLink(code))
    Toast.notify({ type: 'success', message: '邀请链接已复制' })
  }

  return (
    <div className="space-y-4">
      <div className="rounded-xl border border-divider-subtle bg-background-section-burn p-4">
        <div className="system-md-semibold text-text-primary">我的邀请码</div>
        <div className="system-sm-regular mt-1 text-text-secondary">
          每个账号固定 5 个邀请码，邀请码使用后立即失效。点击邀请码可复制带邀请码的申请链接。当前剩余
          {' '}
          <span className="system-sm-semibold text-text-primary">{unusedCount}</span>
          {' '}
          个。
        </div>
      </div>

      <div className="rounded-xl border border-divider-subtle bg-components-panel-bg">
        {isLoading && (
          <div className="system-sm-regular p-4 text-text-tertiary">正在加载邀请码...</div>
        )}
        {!isLoading && inviteCodes.length === 0 && (
          <div className="system-sm-regular p-4 text-text-tertiary">暂无邀请码</div>
        )}
        {inviteCodes.map(inviteCode => (
          <div
            key={inviteCode.id}
            className="flex items-center justify-between gap-4 border-b border-divider-subtle p-4 last:border-b-0"
          >
            <div>
              <div
                role="button"
                tabIndex={0}
                className={cn(
                  'system-md-semibold font-mono tracking-wide',
                  inviteCode.status === 'unused'
                    ? 'cursor-pointer text-text-primary hover:text-text-accent'
                    : 'text-text-tertiary line-through',
                )}
                onClick={() => inviteCode.status === 'unused' && handleCopyLink(inviteCode.code)}
                onKeyDown={(e) => {
                  if (inviteCode.status === 'unused' && (e.key === 'Enter' || e.key === ' '))
                    handleCopyLink(inviteCode.code)
                }}
              >
                {inviteCode.code}
              </div>
              <div className="system-xs-regular mt-1 text-text-tertiary">
                {inviteCode.status === 'unused' ? '未使用' : '已使用'}
              </div>
            </div>
            <button
              type="button"
              className="flex h-8 items-center gap-1 rounded-lg border border-components-button-secondary-border px-3 text-text-secondary hover:bg-state-base-hover disabled:cursor-not-allowed disabled:opacity-50"
              disabled={inviteCode.status !== 'unused'}
              onClick={() => handleCopyLink(inviteCode.code)}
            >
              <RiFileCopyLine className="h-4 w-4" />
              <span className="system-sm-medium">复制链接</span>
            </button>
          </div>
        ))}
      </div>
    </div>
  )
}

export default InviteCodesPage
