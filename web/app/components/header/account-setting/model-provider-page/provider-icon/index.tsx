import type { FC } from 'react'
import type { ModelProvider } from '../declarations'
import { AnthropicDark, AnthropicLight } from '@/app/components/base/icons/src/public/llm'
import { Openai } from '@/app/components/base/icons/src/vender/other'
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
      // 如果是绝对 URL，提取路径部分，实现“从当前客户端 URL 动态获取”
      // 这样无论后端配置的域名是什么（如 desktop.cheersai.cloud），前端都会使用当前访问的域名
      if (url.startsWith('http://') || url.startsWith('https://')) {
        const urlObj = new URL(url)
        let path = urlObj.pathname + urlObj.search

        // 同时修复可能存在的路径重复问题
        if (path.includes('/console/api/console/api/'))
          path = path.replace('/console/api/console/api/', '/console/api/')

        return path
      }
    }
    catch (e) {
      // Ignore parsing errors
    }

    // 对于相对路径，也进行重复路径检查
    if (url.includes('/console/api/console/api/'))
      return url.replace('/console/api/console/api/', '/console/api/')

    return url
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
