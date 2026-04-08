import type { SlashCommandHandler } from './types'
import { RiFeedbackLine } from '@remixicon/react'
import * as React from 'react'
import { getI18n } from 'react-i18next'
import { registerCommands, unregisterCommands } from './command-bus'

// Forum command dependency types
type ForumDeps = Record<string, never>

const tr = (key: string, fallback: string, locale: string, ns: 'app' | 'common') => {
  return getI18n()?.t?.(key as any, { ns, lng: locale }) ?? fallback
}

/**
 * Forum command - Opens Dify community forum
 */
export const forumCommand: SlashCommandHandler<ForumDeps> = {
  name: 'forum',
  description: 'Open Dify community forum',
  mode: 'direct',

  // Direct execution function
  execute: () => {
    const url = 'https://forum.dify.ai'
    window.open(url, '_blank', 'noopener,noreferrer')
  },

  async search(args: string, locale: string = 'en') {
    return [{
      id: 'forum',
      title: tr('userProfile.forum', 'Forum', locale, 'common'),
      description: tr('gotoAnything.actions.feedbackDesc', 'Open community feedback discussions', locale, 'app'),
      type: 'command' as const,
      icon: (
        <div className="flex h-6 w-6 items-center justify-center rounded-md border-[0.5px] border-divider-regular bg-components-panel-bg">
          <RiFeedbackLine className="h-4 w-4 text-text-tertiary" />
        </div>
      ),
      data: { command: 'navigation.forum', args: { url: 'https://forum.dify.ai' } },
    }]
  },

  register(_deps: ForumDeps) {
    registerCommands({
      'navigation.forum': async (args) => {
        const url = args?.url || 'https://forum.dify.ai'
        window.open(url, '_blank', 'noopener,noreferrer')
      },
    })
  },

  unregister() {
    unregisterCommands(['navigation.forum'])
  },
}
