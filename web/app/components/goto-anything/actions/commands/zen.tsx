import type { SlashCommandHandler } from './types'
import { RiFullscreenLine } from '@remixicon/react'
import * as React from 'react'
import { getI18n } from 'react-i18next'
import { isInWorkflowPage } from '@/app/components/workflow/constants'
import { registerCommands, unregisterCommands } from './command-bus'

// Zen command dependency types - no external dependencies needed
type ZenDeps = Record<string, never>

const tr = (key: string, fallback: string, locale: string) => {
  return getI18n()?.t?.(key as any, { ns: 'app', lng: locale }) ?? fallback
}

// Custom event name for zen toggle
export const ZEN_TOGGLE_EVENT = 'zen-toggle-maximize'

// Shared function to dispatch zen toggle event
const toggleZenMode = () => {
  window.dispatchEvent(new CustomEvent(ZEN_TOGGLE_EVENT))
}

/**
 * Zen command - Toggle canvas maximize (focus mode) in workflow pages
 * Only available in workflow and chatflow pages
 */
export const zenCommand: SlashCommandHandler<ZenDeps> = {
  name: 'zen',
  description: 'Toggle canvas focus mode',
  mode: 'direct',

  // Only available in workflow/chatflow pages
  isAvailable: () => isInWorkflowPage(),

  // Direct execution function
  execute: toggleZenMode,

  async search(_args: string, locale: string = 'en') {
    return [{
      id: 'zen',
      title: tr('gotoAnything.actions.zenTitle', 'Zen Mode', locale),
      description: tr('gotoAnything.actions.zenDesc', 'Toggle canvas focus mode', locale),
      type: 'command' as const,
      icon: (
        <div className="flex h-6 w-6 items-center justify-center rounded-md border-[0.5px] border-divider-regular bg-components-panel-bg">
          <RiFullscreenLine className="h-4 w-4 text-text-tertiary" />
        </div>
      ),
      data: { command: 'workflow.zen', args: {} },
    }]
  },

  register(_deps: ZenDeps) {
    registerCommands({
      'workflow.zen': async () => toggleZenMode(),
    })
  },

  unregister() {
    unregisterCommands(['workflow.zen'])
  },
}
