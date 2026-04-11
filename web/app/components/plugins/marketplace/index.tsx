'use client'

import { TanstackQueryInitializer } from '@/context/query-client'
import Description from './description'
import ListWrapper from './list/list-wrapper'
import StickySearchAndSwitchWrapper from './sticky-search-and-switch-wrapper'

type MarketplaceProps = {
  showInstallButton?: boolean
  pluginTypeSwitchClassName?: string
}

const Marketplace = ({
  showInstallButton = true,
  pluginTypeSwitchClassName,
}: MarketplaceProps) => {
  return (
    <TanstackQueryInitializer>
      <Description />
      <StickySearchAndSwitchWrapper
        pluginTypeSwitchClassName={pluginTypeSwitchClassName}
      />
      <ListWrapper
        showInstallButton={showInstallButton}
      />
    </TanstackQueryInitializer>
  )
}

export default Marketplace
