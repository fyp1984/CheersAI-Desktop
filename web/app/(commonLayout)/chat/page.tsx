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

  // 选中的模型状态 - 移到前面声明
  const [selectedModel, setSelectedModel] = useState<SelectedModel | null>(null)

  // 获取模型列表 - 使用更简单的方法
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
    
    // 如果没有模型数据，设置Ollama模型作为默认选项
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
  }

  const handleSelectConversation = (id: string) => {
    setCurrentConversationId(id)
  }

  const handleSelectModel = (provider: string, model: string, label: string) => {
    setSelectedModel({ provider, model, label })
    setShowModelSelector(false)
  }

  const handleSend = async () => {
    if (!inputValue.trim() || isLoading) return

    const userMessage: Message = {
      id: Date.now().toString(),
      type: 'user',
      content: inputValue.trim(),
      timestamp: new Date(),
    }

    // 如果没有当前对话，创建一个新对话
    if (!currentConversationId) {
      const newConversation: Conversation = {
        id: Date.now().toString(),
        title: userMessage.content.slice(0, 20),
        lastMessage: userMessage.content,
        timestamp: new Date(),
        messages: [userMessage],
      }
      setConversations(prev => [newConversation, ...prev])
      setCurrentConversationId(newConversation.id)
      setMessages([userMessage])
    } else {
      const updatedMessages = [...messages, userMessage]
      setMessages(updatedMessages)
      
      // 更新当前对话
      setConversations(prev => prev.map(conv => {
        if (conv.id === currentConversationId) {
          // 如果是第一条用户消息，更新标题
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
    setIsLoading(true)

    try {
      // 使用选中的模型或默认模型
      const modelToUse = selectedModel?.model || 'qwen2.5:1.5b'
      
      // 调用Ollama API
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
      
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: 'assistant',
        content: data.response || '抱歉，我无法生成回复。',
        timestamp: new Date(),
      }
      
      setMessages(prev => [...prev, assistantMessage])
      
      // 更新对话记录
      setConversations(prev => prev.map(conv => {
        if (conv.id === currentConversationId) {
          return {
            ...conv,
            lastMessage: assistantMessage.content,
            timestamp: new Date(),
            messages: [...(conv.messages || []), userMessage, assistantMessage],
          }
        }
        return conv
      }))
      
    } catch (error) {
      console.error('Ollama API调用失败:', error)
      
      // 显示错误消息
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: 'assistant',
        content: `连接Ollama失败: ${error instanceof Error ? error.message : '未知错误'}。请确保Ollama服务正在运行。`,
        timestamp: new Date(),
      }
      
      setMessages(prev => [...prev, errorMessage])
      
      // 更新对话记录
      setConversations(prev => prev.map(conv => {
        if (conv.id === currentConversationId) {
          return {
            ...conv,
            lastMessage: errorMessage.content,
            timestamp: new Date(),
            messages: [...(conv.messages || []), userMessage, errorMessage],
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
    // 自动调整高度
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

      {/* 主聊天区域 */}
      <div className="flex flex-1 flex-col">
        {/* 头部 */}
        <div className="flex items-center justify-between bg-white px-6 py-4 border-b border-gray-200">
          <div className="flex items-center gap-3">
            <h1 className="text-lg font-medium text-gray-900">
              {currentConversationId 
                ? conversations.find(c => c.id === currentConversationId)?.title || 'Python数据分析脚本'
                : 'Python数据分析脚本'
              }
            </h1>
            <span className="px-2 py-1 text-xs bg-gray-100 text-gray-600 rounded">
              草稿
            </span>
            <span className="px-2 py-1 text-xs bg-gray-100 text-gray-600 rounded">
              自动
            </span>
          </div>
          <div className="flex items-center gap-3">
            {/* 模型选择器 */}
            <div className="relative" ref={modelSelectorRef}>
              <button
                onClick={() => setShowModelSelector(!showModelSelector)}
                className="flex items-center gap-2 px-3 py-2 text-sm bg-gray-50 border border-gray-200 rounded-lg hover:bg-gray-100 transition-colors"
              >
                <span className="text-gray-700">
                  {selectedModel?.label || '选择模型'}
                </span>
                <RiArrowDownSLine className={cn(
                  "h-4 w-4 text-gray-500 transition-transform",
                  showModelSelector && "rotate-180"
                )} />
              </button>
              
              {showModelSelector && (
                <div className="absolute right-0 top-full mt-1 w-80 bg-white border border-gray-200 rounded-lg shadow-lg z-50 max-h-96 overflow-y-auto">
                  <div className="p-3 border-b border-gray-100">
                    <h3 className="text-sm font-medium text-gray-900">选择模型</h3>
                  </div>
                  <div className="py-2">
                    {isModelListLoading ? (
                      <div className="px-3 py-4 text-center text-gray-500 text-sm">
                        加载模型中...
                      </div>
                    ) : !modelListData || modelListData.length === 0 ? (
                      <div className="px-3 py-4">
                        <div className="text-gray-500 text-sm mb-3">
                          使用本地Ollama模型
                        </div>
                        <div className="space-y-1">
                          <button
                            onClick={() => handleSelectModel('ollama', 'qwen2.5:1.5b', 'Qwen2.5 1.5B (Ollama)')}
                            className={cn(
                              "w-full flex items-center justify-between px-3 py-2 text-sm text-left hover:bg-gray-50 transition-colors rounded",
                              selectedModel?.model === 'qwen2.5:1.5b' && "bg-blue-50 text-blue-700"
                            )}
                          >
                            <div className="flex flex-col">
                              <span className="font-medium">Qwen2.5 1.5B</span>
                              <span className="text-xs text-gray-500">本地Ollama模型 - 轻量级</span>
                            </div>
                            {selectedModel?.model === 'qwen2.5:1.5b' && (
                              <RiCheckLine className="h-4 w-4 text-blue-600" />
                            )}
                          </button>
                          <button
                            onClick={() => handleSelectModel('ollama', 'qwen3-coder:30b', 'Qwen3 Coder 30B (Ollama)')}
                            className={cn(
                              "w-full flex items-center justify-between px-3 py-2 text-sm text-left hover:bg-gray-50 transition-colors rounded",
                              selectedModel?.model === 'qwen3-coder:30b' && "bg-blue-50 text-blue-700"
                            )}
                          >
                            <div className="flex flex-col">
                              <span className="font-medium">Qwen3 Coder 30B</span>
                              <span className="text-xs text-gray-500">本地Ollama模型 - 代码专用</span>
                            </div>
                            {selectedModel?.model === 'qwen3-coder:30b' && (
                              <RiCheckLine className="h-4 w-4 text-blue-600" />
                            )}
                          </button>
                        </div>
                        <div className="mt-3 pt-3 border-t border-gray-100">
                          <div className="text-xs text-gray-400 mb-2">
                            想要更多模型？
                          </div>
                          <button
                            onClick={() => {
                              window.open('/account/model-provider', '_blank')
                            }}
                            className="px-3 py-1.5 text-xs bg-blue-500 text-white rounded hover:bg-blue-600 transition-colors"
                          >
                            配置更多提供商
                          </button>
                        </div>
                      </div>
                    ) : (
                      modelListData.map((provider) => {
                        const activeModels = provider.models?.filter(model => model.status === 'active') || []
                        
                        if (activeModels.length === 0) return null
                        
                        return (
                          <div key={provider.provider} className="mb-2">
                            <div className="px-3 py-1 text-xs font-medium text-gray-500 uppercase tracking-wide">
                              {provider.label?.zh_Hans || provider.label?.en_US || provider.provider}
                            </div>
                            {activeModels.map((model) => {
                              const isSelected = selectedModel?.provider === provider.provider && selectedModel?.model === model.model
                              const modelLabel = model.label?.zh_Hans || model.label?.en_US || model.model
                              
                              return (
                                <button
                                  key={`${provider.provider}-${model.model}`}
                                  onClick={() => handleSelectModel(provider.provider, model.model, modelLabel)}
                                  className={cn(
                                    "w-full flex items-center justify-between px-3 py-2 text-sm text-left hover:bg-gray-50 transition-colors",
                                    isSelected && "bg-blue-50 text-blue-700"
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
          <div className="max-w-4xl mx-auto px-6 py-6">
            {messages.length === 0 && !currentConversationId ? (
              <div className="flex h-full items-center justify-center">
                <div className="text-center">
                  <div className="mx-auto mb-6 flex h-16 w-16 items-center justify-center rounded-full bg-blue-500">
                    <span className="text-xl font-bold text-white">AI</span>
                  </div>
                  <h3 className="mb-3 text-xl font-medium text-gray-900">
                    欢迎使用 CheersAI Desktop
                  </h3>
                  <p className="text-gray-500 mb-6">
                    我是您的AI助手，可以帮助您进行数据分析、编程和各种问题解答
                  </p>
                  <div className="flex flex-wrap gap-2 justify-center">
                    <button className="px-4 py-2 text-sm bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors">
                      数据分析
                    </button>
                    <button className="px-4 py-2 text-sm bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors">
                      代码编写
                    </button>
                    <button className="px-4 py-2 text-sm bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors">
                      问题解答
                    </button>
                  </div>
                </div>
              </div>
            ) : (
              <>
                {messages.map((message) => (
                  <div
                    key={message.id}
                    className={cn(
                      'flex gap-4 mb-6',
                      message.type === 'user' ? 'justify-end' : 'justify-start'
                    )}
                  >
                    {message.type === 'assistant' && (
                      <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-green-500">
                        <span className="text-sm font-medium text-white">AI</span>
                      </div>
                    )}
                    <div
                      className={cn(
                        'max-w-[70%] rounded-2xl px-4 py-3',
                        message.type === 'user'
                          ? 'bg-blue-600 text-white'
                          : 'bg-gray-100 border border-gray-300 text-gray-900'
                      )}
                    >
                      <div className="whitespace-pre-wrap text-sm leading-relaxed">
                        {message.content}
                      </div>
                      <div
                        className={cn(
                          'mt-2 text-xs',
                          message.type === 'user' ? 'text-blue-100' : 'text-gray-600'
                        )}
                      >
                        {message.timestamp.toLocaleTimeString('zh-CN', { 
                          hour: '2-digit', 
                          minute: '2-digit' 
                        })}
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
                  <div className="flex gap-4 justify-start mb-6">
                    <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-green-500">
                      <span className="text-sm font-medium text-white">AI</span>
                    </div>
                    <div className="max-w-[70%] rounded-2xl px-4 py-3 bg-gray-100 border border-gray-300">
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
        <div className="bg-white border-t border-gray-200 px-6 py-4">
          <div className="max-w-4xl mx-auto">
            {/* 警告提示 */}
            <div className="mb-4 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
              <p className="text-sm text-yellow-800">
                系统将自动记录输入内容中的个人身份信息，并将自动脱敏。请避免输入个人身份信息中不应包含敏感信息，如身份证号、银行卡号、手机号等。
              </p>
            </div>
            
            <div className="relative flex items-end gap-3 rounded-xl border border-gray-200 bg-white p-3 focus-within:border-blue-500 focus-within:ring-1 focus-within:ring-blue-500">
              <button className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg text-gray-400 hover:bg-gray-100 hover:text-gray-600 transition-colors">
                <RiAttachmentLine className="h-4 w-4" />
              </button>
              <textarea
                ref={textareaRef}
                value={inputValue}
                onChange={handleTextareaChange}
                onKeyDown={handleKeyDown}
                placeholder="输入消息，Ctrl+Enter 换行"
                className="flex-1 resize-none border-0 bg-transparent text-sm text-gray-900 placeholder-gray-400 focus:outline-none"
                rows={1}
                style={{ maxHeight: '120px' }}
              />
              <div className="flex shrink-0 items-center gap-2">
                <button className="flex h-8 w-8 items-center justify-center rounded-lg text-gray-400 hover:bg-gray-100 hover:text-gray-600 transition-colors">
                  <RiMicLine className="h-4 w-4" />
                </button>
                <button
                  onClick={handleSend}
                  disabled={!inputValue.trim() || isLoading}
                  className={cn(
                    'px-4 py-2 text-sm font-medium rounded-lg transition-colors',
                    inputValue.trim() && !isLoading
                      ? 'bg-green-500 text-white hover:bg-green-600'
                      : 'bg-gray-100 text-gray-400 cursor-not-allowed'
                  )}
                >
                  发送回复
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default ChatPage