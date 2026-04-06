import { describe, expect, it } from 'vitest'
import { getCapabilitiesByRole, getWorkspaceCapabilities, hasWorkspaceCapability, WORKSPACE_CAPABILITIES } from './workspace-capabilities'

describe('workspace capabilities', () => {
  it('returns configured capabilities for dataset operator role', () => {
    const capabilities = getCapabilitiesByRole('dataset_operator')

    expect(capabilities).toContain(WORKSPACE_CAPABILITIES.knowledgeEdit)
    expect(capabilities).not.toContain(WORKSPACE_CAPABILITIES.teamManage)
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
})
