import { NextRequest, NextResponse } from 'next/server'

interface SearchFilters {
  dateRange?: {
    start: string
    end: string
  }
  messageType?: 'all' | 'user' | 'ai'
  hasFiles?: boolean
}

interface SearchResult {
  messageId: string
  conversationId: string
  content: string
  timestamp: string
  isUser: boolean
  matchIndex: number
  matchLength: number
}

// 模拟的对话数据（实际项目中应该从数据库获取）
const mockConversations = [
  {
    id: '1',
    messages: [
      {
        id: 'm1',
        content: '你好，我想了解一下人工智能的发展历史',
        timestamp: '2024-03-13T10:00:00Z',
        isUser: true,
      },
      {
        id: 'm2',
        content: '人工智能的发展可以追溯到20世纪50年代。1950年，艾伦·图灵提出了著名的图灵测试，这被认为是人工智能领域的开端。随后，达特茅斯会议在1956年正式确立了人工智能作为一个学科领域。',
        timestamp: '2024-03-13T10:01:00Z',
        isUser: false,
      },
      {
        id: 'm3',
        content: '机器学习和深度学习有什么区别？',
        timestamp: '2024-03-13T10:05:00Z',
        isUser: true,
      },
      {
        id: 'm4',
        content: '机器学习是人工智能的一个子领域，它让计算机能够在没有明确编程的情况下学习。深度学习则是机器学习的一个子集，它使用多层神经网络来模拟人脑的工作方式。深度学习在图像识别、自然语言处理等领域取得了突破性进展。',
        timestamp: '2024-03-13T10:06:00Z',
        isUser: false,
      },
    ],
  },
  {
    id: '2',
    messages: [
      {
        id: 'm5',
        content: '请帮我写一个Python函数来计算斐波那契数列',
        timestamp: '2024-03-13T14:00:00Z',
        isUser: true,
      },
      {
        id: 'm6',
        content: '好的，我来为你写一个计算斐波那契数列的Python函数：\n\n```python\ndef fibonacci(n):\n    if n <= 1:\n        return n\n    return fibonacci(n-1) + fibonacci(n-2)\n\n# 优化版本（使用动态规划）\ndef fibonacci_dp(n):\n    if n <= 1:\n        return n\n    \n    dp = [0] * (n + 1)\n    dp[1] = 1\n    \n    for i in range(2, n + 1):\n        dp[i] = dp[i-1] + dp[i-2]\n    \n    return dp[n]\n```',
        timestamp: '2024-03-13T14:01:00Z',
        isUser: false,
      },
    ],
  },
]

function searchInText(text: string, query: string): { index: number; length: number } | null {
  const lowerText = text.toLowerCase()
  const lowerQuery = query.toLowerCase()
  const index = lowerText.indexOf(lowerQuery)
  
  if (index === -1) return null
  
  return {
    index,
    length: query.length,
  }
}

function filterByDateRange(timestamp: string, dateRange?: { start: string; end: string }): boolean {
  if (!dateRange) return true
  
  const messageDate = new Date(timestamp)
  const startDate = new Date(dateRange.start)
  const endDate = new Date(dateRange.end)
  
  return messageDate >= startDate && messageDate <= endDate
}

function filterByMessageType(isUser: boolean, messageType?: string): boolean {
  if (!messageType || messageType === 'all') return true
  
  return messageType === 'user' ? isUser : !isUser
}

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url)
  const query = searchParams.get('q')
  const messageType = searchParams.get('messageType') as 'all' | 'user' | 'ai' | null
  const hasFiles = searchParams.get('hasFiles') === 'true'
  const startDate = searchParams.get('startDate')
  const endDate = searchParams.get('endDate')

  if (!query) {
    return NextResponse.json({ error: '搜索关键词不能为空' }, { status: 400 })
  }

  try {
    const results: SearchResult[] = []

    // 搜索所有对话
    for (const conversation of mockConversations) {
      for (const message of conversation.messages) {
        // 应用过滤器
        if (!filterByDateRange(message.timestamp, startDate && endDate ? { start: startDate, end: endDate } : undefined)) {
          continue
        }

        if (!filterByMessageType(message.isUser, messageType || undefined)) {
          continue
        }

        // 暂时忽略文件过滤器，因为模拟数据中没有文件信息
        // if (hasFiles && !message.hasFiles) continue

        // 搜索匹配
        const match = searchInText(message.content, query)
        if (match) {
          results.push({
            messageId: message.id,
            conversationId: conversation.id,
            content: message.content,
            timestamp: message.timestamp,
            isUser: message.isUser,
            matchIndex: match.index,
            matchLength: match.length,
          })
        }
      }
    }

    // 按时间倒序排列
    results.sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())

    return NextResponse.json({
      success: true,
      results,
      total: results.length,
      query,
    })

  } catch (error) {
    console.error('搜索错误:', error)
    return NextResponse.json({ error: '搜索失败' }, { status: 500 })
  }
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const { query, filters } = body as { query: string; filters?: SearchFilters }

    if (!query) {
      return NextResponse.json({ error: '搜索关键词不能为空' }, { status: 400 })
    }

    const results: SearchResult[] = []

    // 搜索所有对话（与GET方法类似的逻辑）
    for (const conversation of mockConversations) {
      for (const message of conversation.messages) {
        // 应用过滤器
        if (filters?.dateRange) {
          if (!filterByDateRange(message.timestamp, filters.dateRange)) {
            continue
          }
        }

        if (!filterByMessageType(message.isUser, filters?.messageType)) {
          continue
        }

        // 搜索匹配
        const match = searchInText(message.content, query)
        if (match) {
          results.push({
            messageId: message.id,
            conversationId: conversation.id,
            content: message.content,
            timestamp: message.timestamp,
            isUser: message.isUser,
            matchIndex: match.index,
            matchLength: match.length,
          })
        }
      }
    }

    // 按时间倒序排列
    results.sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())

    return NextResponse.json({
      success: true,
      results,
      total: results.length,
      query,
      filters,
    })

  } catch (error) {
    console.error('搜索错误:', error)
    return NextResponse.json({ error: '搜索失败' }, { status: 500 })
  }
}