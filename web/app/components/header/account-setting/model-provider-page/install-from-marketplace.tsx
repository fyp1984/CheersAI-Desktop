import type {
  ModelProvider,
} from './declarations'
import {
  RiArrowRightUpLine,
  RiInformation2Fill,
} from '@remixicon/react'
import { useTheme } from 'next-themes'
import Link from 'next/link'
import { useTranslation } from 'react-i18next'
import Divider from '@/app/components/base/divider'
import { getMarketplaceUrl } from '@/utils/var'

type InstallFromMarketplaceProps = {
  providers: ModelProvider[]
  searchText: string
}
const InstallFromMarketplace = ({
  providers: _providers,
  searchText: _searchText,
}: InstallFromMarketplaceProps) => {
  const { t } = useTranslation()
  const { theme } = useTheme()

  return (
    <div className="mb-2">
      <Divider className="!mt-4 h-px" />
      <div className="mt-4 rounded-xl border border-components-panel-border bg-components-panel-bg p-4">
        <div className="flex items-start justify-between gap-4">
          <div className="flex items-start gap-2">
            <div className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-[#eff6ff] text-[#2563eb]">
              <RiInformation2Fill className="h-4 w-4" />
            </div>
            <div>
              <div className="system-sm-semibold text-text-primary">{t('modelProvider.installProvider', { ns: 'common' })}</div>
              <div className="system-xs-regular mt-1 text-text-secondary">{t('modelProvider.discoverMore', { ns: 'common' })}</div>
            </div>
          </div>
          <Link target="_blank" href={getMarketplaceUrl('', { theme })} className="system-sm-medium inline-flex shrink-0 items-center text-text-accent">
            {t('marketplace.difyMarketplace', { ns: 'plugin' })}
            <RiArrowRightUpLine className="h-4 w-4" />
          </Link>
        </div>
      </div>
    </div>
  )
}

export default InstallFromMarketplace
