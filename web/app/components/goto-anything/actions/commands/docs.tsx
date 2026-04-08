import type { SlashCommandHandler } from './types'
import { RiBookOpenLine } from '@remixicon/react'
import * as React from 'react'
import { getI18n } from 'react-i18next'
import { defaultDocBaseUrl } from '@/context/i18n'
import { getDocLanguage } from '@/i18n-config/language'
import { registerCommands, unregisterCommands } from './command-bus'

// Documentation command dependency types - no external dependencies needed
type DocDeps = Record<string, never>

const tr = (key: string, fallback: string, locale: string, ns: 'app' | 'common') => {
  return getI18n()?.t?.(key as any, { ns, lng: locale }) ?? fallback
}

/**
 * Documentation command - Opens help documentation
 */
export const docsCommand: SlashCommandHandler<DocDeps> = {
  name: 'docs',
  description: 'Open documentation',
  mode: 'direct',

  // Direct execution function
  execute: () => {
    const i18n = getI18n()
    const currentLocale = i18n?.language || 'en'
    const docLanguage = getDocLanguage(currentLocale)
    const url = `${defaultDocBaseUrl}/${docLanguage}`
    window.open(url, '_blank', 'noopener,noreferrer')
  },

  async search(args: string, locale: string = 'en') {
    return [{
      id: 'doc',
      title: tr('userProfile.helpCenter', 'Help Center', locale, 'common'),
      description: tr('gotoAnything.actions.docDesc', 'Open help documentation', locale, 'app'),
      type: 'command' as const,
      icon: (
        <div className="flex h-6 w-6 items-center justify-center rounded-md border-[0.5px] border-divider-regular bg-components-panel-bg">
          <RiBookOpenLine className="h-4 w-4 text-text-tertiary" />
        </div>
      ),
      data: { command: 'navigation.doc', args: {} },
    }]
  },

  register(_deps: DocDeps) {
    registerCommands({
      'navigation.doc': async (_args) => {
        const currentLocale = getI18n()?.language || 'en'
        const docLanguage = getDocLanguage(currentLocale)
        const url = `${defaultDocBaseUrl}/${docLanguage}`
        window.open(url, '_blank', 'noopener,noreferrer')
      },
    })
  },

  unregister() {
    unregisterCommands(['navigation.doc'])
  },
}
