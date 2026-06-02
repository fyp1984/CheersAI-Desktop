import type { StateCreator } from 'zustand'
import type { FileEntity } from '@/app/components/base/file-uploader/types'
import type {
  RunFile,
} from '@/app/components/workflow/types'

type FormInputValue = string | number | boolean | object

const PREVIEW_FILE_INPUTS_STORAGE_PREFIX = 'workflow-preview-file-inputs:'

const getPreviewFileInputsStorageKey = () => {
  if (typeof globalThis.location === 'undefined')
    return ''

  return `${PREVIEW_FILE_INPUTS_STORAGE_PREFIX}${globalThis.location.pathname}`
}

const isFileEntity = (value: unknown): value is FileEntity => {
  if (!value || typeof value !== 'object')
    return false

  const file = value as Partial<FileEntity>
  return typeof file.id === 'string'
    && typeof file.name === 'string'
    && typeof file.size === 'number'
    && typeof file.type === 'string'
    && typeof file.progress === 'number'
    && typeof file.transferMethod === 'string'
}

const getPersistableFile = (file: FileEntity) => {
  if (!file.uploadedId && !file.url)
    return

  const {
    originalFile: _originalFile,
    base64Url: _base64Url,
    ...persistableFile
  } = file

  return persistableFile
}

export const getPersistablePreviewFileInputs = (inputs: Record<string, FormInputValue>) => {
  return Object.entries(inputs).reduce<Record<string, FileEntity | FileEntity[]>>((result, [variable, value]) => {
    if (isFileEntity(value)) {
      const persistableFile = getPersistableFile(value)
      if (persistableFile)
        result[variable] = persistableFile
      return result
    }

    if (Array.isArray(value) && value.every(isFileEntity)) {
      const persistableFiles = value
        .map(getPersistableFile)
        .filter((file): file is FileEntity => !!file)
      if (persistableFiles.length)
        result[variable] = persistableFiles
    }

    return result
  }, {})
}

const restorePreviewFileInputs = () => {
  const storageKey = getPreviewFileInputsStorageKey()
  if (!storageKey || typeof globalThis.sessionStorage === 'undefined')
    return {}

  try {
    const storedInputs = globalThis.sessionStorage.getItem(storageKey)
    return storedInputs ? JSON.parse(storedInputs) as Record<string, FileEntity | FileEntity[]> : {}
  }
  catch {
    globalThis.sessionStorage.removeItem(storageKey)
    return {}
  }
}

const persistPreviewFileInputs = (inputs: Record<string, FormInputValue>) => {
  const storageKey = getPreviewFileInputsStorageKey()
  if (!storageKey || typeof globalThis.sessionStorage === 'undefined')
    return

  const fileInputs = getPersistablePreviewFileInputs(inputs)
  if (Object.keys(fileInputs).length)
    globalThis.sessionStorage.setItem(storageKey, JSON.stringify(fileInputs))
  else
    globalThis.sessionStorage.removeItem(storageKey)
}

export type FormSliceShape = {
  inputs: Record<string, FormInputValue>
  setInputs: (inputs: Record<string, FormInputValue>) => void
  files: RunFile[]
  setFiles: (files: RunFile[]) => void
}

export const createFormSlice: StateCreator<FormSliceShape> = set => ({
  inputs: restorePreviewFileInputs(),
  setInputs: (inputs) => {
    persistPreviewFileInputs(inputs)
    set(() => ({ inputs }))
  },
  files: [],
  setFiles: files => set(() => ({ files })),
})
