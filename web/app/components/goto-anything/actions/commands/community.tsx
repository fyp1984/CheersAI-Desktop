import type { SlashCommandHandler } from './types'
import { RiDiscordLine } from '@remixicon/react'
import * as React from 'react'
import { getI18n } from 'react-i18next'
import { registerCommands, unregisterCommands } from './command-bus'

// Community command dependency types
type CommunityDeps = Record<string, never>

const tr = (key: string, fallback: string, locale: string, ns: 'app' | 'common') => {
  return getI18n()?.t?.(key as any, { ns, lng: locale }) ?? fallback
}

/**
 * Community command - Opens Discord community
 */
export const communityCommand: SlashCommandHandler<CommunityDeps> = {
  name: 'community',
  description: 'Open community Discord',
  mode: 'direct',

  // Direct execution function
  execute: () => {
    const url = 'https://discord.gg/5AEfbxcd9k'
    window.open(url, '_blank', 'noopener,noreferrer')
  },

  async search(args: string, locale: string = 'en') {
    return [{
      id: 'community',
      title: tr('userProfile.community', 'Community', locale, 'common'),
      description: tr('gotoAnything.actions.communityDesc', 'Open Discord community', locale, 'app'),
      type: 'command' as const,
      icon: (
        <div className="flex h-6 w-6 items-center justify-center rounded-md border-[0.5px] border-divider-regular bg-components-panel-bg">
          <RiDiscordLine className="h-4 w-4 text-text-tertiary" />
        </div>
      ),
      data: { command: 'navigation.community', args: { url: 'https://discord.gg/5AEfbxcd9k' } },
    }]
  },

  register(_deps: CommunityDeps) {
    registerCommands({
      'navigation.community': async (args) => {
        const url = args?.url || 'https://discord.gg/5AEfbxcd9k'
        window.open(url, '_blank', 'noopener,noreferrer')
      },
    })
  },

  unregister() {
    unregisterCommands(['navigation.community'])
  },
}
