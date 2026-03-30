'use client'

import { RiAddLine, RiArrowDownSLine, RiAttachmentLine, RiCheckLine, RiCloseLine, RiDeleteBinLine, RiDownloadLine, RiFileCopyLine, RiMenuLine, RiMicLine, RiMoreLine, RiRefreshLine, RiSearchLine } from '@remixicon/react'
import { useEffect, useMemo, useRef, useState } from 'react'
import { Markdown } from '@/app/components/base/markdown'
import { SandboxFilePicker } from '@/app/components/base/sandbox-file-picker'
import Toast from '@/app/components/base/toast'
import { ModelTypeEnum } from '@/app/components/header/account-setting/model-provider-page/declarations'
import { useDefaultModel, useModelList } from '@/app/components/header/account-setting/model-provider-page/hooks'
import { sendSimpleChatMessage } from '@/service/chat'
import { cn } from '@/utils/classnames'

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
  const STORAGE_KEY = 'cheersai_conversations'
  const SIDEBAR_STORAGE_KEY = 'cheersai_sidebar_collapsed'

  const [conversations, setConversations] = useState<Conversation[]>(() => getInitialConversations(STORAGE_KEY))
  const [currentConversationId, setCurrentConversationId] = useState<string | null>(null)
  const [messages, setMessages] = useState<Message[]>([])
  const [inputValue, setInputValue] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const [showModelSelector, setShowModelSelector] = useState(false)
  const modelSelectorRef = useRef<HTMLDivElement>(null)

  // 选中的模型状态 - 移到前面声明
  const [selectedModel, setSelectedModel] = useState<SelectedModel | null>(null)
  const [uploadedFiles, setUploadedFiles] = useState<UploadedFile[]>([])
  const [showSandboxPicker, setShowSandboxPicker] = useState(false)
  const [sidebarCollapsed, setSidebarCollapsed] = useState(() => getInitialSidebarCollapsed(SIDEBAR_STORAGE_KEY))
  const [streamingMessageId, setStreamingMessageId] = useState<string | null>(null)
  const [isAutoFilled, setIsAutoFilled] = useState(false)
  const [autoFilledText, setAutoFilledText] = useState('')

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
    if (conversations.length > 0) {
      try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(conversations))
      }
      catch {
        // 保存对话到本地存储失败，忽略错误
      }
    }
  }, [conversations])

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
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => {
      document.removeEventListener('mousedown', handleClickOutside)
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
    setSidebarCollapsed(!sidebarCollapsed)
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

  return (
    <div className="flex h-full bg-white">
      {/* 侧边栏 - 历史对话 */}
      <div className={cn(
        'flex flex-col border-r border-gray-200 bg-gray-50 transition-all duration-300 ease-in-out',
        sidebarCollapsed ? 'w-0 overflow-hidden' : 'w-80',
      )}
      >
        {/* 侧边栏头部 */}
        <div className="flex items-center justify-between border-b border-gray-200 px-4 py-4">
          <div className="flex items-center gap-3">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-green-500">
              <span className="text-sm font-medium text-white">AI</span>
            </div>
            <span className="font-medium text-gray-900">CheersAI行业版</span>
          </div>
          <button
            onClick={handleNewConversation}
            className="flex h-8 w-8 items-center justify-center rounded-lg bg-blue-500 text-white transition-colors hover:bg-blue-600"
            title="新建对话"
          >
            <RiAddLine className="h-4 w-4" />
          </button>
        </div>

        {/* 搜索框 */}
        <div className="border-b border-gray-200 px-4 py-3">
          <div className="relative">
            <RiSearchLine className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
            <input
              type="text"
              placeholder="搜索对话..."
              className="w-full rounded-lg border border-gray-200 bg-white py-2 pl-10 pr-4 text-sm focus:border-transparent focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>

        {/* 对话列表 */}
        <div className="flex-1 overflow-y-auto">
          {conversations.length === 0
            ? (
                <div className="p-4 text-center text-sm text-gray-500">
                  暂无对话记录
                </div>
              )
            : (
                conversations.map(conversation => (
                  <div
                    key={conversation.id}
                    onClick={() => handleSelectConversation(conversation.id)}
                    className={cn(
                      'group relative cursor-pointer px-4 py-3 transition-colors hover:bg-white',
                      currentConversationId === conversation.id && 'border-r-2 border-blue-500 bg-white',
                    )}
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex-1 overflow-hidden">
                        <h3 className="mb-1 truncate text-sm font-medium text-gray-900">
                          {conversation.title}
                        </h3>
                        <p className="mb-1 truncate text-xs text-gray-500">
                          {conversation.lastMessage || '暂无消息'}
                        </p>
                        <p className="text-xs text-gray-400">
                          {formatTimestamp(conversation.timestamp)}
                        </p>
                      </div>
                      <button
                        onClick={(e) => {
                          e.stopPropagation()
                          handleDeleteConversation(conversation.id)
                        }}
                        className="flex h-6 w-6 items-center justify-center rounded text-gray-400 opacity-0 transition-all hover:bg-gray-100 hover:text-gray-600 group-hover:opacity-100"
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

      {/* 主聊天区域 */}
      <div className="flex flex-1 flex-col">
        {/* 头部 */}
        <div className="flex items-center justify-between border-b border-gray-200 bg-white px-6 py-4">
          <div className="flex items-center gap-3">
            {/* 折叠按钮 */}
            <button
              onClick={toggleSidebar}
              className="flex h-8 w-8 items-center justify-center rounded-lg text-gray-500 transition-colors hover:bg-gray-100 hover:text-gray-700"
              title={sidebarCollapsed ? '展开侧边栏' : '折叠侧边栏'}
            >
              {sidebarCollapsed
                ? (
                    <RiMenuLine className="h-4 w-4" />
                  )
                : (
                    <RiCloseLine className="h-4 w-4" />
                  )}
            </button>
            <h1 className="text-lg font-medium text-gray-900">
              {currentConversationId
                ? conversations.find(c => c.id === currentConversationId)?.title || 'Python数据分析脚本'
                : 'Python数据分析脚本'}
            </h1>
            <span className="rounded bg-gray-100 px-2 py-1 text-xs text-gray-600">
              草稿
            </span>
            <span className="rounded bg-gray-100 px-2 py-1 text-xs text-gray-600">
              自动
            </span>
          </div>
          <div className="flex items-center gap-3">
            {/* 模型选择器 */}
            <div className="relative" ref={modelSelectorRef}>
              <button
                onClick={() => setShowModelSelector(!showModelSelector)}
                className="flex items-center gap-2 rounded-lg border border-gray-200 bg-gray-50 px-3 py-2 text-sm transition-colors hover:bg-gray-100"
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
                                    想要更多模型？
                                  </div>
                                  <button
                                    onClick={() => {
                                      window.open('/apps/?action=showSettings&tab=provider', '_blank')
                                    }}
                                    className="rounded bg-blue-500 px-3 py-1.5 text-xs text-white transition-colors hover:bg-blue-600"
                                  >
                                    配置更多提供商
                                  </button>
                                </div>
                              </div>
                            )
                          : (
                              modelListData.map((provider) => {
                                const activeModels = provider.models?.filter(model => model.status === 'active') || []

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

            <button className="flex h-8 w-8 items-center justify-center rounded-lg text-gray-400 hover:bg-gray-100 hover:text-gray-600">
              <RiMoreLine className="h-4 w-4" />
            </button>
          </div>
        </div>

        {/* 消息区域 */}
        <div className="flex-1 overflow-y-auto bg-white">
          <div className="mx-auto max-w-4xl px-6 py-6">
            {messages.length === 0 && !currentConversationId
              ? (
                  <div className="flex h-full items-center justify-center">
                    <div className="text-center">
                      <div className="mx-auto mb-6 flex h-16 w-16 items-center justify-center rounded-full bg-blue-500">
                        <span className="text-xl font-bold text-white">AI</span>
                      </div>
                      <h3 className="mb-3 text-xl font-medium text-gray-900">
                        欢迎使用 CheersAI Desktop
                      </h3>
                      <p className="mb-6 text-gray-500">
                        我是您的AI助手，可以帮助您进行数据分析、编程和各种问题解答
                      </p>
                      <div className="flex flex-wrap justify-center gap-2">
                        <button
                          onClick={() => {
                            const text = '请帮我进行数据分析'
                            setInputValue(text)
                            setIsAutoFilled(true)
                            setAutoFilledText(text)
                          }}
                          className="rounded-lg border border-blue-200 bg-blue-50 px-4 py-2 text-sm text-blue-600 transition-colors hover:bg-blue-100"
                        >
                          数据分析
                        </button>
                        <button
                          onClick={() => {
                            const text = '请帮我编写代码'
                            setInputValue(text)
                            setIsAutoFilled(true)
                            setAutoFilledText(text)
                          }}
                          className="rounded-lg border border-blue-200 bg-blue-50 px-4 py-2 text-sm text-blue-600 transition-colors hover:bg-blue-100"
                        >
                          代码编写
                        </button>
                        <button
                          onClick={() => {
                            const text = '我有问题需要解答'
                            setInputValue(text)
                            setIsAutoFilled(true)
                            setAutoFilledText(text)
                          }}
                          className="rounded-lg border border-blue-200 bg-blue-50 px-4 py-2 text-sm text-blue-600 transition-colors hover:bg-blue-100"
                        >
                          问题解答
                        </button>
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
                          <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-green-500">
                            <span className="text-sm font-medium text-white">AI</span>
                          </div>
                        )}
                        <div
                          className={cn(
                            'group max-w-[70%] rounded-2xl px-4 py-3',
                            message.type === 'user'
                              ? 'bg-blue-600 text-white'
                              : 'border border-gray-300 bg-gray-100 text-gray-900',
                          )}
                        >
                          {/* 文件显示 */}
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
                                      message.type === 'user' ? 'text-gray-800' : 'text-gray-900',
                                    )}
                                    >
                                      {file.name}
                                    </div>
                                    <div className={cn(
                                      'text-xs',
                                      message.type === 'user' ? 'text-gray-600' : 'text-gray-500',
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

                          {/* 消息内容 */}
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

                            {/* AI消息操作按钮 */}
                            {message.type === 'assistant' && message.content && !isLoading && (
                              <div className="flex items-center gap-1 opacity-0 transition-opacity group-hover:opacity-100">
                                <button
                                  onClick={() => handleCopyMessage(message.content)}
                                  className="flex h-6 w-6 items-center justify-center rounded text-gray-400 transition-colors hover:bg-gray-100 hover:text-gray-600"
                                  title="复制"
                                >
                                  <RiFileCopyLine className="h-3.5 w-3.5" />
                                </button>
                                <button
                                  onClick={() => handleDownloadMessage(message.content, message.id)}
                                  className="flex h-6 w-6 items-center justify-center rounded text-gray-400 transition-colors hover:bg-gray-100 hover:text-gray-600"
                                  title="下载"
                                >
                                  <RiDownloadLine className="h-3.5 w-3.5" />
                                </button>
                                <button
                                  onClick={() => {
                                    const messageIndex = messages.findIndex(m => m.id === message.id)
                                    if (messageIndex > 0) {
                                      handleRegenerateMessage(messageIndex)
                                    }
                                  }}
                                  className="flex h-6 w-6 items-center justify-center rounded text-gray-400 transition-colors hover:bg-gray-100 hover:text-gray-600"
                                  title="重新生成"
                                >
                                  <RiRefreshLine className="h-3.5 w-3.5" />
                                </button>
                              </div>
                            )}
                          </div>
                        </div>
                        {message.type === 'user' && (
                          <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-blue-600">
                            <span className="text-sm font-medium text-white">我</span>
                          </div>
                        )}
                      </div>
                    ))}
                    {isLoading && (
                      <div className="mb-6 flex justify-start gap-4">
                        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-green-500">
                          <span className="text-sm font-medium text-white">AI</span>
                        </div>
                        <div className="max-w-[70%] rounded-2xl border border-gray-300 bg-gray-100 px-4 py-3">
                          <div className="flex items-center gap-2">
                            <div className="flex space-x-1">
                              <div className="h-2 w-2 animate-bounce rounded-full bg-gray-400 [animation-delay:-0.3s]"></div>
                              <div className="h-2 w-2 animate-bounce rounded-full bg-gray-400 [animation-delay:-0.15s]"></div>
                              <div className="h-2 w-2 animate-bounce rounded-full bg-gray-400"></div>
                            </div>
                            <span className="text-sm text-gray-700">正在思考...</span>
                          </div>
                        </div>
                      </div>
                    )}
                  </>
                )}
            <div ref={messagesEndRef} />
          </div>
        </div>

        {/* 输入区域 */}
        <div className="border-t border-gray-200 bg-white px-6 py-4">
          <div className="mx-auto max-w-4xl">
            {/* 已上传文件列表 */}
            {uploadedFiles.length > 0 && (
              <div className="mb-3 rounded-lg bg-gray-50 p-3">
                <div className="mb-2 text-sm text-gray-600">
                  已选择文件 (
                  {uploadedFiles.length}
                  )
                </div>
                <div className="space-y-2">
                  {uploadedFiles.map(file => (
                    <div key={file.id} className="flex items-center justify-between rounded border bg-white p-2">
                      <div className="flex items-center gap-2">
                        <div className="flex h-8 w-8 items-center justify-center rounded bg-blue-100">
                          <span className="text-xs font-medium text-blue-600">
                            {file.name.split('.').pop()?.toUpperCase()}
                          </span>
                        </div>
                        <div>
                          <div className="text-sm font-medium text-gray-900">{file.name}</div>
                          <div className="text-xs text-gray-500">
                            {formatFileSize(file.size)}
                            <span className="ml-2 rounded bg-green-100 px-1.5 py-0.5 text-xs text-green-700">
                              沙箱文件
                            </span>
                          </div>
                        </div>
                      </div>
                      <button
                        onClick={() => handleRemoveFile(file.id)}
                        className="text-gray-400 transition-colors hover:text-red-500"
                        title="移除文件"
                      >
                        <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                        </svg>
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* 警告提示 */}
            <div className="mb-4 rounded-lg border border-blue-200 bg-blue-50 p-3">
              <p className="text-sm text-blue-800">
                <span className="font-medium">安全模式：</span>
                仅可选择沙箱内的脱敏文件。系统将自动记录并脱敏输入内容中的个人身份信息。
              </p>
            </div>

            <div className="relative flex items-center gap-3 rounded-xl border border-gray-200 bg-white p-3 focus-within:border-blue-500 focus-within:ring-1 focus-within:ring-blue-500">
              {/* 文件选择按钮 */}
              <button
                onClick={handleAttachmentClick}
                className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg text-gray-400 transition-colors hover:bg-gray-100 hover:text-gray-600"
                title="从沙箱选择文件"
              >
                <RiAttachmentLine className="h-4 w-4" />
              </button>

              {/* 输入框容器 */}
              <div className="relative flex min-h-[32px] flex-1 items-center">
                {/* 自动填充文字的背景层 */}
                {isAutoFilled && autoFilledText && (
                  <div className="pointer-events-none absolute inset-0 z-10 flex items-center">
                    <span className="rounded-md border border-blue-200 bg-blue-50 px-2 py-1 text-sm text-blue-600">
                      {autoFilledText}
                    </span>
                    {inputValue.length > autoFilledText.length && (
                      <span className="ml-1 text-sm text-gray-900">
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
                    'w-full resize-none border-0 bg-transparent py-1 text-sm leading-6 placeholder:text-gray-400 focus:outline-none',
                    isAutoFilled ? 'text-transparent' : 'text-gray-900',
                  )}
                  rows={1}
                  style={{ maxHeight: '120px' }}
                />
              </div>
              <div className="flex shrink-0 items-center gap-2">
                <button className="flex h-8 w-8 items-center justify-center rounded-lg text-gray-400 transition-colors hover:bg-gray-100 hover:text-gray-600">
                  <RiMicLine className="h-4 w-4" />
                </button>
                <button
                  onClick={handleSend}
                  disabled={!inputValue.trim() || isLoading}
                  className={cn(
                    'rounded-lg px-4 py-2 text-sm font-medium transition-colors',
                    inputValue.trim() && !isLoading
                      ? 'bg-green-500 text-white hover:bg-green-600'
                      : 'cursor-not-allowed bg-gray-100 text-gray-400',
                  )}
                >
                  发送回复
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* 沙箱文件选择器 */}
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
