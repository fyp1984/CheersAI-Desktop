import { describe, expect, it } from 'vitest'
import {
  getCapabilitiesByRole,
  getWorkspaceCapabilities,
  hasAnyWorkspaceCapability,
  hasPluginManageWorkspaceCapability,
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

  it('checks single and multi capability helpers correctly', () => {
    const workspace = {
      role: 'normal',
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
})
