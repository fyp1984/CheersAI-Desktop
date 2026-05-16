import type { FC } from 'react'
import type { ModelProvider } from '../declarations'
import { AnthropicDark, AnthropicLight } from '@/app/components/base/icons/src/public/llm'
import { Openai } from '@/app/components/base/icons/src/vender/other'
import { API_PREFIX } from '@/config'
import useTheme from '@/hooks/use-theme'
import { renderI18nObject } from '@/i18n-config'
import { Theme } from '@/types/app'
import { cn } from '@/utils/classnames'
import { useLanguage } from '../hooks'

type ProviderIconProps = {
  provider: ModelProvider
  className?: string
}
const ProviderIcon: FC<ProviderIconProps> = ({
  provider,
  className,
}) => {
  const { theme } = useTheme()
  const language = useLanguage()
  const normalizeConsoleApiPath = (path: string) => {
    if (path.includes('/console/api/console/api/'))
      return path.replace('/console/api/console/api/', '/console/api/')

    return path
  }

  if (provider.provider === 'langgenius/anthropic/anthropic') {
    return (
      <div className="mb-2 py-[7px]">
        {theme === Theme.dark && <AnthropicLight className="h-2.5 w-[90px]" />}
        {theme === Theme.light && <AnthropicDark className="h-2.5 w-[90px]" />}
      </div>
    )
  }

  if (provider.provider === 'langgenius/openai/openai') {
    return (
      <div className="mb-2">
        <Openai className="h-6 w-auto text-text-inverted-dimmed" />
      </div>
    )
  }

  const iconSrc = renderI18nObject(
    theme === Theme.dark && provider.icon_small_dark
      ? provider.icon_small_dark
      : provider.icon_small,
    language,
  )

  const getIconUrl = (url: string) => {
    if (!url)
      return ''

    try {
      if (url.startsWith('http://') || url.startsWith('https://')) {
        const urlObj = new URL(url)
        const path = normalizeConsoleApiPath(urlObj.pathname + urlObj.search)

        if (typeof window !== 'undefined') {
          const currentUrl = new URL(window.location.href)
          const loopbackHosts = new Set(['localhost', '127.0.0.1', '0.0.0.0'])
          const useAbsoluteLocalUrl = loopbackHosts.has(currentUrl.hostname) && loopbackHosts.has(urlObj.hostname)
          const sameHostDifferentPort = currentUrl.hostname === urlObj.hostname && currentUrl.port !== urlObj.port

          // Localhost 调试场景下必须保留 5001 端口，否则会错误命中 localhost 网关并得到 502。
          if (useAbsoluteLocalUrl || sameHostDifferentPort)
            return `${urlObj.origin}${path}`
        }

        return path
      }
    }
    catch (e) {
      // Ignore parsing errors
    }

    if (typeof window !== 'undefined' && url.startsWith('/console/api/')) {
      const currentUrl = new URL(window.location.href)
      const loopbackHosts = new Set(['localhost', '127.0.0.1', '0.0.0.0'])

      if (loopbackHosts.has(currentUrl.hostname))
        return new URL(normalizeConsoleApiPath(url), API_PREFIX).toString()
    }

    return normalizeConsoleApiPath(url)
  }

  return (
    <div className={cn('inline-flex items-center gap-2', className)}>
      <img
        alt="provider-icon"
        src={getIconUrl(iconSrc)}
        className="h-6 w-6"
      />
      <div className="system-md-semibold text-text-primary">
        {renderI18nObject(provider.label, language)}
      </div>
    </div>
  )
}

export default ProviderIcon
