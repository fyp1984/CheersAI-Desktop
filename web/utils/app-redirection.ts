import { AppModeEnum } from '@/types/app'

type WorkspaceAppCapabilities = {
  canEditApp: boolean
  canViewWorkflow: boolean
  canEditWorkflow: boolean
}

const normalizeWorkspaceCapabilities = (
  workspaceCapabilities: WorkspaceAppCapabilities | boolean,
): WorkspaceAppCapabilities => {
  if (typeof workspaceCapabilities === 'boolean') {
    return {
      canEditApp: workspaceCapabilities,
      canViewWorkflow: workspaceCapabilities,
      canEditWorkflow: workspaceCapabilities,
    }
  }

  return workspaceCapabilities
}

export const getRedirectionPath = (
  workspaceCapabilities: WorkspaceAppCapabilities | boolean,
  app: { id: string, mode: AppModeEnum },
) => {
  const normalizedCapabilities = normalizeWorkspaceCapabilities(workspaceCapabilities)
  const isWorkflowApp = app.mode === AppModeEnum.WORKFLOW || app.mode === AppModeEnum.ADVANCED_CHAT

  if (isWorkflowApp) {
    if (normalizedCapabilities.canEditWorkflow)
      return `/app/${app.id}/workflow`

    return `/app/${app.id}/overview`
  }

  if (!normalizedCapabilities.canEditApp)
    return `/app/${app.id}/overview`

  return `/app/${app.id}/configuration`
}

export const getRedirection = (
  workspaceCapabilities: WorkspaceAppCapabilities | boolean,
  app: { id: string, mode: AppModeEnum },
  redirectionFunc: (href: string) => void,
) => {
  const redirectionPath = getRedirectionPath(workspaceCapabilities, app)
  redirectionFunc(redirectionPath)
}
