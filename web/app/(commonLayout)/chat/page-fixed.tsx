'use client'

import { useState, useRef, useEffect } from 'react'
import { RiSendPlaneLine, RiAttachmentLine, RiMicLine, RiAddLine, RiDeleteBinLine, RiSearchLine, RiMoreLine, RiArrowDownSLine, RiCheckLine } from '@remixicon/react'
import { cn } from '@/utils/classnames'
import { ModelTypeEnum } from '@/app/components/header/account-setting/model-provider-page/declarations'
import { useModelList, useDefaultModel } from '@/app/components/header/account-setting/model-provider-page/hooks'

interface Message {
  id: string
  type: 'user' | 'assistant'
  content: string
  timestamp: Date
}

interface Conversation {
  id: string
  title: string
  lastMessage: string
  timestamp: Date
  messages: Message[]
}

interface SelectedModel {
  provider: string
  model: string
  label: string
}

// 格式化时间戳
function formatTimestamp(date: Date): string {
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  const minutes = Math.floor(diff / 60000)
  const hours = Math.floor(diff / 3600000)
  const days = Math.floor(diff / 86400000)

  if (minutes < 1) return '刚刚'
  if (minutes < 60) return `${minutes}分钟前`
  if (hours < 24) return `${hours}小时前`
  if (days < 7) return `${days}天前`
  
  return date.toLocaleDateString('zh-CN', { month: 'numeric', day: 'numeric' })
}

const ChatPage = () => {
  const [conversations, setConversations] = useState<Conversation[]>([])
  const [currentConversationId, setCurrentConversationId] = useState<string | null>(null)
  const [messages, setMessages] = useState<Message[]>([])
  const [inputValue, setInputValue] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const [showModelSelector, setShowModelSelector] = useState(false)
  const modelSelectorRef = useRef<HTMLDivElement>(null)
  const [selectedModel, setSelectedModel] = useState<SelectedModel | null>(null)

  // 本地存储的 key
  const STORAGE_KEY = 'cheersai_conversations'

  // 从本地存储加载对话
  useEffect(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY)
      if (stored) {
        const parsed = JSON.parse(stored)
        // 恢复 Date 对象
        const restored = parsed.map((conv: any) => ({
          ...conv,
          timestamp: new Date(conv.timestamp),
          messages: conv.messages.map((msg: any) => ({
            ...msg,
            timestamp: new Date(msg.timestamp),
          })),
        }))
        setConversations(restored)
        console.log('✅ 已从本地存储加载对话:', restored.length, '条')
      }
    } catch (error) {
      console.error('❌ 加载本地对话失败:', error)
    }
  }, [])

  // 保存对话到本地存储
  useEffect(() => {
    if (conversations.length > 0) {
      try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(conversations))
        console.log('💾 已保存对话到本地存储:', conversations.length, '条')
      } catch (error) {
        console.error('❌ 保存对话到本地存储失败:', error)
      }
    }
  }, [conversations])

  // 获取模型列表
  const { data: modelListData, isLoading: isModelListLoading } = useModelList(ModelTypeEnum.textGeneration)
  const { data: defaultModelData } = useDefaultModel(ModelTypeEnum.textGeneration)
  
  // 调试信息
  useEffect(() => {
    console.log('模型数据调试:', {
      modelListData,
      defaultModelData,
      isModelListLoading,
      modelListLength: modelListData?.length || 0
    })
    
    if (!isModelListLoading && (!modelListData || modelListData.length === 0) && !selectedModel) {
      console.log('没有检测到配置的模型，使用Ollama模型')
      setSelectedModel({
        provider: 'ollama',
        model: 'qwen2.5:1.5b',
        label: 'Qwen2.5 1.5B (Ollama)',
      })
    }
  }, [modelListData, defaultModelData, isModelListLoading, selectedModel])

  // 初始化选中的模型
  useEffect(() => {
    if (defaultModelData && modelListData && !selectedModel) {
      const defaultProvider = modelListData.find(provider => provider.provider === defaultModelData.provider.provider)
      const defaultModel = defaultProvider?.models.find(model => model.model === defaultModelData.model)
      
      if (defaultProvider && defaultModel) {
        setSelectedModel({
          provider: defaultProvider.provider,
          model: defaultModel.model,
          label: defaultModel.label?.zh_Hans || defaultModel.label?.en_US || defaultModel.model,
        })
      }
    }
  }, [defaultModelData, modelListData, selectedModel])

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

  // 切换对话时更新消息
  useEffect(() => {
    const conversation = conversations.find(c => c.id === currentConversationId)
    if (conversation) {
      setMessages(conversation.messages)
      console.log('📝 切换到对话:', conversation.title, '消息数:', conversation.messages.length)
    }
  }, [currentConversationId, conversations])

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
    console.log('➕ 创建新对话:', newConversation.id)
  }

  const handleDeleteConversation = (id: string) => {
    setConversations(prev => prev.filter(c => c.id !== id))
    if (currentConversationId === id) {
      const remainingConversations = conversations.filter(c => c.id !== id)
      if (remainingConversations.length > 0) {
        setCurrentConversationId(remainingConversations[0].id)
      } else {
        setCurrentConversationId(null)
        setMessages([])
      }
    }
    console.log('🗑️ 删除对话:', id)
  }

  const handleSelectConversation = (id: string) => {
    setCurrentConversationId(id)
  }

  const handleSelectModel = (provider: string, model: string, label: string) => {
    setSelectedModel({ provider, model, label })
    setShowModelSelector(false)
    console.log('🤖 选择模型:', label)
  }

  const handleSend = async () => {
    if (!inputValue.trim() || isLoading) return

    const userMessage: Message = {
      id: Date.now().toString(),
      type: 'user',
      content: inputValue.trim(),
      timestamp: new Date(),
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
      console.log('🆕 创建新对话并发送消息:', conversationId)
    } else {
      // 更新现有对话
      const updatedMessages = [...messages, userMessage]
      setMessages(updatedMessages)
      
      setConversations(prev => prev.map(conv => {
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
      console.log('💬 在现有对话中发送消息:', conversationId)
    }

    setInputValue('')
    setIsLoading(true)

    try {
      const modelToUse = selectedModel?.model || 'qwen2.5:1.5b'
      
      console.log('📤 发送请求到 Ollama:', { model: modelToUse, prompt: userMessage.content.slice(0, 50) + '...' })
      
      const response = await fetch('http://localhost:11434/api/generate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          model: modelToUse,
          prompt: userMessage.content,
          stream: false,
        }),
      })

      if (!response.ok) {
        throw new Error(`Ollama API error: ${response.status}`)
      }

      const data = await response.json()
      console.log('📥 收到 Ollama 响应，长度:', data.response?.length || 0)
      
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: 'assistant',
        content: data.response || '抱歉，我无法生成回复。',
        timestamp: new Date(),
      }
      
      // 更新消息列表
      setMessages(prev => [...prev, assistantMessage])
      
      // 更新对话记录
      setConversations(prev => prev.map(conv => {
        if (conv.id === conversationId) {
          return {
            ...conv,
            lastMessage: assistantMessage.content.slice(0, 50),
            timestamp: new Date(),
            messages: [...conv.messages, userMessage, assistantMessage],
          }
        }
        return conv
      }))
      
      console.log('✅ 消息已添加到对话，当前消息数:', messages.length + 2)
      
    } catch (error) {
      console.error('❌ Ollama API调用失败:', error)
      
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: 'assistant',
        content: `连接Ollama失败: ${error instanceof Error ? error.message : '未知错误'}。请确保Ollama服务正在运行。`,
        timestamp: new Date(),
      }
      
      setMessages(prev => [...prev, errorMessage])
      
      setConversations(prev => prev.map(conv => {
        if (conv.id === conversationId) {
          return {
            ...conv,
            lastMessage: errorMessage.content.slice(0, 50),
            timestamp: new Date(),
            messages: [...conv.messages, userMessage, errorMessage],
          }
        }
        return conv
      }))
    } finally {
      setIsLoading(false)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const handleTextareaChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInputValue(e.target.value)
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`
    }
  }

  return (
    <div className="flex h-full bg-white">
      {/* 侧边栏 - 历史对话 */}
      <div className="flex w-80 flex-col bg-gray-50 border-r border-gray-200">
        {/* 侧边栏头部 */}
        <div className="flex items-center justify-between px-4 py-4 border-b border-gray-200">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-green-500 rounded-lg flex items-center justify-center">
              <span className="text-white text-sm font-medium">AI</span>
            </div>
            <span className="text-gray-900 font-medium">CheersAI行业版</span>
          </div>
          <button
            onClick={handleNewConversation}
            className="flex h-8 w-8 items-center justify-center rounded-lg bg-blue-500 text-white hover:bg-blue-600 transition-colors"
            title="新建对话"
          >
            <RiAddLine className="h-4 w-4" />
          </button>
        </div>

        {/* 搜索框 */}
        <div className="px-4 py-3 border-b border-gray-200">
          <div className="relative">
            <RiSearchLine className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
            <input
              type="text"
              placeholder="搜索对话..."
              className="w-full pl-10 pr-4 py-2 text-sm bg-white border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
        </div>

        {/* 对话列表 */}
        <div className="flex-1 overflow-y-auto">
          {conversations.length === 0 ? (
            <div className="p-4 text-center text-gray-500 text-sm">
              暂无对话记录
            </div>
          ) : (
            conversations.map((conversation) => (
              <div
                key={conversation.id}
                onClick={() => handleSelectConversation(conversation.id)}
                className={cn(
                  'group relative cursor-pointer px-4 py-3 transition-colors hover:bg-white',
                  currentConversationId === conversation.id && 'bg-white border-r-2 border-blue-500'
                )}
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="flex-1 overflow-hidden">
                    <h3 className="truncate text-sm font-medium text-gray-900 mb-1">
                      {conversation.title}
                    </h3>
                    <p className="truncate text-xs text-gray-500 mb-1">
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
                    className="opacity-0 group-hover:opacity-100 flex h-6 w-6 items-center justify-center rounded text-gray-400 hover:bg-gray-100 hover:text-gray-600 transition-all"
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

      {/* 主聊天区域 - 其余部分保持不变 */}
      {/* ... 省略其余UI代码，与原文件相同 ... */}
    </div>
  )
}

export default ChatPage
