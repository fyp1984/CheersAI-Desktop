/**
 * Gitea file service for retrieving files from Gitea repository
 */
import { del, get, post } from './base'

export type GiteaFileMetadata = {
  name: string
  path: string
  size: number
  sha: string
  url: string
  type: string
}

export type GiteaFileListResponse = {
  files: GiteaFileMetadata[]
}

/**
 * Get file metadata from Gitea
 */
export const getGiteaFileMetadata = (filePath: string) => {
  return get<GiteaFileMetadata>(`/gitea/files/${filePath}/metadata`)
}

/**
 * Get file download URL from Gitea
 */
export const getGiteaFileUrl = (filePath: string) => {
  return get<{ url: string; path: string }>(`/gitea/files/${filePath}/url`)
}

/**
 * List files in Gitea repository directory
 */
export const listGiteaFiles = (directoryPath: string = '') => {
  return get<GiteaFileListResponse>('/gitea/files', {
    params: { path: directoryPath },
  })
}

/**
 * Download file from Gitea
 */
export const downloadGiteaFile = async (filePath: string): Promise<Blob> => {
  const response = await fetch(`/console/api/gitea/files/${filePath}`, {
    method: 'GET',
    credentials: 'include',
  })

  if (!response.ok) {
    throw new Error(`Failed to download file: ${response.statusText}`)
  }

  return response.blob()
}

/**
 * Get file content as text from Gitea
 */
export const getGiteaFileContent = async (filePath: string): Promise<string> => {
  const blob = await downloadGiteaFile(filePath)
  return blob.text()
}

/**
 * Get file content as data URL from Gitea (useful for images)
 */
export const getGiteaFileDataUrl = async (filePath: string): Promise<string> => {
  const blob = await downloadGiteaFile(filePath)
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onloadend = () => resolve(reader.result as string)
    reader.onerror = reject
    reader.readAsDataURL(blob)
  })
}
