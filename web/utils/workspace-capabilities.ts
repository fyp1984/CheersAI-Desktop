import type { ICurrentWorkspace } from '@/models/common'

export const WORKSPACE_CAPABILITIES = {
  desktopAccess: 'desktop_access',
  agentUse: 'desktop_agent_use',
  agentTest: 'desktop_agent_test',
  agentManage: 'desktop_agent_manage',
  pluginManage: 'desktop_plugin_manage',
  chatUse: 'desktop_chat_use',
  knowledgeView: 'desktop_knowledge_view',
  knowledgeEdit: 'desktop_knowledge_edit',
  workflowView: 'desktop_workflow_view',
  workflowEdit: 'desktop_workflow_edit',
  appView: 'desktop_app_view',
  appEdit: 'desktop_app_edit',
  exploreView: 'desktop_explore_view',
  settingsPersonal: 'desktop_settings_personal',
  settingsTeam: 'desktop_settings_team',
  teamManage: 'desktop_team_manage',
  auditView: 'desktop_audit_view',
  modelManage: 'desktop_model_manage',
} as const

const WORKSPACE_ROLE_CAPABILITIES: Record<string, string[]> = {
  owner: [
    WORKSPACE_CAPABILITIES.desktopAccess,
    WORKSPACE_CAPABILITIES.agentUse,
    WORKSPACE_CAPABILITIES.agentTest,
    WORKSPACE_CAPABILITIES.agentManage,
    WORKSPACE_CAPABILITIES.pluginManage,
    WORKSPACE_CAPABILITIES.chatUse,
    WORKSPACE_CAPABILITIES.knowledgeView,
    WORKSPACE_CAPABILITIES.knowledgeEdit,
    WORKSPACE_CAPABILITIES.workflowView,
    WORKSPACE_CAPABILITIES.workflowEdit,
    WORKSPACE_CAPABILITIES.appView,
    WORKSPACE_CAPABILITIES.appEdit,
    WORKSPACE_CAPABILITIES.exploreView,
    WORKSPACE_CAPABILITIES.settingsPersonal,
    WORKSPACE_CAPABILITIES.settingsTeam,
    WORKSPACE_CAPABILITIES.teamManage,
    WORKSPACE_CAPABILITIES.auditView,
    WORKSPACE_CAPABILITIES.modelManage,
  ],
  admin: [
    WORKSPACE_CAPABILITIES.desktopAccess,
    WORKSPACE_CAPABILITIES.agentUse,
    WORKSPACE_CAPABILITIES.agentTest,
    WORKSPACE_CAPABILITIES.agentManage,
    WORKSPACE_CAPABILITIES.pluginManage,
    WORKSPACE_CAPABILITIES.chatUse,
    WORKSPACE_CAPABILITIES.knowledgeView,
    WORKSPACE_CAPABILITIES.knowledgeEdit,
    WORKSPACE_CAPABILITIES.workflowView,
    WORKSPACE_CAPABILITIES.workflowEdit,
    WORKSPACE_CAPABILITIES.appView,
    WORKSPACE_CAPABILITIES.appEdit,
    WORKSPACE_CAPABILITIES.exploreView,
    WORKSPACE_CAPABILITIES.settingsPersonal,
    WORKSPACE_CAPABILITIES.settingsTeam,
    WORKSPACE_CAPABILITIES.teamManage,
    WORKSPACE_CAPABILITIES.auditView,
    WORKSPACE_CAPABILITIES.modelManage,
  ],
  editor: [
    WORKSPACE_CAPABILITIES.desktopAccess,
    WORKSPACE_CAPABILITIES.agentUse,
    WORKSPACE_CAPABILITIES.agentTest,
    WORKSPACE_CAPABILITIES.agentManage,
    WORKSPACE_CAPABILITIES.pluginManage,
    WORKSPACE_CAPABILITIES.chatUse,
    WORKSPACE_CAPABILITIES.knowledgeView,
    WORKSPACE_CAPABILITIES.knowledgeEdit,
    WORKSPACE_CAPABILITIES.workflowView,
    WORKSPACE_CAPABILITIES.workflowEdit,
    WORKSPACE_CAPABILITIES.appView,
    WORKSPACE_CAPABILITIES.appEdit,
    WORKSPACE_CAPABILITIES.exploreView,
    WORKSPACE_CAPABILITIES.settingsPersonal,
  ],
  normal: [
    WORKSPACE_CAPABILITIES.desktopAccess,
    WORKSPACE_CAPABILITIES.agentUse,
    WORKSPACE_CAPABILITIES.chatUse,
    WORKSPACE_CAPABILITIES.knowledgeView,
    WORKSPACE_CAPABILITIES.exploreView,
    WORKSPACE_CAPABILITIES.settingsPersonal,
  ],
  dataset_operator: [
    WORKSPACE_CAPABILITIES.desktopAccess,
    WORKSPACE_CAPABILITIES.agentUse,
    WORKSPACE_CAPABILITIES.agentTest,
    WORKSPACE_CAPABILITIES.chatUse,
    WORKSPACE_CAPABILITIES.knowledgeView,
    WORKSPACE_CAPABILITIES.knowledgeEdit,
    WORKSPACE_CAPABILITIES.settingsPersonal,
  ],
}

export const getCapabilitiesByRole = (role?: string) => {
  if (!role)
    return []

  return WORKSPACE_ROLE_CAPABILITIES[role] || []
}

export const getWorkspaceCapabilities = (workspace?: Pick<ICurrentWorkspace, 'role' | 'capabilities'> | null) => {
  if (!workspace)
    return []

  if (workspace.capabilities?.length)
    return [...new Set(workspace.capabilities)]

  return getCapabilitiesByRole(workspace.role)
}

export const hasWorkspaceCapability = (
  workspace: Pick<ICurrentWorkspace, 'role' | 'capabilities'> | null | undefined,
  capability: string,
) => getWorkspaceCapabilities(workspace).includes(capability)

export const hasAnyWorkspaceCapability = (
  workspace: Pick<ICurrentWorkspace, 'role' | 'capabilities'> | null | undefined,
  capabilities: string[],
) => capabilities.some(capability => hasWorkspaceCapability(workspace, capability))

export const hasPluginManageWorkspaceCapability = (
  workspace: Pick<ICurrentWorkspace, 'role' | 'capabilities'> | null | undefined,
) => hasAnyWorkspaceCapability(workspace, [
  WORKSPACE_CAPABILITIES.pluginManage,
  WORKSPACE_CAPABILITIES.agentManage,
])
