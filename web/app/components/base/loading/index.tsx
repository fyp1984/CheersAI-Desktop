'use client'

import { RiLoader4Line } from '@remixicon/react'
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
      <RiLoader4Line
        className="spin-animation h-8 w-8 text-text-accent"
        aria-hidden="true"
      />
    </div>
  )
}

export default Loading
