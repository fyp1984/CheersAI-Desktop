import { describe, expect, it } from 'vitest'
import { InstallationScope } from '@/types/feature'
import {
  getCapabilitiesByRole,
  getWorkspaceCapabilities,
  hasAnyWorkspaceCapability,
  hasBuiltInAdminAccess,
  hasPluginManageWorkspaceCapability,
  hasPluginReadWorkspaceCapability,
  hasWorkspaceCapability,
  WORKSPACE_CAPABILITIES,
} from './workspace-capabilities'

describe('workspace-capabilities', () => {
  it('returns empty capabilities for unknown roles', () => {
    expect(getCapabilitiesByRole()).toEqual([])
    expect(getCapabilitiesByRole('unknown-role')).toEqual([])
  })

  it('prefers explicit workspace capabilities over role defaults', () => {
    expect(getWorkspaceCapabilities({
      role: 'normal',
      capabilities: [
        WORKSPACE_CAPABILITIES.settingsTeam,
        WORKSPACE_CAPABILITIES.settingsTeam,
        WORKSPACE_CAPABILITIES.teamManage,
      ],
    })).toEqual([
      WORKSPACE_CAPABILITIES.settingsTeam,
      WORKSPACE_CAPABILITIES.teamManage,
    ])
  })

  it('falls back to role defaults when workspace capabilities are absent', () => {
    expect(getWorkspaceCapabilities({
      role: 'admin',
      capabilities: [],
    })).toContain(WORKSPACE_CAPABILITIES.teamManage)
  })

  it('keeps team editor away from provider and plugin governance defaults', () => {
    const editorCapabilities = getCapabilitiesByRole('editor')

    expect(editorCapabilities).not.toContain(WORKSPACE_CAPABILITIES.modelManage)
    expect(editorCapabilities).not.toContain(WORKSPACE_CAPABILITIES.modelProviderManage)
    expect(editorCapabilities).not.toContain(WORKSPACE_CAPABILITIES.pluginManage)
    expect(editorCapabilities).toContain(WORKSPACE_CAPABILITIES.knowledgeEdit)
    expect(editorCapabilities).toContain(WORKSPACE_CAPABILITIES.workflowEdit)
  })

  it('checks single and multi capability helpers correctly', () => {
    const workspace = {
      role: 'normal' as const,
      capabilities: [WORKSPACE_CAPABILITIES.settingsPersonal],
    }

    expect(hasWorkspaceCapability(workspace, WORKSPACE_CAPABILITIES.settingsPersonal)).toBe(true)
    expect(hasWorkspaceCapability(workspace, WORKSPACE_CAPABILITIES.teamManage)).toBe(false)
    expect(hasAnyWorkspaceCapability(workspace, [
      WORKSPACE_CAPABILITIES.teamManage,
      WORKSPACE_CAPABILITIES.settingsPersonal,
    ])).toBe(true)
  })

  it('recognizes either plugin or api-extension manage for plugin governance', () => {
    expect(hasPluginManageWorkspaceCapability({
      role: 'normal',
      capabilities: [WORKSPACE_CAPABILITIES.pluginManage],
    })).toBe(true)

    expect(hasPluginManageWorkspaceCapability({
      role: 'normal',
      capabilities: [WORKSPACE_CAPABILITIES.apiExtensionManage],
    })).toBe(true)

    expect(hasPluginManageWorkspaceCapability({
      role: 'normal',
      capabilities: [WORKSPACE_CAPABILITIES.settingsPersonal],
    })).toBe(false)
  })

  it('treats built-in admin install scope as a system admin fallback', () => {
    expect(hasBuiltInAdminAccess({
      role: 'normal',
      capabilities: [],
    }, {
      plugin_installation_permission: {
        plugin_installation_scope: InstallationScope.ALL,
        restrict_to_marketplace_only: false,
      },
    })).toBe(true)

    expect(hasBuiltInAdminAccess({
      role: 'normal',
      capabilities: [],
    }, {
      plugin_installation_permission: {
        plugin_installation_scope: InstallationScope.NONE,
        restrict_to_marketplace_only: false,
      },
    })).toBe(false)

    expect(hasBuiltInAdminAccess({
      role: 'normal',
      capabilities: [WORKSPACE_CAPABILITIES.systemAdmin],
    }, {
      plugin_installation_permission: {
        plugin_installation_scope: InstallationScope.NONE,
        restrict_to_marketplace_only: false,
      },
    })).toBe(true)
  })

  it('allows desktop members to read the plugins page without manage permission', () => {
    expect(hasPluginReadWorkspaceCapability({
      role: 'normal',
      capabilities: [WORKSPACE_CAPABILITIES.desktopAccess],
    })).toBe(true)

    expect(hasPluginReadWorkspaceCapability({
      role: 'normal',
      capabilities: [WORKSPACE_CAPABILITIES.pluginManage],
    })).toBe(true)

    expect(hasPluginReadWorkspaceCapability({
      role: 'normal',
      capabilities: [WORKSPACE_CAPABILITIES.settingsPersonal],
    })).toBe(false)
  })
})
