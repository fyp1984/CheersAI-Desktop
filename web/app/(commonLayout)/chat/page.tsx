'use client'

import { RiAddLine, RiArrowDownSLine, RiArrowLeftSLine, RiArrowRightSLine, RiAttachmentLine, RiCheckLine, RiCloseLine, RiDeleteBinLine, RiDownloadLine, RiFileCopyLine, RiMicFill, RiMicLine, RiMoreLine, RiRefreshLine, RiSearchLine } from '@remixicon/react'
import { useRouter } from 'next/navigation'
import { useEffect, useMemo, useRef, useState } from 'react'
import Loading from '@/app/components/base/loading'
import { Markdown } from '@/app/components/base/markdown'
import { SandboxFilePicker } from '@/app/components/base/sandbox-file-picker'
import Toast from '@/app/components/base/toast'
import { ModelTypeEnum } from '@/app/components/header/account-setting/model-provider-page/declarations'
import { useDefaultModel, useModelList } from '@/app/components/header/account-setting/model-provider-page/hooks'
import { useAppContext } from '@/context/app-context'
import useDocumentTitle from '@/hooks/use-document-title'
import { sendSimpleChatMessage } from '@/service/chat'
import { cn } from '@/utils/classnames'
import { hasWorkspaceCapability, WORKSPACE_CAPABILITIES } from '@/utils/workspace-capabilities'

type Message = {
  id: string
  type: 'user' | 'assistant'
  content: string
  timestamp: Date
  files?: UploadedFile[]
}

type UploadedFile = {
  id: string
  name: string
  size: number
  type: string
  url: string
  isDesensitized?: boolean
  content?: string
}

type Conversation = {
  id: string
  title: string
  lastMessage: string
  timestamp: Date
  messages: Message[]
}

type SelectedModel = {
  provider: string
  model: string
  label: string
}

type SpeechRecognitionAlternativeLike = {
  transcript?: string
}

type SpeechRecognitionResultLike = {
  isFinal?: boolean
  0?: SpeechRecognitionAlternativeLike
}

type SpeechRecognitionEventLike = {
  error?: string
  resultIndex?: number
  results?: ArrayLike<SpeechRecognitionResultLike>
}

type SpeechRecognitionLike = {
  lang: string
  continuous: boolean
  interimResults: boolean
  maxAlternatives: number
  onstart: (() => void) | null
  onend: (() => void) | null
  onerror: ((event: SpeechRecognitionEventLike) => void) | null
  onresult: ((event: SpeechRecognitionEventLike) => void) | null
  start: () => void
  stop: () => void
}

type StoredMessage = Omit<Message, 'timestamp'> & {
  timestamp: string
}

type StoredConversation = Omit<Conversation, 'messages' | 'timestamp'> & {
  messages: StoredMessage[]
  timestamp: string
}

// 格式化时间戳
function formatTimestamp(date: Date): string {
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  const minutes = Math.floor(diff / 60000)
  const hours = Math.floor(diff / 3600000)
  const days = Math.floor(diff / 86400000)

  if (minutes < 1)
    return '刚刚'
  if (minutes < 60)
    return `${minutes}分钟前`
  if (hours < 24)
    return `${hours}小时前`
  if (days < 7)
    return `${days}天前`

  return date.toLocaleDateString('zh-CN', { month: 'numeric', day: 'numeric' })
}

function getInitialSidebarCollapsed(storageKey: string) {
  if (typeof window === 'undefined')
    return false

  try {
    const stored = window.localStorage.getItem(storageKey)
    return stored ? JSON.parse(stored) : false
  }
  catch {
    return false
  }
}

function getInitialConversations(storageKey: string): Conversation[] {
  if (typeof window === 'undefined')
    return []

  try {
    const stored = window.localStorage.getItem(storageKey)
    if (!stored)
      return []

    return (JSON.parse(stored) as StoredConversation[]).map(conv => ({
      ...conv,
      timestamp: new Date(conv.timestamp),
      messages: conv.messages.map(msg => ({
        ...msg,
        timestamp: new Date(msg.timestamp),
      })),
    }))
  }
  catch {
    return []
  }
}

const ChatPage = () => {
  useDocumentTitle('对话')
  const STORAGE_KEY = 'cheersai_conversations'
  const SIDEBAR_STORAGE_KEY = 'cheersai_sidebar_collapsed'
  const { currentWorkspace } = useAppContext()
  const canManageModels = hasWorkspaceCapability(currentWorkspace, WORKSPACE_CAPABILITIES.modelManage)
  const router = useRouter()
  const { canUseChat, isLoadingCurrentWorkspace } = useAppContext()

  const [conversations, setConversations] = useState<Conversation[]>(() => getInitialConversations(STORAGE_KEY))
  const [currentConversationId, setCurrentConversationId] = useState<string | null>(null)
  const [messages, setMessages] = useState<Message[]>([])
  const [inputValue, setInputValue] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const [showModelSelector, setShowModelSelector] = useState(false)
  const modelSelectorRef = useRef<HTMLDivElement>(null)
  const actionsMenuRef = useRef<HTMLDivElement>(null)

  // 选中的模型状态 - 移到前面声明
  const [selectedModel, setSelectedModel] = useState<SelectedModel | null>(null)
  const [uploadedFiles, setUploadedFiles] = useState<UploadedFile[]>([])
  const [showSandboxPicker, setShowSandboxPicker] = useState(false)
  const [sidebarCollapsed, setSidebarCollapsed] = useState<boolean>(() => getInitialSidebarCollapsed(SIDEBAR_STORAGE_KEY))
  const [streamingMessageId, setStreamingMessageId] = useState<string | null>(null)
  const [isAutoFilled, setIsAutoFilled] = useState(false)
  const [autoFilledText, setAutoFilledText] = useState('')
  const [searchQuery, setSearchQuery] = useState('')
  const [showConversationActions, setShowConversationActions] = useState(false)
  const [isVoiceSupported] = useState(() => {
    if (typeof window === 'undefined')
      return false

    const speechWindow = window as Window & {
      SpeechRecognition?: new () => SpeechRecognitionLike
      webkitSpeechRecognition?: new () => SpeechRecognitionLike
    }

    return Boolean(speechWindow.SpeechRecognition || speechWindow.webkitSpeechRecognition)
  })
  const [isVoiceListening, setIsVoiceListening] = useState(false)
  const [voiceDraft, setVoiceDraft] = useState('')
  const [renameConversationId, setRenameConversationId] = useState<string | null>(null)
  const [renameDraft, setRenameDraft] = useState('')
  const recognitionRef = useRef<SpeechRecognitionLike | null>(null)
  const inputValueRef = useRef('')

  useEffect(() => {
    if (!isLoadingCurrentWorkspace && !canUseChat)
      router.replace('/apps')
  }, [canUseChat, isLoadingCurrentWorkspace, router])

  // 保存侧边栏状态到本地存储
  useEffect(() => {
    try {
      localStorage.setItem(SIDEBAR_STORAGE_KEY, JSON.stringify(sidebarCollapsed))
    }
    catch {
      // 保存侧边栏状态失败，忽略错误
    }
  }, [sidebarCollapsed])

  // 保存对话到本地存储
  useEffect(() => {
    try {
      if (conversations.length > 0)
        localStorage.setItem(STORAGE_KEY, JSON.stringify(conversations))
      else
        localStorage.removeItem(STORAGE_KEY)
    }
    catch {
      // 保存对话到本地存储失败，忽略错误
    }
  }, [conversations])

  useEffect(() => {
    inputValueRef.current = inputValue
  }, [inputValue])

  // 获取模型列表 - 使用更简单的方法
  const { data: modelListData, isLoading: isModelListLoading } = useModelList(ModelTypeEnum.textGeneration)
  const { data: defaultModelData } = useDefaultModel(ModelTypeEnum.textGeneration)

  const resolvedSelectedModel = useMemo(() => {
    if (selectedModel)
      return selectedModel

    if (defaultModelData && modelListData) {
      const defaultProvider = modelListData.find(provider => provider.provider === defaultModelData.provider.provider)
      const defaultModel = defaultProvider?.models.find(model => model.model === defaultModelData.model)

      if (defaultProvider && defaultModel) {
        return {
          provider: defaultProvider.provider,
          model: defaultModel.model,
          label: defaultModel.label?.zh_Hans || defaultModel.label?.en_US || defaultModel.model,
        }
      }
    }

    if (!isModelListLoading && (!modelListData || modelListData.length === 0)) {
      return {
        provider: 'ollama',
        model: 'qwen2.5:1.5b',
        label: 'Qwen2.5 1.5B (Ollama)',
      }
    }

    return null
  }, [defaultModelData, isModelListLoading, modelListData, selectedModel])

  // 点击外部关闭模型选择器
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (modelSelectorRef.current && !modelSelectorRef.current.contains(event.target as Node)) {
        setShowModelSelector(false)
      }
      if (actionsMenuRef.current && !actionsMenuRef.current.contains(event.target as Node)) {
        setShowConversationActions(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => {
      document.removeEventListener('mousedown', handleClickOutside)
    }
  }, [])

  useEffect(() => {
    if (typeof window === 'undefined')
      return

    const speechWindow = window as Window & {
      SpeechRecognition?: new () => SpeechRecognitionLike
      webkitSpeechRecognition?: new () => SpeechRecognitionLike
    }
    const SpeechRecognition = speechWindow.SpeechRecognition || speechWindow.webkitSpeechRecognition

    if (!SpeechRecognition)
      return

    const recognition = new SpeechRecognition()
    recognition.lang = 'zh-CN'
    recognition.continuous = false
    recognition.interimResults = true
    recognition.maxAlternatives = 1
    recognition.onstart = () => setIsVoiceListening(true)
    recognition.onend = () => {
      setIsVoiceListening(false)
      setVoiceDraft('')
    }
    recognition.onerror = (event: SpeechRecognitionEventLike) => {
      setIsVoiceListening(false)
      setVoiceDraft('')
      if (event?.error === 'aborted')
        return
      Toast.notify({ type: 'error', message: '语音输入暂不可用，请检查麦克风权限。' })
    }
    recognition.onresult = (event: SpeechRecognitionEventLike) => {
      const results = Array.from(event.results || [])
        .slice(event.resultIndex || 0)
      const transcript = results
        .filter(result => result.isFinal)
        .map(result => result[0]?.transcript || '')
        .join('')
        .trim()
      const interimTranscript = results
        .filter(result => !result.isFinal)
        .map(result => result[0]?.transcript || '')
        .join('')
        .trim()

      setVoiceDraft(interimTranscript)

      if (!transcript)
        return

      setInputValue((prev) => {
        const nextValue = prev.trim() ? `${prev.trimEnd()} ${transcript}` : transcript
        requestAnimationFrame(() => {
          if (textareaRef.current) {
            textareaRef.current.style.height = 'auto'
            textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`
          }
        })
        return nextValue
      })
    }

    recognitionRef.current = recognition

    return () => {
      recognition.stop()
      recognitionRef.current = null
    }
  }, [])

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleNewConversation = () => {
    const newConversation: Conversation = {
      id: Date.now().toString(),
      title: '新建对话',
      lastMessage: '',
      timestamp: new Date(),
      messages: [],
    }
    setConversations(prev => [newConversation, ...prev])
    setCurrentConversationId(newConversation.id)
    setMessages([])
    setShowConversationActions(false)
  }

  const handleDeleteConversation = (id: string) => {
    setConversations(prev => prev.filter(c => c.id !== id))
    if (currentConversationId === id) {
      const remainingConversations = conversations.filter(c => c.id !== id)
      if (remainingConversations.length > 0) {
        setCurrentConversationId(remainingConversations[0].id)
        setMessages(remainingConversations[0].messages)
      }
      else {
        setCurrentConversationId(null)
        setMessages([])
      }
    }
  }

  const handleSelectConversation = (id: string) => {
    const conversation = conversations.find(item => item.id === id)
    setCurrentConversationId(id)
    setMessages(conversation?.messages || [])
  }

  const handleSelectModel = (provider: string, model: string, label: string) => {
    setSelectedModel({ provider, model, label })
    setShowModelSelector(false)
  }

  const currentConversation = useMemo(
    () => conversations.find(conversation => conversation.id === currentConversationId) || null,
    [conversations, currentConversationId],
  )

  const filteredConversations = useMemo(() => {
    const normalizedQuery = searchQuery.trim().toLowerCase()
    const sortedConversations = [...conversations].sort((a, b) => b.timestamp.getTime() - a.timestamp.getTime())

    if (!normalizedQuery)
      return sortedConversations

    return sortedConversations.filter((conversation) => {
      const searchableText = [
        conversation.title,
        conversation.lastMessage,
        ...conversation.messages.map(message => message.content),
      ]
        .join('\n')
        .toLowerCase()

      return searchableText.includes(normalizedQuery)
    })
  }, [conversations, searchQuery])

  const handleRemoveFile = (fileId: string) => {
    setUploadedFiles(prev => prev.filter(f => f.id !== fileId))
  }

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0)
      return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return `${Number.parseFloat((bytes / k ** i).toFixed(2))} ${sizes[i]}`
  }

  // 读取文件内容
  const readFileContent = async (file: UploadedFile): Promise<string> => {
    try {
      // 文件内容已在选择时读取
      if (file.content) {
        return file.content
      }
      else if (file.type.startsWith('text/') || file.type === 'application/json') {
        return `[文件: ${file.name} - 内容未加载]`
      }
      else {
        return `[文件: ${file.name}, 大小: ${formatFileSize(file.size)}, 类型: ${file.type}]`
      }
    }
    catch {
      return `[无法读取文件: ${file.name}]`
    }
  }

  // 处理沙箱文件选择
  const handleSandboxFilesSelected = async (selectedFiles: File[]) => {
    const newFiles: UploadedFile[] = []

    for (let i = 0; i < selectedFiles.length; i++) {
      const file = selectedFiles[i]

      // 读取文件内容
      let content = ''
      try {
        // 直接读取File对象的内容，不管文件类型
        content = await file.text()
      }
      catch {
        content = `[无法读取文件内容: ${file.name}]`
      }

      newFiles.push({
        id: Date.now().toString() + i,
        name: file.name,
        size: file.size,
        type: file.type,
        url: '', // 沙箱文件不需要URL
        isDesensitized: true,
        content,
      })
    }

    setUploadedFiles(prev => [...prev, ...newFiles])
  }

  // 处理附件按钮点击
  const handleAttachmentClick = () => {
    setShowSandboxPicker(true)
  }

  const toggleSidebar = () => {
    setSidebarCollapsed(prev => !prev)
  }

  const handleVoiceInput = () => {
    if (!isVoiceSupported || !recognitionRef.current) {
      Toast.notify({ type: 'error', message: '当前浏览器不支持语音输入。' })
      return
    }

    if (isVoiceListening) {
      recognitionRef.current.stop()
      return
    }

    try {
      recognitionRef.current.start()
    }
    catch {
      Toast.notify({ type: 'warning', message: '语音输入正在准备中，请稍后再试。' })
    }
  }

  const handleRenameConversation = (conversationId: string) => {
    const conversation = conversations.find(item => item.id === conversationId)
    setRenameConversationId(conversationId)
    setRenameDraft(conversation?.title || '')
    setShowConversationActions(false)
  }

  const handleConfirmRenameConversation = () => {
    if (!renameConversationId || !renameDraft.trim())
      return

    setConversations(prev => prev.map(item =>
      item.id === renameConversationId
        ? { ...item, title: renameDraft.trim(), timestamp: new Date() }
        : item,
    ))
    setRenameConversationId(null)
    setRenameDraft('')
  }

  const handleExportConversation = () => {
    if (!currentConversation)
      return

    const content = currentConversation.messages
      .map(message => [
        `## ${message.type === 'user' ? '用户' : 'AI'} · ${message.timestamp.toLocaleString('zh-CN')}`,
        '',
        message.content || '暂无消息',
      ].join('\n'))
      .join('\n\n')

    const blob = new Blob([content], { type: 'text/markdown;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `${currentConversation.title || 'conversation'}.md`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
    setShowConversationActions(false)
  }

  const handleClearCurrentConversation = () => {
    if (!currentConversationId)
      return

    setMessages([])
    setConversations(prev => prev.map(item =>
      item.id === currentConversationId
        ? { ...item, lastMessage: '', messages: [], timestamp: new Date() }
        : item,
    ))
    setShowConversationActions(false)
  }

  // 复制AI回复内容
  const handleCopyMessage = async (content: string) => {
    try {
      await navigator.clipboard.writeText(content)
      // 可以添加一个toast提示
    }
    catch {
      // 降级方案
      const textArea = document.createElement('textarea')
      textArea.value = content
      document.body.appendChild(textArea)
      textArea.select()
      document.execCommand('copy')
      document.body.removeChild(textArea)
    }
  }

  // 下载AI回复内容
  const handleDownloadMessage = (content: string, messageId: string) => {
    const blob = new Blob([content], { type: 'text/markdown' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `ai-response-${messageId}.md`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  // 重新生成AI回复
  const handleRegenerateMessage = async (messageIndex: number) => {
    if (isLoading)
      return

    if (!resolvedSelectedModel?.provider || !resolvedSelectedModel?.model) {
      Toast.notify({ type: 'error', message: '请先在右上角选择模型' })
      return
    }

    // 获取到指定消息为止的对话历史
    const messagesToRegenerate = messages.slice(0, messageIndex)
    const lastUserMessage = messagesToRegenerate.filter(m => m.type === 'user').pop()

    if (!lastUserMessage)
      return

    // 移除从指定位置开始的所有消息
    const newMessages = messages.slice(0, messageIndex)
    setMessages(newMessages)

    // 更新对话记录
    if (currentConversationId) {
      setConversations(prev => prev.map((conv) => {
        if (conv.id === currentConversationId) {
          return {
            ...conv,
            messages: newMessages,
            timestamp: new Date(),
          }
        }
        return conv
      }))
    }

    // 重新发送请求
    setIsLoading(true)

    // 添加新的AI消息占位
    const assistantMessageId = Date.now().toString()
    const assistantMessage: Message = {
      id: assistantMessageId,
      type: 'assistant',
      content: '',
      timestamp: new Date(),
    }
    setMessages(prev => [...prev, assistantMessage])
    setStreamingMessageId(assistantMessageId)

    try {
      // 构建对话历史
      const recentMessages = newMessages.slice(-20)
      const history = recentMessages.map(msg => ({
        type: msg.type,
        content: msg.content,
      }))

      // 添加文件内容到查询
      let queryWithFiles = lastUserMessage.content
      if (lastUserMessage.files && lastUserMessage.files.length > 0) {
        const fileContents = await Promise.all(
          lastUserMessage.files.map(async (file) => {
            const content = await readFileContent(file)
            return `\n\n--- 文件: ${file.name} ---\n${content}\n--- 文件结束 ---`
          }),
        )
        queryWithFiles += `\n\n以下是用户上传的文件内容：${fileContents.join('')}`
      }

      let fullResponse = ''

      await sendSimpleChatMessage(
        queryWithFiles,
        resolvedSelectedModel.provider,
        resolvedSelectedModel.model,
        history,
        (content) => {
          fullResponse += content
          setMessages(prev => prev.map(msg =>
            msg.id === assistantMessageId
              ? { ...msg, content: fullResponse }
              : msg,
          ))
        },
        (error) => {
          throw new Error(error)
        },
      )

      // 流式输出完成，清除流式状态
      setStreamingMessageId(null)

      // 更新对话记录
      if (currentConversationId) {
        setConversations(prev => prev.map((conv) => {
          if (conv.id === currentConversationId) {
            return {
              ...conv,
              lastMessage: fullResponse.slice(0, 50),
              timestamp: new Date(),
              messages: [...conv.messages, { ...assistantMessage, content: fullResponse }],
            }
          }
          return conv
        }))
      }
    }
    catch (error) {
      setStreamingMessageId(null)

      const errorMessage: Message = {
        id: Date.now().toString(),
        type: 'assistant',
        content: `调用模型失败: ${error instanceof Error ? error.message : '未知错误'}。请确保已在设置中配置模型。`,
        timestamp: new Date(),
      }

      setMessages(prev => prev.map(msg =>
        msg.id === assistantMessageId ? errorMessage : msg,
      ))

      if (currentConversationId) {
        setConversations(prev => prev.map((conv) => {
          if (conv.id === currentConversationId) {
            return {
              ...conv,
              lastMessage: errorMessage.content.slice(0, 50),
              timestamp: new Date(),
              messages: [...conv.messages, errorMessage],
            }
          }
          return conv
        }))
      }
    }
    finally {
      setIsLoading(false)
      setStreamingMessageId(null)
    }
  }

  const handleSend = async () => {
    if (!inputValue.trim() || isLoading)
      return

    if (!resolvedSelectedModel?.provider || !resolvedSelectedModel?.model) {
      Toast.notify({ type: 'error', message: '请先在右上角选择模型' })
      return
    }

    const userMessage: Message = {
      id: Date.now().toString(),
      type: 'user',
      content: inputValue.trim(),
      timestamp: new Date(),
      files: uploadedFiles.length > 0 ? [...uploadedFiles] : undefined,
    }

    let conversationId = currentConversationId

    // 如果没有当前对话，创建一个新对话
    if (!conversationId) {
      const newConversation: Conversation = {
        id: Date.now().toString(),
        title: userMessage.content.slice(0, 20),
        lastMessage: userMessage.content,
        timestamp: new Date(),
        messages: [userMessage],
      }
      conversationId = newConversation.id
      setConversations(prev => [newConversation, ...prev])
      setCurrentConversationId(conversationId)
      setMessages([userMessage])
    }
    else {
      // 更新现有对话
      const updatedMessages = [...messages, userMessage]
      setMessages(updatedMessages)

      setConversations(prev => prev.map((conv) => {
        if (conv.id === conversationId) {
          const title = conv.messages.length === 0 ? userMessage.content.slice(0, 20) : conv.title
          return {
            ...conv,
            title,
            lastMessage: userMessage.content,
            timestamp: new Date(),
            messages: updatedMessages,
          }
        }
        return conv
      }))
    }

    setInputValue('')
    setUploadedFiles([])
    setIsAutoFilled(false)
    setAutoFilledText('')
    setIsLoading(true)

    // 先添加一个空的 AI 消息占位
    const assistantMessageId = (Date.now() + 1).toString()
    const assistantMessage: Message = {
      id: assistantMessageId,
      type: 'assistant',
      content: '',
      timestamp: new Date(),
    }
    setMessages(prev => [...prev, assistantMessage])
    setStreamingMessageId(assistantMessageId)

    try {
      // 构建对话历史
      const currentMessages = messages.length > 0 ? messages : []
      const recentMessages = currentMessages.slice(-20)
      const history = recentMessages.map(msg => ({
        type: msg.type,
        content: msg.content,
      }))

      // 添加文件内容到查询
      let queryWithFiles = userMessage.content
      if (uploadedFiles.length > 0) {
        const fileContents = await Promise.all(
          uploadedFiles.map(async (file) => {
            const content = await readFileContent(file)
            return `\n\n--- 文件: ${file.name} ---\n${content}\n--- 文件结束 ---`
          }),
        )
        queryWithFiles += `\n\n以下是用户上传的文件内容：${fileContents.join('')}`
      }

      let fullResponse = ''

      await sendSimpleChatMessage(
        queryWithFiles,
        resolvedSelectedModel.provider,
        resolvedSelectedModel.model,
        history,
        (content) => {
          fullResponse += content
          setMessages(prev => prev.map(msg =>
            msg.id === assistantMessageId
              ? { ...msg, content: fullResponse }
              : msg,
          ))
        },
        (error) => {
          throw new Error(error)
        },
      )

      // 流式输出完成，清除流式状态
      setStreamingMessageId(null)

      // 更新对话记录
      setConversations(prev => prev.map((conv) => {
        if (conv.id === conversationId) {
          return {
            ...conv,
            lastMessage: fullResponse.slice(0, 50),
            timestamp: new Date(),
            messages: [...conv.messages, { ...assistantMessage, content: fullResponse }],
          }
        }
        return conv
      }))
    }
    catch (error) {
      setStreamingMessageId(null)

      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: 'assistant',
        content: `调用模型失败: ${error instanceof Error ? error.message : '未知错误'}。请确保已在设置中配置模型。`,
        timestamp: new Date(),
      }

      setMessages(prev => prev.map(msg =>
        msg.id === assistantMessageId ? errorMessage : msg,
      ))

      setConversations(prev => prev.map((conv) => {
        if (conv.id === conversationId) {
          return {
            ...conv,
            lastMessage: errorMessage.content.slice(0, 50),
            timestamp: new Date(),
            messages: [...conv.messages, errorMessage],
          }
        }
        return conv
      }))
    }
    finally {
      setIsLoading(false)
      setStreamingMessageId(null)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const handleTextareaChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const newValue = e.target.value

    // 如果是自动填充状态，检查用户是否在自动填充文字后面添加内容
    if (isAutoFilled && autoFilledText) {
      // 如果新输入的内容以自动填充文字开头，保持自动填充状态
      if (newValue.startsWith(autoFilledText)) {
        setInputValue(newValue)
      }
      else {
        // 如果用户修改了自动填充的部分，清除自动填充状态
        setIsAutoFilled(false)
        setAutoFilledText('')
        setInputValue(newValue)
      }
    }
    else {
      setInputValue(newValue)
    }

    // 自动调整高度
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`
    }
  }

  const renderMessageContent = (message: Message) => {
    if (message.type !== 'assistant')
      return <div className="whitespace-pre-wrap">{message.content}</div>

    if (message.id === streamingMessageId)
      return <div className="whitespace-pre-wrap">{message.content}</div>

    return <Markdown content={message.content} />
  }

  const promptSuggestions = [
    '请帮我进行数据分析',
    '请帮我编写代码',
    '我有问题需要解答',
  ]

  const searchResultText = searchQuery.trim()
    ? `找到 ${filteredConversations.length} 条相关对话`
    : `共 ${conversations.length} 条对话`

  if (isLoadingCurrentWorkspace || !canUseChat)
    return <Loading type="app" />

  return (
    <div className="flex h-full bg-[#f9fafb] font-sans text-[#111827]">
      <div className={cn(
        'flex flex-col border-r border-white/10 bg-[linear-gradient(180deg,#111827_0%,#1f2937_100%)] text-white transition-all duration-300 ease-in-out',
        sidebarCollapsed ? 'w-0 overflow-hidden border-r-0' : 'w-64',
      )}
      >
        <div className="flex min-h-16 items-center justify-between border-b border-white/10 px-4 py-4">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-[linear-gradient(135deg,#3b82f6_0%,#2563eb_100%)] shadow-md">
              <span className="text-sm font-semibold text-white">AI</span>
            </div>
            <div className="min-w-0">
              <div className="truncate text-sm font-semibold text-white">CheersAI</div>
              <div className="truncate text-xs text-gray-400">安全对话</div>
            </div>
          </div>
          <button
            onClick={handleNewConversation}
            className="flex h-9 w-9 items-center justify-center rounded-lg bg-[#3b82f6] text-white transition-colors hover:bg-[#2563eb]"
            title="新建对话"
          >
            <RiAddLine className="h-4 w-4" />
          </button>
        </div>

        <div className="border-b border-white/10 px-4 py-3">
          <div className="relative">
            <RiSearchLine className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-500" />
            <input
              type="text"
              placeholder="搜索对话..."
              value={searchQuery}
              onChange={e => setSearchQuery(e.target.value)}
              className="w-full rounded-lg border border-white/10 bg-white/95 py-2 pl-10 pr-10 text-sm text-[#111827] placeholder:text-gray-400 focus:border-transparent focus:outline-none focus:ring-2 focus:ring-[#3b82f6]"
            />
            {searchQuery && (
              <button
                onClick={() => setSearchQuery('')}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 transition-colors hover:text-gray-600"
                title="清空搜索"
              >
                <RiCloseLine className="h-4 w-4" />
              </button>
            )}
          </div>
          <p className="mt-2 text-xs text-gray-400">{searchResultText}</p>
        </div>

        <div className="flex-1 overflow-y-auto py-2">
          {filteredConversations.length === 0
            ? (
                <div className="px-4 py-10 text-center text-sm text-gray-400">
                  {searchQuery ? '未找到匹配的对话' : '暂无对话记录'}
                </div>
              )
            : (
                filteredConversations.map(conversation => (
                  <div
                    key={conversation.id}
                    onClick={() => handleSelectConversation(conversation.id)}
                    className={cn(
                      'group relative mx-2 my-1 cursor-pointer rounded-lg border border-transparent px-3 py-3 transition-all',
                      currentConversationId === conversation.id
                        ? 'border-[#3b82f6] bg-white/10 shadow-sm'
                        : 'hover:bg-white/5',
                    )}
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex-1 overflow-hidden">
                        <h3 className="mb-1 truncate text-sm font-medium text-white">
                          {conversation.title}
                        </h3>
                        <p className="mb-1 truncate text-xs text-gray-400">
                          {conversation.lastMessage || '暂无消息'}
                        </p>
                        <p className="text-xs text-gray-500">
                          {formatTimestamp(conversation.timestamp)}
                        </p>
                      </div>
                      <button
                        onClick={(e) => {
                          e.stopPropagation()
                          handleDeleteConversation(conversation.id)
                        }}
                        className="flex h-6 w-6 items-center justify-center rounded text-gray-500 opacity-0 transition-all hover:bg-white/10 hover:text-white group-hover:opacity-100"
                        title="删除对话"
                      >
                        <RiDeleteBinLine className="h-3.5 w-3.5" />
                      </button>
                    </div>
                  </div>
                ))
              )}
        </div>
      </div>

      <div className="flex flex-1 flex-col overflow-hidden">
        <div className="flex min-h-16 items-center justify-between border-b border-[#e5e7eb] bg-white px-8 py-4">
          <div className="flex items-center gap-3">
            <button
              onClick={toggleSidebar}
              className="flex h-10 w-10 items-center justify-center rounded-lg text-gray-500 transition-colors hover:bg-[#f3f4f6] hover:text-gray-700"
              title={sidebarCollapsed ? '展开侧边栏' : '折叠侧边栏'}
            >
              {sidebarCollapsed ? <RiArrowRightSLine className="h-4 w-4" /> : <RiArrowLeftSLine className="h-4 w-4" />}
            </button>
            <div>
              <h1 className="text-lg font-semibold text-[#111827]">
                {currentConversation?.title || '新建对话'}
              </h1>
              <p className="mt-1 text-xs text-[#4b5563]">已启用安全对话与 FileBay 文件接入</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <div className="hidden rounded-full bg-[#d1fae5] px-3 py-1 text-xs font-medium text-[#065f46] md:block">
              隐私保护已开启
            </div>
            <div className="relative" ref={modelSelectorRef}>
              <button
                onClick={() => setShowModelSelector(!showModelSelector)}
                className="flex items-center gap-2 rounded-lg border border-[#e5e7eb] bg-[#f9fafb] px-3 py-2 text-sm transition-colors hover:bg-[#f3f4f6]"
              >
                <span className="text-gray-700">
                  {resolvedSelectedModel?.label || '选择模型'}
                </span>
                <RiArrowDownSLine className={cn(
                  'h-4 w-4 text-gray-500 transition-transform',
                  showModelSelector && 'rotate-180',
                )}
                />
              </button>

              {showModelSelector && (
                <div className="absolute right-0 top-full z-50 mt-1 max-h-96 w-80 overflow-y-auto rounded-lg border border-gray-200 bg-white shadow-lg">
                  <div className="border-b border-gray-100 p-3">
                    <h3 className="text-sm font-medium text-gray-900">选择模型</h3>
                  </div>
                  <div className="py-2">
                    {isModelListLoading
                      ? (
                          <div className="px-3 py-4 text-center text-sm text-gray-500">
                            加载模型中...
                          </div>
                        )
                      : !modelListData || modelListData.length === 0
                          ? (
                              <div className="px-3 py-4">
                                <div className="mb-3 text-sm text-gray-500">
                                  使用本地Ollama模型
                                </div>
                                <div className="space-y-1">
                                  <button
                                    onClick={() => handleSelectModel('ollama', 'qwen2.5:1.5b', 'Qwen2.5 1.5B (Ollama)')}
                                    className={cn(
                                      'flex w-full items-center justify-between rounded px-3 py-2 text-left text-sm transition-colors hover:bg-gray-50',
                                      resolvedSelectedModel?.model === 'qwen2.5:1.5b' && 'bg-blue-50 text-blue-700',
                                    )}
                                  >
                                    <div className="flex flex-col">
                                      <span className="font-medium">Qwen2.5 1.5B</span>
                                      <span className="text-xs text-gray-500">本地Ollama模型 - 轻量级</span>
                                    </div>
                                    {resolvedSelectedModel?.model === 'qwen2.5:1.5b' && (
                                      <RiCheckLine className="h-4 w-4 text-blue-600" />
                                    )}
                                  </button>
                                  <button
                                    onClick={() => handleSelectModel('ollama', 'qwen3-coder:30b', 'Qwen3 Coder 30B (Ollama)')}
                                    className={cn(
                                      'flex w-full items-center justify-between rounded px-3 py-2 text-left text-sm transition-colors hover:bg-gray-50',
                                      resolvedSelectedModel?.model === 'qwen3-coder:30b' && 'bg-blue-50 text-blue-700',
                                    )}
                                  >
                                    <div className="flex flex-col">
                                      <span className="font-medium">Qwen3 Coder 30B</span>
                                      <span className="text-xs text-gray-500">本地Ollama模型 - 代码专用</span>
                                    </div>
                                    {resolvedSelectedModel?.model === 'qwen3-coder:30b' && (
                                      <RiCheckLine className="h-4 w-4 text-blue-600" />
                                    )}
                                  </button>
                                </div>
                                <div className="mt-3 border-t border-gray-100 pt-3">
                                  <div className="mb-2 text-xs text-gray-400">
                                    {canManageModels ? '想要更多模型？' : '模型配置由工作区统一管理'}
                                  </div>
                                  {canManageModels ? (
                                    <button
                                      onClick={() => {
                                        window.open('/apps/?action=showSettings&tab=provider', '_blank')
                                      }}
                                      className="rounded bg-blue-500 px-3 py-1.5 text-xs text-white transition-colors hover:bg-blue-600"
                                    >
                                      配置更多提供商
                                    </button>
                                  ) : (
                                    <div className="text-xs text-gray-500">
                                      如需更多模型，请联系工作区管理员统一配置。
                                    </div>
                                  )}
                                </div>
                              </div>
                            )
                          : (
                              modelListData.map((provider) => {
                                const activeModels = (provider.models?.filter(model => model.status === 'active') || [])
                                  .filter((model, index, models) => {
                                    return index === models.findIndex(item => item.model === model.model)
                                  })

                                if (activeModels.length === 0)
                                  return null

                                return (
                                  <div key={provider.provider} className="mb-2">
                                    <div className="px-3 py-1 text-xs font-medium uppercase tracking-wide text-gray-500">
                                      {provider.label?.zh_Hans || provider.label?.en_US || provider.provider}
                                    </div>
                                    {activeModels.map((model) => {
                                      const isSelected = resolvedSelectedModel?.provider === provider.provider && resolvedSelectedModel?.model === model.model
                                      const modelLabel = model.label?.zh_Hans || model.label?.en_US || model.model

                                      return (
                                        <button
                                          key={`${provider.provider}-${model.model}`}
                                          onClick={() => handleSelectModel(provider.provider, model.model, modelLabel)}
                                          className={cn(
                                            'flex w-full items-center justify-between px-3 py-2 text-left text-sm transition-colors hover:bg-gray-50',
                                            isSelected && 'bg-blue-50 text-blue-700',
                                          )}
                                        >
                                          <div className="flex flex-col">
                                            <span className="font-medium">{modelLabel}</span>
                                            <span className="text-xs text-gray-500">{model.model}</span>
                                          </div>
                                          {isSelected && (
                                            <RiCheckLine className="h-4 w-4 text-blue-600" />
                                          )}
                                        </button>
                                      )
                                    })}
                                  </div>
                                )
                              })
                            )}
                  </div>
                </div>
              )}
            </div>

            <div className="relative" ref={actionsMenuRef}>
              <button
                onClick={() => setShowConversationActions(prev => !prev)}
                className="flex h-10 w-10 items-center justify-center rounded-lg border border-[#e5e7eb] text-gray-400 transition-colors hover:bg-[#f3f4f6] hover:text-gray-600"
                title="会话工具"
              >
                <RiMoreLine className="h-4 w-4" />
              </button>
              {showConversationActions && (
                <div className="absolute right-0 top-full z-50 mt-2 w-44 rounded-lg border border-gray-200 bg-white py-1 shadow-lg">
                  <button
                    onClick={() => {
                      if (currentConversationId)
                        handleRenameConversation(currentConversationId)
                      setShowConversationActions(false)
                    }}
                    disabled={!currentConversationId}
                    className="w-full px-3 py-2 text-left text-sm text-gray-700 transition-colors hover:bg-gray-50 disabled:cursor-not-allowed disabled:text-gray-300"
                  >
                    重命名对话
                  </button>
                  <button
                    onClick={handleExportConversation}
                    disabled={!currentConversationId}
                    className="flex w-full items-center justify-between px-3 py-2 text-left text-sm text-gray-700 transition-colors hover:bg-gray-50 disabled:cursor-not-allowed disabled:text-gray-300"
                  >
                    <span>导出 Markdown</span>
                    <RiDownloadLine className="h-4 w-4" />
                  </button>
                  <button
                    onClick={handleClearCurrentConversation}
                    disabled={!currentConversationId}
                    className="flex w-full items-center justify-between px-3 py-2 text-left text-sm text-red-600 transition-colors hover:bg-red-50 disabled:cursor-not-allowed disabled:text-gray-300"
                  >
                    <span>清空当前对话</span>
                    <RiDeleteBinLine className="h-4 w-4" />
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto bg-[#f9fafb]">
          <div className="mx-auto max-w-5xl px-8 py-8">
            {messages.length === 0 && !currentConversationId
              ? (
                  <div className="flex h-full items-center justify-center">
                    <div className="w-full max-w-3xl rounded-2xl border border-[#e5e7eb] bg-white p-10 text-center shadow-sm">
                      <div className="mx-auto mb-6 flex h-16 w-16 items-center justify-center rounded-2xl bg-[linear-gradient(135deg,#3b82f6_0%,#2563eb_100%)] shadow-md">
                        <span className="text-xl font-bold text-white">AI</span>
                      </div>
                      <h3 className="mb-3 text-2xl font-bold text-[#111827]">
                        欢迎使用 CheersAI
                      </h3>
                      <p className="mx-auto mb-6 max-w-2xl text-sm leading-6 text-[#4b5563]">
                        我是您的 AI 助手，可协助完成数据分析、代码编写、问题解答与文件协同。
                        当前页面支持安全输入、语音录入与 FileBay 沙箱文件选择。
                      </p>
                      <div className="mb-6 flex flex-wrap justify-center gap-2">
                        {promptSuggestions.map(text => (
                          <button
                            key={text}
                            onClick={() => {
                              setInputValue(text)
                              setIsAutoFilled(true)
                              setAutoFilledText(text)
                            }}
                            className="rounded-full bg-[#f3f4f6] px-4 py-2 text-xs font-medium text-[#4b5563] transition-colors hover:bg-[#e5e7eb]"
                          >
                            {text.replace('请帮我', '').replace('我有', '').replace('需要', '')}
                          </button>
                        ))}
                      </div>
                      <div className="grid gap-3 text-left md:grid-cols-3">
                        <div className="rounded-xl border border-[#e5e7eb] bg-[#f9fafb] p-4">
                          <div className="mb-1 text-sm font-semibold text-[#111827]">对话更聚焦</div>
                          <div className="text-xs leading-5 text-[#4b5563]">搜索历史会话、重命名、导出 Markdown，并支持重新生成回复。</div>
                        </div>
                        <div className="rounded-xl border border-[#e5e7eb] bg-[#f9fafb] p-4">
                          <div className="mb-1 text-sm font-semibold text-[#111827]">输入更自然</div>
                          <div className="text-xs leading-5 text-[#4b5563]">支持语音输入、附件上传与多行编辑，适合持续协作场景。</div>
                        </div>
                        <div className="rounded-xl border border-[#e5e7eb] bg-[#f9fafb] p-4">
                          <div className="mb-1 text-sm font-semibold text-[#111827]">安全更清晰</div>
                          <div className="text-xs leading-5 text-[#4b5563]">仅允许选择沙箱脱敏文件，并在当前页持续展示安全状态提示。</div>
                        </div>
                      </div>
                    </div>
                  </div>
                )
              : (
                  <>
                    {messages.map(message => (
                      <div
                        key={message.id}
                        className={cn(
                          'mb-6 flex gap-4',
                          message.type === 'user' ? 'justify-end' : 'justify-start',
                        )}
                      >
                        {message.type === 'assistant' && (
                          <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-xl bg-[linear-gradient(135deg,#3b82f6_0%,#2563eb_100%)] shadow-sm">
                            <span className="text-sm font-semibold text-white">AI</span>
                          </div>
                        )}
                        <div
                          className={cn(
                            'group max-w-[768px] rounded-2xl px-4 py-3 shadow-sm',
                            message.type === 'user'
                              ? 'bg-[#3b82f6] text-white'
                              : 'border border-[#e5e7eb] bg-white text-[#111827]',
                          )}
                        >
                          {message.files && message.files.length > 0 && (
                            <div className="mb-3 space-y-2">
                              {message.files.map(file => (
                                <div
                                  key={file.id}
                                  className={cn(
                                    'flex items-center gap-2 rounded border p-2',
                                    message.type === 'user'
                                      ? 'border-blue-200 bg-blue-50'
                                      : 'border-gray-200 bg-white',
                                  )}
                                >
                                  <div className={cn(
                                    'flex h-6 w-6 items-center justify-center rounded text-xs font-medium',
                                    message.type === 'user'
                                      ? 'bg-blue-400 text-white'
                                      : 'bg-blue-100 text-blue-600',
                                  )}
                                  >
                                    {file.name.split('.').pop()?.toUpperCase().slice(0, 2)}
                                  </div>
                                  <div className="min-w-0 flex-1">
                                    <div className={cn(
                                      'truncate text-xs font-medium',
                                      message.type === 'user' ? 'text-gray-800' : 'text-[#111827]',
                                    )}
                                    >
                                      {file.name}
                                    </div>
                                    <div className={cn(
                                      'text-xs',
                                      message.type === 'user' ? 'text-gray-600' : 'text-[#4b5563]',
                                    )}
                                    >
                                      {formatFileSize(file.size)}
                                      {file.isDesensitized && (
                                        <span className="ml-1">• 已脱敏</span>
                                      )}
                                    </div>
                                  </div>
                                </div>
                              ))}
                            </div>
                          )}

                          <div className="text-sm leading-relaxed">
                            {renderMessageContent(message)}
                          </div>
                          <div className="mt-2 flex items-center justify-between">
                            <div
                              className={cn(
                                'text-xs',
                                message.type === 'user' ? 'text-blue-100' : 'text-gray-600',
                              )}
                            >
                              {message.timestamp.toLocaleTimeString('zh-CN', {
                                hour: '2-digit',
                                minute: '2-digit',
                              })}
                            </div>

                            {message.type === 'assistant' && message.content && !isLoading && (
                              <div className="flex items-center gap-1 opacity-0 transition-opacity group-hover:opacity-100">
                                <button
                                  onClick={() => handleCopyMessage(message.content)}
                                  className="flex h-7 w-7 items-center justify-center rounded-lg text-gray-400 transition-colors hover:bg-[#f3f4f6] hover:text-gray-600"
                                  title="复制"
                                >
                                  <RiFileCopyLine className="h-3.5 w-3.5" />
                                </button>
                                <button
                                  onClick={() => handleDownloadMessage(message.content, message.id)}
                                  className="flex h-7 w-7 items-center justify-center rounded-lg text-gray-400 transition-colors hover:bg-[#f3f4f6] hover:text-gray-600"
                                  title="下载"
                                >
                                  <RiDownloadLine className="h-3.5 w-3.5" />
                                </button>
                                <button
                                  onClick={() => {
                                    const messageIndex = messages.findIndex(m => m.id === message.id)
                                    if (messageIndex > 0)
                                      handleRegenerateMessage(messageIndex)
                                  }}
                                  className="flex h-7 w-7 items-center justify-center rounded-lg text-gray-400 transition-colors hover:bg-[#f3f4f6] hover:text-gray-600"
                                  title="重新生成"
                                >
                                  <RiRefreshLine className="h-3.5 w-3.5" />
                                </button>
                              </div>
                            )}
                          </div>
                        </div>
                        {message.type === 'user' && (
                          <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-xl bg-[#1f2937] shadow-sm">
                            <span className="text-sm font-semibold text-white">我</span>
                          </div>
                        )}
                      </div>
                    ))}
                    {isLoading && (
                      <div className="mb-6 flex justify-start gap-4">
                        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-xl bg-[linear-gradient(135deg,#3b82f6_0%,#2563eb_100%)] shadow-sm">
                          <span className="text-sm font-semibold text-white">AI</span>
                        </div>
                        <div className="max-w-[768px] rounded-2xl border border-[#e5e7eb] bg-white px-4 py-3 shadow-sm">
                          <div className="flex items-center gap-2">
                            <div className="flex space-x-1">
                              <div className="h-2 w-2 animate-bounce rounded-full bg-[#3b82f6] [animation-delay:-0.3s]"></div>
                              <div className="h-2 w-2 animate-bounce rounded-full bg-[#3b82f6] [animation-delay:-0.15s]"></div>
                              <div className="h-2 w-2 animate-bounce rounded-full bg-[#3b82f6]"></div>
                            </div>
                            <span className="text-sm text-[#4b5563]">正在思考...</span>
                          </div>
                        </div>
                      </div>
                    )}
                  </>
                )}
            <div ref={messagesEndRef} />
          </div>
        </div>

        <div className="border-t border-[#e5e7eb] bg-white px-8 py-5">
          <div className="mx-auto max-w-5xl">
            {uploadedFiles.length > 0 && (
              <div className="mb-3 rounded-xl border border-[#e5e7eb] bg-[#f9fafb] p-3">
                <div className="mb-2 text-sm font-medium text-[#4b5563]">{`已选择文件（${uploadedFiles.length}）`}</div>
                <div className="space-y-2">
                  {uploadedFiles.map(file => (
                    <div key={file.id} className="flex items-center justify-between rounded-lg border border-[#e5e7eb] bg-white p-2">
                      <div className="flex items-center gap-2">
                        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-[#dbeafe]">
                          <span className="text-xs font-medium text-blue-600">
                            {file.name.split('.').pop()?.toUpperCase()}
                          </span>
                        </div>
                        <div>
                          <div className="text-sm font-medium text-gray-900">{file.name}</div>
                          <div className="text-xs text-gray-500">
                            {formatFileSize(file.size)}
                            <span className="ml-2 rounded-full bg-[#d1fae5] px-2 py-0.5 text-xs text-[#065f46]">
                              沙箱文件
                            </span>
                          </div>
                        </div>
                      </div>
                      <button
                        onClick={() => handleRemoveFile(file.id)}
                        className="flex h-7 w-7 items-center justify-center rounded-lg text-gray-400 transition-colors hover:bg-[#fee2e2] hover:text-[#ef4444]"
                        title="移除文件"
                      >
                        <RiCloseLine className="h-4 w-4" />
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            )}

            <div className="mb-4 rounded-xl border border-[#bfdbfe] bg-[#eff6ff] p-4">
              <p className="text-sm leading-6 text-[#1e40af]">
                <span className="font-medium">安全模式：</span>
                仅可选择沙箱内的脱敏文件。系统将自动记录并脱敏输入内容中的个人身份信息。
              </p>
            </div>

            <div className="rounded-2xl border border-[#e5e7eb] bg-white p-4 shadow-sm transition-all duration-200 focus-within:border-[#3b82f6] focus-within:ring-2 focus-within:ring-[rgba(59,130,246,0.12)]">
              <div className="mb-3 flex items-center justify-between gap-3">
                <div className="flex items-center gap-2 text-xs text-[#4b5563]">
                  <span className="rounded-full bg-[#d1fae5] px-2 py-1 font-medium text-[#065f46]">已脱敏保护</span>
                  <span>支持语音输入、搜索历史和 Markdown 导出</span>
                </div>
                {voiceDraft && (
                  <div className="max-w-[280px] truncate rounded-full bg-[#fff3cc] px-3 py-1 text-xs text-[#92400e]">
                    正在识别：
                    {voiceDraft}
                  </div>
                )}
              </div>
              <div className="relative flex items-end gap-3">
                <button
                  onClick={handleAttachmentClick}
                  className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg text-gray-400 transition-colors hover:bg-[#f3f4f6] hover:text-gray-600"
                  title="从沙箱选择文件"
                >
                  <RiAttachmentLine className="h-4 w-4" />
                </button>

                <div className="relative flex min-h-[96px] flex-1 items-start">
                  {isAutoFilled && autoFilledText && (
                    <div className="pointer-events-none absolute inset-0 z-10 flex items-start pt-3">
                      <span className="rounded-md border border-[#bfdbfe] bg-[#eff6ff] px-2 py-1 text-sm text-[#2563eb]">
                        {autoFilledText}
                      </span>
                      {inputValue.length > autoFilledText.length && (
                        <span className="ml-1 pt-1 text-sm text-[#111827]">
                          {inputValue.slice(autoFilledText.length)}
                        </span>
                      )}
                    </div>
                  )}

                  <textarea
                    ref={textareaRef}
                    value={inputValue}
                    onChange={handleTextareaChange}
                    onKeyDown={handleKeyDown}
                    placeholder="输入消息，Ctrl+Enter 换行"
                    className={cn(
                      'min-h-[96px] w-full resize-none border-0 bg-transparent py-3 text-sm leading-6 placeholder:text-gray-400 focus:outline-none',
                      isAutoFilled ? 'text-transparent' : 'text-gray-900',
                    )}
                    rows={4}
                    style={{ maxHeight: '160px' }}
                  />
                </div>
                <div className="flex shrink-0 items-center gap-2">
                  <button
                    onClick={handleVoiceInput}
                    className={cn(
                      'flex h-10 w-10 items-center justify-center rounded-lg border transition-colors',
                      isVoiceListening
                        ? 'border-red-100 bg-red-50 text-red-500 hover:bg-red-100'
                        : 'border-[#e5e7eb] text-gray-400 hover:bg-[#f3f4f6] hover:text-gray-600',
                      !isVoiceSupported && 'cursor-not-allowed opacity-50',
                    )}
                    title={isVoiceSupported ? (isVoiceListening ? '停止语音输入' : '语音输入') : '当前浏览器不支持语音输入'}
                    disabled={!isVoiceSupported}
                  >
                    {isVoiceListening ? <RiMicFill className="h-4 w-4" /> : <RiMicLine className="h-4 w-4" />}
                  </button>
                  <button
                    onClick={handleSend}
                    disabled={!inputValue.trim() || isLoading}
                    className={cn(
                      'rounded-lg px-4 py-2 text-sm font-medium transition-colors',
                      inputValue.trim() && !isLoading
                        ? 'bg-[#3b82f6] text-white hover:bg-[#2563eb]'
                        : 'cursor-not-allowed bg-gray-100 text-gray-400',
                    )}
                  >
                    发送回复
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>

        {renameConversationId && (
          <div className="absolute inset-0 z-[60] flex items-center justify-center bg-[rgba(17,24,39,0.35)] px-4">
            <div className="w-full max-w-md rounded-2xl border border-[#e5e7eb] bg-white p-6 shadow-xl">
              <div className="mb-4">
                <h3 className="text-lg font-semibold text-[#111827]">重命名对话</h3>
                <p className="mt-1 text-sm text-[#4b5563]">使用更清晰的标题，方便后续搜索与归档。</p>
              </div>
              <input
                value={renameDraft}
                onChange={e => setRenameDraft(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter')
                    handleConfirmRenameConversation()
                  if (e.key === 'Escape') {
                    setRenameConversationId(null)
                    setRenameDraft('')
                  }
                }}
                placeholder="请输入新的对话标题"
                className="w-full rounded-lg border border-[#d1d5db] px-4 py-3 text-sm text-[#111827] focus:border-transparent focus:outline-none focus:ring-2 focus:ring-[#3b82f6]"
                autoFocus
              />
              <div className="mt-5 flex justify-end gap-3">
                <button
                  onClick={() => {
                    setRenameConversationId(null)
                    setRenameDraft('')
                  }}
                  className="rounded-lg border border-[#d1d5db] px-4 py-2 text-sm text-[#4b5563] transition-colors hover:bg-[#f3f4f6]"
                >
                  取消
                </button>
                <button
                  onClick={handleConfirmRenameConversation}
                  disabled={!renameDraft.trim()}
                  className={cn(
                    'rounded-lg px-4 py-2 text-sm font-medium text-white transition-colors',
                    renameDraft.trim() ? 'bg-[#3b82f6] hover:bg-[#2563eb]' : 'cursor-not-allowed bg-gray-300',
                  )}
                >
                  保存
                </button>
              </div>
            </div>
          </div>
        )}

        <SandboxFilePicker
          open={showSandboxPicker}
          onClose={() => setShowSandboxPicker(false)}
          onSelect={handleSandboxFilesSelected}
          accept=".txt,.md,.pdf,.doc,.docx,.xls,.xlsx,.ppt,.pptx,.jpg,.jpeg,.png,.gif,.csv,.json"
          multiple={true}
        />
      </div>
    </div>
  )
}

export default ChatPage
