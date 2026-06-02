import { getProcessedFilesFromResponse } from '@/app/components/base/file-uploader/utils'
import { downloadUrl } from '@/utils/download'

const downloadedToolFileUrls = new Set<string>()

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

  toolFiles.forEach((file) => {
    downloadedToolFileUrls.add(file.url!)
    if (downloadedToolFileUrls.size > 1000)
      downloadedToolFileUrls.clear()

    const separator = file.url!.includes('?') ? '&' : '?'
    download({
      url: `${file.url}${separator}as_attachment=true`,
      fileName: file.name,
    })
  })

  return toolFiles.length
}
