import { RiArrowRightUpLine, RiChatSmile2Line, RiMailSendLine, RiQuestionLine } from '@remixicon/react'
import { useTranslation } from 'react-i18next'
import { toggleZendeskWindow } from '@/app/components/base/zendesk/utils'
import { Plan } from '@/app/components/billing/type'
import { ZENDESK_WIDGET_KEY } from '@/config'
import { useAppContext } from '@/context/app-context'
import { useProviderContext } from '@/context/provider-context'
import { cn } from '@/utils/classnames'
import { mailToSupport } from '../utils/util'

type SupportProps = {
  closeAccountDropdown: () => void
}

export default function Support({ closeAccountDropdown }: SupportProps) {
  const itemClassName = `
  flex items-center w-full h-9 pl-3 pr-2 text-text-secondary system-md-regular
  rounded-lg hover:bg-state-base-hover cursor-pointer gap-1
`
  const { t } = useTranslation()
  const { plan } = useProviderContext()
  const { userProfile, langGeniusVersionInfo } = useAppContext()
  const hasDedicatedChannel = plan.type !== Plan.sandbox

  const handleOpenSupport = () => {
    if (ZENDESK_WIDGET_KEY && ZENDESK_WIDGET_KEY.trim() !== '') {
      toggleZendeskWindow(true)
      closeAccountDropdown()
      return
    }

    const fallbackUrl = hasDedicatedChannel
      ? mailToSupport(userProfile.email, plan.type, langGeniusVersionInfo?.current_version)
      : 'https://forum.dify.ai/'

    window.open(fallbackUrl, '_blank', 'noopener,noreferrer')
    closeAccountDropdown()
  }

  return (
    <button
      type="button"
      className={cn(itemClassName, 'group justify-between text-left')}
      onClick={handleOpenSupport}
    >
      {ZENDESK_WIDGET_KEY && ZENDESK_WIDGET_KEY.trim() !== ''
        ? <RiChatSmile2Line className="size-4 shrink-0 text-text-tertiary" />
        : <RiMailSendLine className="size-4 shrink-0 text-text-tertiary" />}
      <div className="system-md-regular grow px-1 text-text-secondary">{t('userProfile.support', { ns: 'common' })}</div>
      <RiArrowRightUpLine className="size-[14px] shrink-0 text-text-tertiary" />
    </button>
  )
}
