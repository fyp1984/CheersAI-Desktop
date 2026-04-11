import { describe, expect, it } from 'vitest'
import { getCapabilitiesByRole, getWorkspaceCapabilities, hasPluginManageWorkspaceCapability, hasWorkspaceCapability, WORKSPACE_CAPABILITIES } from './workspace-capabilities'

describe('workspace capabilities', () => {
  it('returns configured capabilities for dataset operator role', () => {
    const capabilities = getCapabilitiesByRole('dataset_operator')

    expect(capabilities).toContain(WORKSPACE_CAPABILITIES.knowledgeEdit)
    expect(capabilities).toContain(WORKSPACE_CAPABILITIES.appView)
    expect(capabilities).not.toContain(WORKSPACE_CAPABILITIES.memberManage)
  })

  it('prefers workspace capabilities from backend payload', () => {
    const capabilities = getWorkspaceCapabilities({
      role: 'normal',
      capabilities: [WORKSPACE_CAPABILITIES.auditView],
    })

    expect(capabilities).toEqual([WORKSPACE_CAPABILITIES.auditView])
  })

  it('falls back to role-derived capabilities when backend payload is empty', () => {
    expect(hasWorkspaceCapability({
      role: 'editor',
      capabilities: [],
    }, WORKSPACE_CAPABILITIES.workflowEdit)).toBe(true)

    expect(hasWorkspaceCapability({
      role: 'normal',
      capabilities: [],
    }, WORKSPACE_CAPABILITIES.workflowEdit)).toBe(false)
  })

  it('grants member users shared view and run capabilities', () => {
    expect(hasWorkspaceCapability({
      role: 'normal',
      capabilities: [],
    }, WORKSPACE_CAPABILITIES.appView)).toBe(true)

    expect(hasWorkspaceCapability({
      role: 'normal',
      capabilities: [],
    }, WORKSPACE_CAPABILITIES.workflowRun)).toBe(true)

    expect(hasWorkspaceCapability({
      role: 'normal',
      capabilities: [],
    }, WORKSPACE_CAPABILITIES.languageManage)).toBe(true)
  })

  it('grants editors model provider and data source management but not member management', () => {
    expect(hasWorkspaceCapability({
      role: 'editor',
      capabilities: [],
    }, WORKSPACE_CAPABILITIES.modelProviderManage)).toBe(true)

    expect(hasWorkspaceCapability({
      role: 'editor',
      capabilities: [],
    }, WORKSPACE_CAPABILITIES.dataSourceManage)).toBe(true)

    expect(hasWorkspaceCapability({
      role: 'editor',
      capabilities: [],
    }, WORKSPACE_CAPABILITIES.memberManage)).toBe(false)
  })

  it('treats plugin manage as compatible with legacy and new API extension capabilities', () => {
    expect(hasPluginManageWorkspaceCapability({
      role: 'normal',
      capabilities: [WORKSPACE_CAPABILITIES.apiExtensionManage],
    })).toBe(true)

    expect(hasPluginManageWorkspaceCapability({
      role: 'normal',
      capabilities: [WORKSPACE_CAPABILITIES.pluginManage],
    })).toBe(true)

    expect(hasPluginManageWorkspaceCapability({
      role: 'editor',
      capabilities: [],
    })).toBe(false)
  })
})
