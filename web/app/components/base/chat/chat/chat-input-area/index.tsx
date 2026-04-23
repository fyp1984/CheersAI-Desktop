import type { Theme } from '../../embedded-chatbot/theme/theme-context'
import type {
  EnableType,
  OnSend,
} from '../../types'
import type { InputForm } from '../type'
import type { FileUpload } from '@/app/components/base/features/types'
import { noop } from 'es-toolkit/function'
import { decode } from 'html-entities'
import Recorder from 'js-audio-recorder'
import {
  useCallback,
  useRef,
  useState,
} from 'react'
import { useTranslation } from 'react-i18next'
import Textarea from 'react-textarea-autosize'
import FeatureBar from '@/app/components/base/features/new-feature-panel/feature-bar'
import { FileListInChatInput } from '@/app/components/base/file-uploader'
import { useFile } from '@/app/components/base/file-uploader/hooks'
import {
  FileContextProvider,
  useFileStore,
} from '@/app/components/base/file-uploader/store'
import { useToastContext } from '@/app/components/base/toast'
import VoiceInput from '@/app/components/base/voice-input'
import Checkbox from '@/app/components/base/checkbox'
import { TransferMethod } from '@/types/app'
import { cn } from '@/utils/classnames'
import { useCheckInputsForms } from '../check-input-forms-hooks'
import { useTextAreaHeight } from './hooks'
import Operation from './operation'

const SENSITIVE_SEND_WARNING_KEY = 'sensitive_send_warning'

type ChatInputAreaProps = {
  readonly?: boolean
  botName?: string
  showFeatureBar?: boolean
  showFileUpload?: boolean
  featureBarDisabled?: boolean
  onFeatureBarClick?: (state: boolean) => void
  visionConfig?: FileUpload
  speechToTextConfig?: EnableType
  onSend?: OnSend
  inputs?: Record<string, any>
  inputsForm?: InputForm[]
  theme?: Theme | null
  isResponding?: boolean
  disabled?: boolean
}
const ChatInputArea = ({
  readonly,
  botName,
  showFeatureBar,
  showFileUpload,
  featureBarDisabled,
  onFeatureBarClick,
  visionConfig,
  speechToTextConfig = { enabled: true },
  onSend,
  inputs = {},
  inputsForm = [],
  theme,
  isResponding,
  disabled,
}: ChatInputAreaProps) => {
  const { t } = useTranslation()
  const { notify } = useToastContext()
  const {
    wrapperRef,
    textareaRef,
    textValueRef,
    holdSpaceRef,
    handleTextareaResize,
    isMultipleLine,
  } = useTextAreaHeight()
  const [query, setQuery] = useState('')
  const [showVoiceInput, setShowVoiceInput] = useState(false)
  const filesStore = useFileStore()
  const {
    handleDragFileEnter,
    handleDragFileLeave,
    handleDragFileOver,
    handleDropFile,
    handleClipboardPasteFile,
    isDragActive,
  } = useFile(visionConfig!, false)
  const { checkInputsForm } = useCheckInputsForms()
  const historyRef = useRef([''])
  const [currentIndex, setCurrentIndex] = useState(-1)
  const isComposingRef = useRef(false)
  const [showSensitiveConfirm, setShowSensitiveConfirm] = useState(false)
  const [skipSensitiveConfirm, setSkipSensitiveConfirm] = useState(false)
  const pendingSendRef = useRef(false)

  const handleQueryChange = useCallback(
    (value: string) => {
      setQuery(value)
      setTimeout(handleTextareaResize, 0)
    },
    [handleTextareaResize],
  )

  const doActualSend = useCallback(() => {
    if (onSend) {
      const { files, setFiles } = filesStore.getState()
      if (files.find(item => item.transferMethod === TransferMethod.local_file && !item.uploadedId)) {
        notify({ type: 'info', message: t('errorMessage.waitForFileUpload', { ns: 'appDebug' }) })
        return
      }
      if (!query || !query.trim()) {
        notify({ type: 'info', message: t('errorMessage.queryRequired', { ns: 'appAnnotation' }) })
        return
      }
      if (checkInputsForm(inputs, inputsForm)) {
        onSend(query, files)
        handleQueryChange('')
        setFiles([])
      }
    }
  }, [onSend, filesStore, query, notify, t, checkInputsForm, inputs, inputsForm, handleQueryChange])

  const handleSend = () => {
    if (isResponding) {
      notify({ type: 'info', message: t('errorMessage.waitForResponse', { ns: 'appDebug' }) })
      return
    }

    // Check if sensitive data warning is enabled
    const sensitiveWarningEnabled = typeof window !== 'undefined'
      && localStorage.getItem(SENSITIVE_SEND_WARNING_KEY) !== 'false'

    if (sensitiveWarningEnabled && !pendingSendRef.current) {
      // Validate first before showing dialog
      if (!onSend) return
      const { files } = filesStore.getState()
      if (files.find(item => item.transferMethod === TransferMethod.local_file && !item.uploadedId)) {
        notify({ type: 'info', message: t('errorMessage.waitForFileUpload', { ns: 'appDebug' }) })
        return
      }
      if (!query || !query.trim()) {
        notify({ type: 'info', message: t('errorMessage.queryRequired', { ns: 'appAnnotation' }) })
        return
      }
      setSkipSensitiveConfirm(false)
      setShowSensitiveConfirm(true)
      return
    }

    pendingSendRef.current = false
    doActualSend()
  }
  const handleCompositionStart = () => {
    // e: React.CompositionEvent<HTMLTextAreaElement>
    isComposingRef.current = true
  }
  const handleCompositionEnd = () => {
    // safari or some browsers will trigger compositionend before keydown.
    // delay 50ms for safari.
    setTimeout(() => {
      isComposingRef.current = false
    }, 50)
  }
  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey && !e.nativeEvent.isComposing) {
      // if isComposing, exit
      if (isComposingRef.current)
        return
      e.preventDefault()
      setQuery(query.replace(/\n$/, ''))
      historyRef.current.push(query)
      setCurrentIndex(historyRef.current.length)
      handleSend()
    }
    else if (e.key === 'ArrowUp' && !e.shiftKey && !e.nativeEvent.isComposing && e.metaKey) {
      // When the cmd + up key is pressed, output the previous element
      if (currentIndex > 0) {
        setCurrentIndex(currentIndex - 1)
        handleQueryChange(historyRef.current[currentIndex - 1])
      }
    }
    else if (e.key === 'ArrowDown' && !e.shiftKey && !e.nativeEvent.isComposing && e.metaKey) {
      // When the cmd + down key is pressed, output the next element
      if (currentIndex < historyRef.current.length - 1) {
        setCurrentIndex(currentIndex + 1)
        handleQueryChange(historyRef.current[currentIndex + 1])
      }
      else if (currentIndex === historyRef.current.length - 1) {
        // If it is the last element, clear the input box
        setCurrentIndex(historyRef.current.length)
        handleQueryChange('')
      }
    }
  }

  const handleShowVoiceInput = useCallback(() => {
    (Recorder as any).getPermission().then(() => {
      setShowVoiceInput(true)
    }, () => {
      notify({ type: 'error', message: t('voiceInput.notAllow', { ns: 'common' }) })
    })
  }, [t, notify])

  const operation = (
    <Operation
      ref={holdSpaceRef}
      readonly={readonly}
      fileConfig={visionConfig}
      speechToTextConfig={speechToTextConfig}
      onShowVoiceInput={handleShowVoiceInput}
      onSend={handleSend}
      theme={theme}
    />
  )

  return (
    <>
      <div
        className={cn(
          'relative z-10 overflow-hidden rounded-xl border border-components-chat-input-border bg-components-panel-bg-blur pb-[9px] shadow-md',
          isDragActive && 'border border-dashed border-components-option-card-option-selected-border',
          disabled && 'pointer-events-none border-components-panel-border opacity-50 shadow-none',
        )}
      >
        <div className="relative max-h-[158px] overflow-y-auto overflow-x-hidden px-[9px] pt-[9px]">
          <FileListInChatInput fileConfig={visionConfig!} />
          <div
            ref={wrapperRef}
            className="flex items-center justify-between"
          >
            <div className="relative flex w-full grow items-center">
              <div
                ref={textValueRef}
                className="body-lg-regular pointer-events-none invisible absolute h-auto w-auto whitespace-pre p-1 leading-6"
              >
                {query}
              </div>
              <Textarea
                ref={ref => textareaRef.current = ref as any}
                className={cn(
                  'body-lg-regular w-full resize-none bg-transparent p-1 leading-6 text-text-primary outline-none',
                )}
                placeholder={decode(t(readonly ? 'chat.inputDisabledPlaceholder' : 'chat.inputPlaceholder', { ns: 'common', botName }) || '')}
                autoFocus
                minRows={1}
                value={query}
                onChange={e => handleQueryChange(e.target.value)}
                onKeyDown={handleKeyDown}
                onCompositionStart={handleCompositionStart}
                onCompositionEnd={handleCompositionEnd}
                onPaste={handleClipboardPasteFile}
                onDragEnter={handleDragFileEnter}
                onDragLeave={handleDragFileLeave}
                onDragOver={handleDragFileOver}
                onDrop={handleDropFile}
                readOnly={readonly}
              />
            </div>
            {
              !isMultipleLine && operation
            }
          </div>
          {
            showVoiceInput && (
              <VoiceInput
                onCancel={() => setShowVoiceInput(false)}
                onConverted={text => handleQueryChange(text)}
              />
            )
          }
        </div>
        {
          isMultipleLine && (
            <div className="px-[9px]">{operation}</div>
          )
        }
      </div>
      {showFeatureBar && (
        <FeatureBar
          showFileUpload={showFileUpload}
          disabled={featureBarDisabled}
          onFeatureBarClick={readonly ? noop : onFeatureBarClick}
          hideEditEntrance={readonly}
        />
      )}
      {showSensitiveConfirm && (
        <div className="fixed inset-0 z-[9999] flex items-center justify-center bg-[rgba(17,24,39,0.45)] px-4">
          <div className="w-full max-w-md rounded-2xl border border-[#e5e7eb] bg-white p-6 shadow-xl">
            <div className="mb-4 flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-[#eff6ff] text-[#2563eb] shadow-sm">
                <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <div>
                <h3 className="text-base font-semibold text-[#111827]">敏感信息确认</h3>
                <p className="mt-1 text-xs text-[#4b5563]">发送前再确认一次，确保内容安全可控。</p>
              </div>
            </div>
            <div className="rounded-xl border border-[#bfdbfe] bg-[#eff6ff] p-4">
              <p className="text-sm leading-6 text-[#4b5563]">
                当前内容即将发送至互联网，请务必确认内容中无敏感信息，例如个人隐私、密码、密钥或内部凭据。
              </p>
            </div>
            <label
              className="mt-4 flex cursor-pointer items-center gap-3 rounded-xl border border-[#e5e7eb] bg-[#f9fafb] px-4 py-3 transition-colors duration-200 ease-in-out hover:bg-white"
              onClick={(e) => {
                e.preventDefault()
                setSkipSensitiveConfirm(value => !value)
              }}
            >
              <Checkbox
                id="skip-sensitive-confirm"
                checked={skipSensitiveConfirm}
                onCheck={(event) => {
                  event.preventDefault()
                  event.stopPropagation()
                  setSkipSensitiveConfirm(value => !value)
                }}
                  className="rounded"
              />
              <div>
                <div className="text-sm font-medium text-[#111827]">下次不用再提醒</div>
                <div className="text-xs text-[#4b5563]">勾选后，将默认跳过该确认弹窗。</div>
              </div>
            </label>
            <div className="mt-6 flex justify-end gap-3">
              <button
                type="button"
                onClick={() => {
                  setSkipSensitiveConfirm(false)
                  setShowSensitiveConfirm(false)
                }}
                className="rounded-lg border border-[#d1d5db] px-6 py-2.5 text-sm font-medium text-[#4b5563] transition-colors duration-200 ease-in-out hover:bg-[#f3f4f6]"
              >
                取消发送
              </button>
              <button
                type="button"
                onClick={() => {
                  if (typeof window !== 'undefined')
                    localStorage.setItem(SENSITIVE_SEND_WARNING_KEY, skipSensitiveConfirm ? 'false' : 'true')

                  setShowSensitiveConfirm(false)
                  pendingSendRef.current = true
                  handleSend()
                }}
                className="rounded-lg bg-[#3b82f6] px-6 py-2.5 text-sm font-medium text-white shadow-sm transition-colors duration-200 ease-in-out hover:bg-[#2563eb]"
              >
                确认发送
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  )
}

const ChatInputAreaWrapper = (props: ChatInputAreaProps) => {
  return (
    <FileContextProvider>
      <ChatInputArea {...props} />
    </FileContextProvider>
  )
}

export default ChatInputAreaWrapper
