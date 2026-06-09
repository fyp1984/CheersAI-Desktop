import type { FileEntity } from '@/app/components/base/file-uploader/types'
import type { FileResponse } from '@/types/workflow'
import { uniqBy } from 'es-toolkit/compat'
import { getProcessedFilesFromResponse } from '@/app/components/base/file-uploader/utils'
import { getOutputFiles } from '@/app/components/workflow/run/output-panel-utils'

export const mergeWorkflowOutputFiles = (
  currentFiles: FileEntity[] | undefined,
  outputs: unknown,
  files: FileResponse[] = [],
) => {
  return uniqBy([
    ...(currentFiles || []),
    ...getOutputFiles(outputs),
    ...getProcessedFilesFromResponse(files),
  ], 'id')
}
