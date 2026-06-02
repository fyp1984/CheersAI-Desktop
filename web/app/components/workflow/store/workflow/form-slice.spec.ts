import { describe, expect, it } from 'vitest'
import { TransferMethod } from '@/types/app'
import { getPersistablePreviewFileInputs } from './form-slice'

describe('getPersistablePreviewFileInputs', () => {
  it('keeps reusable upload references without persisting original file content', () => {
    const originalFile = new File(['private content'], 'document.txt', { type: 'text/plain' })
    const result = getPersistablePreviewFileInputs({
      document: {
        id: 'local-id',
        name: 'document.txt',
        size: originalFile.size,
        type: 'text/plain',
        progress: 100,
        transferMethod: TransferMethod.local_file,
        supportFileType: 'document',
        uploadedId: 'uploaded-id',
        originalFile,
        base64Url: 'data:text/plain;base64,cHJpdmF0ZSBjb250ZW50',
      },
      prompt: 'do not persist text inputs',
    })

    expect(result).toEqual({
      document: {
        id: 'local-id',
        name: 'document.txt',
        size: originalFile.size,
        type: 'text/plain',
        progress: 100,
        transferMethod: TransferMethod.local_file,
        supportFileType: 'document',
        uploadedId: 'uploaded-id',
      },
    })
  })

  it('ignores uploads that are not reusable yet', () => {
    const result = getPersistablePreviewFileInputs({
      documents: [{
        id: 'pending-id',
        name: 'pending.txt',
        size: 1,
        type: 'text/plain',
        progress: 40,
        transferMethod: TransferMethod.local_file,
        supportFileType: 'document',
      }],
    })

    expect(result).toEqual({})
  })
})
