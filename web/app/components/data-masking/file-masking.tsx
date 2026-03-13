'use client'

import { useState, useRef, useCallback } from 'react'
import {
  DocumentIcon,
  EyeIcon,
  CheckCircleIcon,
  MagnifyingGlassIcon,
  PlusIcon,
  XMarkIcon,
  ArrowUpTrayIcon,
  DocumentTextIcon,
  ShieldCheckIcon,
  ClockIcon,
} from '@heroicons/react/24/outline'
import { saveSandboxFile, scanEntities, extractTextFromFile } from '@/service/sandbox-files'
import type { NerEntity } from '@/service/sandbox-files'
import { encrypt, generateKey } from '@/lib/data-masking/crypto-utils'

// Text-based formats readable in browser
const TEXT_EXTENSIONS = new Set(['.md', '.txt', '.csv', '.json', '.xml', '.yaml', '.yml', '.log', '.conf', '.ini', '.toml', '.html', '.htm', '.css', '.js', '.ts', '.py', '.java', '.sql', '.sh', '.bat'])
// Binary formats requiring backend extraction
const BINARY_EXTENSIONS = new Set(['.docx', '.pdf'])
const IMAGE_EXTENSIONS = new Set(['.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.tif', '.webp'])
const ALL_EXTENSIONS = [...TEXT_EXTENSIONS, ...BINARY_EXTENSIONS, ...IMAGE_EXTENSIONS]
const ACCEPT_STRING = ALL_EXTENSIONS.join(',')

interface FileMaskingProps {
  sandboxPath: string
}

interface ConfirmableEntity extends NerEntity {
  checked: boolean
  replacement: string
}

interface ManualReplacement {
  find: string
  replace: string
}

function getMaskedFileName(originalName: string): string {
  const dotIdx = originalName.lastIndexOf('.')
  if (dotIdx === -1) return `${originalName}.masked.txt`
  const ext = originalName.substring(dotIdx)
  const base = originalName.substring(0, dotIdx)
  return `${base}.masked${ext}`
}

function getMappingFileName(originalName: string): string {
  const dotIdx = originalName.lastIndexOf('.')
  const base = dotIdx === -1 ? originalName : originalName.substring(0, dotIdx)
  return `${base}.mapping.json`
}

function getFileExtension(name: string): string {
  const dotIdx = name.lastIndexOf('.')
  return dotIdx === -1 ? '' : name.substring(dotIdx).toLowerCase()
}

function isSupportedFile(name: string): boolean {
  const ext = getFileExtension(name)
  return TEXT_EXTENSIONS.has(ext) || BINARY_EXTENSIONS.has(ext) || IMAGE_EXTENSIONS.has(ext)
}
function isBinaryFile(name: string): boolean {
  const ext = getFileExtension(name)
  return BINARY_EXTENSIONS.has(ext) || IMAGE_EXTENSIONS.has(ext)
}

function escapeRegex(str: string): string {
  return str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
}

function applyEntityMasking(
  content: string,
  entities: ConfirmableEntity[],
  manualReplacements: ManualReplacement[],
): { masked: string; count: number } {
  let masked = content
  let totalCount = 0

  const sortedManual = [...manualReplacements]
    .filter(mr => mr.find.length > 0)
    .sort((a, b) => b.find.length - a.find.length)
  for (const mr of sortedManual) {
    const regex = new RegExp(escapeRegex(mr.find), 'g')
    let matchCount = 0
    masked = masked.replace(regex, () => { matchCount++; return mr.replace })
    totalCount += matchCount
  }

  const sorted = [...entities]
    .filter(e => e.checked)
    .sort((a, b) => b.text.length - a.text.length)
  for (const entity of sorted) {
    const regex = new RegExp(escapeRegex(entity.text), 'g')
    let matchCount = 0
    masked = masked.replace(regex, () => { matchCount++; return entity.replacement })
    totalCount += matchCount
  }
  return { masked, count: totalCount }
}

type Step = 'upload' | 'scanning' | 'confirm' | 'preview' | 'encryption-setup' | 'done'

export function FileMasking({ sandboxPath }: FileMaskingProps) {
  const [step, setStep] = useState<Step>('upload')
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [selectedFiles, setSelectedFiles] = useState<File[]>([])
  const [batchMode, setBatchMode] = useState(false)
  const [currentFileIndex, setCurrentFileIndex] = useState(0)
  const [processedFiles, setProcessedFiles] = useState<string[]>([])
  const [batchProgress, setBatchProgress] = useState(0)
  const [fileContent, setFileContent] = useState('')
  const [entities, setEntities] = useState<ConfirmableEntity[]>([])
  const [manualReplacements, setManualReplacements] = useState<ManualReplacement[]>([])
  const [preview, setPreview] = useState('')
  const [maskedContent, setMaskedContent] = useState('')
  const [matchCount, setMatchCount] = useState(0)
  const [error, setError] = useState('')
  const [dragging, setDragging] = useState(false)
  const [extracting, setExtracting] = useState(false)
  const [extractProgress, setExtractProgress] = useState(0)
  const [needsOcr, setNeedsOcr] = useState(false)
  const [ocrRunning, setOcrRunning] = useState(false)
  const [encryptionKey, setEncryptionKey] = useState('')
  const [showKey, setShowKey] = useState(false)
  const [useCustomKey, setUseCustomKey] = useState(false)
  const [savingFiles, setSavingFiles] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const dropRef = useRef<HTMLDivElement>(null)

  const progressTimerRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const startProgress = useCallback((cap: number, step: number, interval: number) => {
    if (progressTimerRef.current) clearInterval(progressTimerRef.current)
    setExtractProgress(0)
    progressTimerRef.current = setInterval(() => {
      setExtractProgress(prev => {
        if (prev >= cap) return cap
        return prev + step
      })
    }, interval)
  }, [])

  const finishProgress = useCallback((onDone: () => void) => {
    if (progressTimerRef.current) {
      clearInterval(progressTimerRef.current)
      progressTimerRef.current = null
    }
    setExtractProgress(100)
    setTimeout(onDone, 400)
  }, [])

  const processFile = useCallback((file: File) => {
    setError('')
    if (!isSupportedFile(file.name)) {
      setError(`不支持的文件格式。支持: ${ALL_EXTENSIONS.join(', ')}`)
      return
    }
    setSelectedFile(file)
    setStep('upload')
    setEntities([])
    setManualReplacements([])
    setPreview('')
    setMaskedContent('')
    setNeedsOcr(false)

    if (isBinaryFile(file.name)) {
      setFileContent('')
      setExtracting(true)
      startProgress(90, 8, 300)
      extractTextFromFile(file)
        .then((result) => {
          if (result.needs_ocr) {
            if (progressTimerRef.current) { 
              clearInterval(progressTimerRef.current)
              progressTimerRef.current = null 
            }
            setExtractProgress(0)
            setNeedsOcr(true)
            setFileContent('')
            setExtracting(false)
          } else {
            setFileContent(result.content)
            finishProgress(() => setExtracting(false))
          }
        })
        .catch((err) => {
          if (progressTimerRef.current) { 
            clearInterval(progressTimerRef.current)
            progressTimerRef.current = null 
          }
          setExtractProgress(0)
          setError(`文件解析失败: ${err instanceof Error ? err.message : err}`)
          setSelectedFile(null)
          setExtracting(false)
        })
    } else {
      const reader = new FileReader()
      reader.onload = (ev) => { setFileContent(ev.target?.result as string ?? '') }
      reader.onerror = () => setError('读取文件失败')
      reader.readAsText(file)
    }
  }, [startProgress, finishProgress])
  const processBatchFiles = useCallback(async (files: File[]) => {
    setBatchMode(true)
    setSelectedFiles(files)
    setCurrentFileIndex(0)
    setProcessedFiles([])
    setBatchProgress(0)
    setStep('scanning')

    for (let i = 0; i < files.length; i++) {
      const file = files[i]
      setCurrentFileIndex(i)
      setBatchProgress((i / files.length) * 100)

      try {
        let content = ''
        
        if (isBinaryFile(file.name)) {
          const result = await extractTextFromFile(file)
          if (result.needs_ocr) {
            continue
          }
          content = result.content
        } else {
          content = await new Promise<string>((resolve, reject) => {
            const reader = new FileReader()
            reader.onload = (ev) => resolve(ev.target?.result as string ?? '')
            reader.onerror = () => reject(new Error('读取文件失败'))
            reader.readAsText(file)
          })
        }

        const scannedEntities = await scanEntities(content)
        const confirmableEntities: ConfirmableEntity[] = scannedEntities.map(entity => ({
          ...entity,
          checked: true,
          replacement: `[${entity.label}]`
        }))

        const { masked } = applyEntityMasking(content, confirmableEntities, [])
        const key = generateKey()
        const encryptedContent = await encrypt(masked, key)

        const maskedFileName = getMaskedFileName(file.name)
        const mappingFileName = getMappingFileName(file.name)

        const mapping = {
          original_file: file.name,
          masked_file: maskedFileName,
          encryption_key: key,
          entities: confirmableEntities.filter(e => e.checked),
          manual_replacements: [],
          created_at: new Date().toISOString()
        }

        await saveSandboxFile(sandboxPath, maskedFileName, encryptedContent)
        await saveSandboxFile(sandboxPath, mappingFileName, JSON.stringify(mapping, null, 2))

        setProcessedFiles(prev => [...prev, file.name])
      } catch (error) {
        console.error(`处理文件 ${file.name} 失败:`, error)
      }
    }

    setBatchProgress(100)
    setStep('done')
  }, [sandboxPath])
  const handleFileSelect = useCallback((files: FileList | null) => {
    if (!files || files.length === 0) return
    
    const fileArray = Array.from(files)
    const supportedFiles = fileArray.filter(file => isSupportedFile(file.name))
    
    if (supportedFiles.length === 0) {
      setError(`没有支持的文件格式。支持: ${ALL_EXTENSIONS.join(', ')}`)
      return
    }

    if (supportedFiles.length > 1) {
      processBatchFiles(supportedFiles)
    } else {
      processFile(supportedFiles[0])
    }
  }, [processFile, processBatchFiles])

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files
    if (files) handleFileSelect(files)
  }

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setDragging(true)
  }, [])

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setDragging(false)
  }, [])

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setDragging(false)
    const files = e.dataTransfer.files
    if (files) handleFileSelect(files)
  }, [handleFileSelect])

  const handleOcrExtract = useCallback(() => {
    if (!selectedFile) return
    setError('')
    setOcrRunning(true)
    setNeedsOcr(false)
    setExtracting(true)
    startProgress(85, 3, 600)
    extractTextFromFile(selectedFile, 'force')
      .then((result) => {
        setFileContent(result.content)
        finishProgress(() => {
          setExtracting(false)
          setOcrRunning(false)
        })
      })
      .catch((err) => {
        if (progressTimerRef.current) { 
          clearInterval(progressTimerRef.current)
          progressTimerRef.current = null 
        }
        setExtractProgress(0)
        setError(`OCR扫描失败: ${err instanceof Error ? err.message : err}`)
        setExtracting(false)
        setOcrRunning(false)
      })
  }, [selectedFile, startProgress, finishProgress])
  const handleScan = async () => {
    if (!fileContent) return
    setStep('scanning')
    setError('')
    try {
      const result = await scanEntities(fileContent)
      const confirmable: ConfirmableEntity[] = result.map((e, i) => ({
        ...e,
        checked: true,
        replacement: `[${e.label}_${String(i + 1).padStart(3, '0')}]`,
      }))
      setEntities(confirmable)
      setStep('confirm')
    } catch (err) {
      setError(`NER 扫描失败: ${err instanceof Error ? err.message : err}`)
      setStep('upload')
    }
  }

  const handleToggleEntity = (idx: number) => {
    setEntities(prev => prev.map((e, i) => i === idx ? { ...e, checked: !e.checked } : e))
  }

  const handleToggleAll = (checked: boolean) => {
    setEntities(prev => prev.map(e => ({ ...e, checked })))
  }

  const handleReplacementChange = (idx: number, value: string) => {
    setEntities(prev => prev.map((e, i) => i === idx ? { ...e, replacement: value } : e))
  }

  const handleAddManualReplacement = () => {
    setManualReplacements(prev => [...prev, { find: '', replace: '' }])
  }

  const handleRemoveManualReplacement = (idx: number) => {
    setManualReplacements(prev => prev.filter((_, i) => i !== idx))
  }

  const handleManualFindChange = (idx: number, value: string) => {
    setManualReplacements(prev => prev.map((mr, i) => i === idx ? { ...mr, find: value } : mr))
  }

  const handleManualReplaceChange = (idx: number, value: string) => {
    setManualReplacements(prev => prev.map((mr, i) => i === idx ? { ...mr, replace: value } : mr))
  }

  const handlePreview = () => {
    const checkedEntities = entities.filter(e => e.checked)
    const validManual = manualReplacements.filter(mr => mr.find.length > 0)
    if (checkedEntities.length === 0 && validManual.length === 0) {
      setError('请至少选择一个实体或添加一条替换规则')
      return
    }
    const { masked, count } = applyEntityMasking(fileContent, entities, manualReplacements)
    setMaskedContent(masked)
    setMatchCount(count)
    setPreview(masked.length > 3000 ? masked.substring(0, 3000) + '\n\n... (已截断)' : masked)
    setStep('preview')
  }
  const handleExecute = async () => {
    if (!selectedFile || !maskedContent) return
    setError('')
    
    const encryptionEnabled = localStorage.getItem('mapping_encryption_enabled')
    if (encryptionEnabled === 'false') {
      await handleSaveWithoutEncryption()
      return
    }
    
    const globalPassphrase = localStorage.getItem('mapping_encryption_passphrase')
    if (globalPassphrase && globalPassphrase.length >= 32) {
      await handleConfirmEncryptionWithKey(globalPassphrase)
    } else {
      setError('请先在"设置 → 数据安全"页面配置全局加密口令（至少32位字符）')
    }
  }

  const handleSaveWithoutEncryption = async () => {
    if (!selectedFile || !maskedContent) return
    setSavingFiles(true)
    setError('')
    const maskedFileName = getMaskedFileName(selectedFile.name)
    const messages: string[] = []

    const mappingRules: { original: string; replacement: string; label: string; type: string; count: string }[] = []
    for (const e of entities) {
      if (e.checked) {
        mappingRules.push({
          original: e.text,
          replacement: e.replacement,
          label: e.label,
          type: e.type,
          count: e.count,
        })
      }
    }
    for (const mr of manualReplacements) {
      if (mr.find.length > 0) {
        const cnt = fileContent.split(mr.find).length - 1
        mappingRules.push({
          original: mr.find,
          replacement: mr.replace,
          label: '手动替换',
          type: 'manual',
          count: String(cnt),
        })
      }
    }

    const mappingData = {
      version: '1.0',
      source_file: selectedFile.name,
      masked_file: maskedFileName,
      created_at: new Date().toISOString(),
      total_replacements: matchCount,
      rules: mappingRules,
    }
    const mappingJson = JSON.stringify(mappingData, null, 2)
    const mappingFileName = getMappingFileName(selectedFile.name)

    if (sandboxPath) {
      try {
        const result = await saveSandboxFile(sandboxPath, maskedFileName, maskedContent)
        messages.push(`脱敏文件已保存到 ${result.file_path}`)
      } catch (saveErr) {
        messages.push(`脱敏文件保存失败: ${saveErr instanceof Error ? saveErr.message : saveErr}`)
      }
      try {
        await saveSandboxFile(sandboxPath, mappingFileName, mappingJson)
        messages.push(`映射规则已保存（未加密）`)
      } catch (saveErr) {
        messages.push(`映射规则保存失败: ${saveErr instanceof Error ? saveErr.message : saveErr}`)
      }
    }

    setSavingFiles(false)
    const hasError = messages.some(m => m.includes('失败'))
    if (hasError) {
      setError(messages.join('；'))
    } else {
      setStep('done')
    }
  }
  const handleConfirmEncryptionWithKey = async (key: string) => {
    if (!selectedFile || !maskedContent) return

    setSavingFiles(true)
    setError('')
    const maskedFileName = getMaskedFileName(selectedFile.name)
    const messages: string[] = []

    const mappingRules: { original: string; replacement: string; label: string; type: string; count: string }[] = []
    for (const e of entities) {
      if (e.checked) {
        mappingRules.push({
          original: e.text,
          replacement: e.replacement,
          label: e.label,
          type: e.type,
          count: e.count,
        })
      }
    }
    for (const mr of manualReplacements) {
      if (mr.find.length > 0) {
        const cnt = fileContent.split(mr.find).length - 1
        mappingRules.push({
          original: mr.find,
          replacement: mr.replace,
          label: '手动替换',
          type: 'manual',
          count: String(cnt),
        })
      }
    }

    const mappingData = {
      version: '1.0',
      source_file: selectedFile.name,
      masked_file: maskedFileName,
      created_at: new Date().toISOString(),
      total_replacements: matchCount,
      rules: mappingRules,
    }
    const mappingJson = JSON.stringify(mappingData, null, 2)

    let encryptedMappingJson: string
    try {
      encryptedMappingJson = await encrypt(mappingJson, key)
    } catch (encErr) {
      setSavingFiles(false)
      setError(`加密失败: ${encErr instanceof Error ? encErr.message : encErr}`)
      return
    }

    const encryptedMappingData = {
      version: '1.0',
      encrypted: true,
      data: encryptedMappingJson,
    }
    const encryptedMappingJsonStr = JSON.stringify(encryptedMappingData, null, 2)
    const mappingFileName = getMappingFileName(selectedFile.name)

    if (sandboxPath) {
      try {
        const result = await saveSandboxFile(sandboxPath, maskedFileName, maskedContent)
        messages.push(`脱敏文件已保存到 ${result.file_path}`)
      } catch (saveErr) {
        messages.push(`脱敏文件保存失败: ${saveErr instanceof Error ? saveErr.message : saveErr}`)
      }
      try {
        await saveSandboxFile(sandboxPath, mappingFileName, encryptedMappingJsonStr)
        messages.push(`加密映射规则已保存`)
      } catch (saveErr) {
        messages.push(`映射规则保存失败: ${saveErr instanceof Error ? saveErr.message : saveErr}`)
      }
    }

    setSavingFiles(false)
    const hasError = messages.some(m => m.includes('失败'))
    if (hasError) {
      setError(messages.join('；'))
    } else {
      setStep('done')
    }
  }
  const handleReset = () => {
    setSelectedFile(null)
    setSelectedFiles([])
    setBatchMode(false)
    setCurrentFileIndex(0)
    setProcessedFiles([])
    setBatchProgress(0)
    setFileContent('')
    setEntities([])
    setManualReplacements([])
    setPreview('')
    setMaskedContent('')
    setMatchCount(0)
    setStep('upload')
    setError('')
    setExtracting(false)
    setExtractProgress(0)
    setNeedsOcr(false)
    setOcrRunning(false)
    setEncryptionKey('')
    setShowKey(false)
    setUseCustomKey(false)
    setSavingFiles(false)
  }

  // Done state
  if (step === 'done') {
    return (
      <div className="text-center py-16">
        <CheckCircleIcon className="mx-auto h-14 w-14 text-text-success" />
        <h3 className="mt-3 text-base font-medium text-text-primary">
          {batchMode ? '批量脱敏完成' : '脱敏完成'}
        </h3>
        {batchMode ? (
          <div className="mt-2 space-y-1">
            <p className="text-sm text-text-tertiary">成功处理 {processedFiles.length} 个文件</p>
            <p className="text-xs text-text-quaternary">
              所有脱敏文件已保存到沙箱: {sandboxPath}
            </p>
            {processedFiles.length > 0 && (
              <div className="mt-4 max-w-md mx-auto">
                <p className="text-xs font-medium text-text-secondary mb-2">处理完成的文件:</p>
                <div className="max-h-32 overflow-y-auto space-y-1 text-xs text-text-tertiary">
                  {processedFiles.map((fileName, index) => (
                    <div key={index} className="flex items-center gap-2">
                      <CheckCircleIcon className="w-3 h-3 text-green-500" />
                      <span>{fileName}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        ) : (
          <div className="mt-2 space-y-1">
            <p className="text-sm text-text-tertiary">已替换 {matchCount} 处敏感数据</p>
            <p className="text-xs text-text-quaternary">
              文件: {selectedFile ? getMaskedFileName(selectedFile.name) : ''} → {sandboxPath}
            </p>
            <p className="text-xs text-text-quaternary">
              映射规则: {selectedFile ? getMappingFileName(selectedFile.name) : ''} (可用于反脱敏还原)
            </p>
          </div>
        )}
        <div className="mt-6 flex items-center justify-center gap-3">
          <button onClick={handleReset}
            className="inline-flex items-center px-4 py-2 text-sm font-medium text-components-button-primary-text bg-components-button-primary-bg rounded-lg hover:bg-components-button-primary-bg-hover">
            继续脱敏其他文件
          </button>
        </div>
      </div>
    )
  }
  const checkedCount = entities.filter(e => e.checked).length
  const validManualCount = manualReplacements.filter(mr => mr.find.length > 0).length

  const grouped: Record<string, ConfirmableEntity[]> = {}
  entities.forEach((e) => {
    const key = e.label
    if (!grouped[key]) grouped[key] = []
    grouped[key].push({ ...e })
  })

  return (
    <div className="space-y-6">
      {error && (
        <div className="text-sm text-text-destructive bg-state-destructive-hover px-4 py-3 rounded-lg">{error}</div>
      )}

      {/* Stats cards - show when no file selected */}
      {step === 'upload' && !selectedFile && (
        <div className="grid grid-cols-3 gap-4 mb-2">
          <div className="bg-components-panel-bg rounded-xl border border-divider-regular p-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-state-accent-hover flex items-center justify-center">
                <DocumentTextIcon className="w-5 h-5 text-text-accent" />
              </div>
              <div>
                <p className="text-xs text-text-tertiary">支持格式</p>
                <p className="text-sm font-medium text-text-primary">MD / TXT / Word / PDF / 图片 等</p>
              </div>
            </div>
          </div>
          <div className="bg-components-panel-bg rounded-xl border border-divider-regular p-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-state-success-hover flex items-center justify-center">
                <ShieldCheckIcon className="w-5 h-5 text-text-success" />
              </div>
              <div>
                <p className="text-xs text-text-tertiary">脱敏方式</p>
                <p className="text-sm font-medium text-text-primary">NER + 手动替换</p>
              </div>
            </div>
          </div>
          <div className="bg-components-panel-bg rounded-xl border border-divider-regular p-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-state-accent-hover flex items-center justify-center">
                <ClockIcon className="w-5 h-5 text-text-accent" />
              </div>
              <div>
                <p className="text-xs text-text-tertiary">处理方式</p>
                <p className="text-sm font-medium text-text-primary">本地处理，不上传</p>
              </div>
            </div>
          </div>
        </div>
      )}
      {/* Drag & drop upload area */}
      {step === 'upload' && (
        <div
          ref={dropRef}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
          className={`relative cursor-pointer rounded-xl border-2 border-dashed transition-all ${
            dragging
              ? 'border-state-accent-solid bg-state-accent-hover'
              : selectedFile
                ? 'border-state-success-solid bg-state-success-hover'
                : 'border-divider-regular bg-components-panel-bg hover:border-divider-deep hover:bg-state-base-hover'
          } ${selectedFile ? 'p-5' : 'p-10'}`}
        >
          <input
            ref={fileInputRef}
            type="file"
            multiple
            accept={ACCEPT_STRING}
            onChange={handleFileInputChange}
            className="hidden"
          />
          {batchMode ? (
            <div className="space-y-4" onClick={e => e.stopPropagation()}>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-lg bg-blue-100 flex items-center justify-center">
                    <DocumentIcon className="h-5 w-5 text-blue-600" />
                  </div>
                  <div>
                    <p className="text-sm font-medium text-text-primary">批量处理模式</p>
                    <p className="text-xs text-text-tertiary">
                      共 {selectedFiles.length} 个文件 • 已处理 {processedFiles.length} 个
                    </p>
                  </div>
                </div>
                <button
                  type="button"
                  onClick={() => handleReset()}
                  className="text-xs text-text-tertiary hover:text-text-secondary px-2 py-1 rounded hover:bg-state-base-hover"
                >
                  重新选择
                </button>
              </div>
              
              <div className="space-y-2">
                <div className="flex items-center justify-between text-xs">
                  <span className="text-text-tertiary">处理进度</span>
                  <span className="text-text-secondary">{Math.round(batchProgress)}%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div 
                    className="bg-blue-500 h-2 rounded-full transition-all duration-300"
                    style={{ width: `${batchProgress}%` }}
                  />
                </div>
              </div>

              {currentFileIndex < selectedFiles.length && (
                <div className="text-xs text-text-tertiary">
                  正在处理: {selectedFiles[currentFileIndex]?.name}
                </div>
              )}

              {processedFiles.length > 0 && (
                <div className="space-y-1">
                  <p className="text-xs font-medium text-text-secondary">已完成:</p>
                  <div className="max-h-32 overflow-y-auto space-y-1">
                    {processedFiles.map((fileName, index) => (
                      <div key={index} className="flex items-center gap-2 text-xs text-text-tertiary">
                        <CheckCircleIcon className="w-3 h-3 text-green-500" />
                        <span>{fileName}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ) : selectedFile ? (
            <div className="space-y-3" onClick={e => e.stopPropagation()}>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-lg bg-state-success-hover flex items-center justify-center">
                    <DocumentIcon className="h-5 w-5 text-text-success" />
                  </div>
                  <div>
                    <p className="text-sm font-medium text-text-primary">{selectedFile.name}</p>
                    <p className="text-xs text-text-tertiary">
                      {(selectedFile.size / 1024).toFixed(1)} KB • {getFileExtension(selectedFile.name).toUpperCase()}
                    </p>
                  </div>
                </div>
                <button
                  type="button"
                  onClick={() => setSelectedFile(null)}
                  className="text-text-tertiary hover:text-text-secondary"
                >
                  <XMarkIcon className="w-4 h-4" />
                </button>
              </div>
            </div>
          ) : (
            <div className="text-center">
              <ArrowUpTrayIcon className="mx-auto h-12 w-12 text-text-tertiary" />
              <h3 className="mt-2 text-sm font-medium text-text-primary">选择文件进行脱敏</h3>
              <p className="mt-1 text-sm text-text-tertiary">
                拖拽文件到此处，或点击选择文件
              </p>
              <p className="mt-2 text-xs text-text-quaternary">
                支持: {ALL_EXTENSIONS.slice(0, 8).join(', ')} 等格式
              </p>
            </div>
          )}
        </div>
      )}
      {step === 'scanning' && !batchMode && (
        <div className="text-center py-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-text-accent mx-auto"></div>
          <p className="mt-2 text-sm text-text-secondary">正在扫描敏感信息...</p>
        </div>
      )}

      {step === 'confirm' && (
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-medium text-text-primary">确认脱敏规则</h3>
            <div className="flex items-center gap-2">
              <span className="text-sm text-text-tertiary">
                已选择 {checkedCount} 个实体，{validManualCount} 条手动规则
              </span>
            </div>
          </div>

          {Object.keys(grouped).length > 0 && (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h4 className="text-sm font-medium text-text-secondary">检测到的敏感信息</h4>
                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={() => handleToggleAll(true)}
                    className="text-xs text-text-accent hover:underline"
                  >
                    全选
                  </button>
                  <button
                    type="button"
                    onClick={() => handleToggleAll(false)}
                    className="text-xs text-text-accent hover:underline"
                  >
                    全不选
                  </button>
                </div>
              </div>

              {Object.entries(grouped).map(([label, groupEntities]) => (
                <div key={label} className="border border-divider-regular rounded-lg p-4">
                  <h5 className="text-sm font-medium text-text-primary mb-3">{label}</h5>
                  <div className="space-y-2">
                    {groupEntities.map((entity, idx) => {
                      const globalIdx = entities.findIndex(e => e === entity)
                      return (
                        <div key={globalIdx} className="flex items-center gap-3">
                          <input
                            type="checkbox"
                            checked={entity.checked}
                            onChange={() => handleToggleEntity(globalIdx)}
                            className="rounded border-divider-regular"
                          />
                          <span className="text-sm text-text-primary font-mono bg-state-base-hover px-2 py-1 rounded">
                            {entity.text}
                          </span>
                          <span className="text-xs text-text-tertiary">→</span>
                          <input
                            type="text"
                            value={entity.replacement}
                            onChange={(e) => handleReplacementChange(globalIdx, e.target.value)}
                            className="text-sm border border-divider-regular bg-components-input-bg-normal rounded px-2 py-1 text-text-primary"
                          />
                          <span className="text-xs text-text-quaternary">
                            ({entity.count} 处)
                          </span>
                        </div>
                      )
                    })}
                  </div>
                </div>
              ))}
            </div>
          )}
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h4 className="text-sm font-medium text-text-secondary">手动替换规则</h4>
              <button
                type="button"
                onClick={handleAddManualReplacement}
                className="flex items-center gap-1 text-xs text-text-accent hover:underline"
              >
                <PlusIcon className="w-3 h-3" />
                添加规则
              </button>
            </div>

            {manualReplacements.map((mr, idx) => (
              <div key={idx} className="flex items-center gap-3">
                <input
                  type="text"
                  value={mr.find}
                  onChange={(e) => handleManualFindChange(idx, e.target.value)}
                  placeholder="查找文本"
                  className="flex-1 text-sm border border-divider-regular bg-components-input-bg-normal rounded px-3 py-2 text-text-primary"
                />
                <span className="text-xs text-text-tertiary">→</span>
                <input
                  type="text"
                  value={mr.replace}
                  onChange={(e) => handleManualReplaceChange(idx, e.target.value)}
                  placeholder="替换为"
                  className="flex-1 text-sm border border-divider-regular bg-components-input-bg-normal rounded px-3 py-2 text-text-primary"
                />
                <button
                  type="button"
                  onClick={() => handleRemoveManualReplacement(idx)}
                  className="text-text-tertiary hover:text-text-destructive"
                >
                  <XMarkIcon className="w-4 h-4" />
                </button>
              </div>
            ))}
          </div>

          <div className="flex gap-3 pt-4 border-t border-divider-regular">
            <button
              type="button"
              onClick={() => setStep('upload')}
              className="px-4 py-2 text-sm font-medium text-components-button-secondary-text bg-components-button-secondary-bg border border-components-button-secondary-border rounded-lg hover:bg-components-button-secondary-bg-hover"
            >
              重新选择文件
            </button>
            <button
              type="button"
              onClick={handlePreview}
              className="px-4 py-2 text-sm font-medium text-components-button-primary-text bg-components-button-primary-bg rounded-lg hover:bg-components-button-primary-bg-hover"
            >
              预览脱敏效果
            </button>
          </div>
        </div>
      )}
      {step === 'preview' && (
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-medium text-text-primary">脱敏预览</h3>
            <div className="text-sm text-text-tertiary">
              将替换 {matchCount} 处敏感数据
            </div>
          </div>

          <div className="border border-divider-regular rounded-lg">
            <div className="bg-components-panel-bg px-4 py-2 border-b border-divider-regular">
              <h4 className="text-sm font-medium text-text-secondary">脱敏后内容预览</h4>
            </div>
            <div className="p-4">
              <pre className="text-sm text-text-primary whitespace-pre-wrap font-mono bg-state-base-hover p-3 rounded max-h-96 overflow-y-auto">
                {preview}
              </pre>
            </div>
          </div>

          <div className="flex gap-3 pt-4 border-t border-divider-regular">
            <button
              type="button"
              onClick={() => setStep('confirm')}
              className="px-4 py-2 text-sm font-medium text-components-button-secondary-text bg-components-button-secondary-bg border border-components-button-secondary-border rounded-lg hover:bg-components-button-secondary-bg-hover"
            >
              修改规则
            </button>
            <button
              type="button"
              onClick={handleExecute}
              className="px-4 py-2 text-sm font-medium text-components-button-primary-text bg-components-button-primary-bg rounded-lg hover:bg-components-button-primary-bg-hover"
            >
              执行脱敏
            </button>
          </div>
        </div>
      )}

      {extracting && (
        <div className="text-center py-8">
          <div className="space-y-4">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-text-accent mx-auto"></div>
            <div className="space-y-2">
              <p className="text-sm text-text-secondary">
                {needsOcr ? '正在进行OCR文字识别...' : '正在解析文件内容...'}
              </p>
              <div className="w-64 mx-auto bg-gray-200 rounded-full h-2">
                <div 
                  className="bg-text-accent h-2 rounded-full transition-all duration-300"
                  style={{ width: `${extractProgress}%` }}
                />
              </div>
              <p className="text-xs text-text-tertiary">{extractProgress}%</p>
            </div>
          </div>
        </div>
      )}
      {needsOcr && !extracting && (
        <div className="text-center py-8 space-y-4">
          <div className="w-12 h-12 rounded-full bg-state-warning-hover flex items-center justify-center mx-auto">
            <EyeIcon className="w-6 h-6 text-text-warning" />
          </div>
          <div className="space-y-2">
            <h3 className="text-base font-medium text-text-primary">需要OCR识别</h3>
            <p className="text-sm text-text-tertiary">
              该文件包含图像内容，需要进行OCR文字识别才能提取文本
            </p>
          </div>
          <div className="flex gap-3 justify-center">
            <button
              type="button"
              onClick={() => setSelectedFile(null)}
              className="px-4 py-2 text-sm font-medium text-components-button-secondary-text bg-components-button-secondary-bg border border-components-button-secondary-border rounded-lg hover:bg-components-button-secondary-bg-hover"
            >
              重新选择
            </button>
            <button
              type="button"
              onClick={handleOcrExtract}
              disabled={ocrRunning}
              className="px-4 py-2 text-sm font-medium text-components-button-primary-text bg-components-button-primary-bg rounded-lg hover:bg-components-button-primary-bg-hover disabled:opacity-50"
            >
              {ocrRunning ? '识别中...' : '开始OCR识别'}
            </button>
          </div>
        </div>
      )}

      {selectedFile && fileContent && step === 'upload' && !extracting && !needsOcr && (
        <div className="flex gap-3 justify-center pt-4">
          <button
            type="button"
            onClick={() => setSelectedFile(null)}
            className="px-4 py-2 text-sm font-medium text-components-button-secondary-text bg-components-button-secondary-bg border border-components-button-secondary-border rounded-lg hover:bg-components-button-secondary-bg-hover"
          >
            重新选择
          </button>
          <button
            type="button"
            onClick={handleScan}
            className="px-4 py-2 text-sm font-medium text-components-button-primary-text bg-components-button-primary-bg rounded-lg hover:bg-components-button-primary-bg-hover"
          >
            <MagnifyingGlassIcon className="w-4 h-4 inline mr-2" />
            扫描敏感信息
          </button>
        </div>
      )}
    </div>
  )
}