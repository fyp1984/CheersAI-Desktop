'use client'
import type { FC } from 'react'
import { cn } from '@/utils/classnames'
import { basePath } from '@/utils/var'

type LogoSiteProps = {
  className?: string
}

const LogoSite: FC<LogoSiteProps> = ({
  className,
}) => {
  return (
    <img
      src={`${basePath}/logo/logo-site.png`}
      className={cn('block h-[34px] w-auto', className)}
      alt="logo"
    />
  )
}

export default LogoSite
