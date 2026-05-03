import * as React from 'react'
import { useTranslation } from 'react-i18next'

const DefaultCards = React.memo(() => {
  const renderArray = Array.from({ length: 36 })
  return (
    <>
      {
        renderArray.map((_, index) => (
          <div
            key={index}
            className="inline-flex h-[160px] rounded-xl bg-background-default-lighter"
          />
        ))
      }
    </>
  )
})

type EmptyProps = {
  hint?: string
}

const Empty = ({ hint }: EmptyProps) => {
  const { t } = useTranslation()

  return (
    <>
      <DefaultCards />
      <div className="pointer-events-none absolute inset-0 z-20 flex items-center justify-center bg-gradient-to-t from-background-body to-transparent">
        <div className="flex max-w-[420px] flex-col items-center gap-2 px-6 text-center">
          <span className="system-md-medium text-text-tertiary">
            {t('newApp.noAppsFound', { ns: 'app' })}
          </span>
          {hint && (
            <span className="system-xs-regular text-text-quaternary">
              {hint}
            </span>
          )}
        </div>
      </div>
    </>
  )
}

export default React.memo(Empty)
