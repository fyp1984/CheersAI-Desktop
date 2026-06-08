import type { FileEntity } from '@/app/components/base/file-uploader/types'
import type { FileResponse } from '@/types/workflow'
import { getProcessedFilesFromResponse } from '@/app/components/base/file-uploader/utils'
import { downloadUrl } from '@/utils/download'

const downloadedToolFileUrls = new Set<string>()

export const downloadToolFile = (
  file: Pick<FileEntity, 'transferMethod' | 'url' | 'name'>,
  download: typeof downloadUrl = downloadUrl,
) => {
  if ((file.transferMethod as string) !== 'tool_file' || !file.url || downloadedToolFileUrls.has(file.url))
    return false

  downloadedToolFileUrls.add(file.url)
  if (downloadedToolFileUrls.size > 1000)
    downloadedToolFileUrls.clear()

  const separator = file.url.includes('?') ? '&' : '?'
  download({
    url: `${file.url}${separator}as_attachment=true`,
    fileName: file.name,
  })

  return true
}

export const downloadResponseToolFiles = (
  files: Array<Partial<FileResponse> & { id?: string }>,
  download: typeof downloadUrl = downloadUrl,
) => {
  const processedFiles = getProcessedFilesFromResponse(files.map(file => ({
    ...file,
    related_id: file.related_id || file.id || file.upload_file_id || '',
  })) as FileResponse[])

  return processedFiles.reduce((count, file) => count + (downloadToolFile(file, download) ? 1 : 0), 0)
}

export const getOutputFiles = (outputs: unknown) => {
  if (!outputs || typeof outputs !== 'object')
    return []

  const fileList = Object.values(outputs).flatMap((output) => {
    if (Array.isArray(output))
      return output.filter(item => item?.dify_model_identity === '__dify__file__')

    if ((output as { dify_model_identity?: string })?.dify_model_identity === '__dify__file__')
      return [output]

    return []
  })

  return getProcessedFilesFromResponse(fileList)
}

export const downloadOutputToolFiles = (
  outputs: unknown,
  download: typeof downloadUrl = downloadUrl,
) => {
  const toolFiles = getOutputFiles(outputs).filter(file =>
    (file.transferMethod as string) === 'tool_file'
    && file.url
    && !downloadedToolFileUrls.has(file.url),
  )

  toolFiles.forEach(file => downloadToolFile(file, download))

  return toolFiles.length
}
