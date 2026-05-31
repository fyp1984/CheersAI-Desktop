'use client'

import { RiCloseFill, RiCustomerServiceLine, RiPhoneLine, RiRobotLine, RiSendPlaneLine, RiUserLine } from '@remixicon/react'
import { useEffect, useRef, useState } from 'react'
import { submitUserFeedback } from '@/service/common'
import { cn } from '@/utils/classnames'

type AssistantMessage = {
  id: string
  role: 'assistant' | 'user'
  content: string
}

const presetAnswers = [
  {
    question: '如何接入API？',
    keywords: ['api', '接口', '接入', '扩展'],
    answer: '请进入「设置」-「API 扩展」配置 API 扩展服务；如果是模型调用，请先在「模型供应商」中配置可用模型，再在应用或对话中选择对应模型。',
  },
  {
    question: '收费标准是怎样的？',
    keywords: ['收费', '价格', '计费', '费用', 'token'],
    answer: '当前桌面内测环境未开放在线计费购买。你可以在「积分权益」中查看可兑换权益，Token 额度和服务权益以管理员配置为准。',
  },
  {
    question: '数据安全如何保障？',
    keywords: ['安全', '隐私', '脱敏', '数据', 'filebay'],
    answer: '系统支持安全对话、脱敏文件选择和 FileBay 文件接入。敏感文件优先在沙箱/FileBay 中处理，输入内容会自动记录并脱敏个人身份信息。',
  },
  {
    question: '怎么重置密码？',
    keywords: ['密码', '重置', '登录', '账号'],
    answer: '如果使用 SSO 登录，请在统一身份平台重置密码；如果使用邮箱账号，请在登录页选择找回密码或联系管理员重置。',
  },
]

const createMessage = (role: AssistantMessage['role'], content: string): AssistantMessage => ({
  id: `${Date.now()}-${Math.random().toString(16).slice(2)}`,
  role,
  content,
})

const getAnswer = (message: string) => {
  const normalizedMessage = message.toLowerCase()
  return presetAnswers.find(item =>
    item.question === message
    || item.keywords.some(keyword => normalizedMessage.includes(keyword.toLowerCase())),
  )?.answer
}

export function CustomerServiceFloat() {
  const [showCustomerService, setShowCustomerService] = useState(false)
  const [customerServiceTab, setCustomerServiceTab] = useState<'ai' | 'human' | 'phone'>('ai')
  const [feedbackMessage, setFeedbackMessage] = useState('')
  const [supportNotice, setSupportNotice] = useState('')
  const [isSubmittingFeedback, setIsSubmittingFeedback] = useState(false)
  const [messages, setMessages] = useState<AssistantMessage[]>(() => [
    createMessage('assistant', '您好，我可以回答常见配置、计费、数据安全和账号问题。'),
  ])

  // 悬浮窗位置和拖拽状态
  const [floatPosition, setFloatPosition] = useState({ x: 0, y: 0 })
  const [isDragging, setIsDragging] = useState(false)
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 })
  const floatRef = useRef<HTMLDivElement>(null)
  const [isPositionInitialized, setIsPositionInitialized] = useState(false)

  const answerQuestion = (question: string) => {
    const answer = getAnswer(question)
    setMessages(prev => [
      ...prev,
      createMessage('user', question),
      createMessage('assistant', answer || '这个问题我暂时没有预设答案，你可以提交为反馈，管理员后续会查看。'),
    ])
  }

  const saveFeedback = async (message: string, channel: 'ai' | 'human' | 'phone') => {
    const response = await submitUserFeedback({
      content: message,
      title: message,
      source: 'customer_service',
      channel,
      category: channel === 'ai' ? 'faq_unmatched' : 'support_request',
      page_url: globalThis.location.href,
      metadata: {
        support_tab: channel,
      },
    })
    return response.data?.ticket_no
  }

  // 处理反馈提交
  const handleSubmitFeedback = async () => {
    const message = feedbackMessage.trim()
    if (!message || isSubmittingFeedback)
      return

    if (customerServiceTab === 'ai') {
      const matchedAnswer = getAnswer(message)
      let ticketNo: string | undefined
      if (!matchedAnswer) {
        try {
          setIsSubmittingFeedback(true)
          ticketNo = await saveFeedback(message, 'ai')
        }
        catch (error) {
          console.error('提交反馈失败:', error)
        }
        finally {
          setIsSubmittingFeedback(false)
        }
      }
      setMessages(prev => [
        ...prev,
        createMessage('user', message),
        createMessage(
          'assistant',
          matchedAnswer || (ticketNo
            ? `我没有找到匹配的常见问题答案，已记录为反馈工单 ${ticketNo}，管理员后续会查看。`
            : '我没有找到匹配的常见问题答案，但反馈提交失败了。请稍后再试或联系管理员。'),
        ),
      ])
      setFeedbackMessage('')
      return
    }

    try {
      setIsSubmittingFeedback(true)
      const ticketNo = await saveFeedback(message, customerServiceTab)
      setFeedbackMessage('')
      setSupportNotice(ticketNo
        ? `已记录为反馈工单 ${ticketNo}。管理员会在后台查看。`
        : '已记录为反馈工单。管理员会在后台查看。')
    }
    catch (error) {
      console.error('提交反馈失败:', error)
      setSupportNotice('反馈提交失败了，请稍后再试或联系管理员。')
    }
    finally {
      setIsSubmittingFeedback(false)
    }
  }

  // 处理客服弹窗
  const handleCustomerServiceToggle = () => {
    setShowCustomerService(!showCustomerService)
  }

  // 拖拽处理函数
  const handleMouseDown = (e: React.MouseEvent) => {
    if (showCustomerService)
      return

    setIsDragging(true)
    setDragStart({
      x: e.clientX - floatPosition.x,
      y: e.clientY - floatPosition.y,
    })
    e.preventDefault()
  }
  const handleMouseMove = (e: MouseEvent) => {
    if (!isDragging)
      return

    const newX = e.clientX - dragStart.x
    const newY = e.clientY - dragStart.y

    const windowWidth = window.innerWidth
    const windowHeight = window.innerHeight
    const buttonSize = 56

    const clampedX = Math.max(0, Math.min(windowWidth - buttonSize, newX))
    const clampedY = Math.max(0, Math.min(windowHeight - buttonSize, newY))

    setFloatPosition({ x: clampedX, y: clampedY })
  }

  const handleMouseUp = () => {
    setIsDragging(false)
  }

  // 添加全局鼠标事件监听
  useEffect(() => {
    if (isDragging) {
      document.addEventListener('mousemove', handleMouseMove)
      document.addEventListener('mouseup', handleMouseUp)
      document.body.style.userSelect = 'none'
    }

    return () => {
      document.removeEventListener('mousemove', handleMouseMove)
      document.removeEventListener('mouseup', handleMouseUp)
      document.body.style.userSelect = ''
    }
  }, [isDragging, dragStart])

  // 保存位置到本地存储
  useEffect(() => {
    try {
      localStorage.setItem('cheersai_float_position', JSON.stringify(floatPosition))
    }
    catch {
      // 保存位置失败，忽略错误
    }
  }, [floatPosition])

  // 从本地存储加载位置，或设置默认右下角位置
  useEffect(() => {
    const initializePosition = () => {
      try {
        const stored = localStorage.getItem('cheersai_float_position')
        if (stored) {
          const position = JSON.parse(stored)

          if (position.x > 0 && position.y > 0
            && position.x < window.innerWidth && position.y < window.innerHeight) {
            setFloatPosition(position)
            setIsPositionInitialized(true)
            return
          }
          else {
            localStorage.removeItem('cheersai_float_position')
          }
        }
      }
      catch {
        // 加载本地存储失败，使用默认位置
      }

      const windowWidth = window.innerWidth || 1920
      const windowHeight = window.innerHeight || 1080
      const buttonSize = 56
      const margin = 24

      const defaultX = windowWidth - buttonSize - margin
      const defaultY = windowHeight - buttonSize - margin

      setFloatPosition({ x: defaultX, y: defaultY })
      setIsPositionInitialized(true)
    }

    const timer = setTimeout(initializePosition, 100)
    return () => clearTimeout(timer)
  }, [])

  // 监听窗口大小变化
  useEffect(() => {
    const handleResize = () => {
      const stored = localStorage.getItem('cheersai_float_position')
      if (!stored && isPositionInitialized) {
        const windowWidth = window.innerWidth || 1920
        const windowHeight = window.innerHeight || 1080
        const buttonSize = 56
        const margin = 24

        const newX = windowWidth - buttonSize - margin
        const newY = windowHeight - buttonSize - margin

        setFloatPosition({ x: newX, y: newY })
      }
    }

    window.addEventListener('resize', handleResize)
    return () => window.removeEventListener('resize', handleResize)
  }, [isPositionInitialized])
  return (
    <>
      {/* 悬浮客服气泡 */}
      {isPositionInitialized && (
        <div
          ref={floatRef}
          className="fixed z-50"
          style={{
            left: `${floatPosition.x}px`,
            top: `${floatPosition.y}px`,
          }}
        >
          {/* 客服弹窗 */}
          {showCustomerService && (
            <div className="fixed inset-0 z-50 flex items-center justify-center bg-background-overlay">
              <div className="mx-4 max-h-[90vh] w-full max-w-lg overflow-y-auto rounded-xl bg-components-panel-bg shadow-xl">
                {/* 弹窗头部 */}
                <div className="flex items-center justify-between border-b border-divider-regular px-6 py-4">
                  <div className="flex items-center gap-3">
                    <RiCustomerServiceLine className="h-6 w-6 text-text-accent" />
                    <span className="text-lg font-semibold text-text-primary">在线客服</span>
                  </div>
                  <button
                    onClick={() => setShowCustomerService(false)}
                    className="rounded p-1 hover:bg-state-base-hover"
                  >
                    <RiCloseFill className="h-5 w-5 text-text-tertiary" />
                  </button>
                </div>

                {/* 标签页 */}
                <div className="flex border-b border-divider-regular">
                  <button
                    onClick={() => {
                      setCustomerServiceTab('ai')
                      setSupportNotice('')
                    }}
                    className={cn(
                      'flex flex-1 items-center justify-center gap-2 px-4 py-3 text-sm font-medium transition-colors',
                      customerServiceTab === 'ai'
                        ? 'border-b-2 border-state-accent-solid bg-state-accent-hover text-text-accent'
                        : 'text-text-secondary hover:bg-state-base-hover hover:text-text-primary',
                    )}
                  >
                    <RiRobotLine className="h-4 w-4" />
                    智能助手
                  </button>
                  <button
                    onClick={() => {
                      setCustomerServiceTab('human')
                      setSupportNotice('')
                    }}
                    className={cn(
                      'flex flex-1 items-center justify-center gap-2 px-4 py-3 text-sm font-medium transition-colors',
                      customerServiceTab === 'human'
                        ? 'border-b-2 border-state-accent-solid bg-state-accent-hover text-text-accent'
                        : 'text-text-secondary hover:bg-state-base-hover hover:text-text-primary',
                    )}
                  >
                    <RiUserLine className="h-4 w-4" />
                    人工客服
                  </button>
                  <button
                    onClick={() => {
                      setCustomerServiceTab('phone')
                      setSupportNotice('')
                    }}
                    className={cn(
                      'flex flex-1 items-center justify-center gap-2 px-4 py-3 text-sm font-medium transition-colors',
                      customerServiceTab === 'phone'
                        ? 'border-b-2 border-state-accent-solid bg-state-accent-hover text-text-accent'
                        : 'text-text-secondary hover:bg-state-base-hover hover:text-text-primary',
                    )}
                  >
                    <RiPhoneLine className="h-4 w-4" />
                    电话服务
                  </button>
                </div>
                {/* 内容区域 */}
                <div className="h-72 overflow-y-auto">
                  {customerServiceTab === 'ai' && (
                    <div className="flex min-h-full flex-col p-6">
                      <div className="space-y-3">
                        {messages.map(message => (
                          <div
                            key={message.id}
                            className={cn(
                              'max-w-[88%] rounded-xl px-3 py-2 text-sm leading-6',
                              message.role === 'assistant'
                                ? 'bg-background-section-burn text-text-primary'
                                : 'ml-auto bg-state-accent-hover text-text-accent',
                            )}
                          >
                            {message.content}
                          </div>
                        ))}
                      </div>

                      {/* 预设问题 */}
                      <div className="mt-4 space-y-2">
                        {presetAnswers.map(item => (
                          <button
                            key={item.question}
                            onClick={() => answerQuestion(item.question)}
                            className="w-full rounded-lg bg-state-accent-hover p-3 text-left text-sm text-text-accent transition-colors hover:bg-state-accent-solid hover:text-components-button-primary-text"
                          >
                            {item.question}
                          </button>
                        ))}
                      </div>
                    </div>
                  )}

                  {customerServiceTab === 'human' && (
                    <div className="flex h-full flex-col p-6">
                      <div className="mb-4 text-sm text-text-primary">
                        当前未配置在线人工客服通道。
                      </div>
                      <div className="flex flex-1 items-center justify-center">
                        <div className="text-center text-text-tertiary">
                          <RiUserLine className="mx-auto mb-3 h-8 w-8 text-text-quaternary" />
                          <div className="text-sm">你可以在下方提交问题，系统会保存为反馈工单。</div>
                          {supportNotice && (
                            <div className="mt-3 rounded-lg bg-state-success-hover px-3 py-2 text-sm text-text-success">
                              {supportNotice}
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  )}

                  {customerServiceTab === 'phone' && (
                    <div className="flex h-full flex-col p-6">
                      <div className="mb-4 text-sm text-text-primary">
                        当前未配置电话客服。
                      </div>
                      <div className="flex flex-1 items-center justify-center">
                        <div className="text-center text-text-tertiary">
                          <RiPhoneLine className="mx-auto mb-3 h-8 w-8 text-text-quaternary" />
                          <div className="text-sm text-text-tertiary">
                            请联系管理员配置真实服务电话后再展示。
                          </div>
                          {supportNotice && (
                            <div className="mt-3 rounded-lg bg-state-success-hover px-3 py-2 text-sm text-text-success">
                              {supportNotice}
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  )}
                </div>

                {/* 输入区域 */}
                <div className="rounded-b-xl border-t border-divider-regular bg-background-section px-6 py-4">
                  <div className="flex gap-2">
                    <input
                      type="text"
                      value={feedbackMessage}
                      onChange={e => setFeedbackMessage(e.target.value)}
                      placeholder={customerServiceTab === 'ai' ? '输入问题或提交反馈...' : '描述你的问题，保存为反馈...'}
                      className="flex-1 rounded-lg border border-components-input-border-active bg-components-input-bg-normal px-3 py-2 text-sm text-text-primary placeholder:text-text-placeholder focus:border-state-accent-solid focus:ring-2 focus:ring-state-accent-solid"
                      onKeyDown={(e) => {
                        if (e.key === 'Enter' && !e.shiftKey) {
                          e.preventDefault()
                          handleSubmitFeedback()
                        }
                      }}
                    />
                    <button
                      onClick={handleSubmitFeedback}
                      disabled={!feedbackMessage.trim() || isSubmittingFeedback}
                      className={cn(
                        'rounded-lg px-4 py-2 transition-colors',
                        feedbackMessage.trim() && !isSubmittingFeedback
                          ? 'bg-components-button-primary-bg text-components-button-primary-text hover:bg-components-button-primary-bg-hover'
                          : 'cursor-not-allowed bg-components-button-secondary-bg text-components-button-secondary-text',
                      )}
                    >
                      <RiSendPlaneLine className="h-4 w-4" />
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* 客服气泡按钮 */}
          <button
            onMouseDown={handleMouseDown}
            onClick={!isDragging ? handleCustomerServiceToggle : undefined}
            className={cn(
              'flex h-14 w-14 items-center justify-center rounded-full bg-blue-500 text-white shadow-lg transition-all',
              isDragging
                ? 'scale-110 cursor-grabbing'
                : 'cursor-grab hover:scale-105 hover:bg-blue-600',
            )}
            title={isDragging ? '拖拽移动' : '在线客服'}
          >
            <RiCustomerServiceLine className="h-6 w-6" />
          </button>
        </div>
      )}
    </>
  )
}
