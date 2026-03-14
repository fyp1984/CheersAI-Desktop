'use client'

import { useTranslation } from 'react-i18next'
import { cn } from '@/utils/classnames'
import './style.css'

type ILoadingProps = {
  type?: 'area' | 'app'
  className?: string
}

const Loading = (props?: ILoadingProps) => {
  const { type = 'area', className } = props || {}
  const { t } = useTranslation()

  return (
    <div
      className={cn(
        'flex w-full items-center justify-center',
        type === 'app' && 'h-full',
        className,
      )}
      role="status"
      aria-live="polite"
      aria-label={t('loading', { ns: 'appApi' })}
    >
      <img
        src={`${process.env.NEXT_PUBLIC_BASE_PATH || ''}/logo/CheersAI.png`}
        className="spin-animation w-8 h-8 object-contain"
        alt="Loading..."
      />

    </div>
  )
}

export default Loading
