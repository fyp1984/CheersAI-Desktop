'use client'
import type { SuccessInvitationResult } from '.'
import copy from 'copy-to-clipboard'
import * as React from 'react'
import { useCallback, useEffect, useMemo, useState } from 'react'
import { useTranslation } from 'react-i18next'
import Tooltip from '@/app/components/base/tooltip'
import s from './index.module.css'

type IInvitationLinkProps = {
  value: SuccessInvitationResult
}

const InvitationLink = ({
  value,
}: IInvitationLinkProps) => {
  const { t } = useTranslation()
  const [isCopied, setIsCopied] = useState(false)
  const fullUrl = useMemo(() => {
    if (value.url.startsWith('http'))
      return value.url

    if (typeof window === 'undefined')
      return value.url

    return `${window.location.origin}${value.url}`
  }, [value.url])

  const copyHandle = useCallback(() => {
    copy(fullUrl)
    setIsCopied(true)
  }, [fullUrl])

  useEffect(() => {
    if (isCopied) {
      const timeout = setTimeout(() => {
        setIsCopied(false)
      }, 1000)

      return () => {
        clearTimeout(timeout)
      }
    }
  }, [isCopied])

  return (
    <div className="flex items-stretch rounded-lg border border-components-input-border-active bg-components-input-bg-normal hover:bg-state-base-hover">
      <div className="flex min-w-0 grow items-stretch">
        <div className="min-w-0 grow text-[13px]">
          <Tooltip
            popupContent={fullUrl}
          >
            <div className="flex h-full cursor-pointer items-center px-2 py-2 text-text-primary" onClick={copyHandle}>
              <div className="break-all">{fullUrl}</div>
            </div>
          </Tooltip>
        </div>
        <div className="my-2 h-auto w-px shrink-0 bg-divider-regular" />
        <Tooltip
          popupContent={isCopied ? t('copied', { ns: 'appApi' }) : t('copy', { ns: 'appApi' })}
        >
          <div className="shrink-0 px-0.5">
            <div className={`box-border flex h-[30px] w-[30px] cursor-pointer items-center justify-center rounded-lg hover:bg-state-base-hover ${s.copyIcon} ${isCopied ? s.copied : ''}`} onClick={copyHandle}>
            </div>
          </div>
        </Tooltip>
      </div>
    </div>
  )
}

export default InvitationLink
