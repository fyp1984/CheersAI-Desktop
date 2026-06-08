import { describe, expect, it } from 'vitest'
import { TransferMethod } from '@/types/app'
import { downloadOutputToolFiles, downloadResponseToolFiles, getOutputFiles } from './output-panel-utils'

describe('getOutputFiles', () => {
  it('extracts downloadable tool files from multi-field outputs', () => {
    const result = getOutputFiles({
      text: 'HTML document generated',
      files: [{
        dify_model_identity: '__dify__file__',
        type: 'document',
        transfer_method: 'tool_file',
        related_id: 'tool-file-id',
        filename: 'document.html',
        mime_type: 'text/html',
        size: 4320,
        url: '/files/tools/tool-file-id.html?sign=signed',
      }],
      json: [{ data: [] }],
    })

    expect(result).toEqual([{
      id: 'tool-file-id',
      name: 'document.html',
      size: 4320,
      type: 'text/html',
      progress: 100,
      transferMethod: 'tool_file',
      supportFileType: 'document',
      uploadedId: 'tool-file-id',
      url: '/files/tools/tool-file-id.html?sign=signed',
    }])
  })

  it('still extracts a single local file output', () => {
    const result = getOutputFiles({
      file: {
        dify_model_identity: '__dify__file__',
        type: 'document',
        transfer_method: TransferMethod.local_file,
        related_id: 'local-file-id',
        filename: 'notes.txt',
        mime_type: 'text/plain',
        size: 12,
        url: '/files/local-file-id',
      },
    })

    expect(result).toHaveLength(1)
    expect(result[0].name).toBe('notes.txt')
  })

  it('automatically downloads generated tool files as attachments', () => {
    const downloads: Array<{ url: string, fileName?: string }> = []
    const count = downloadOutputToolFiles({
      files: [{
        dify_model_identity: '__dify__file__',
        type: 'document',
        transfer_method: 'tool_file',
        related_id: 'tool-file-id',
        filename: 'document.html',
        mime_type: 'text/html',
        size: 4320,
        url: '/files/tools/tool-file-id.html?sign=signed',
      }],
    }, options => downloads.push(options))

    expect(count).toBe(1)
    expect(downloads).toEqual([{
      url: '/files/tools/tool-file-id.html?sign=signed&as_attachment=true',
      fileName: 'document.html',
    }])
  })

  it('downloads the same generated tool file only once', () => {
    const downloads: Array<{ url: string, fileName?: string }> = []
    const outputs = {
      files: [{
        dify_model_identity: '__dify__file__',
        type: 'document',
        transfer_method: 'tool_file',
        related_id: 'deduplicated-tool-file-id',
        filename: 'deduplicated.html',
        mime_type: 'text/html',
        size: 4320,
        url: '/files/tools/deduplicated-tool-file-id.html?sign=signed',
      }],
    }

    downloadOutputToolFiles(outputs, options => downloads.push(options))
    downloadOutputToolFiles(outputs, options => downloads.push(options))

    expect(downloads).toHaveLength(1)
  })

  it('downloads tool files from streamed file events', () => {
    const downloads: Array<{ url: string, fileName?: string }> = []
    const count = downloadResponseToolFiles([{
      id: 'streamed-tool-file-id',
      type: 'document',
      transfer_method: 'tool_file' as TransferMethod,
      filename: 'export.docx',
      mime_type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      size: 2048,
      url: '/files/tools/streamed-tool-file-id.docx?sign=signed',
      upload_file_id: 'streamed-tool-file-id',
    }], options => downloads.push(options))

    expect(count).toBe(1)
    expect(downloads).toEqual([{
      url: '/files/tools/streamed-tool-file-id.docx?sign=signed&as_attachment=true',
      fileName: 'export.docx',
    }])
  })
})
