// Chat API service
import Cookies from 'js-cookie'
import { API_PREFIX, CSRF_COOKIE_NAME, CSRF_HEADER_NAME } from '@/config'
import { del, get, post } from './base'

// Types
export type Message = {
  id: string
  conversation_id: string
  query: string
  answer: string
  created_at: number
  feedback: {
    rating: 'like' | 'dislike' | null
  } | null
}

export type Conversation = {
  id: string
  name: string
  status: string
  created_at: number
  updated_at: number
}

export type ChatResponse = {
  event: string
  task_id: string
  id: string
  message_id: string
  conversation_id: string
  answer: string
  created_at: number
}

export type ChatInputValue = string | number | boolean | null | ChatInputValue[] | { [key: string]: ChatInputValue }

// API endpoints
const prefix = '/api'

// Send chat message
export const sendChatMessage = (
  appId: string,
  body: {
    query: string
    inputs: Record<string, ChatInputValue>
    conversation_id?: string
    response_mode: 'blocking' | 'streaming'
  },
) => {
  return post<ChatResponse>(`${prefix}/apps/${appId}/chat-messages`, {
    body,
  })
}

// Get conversation list
export const fetchConversations = (appId: string, params?: { limit?: number, last_id?: string }) => {
  return get<{ data: Conversation[], has_more: boolean, limit: number }>(
    `${prefix}/apps/${appId}/conversations`,
    params,
  )
}

// Get conversation messages
export const fetchChatMessages = (
  appId: string,
  conversationId: string,
  params?: { limit?: number, last_id?: string },
) => {
  return get<{ data: Message[], has_more: boolean, limit: number }>(
    `${prefix}/apps/${appId}/conversations/${conversationId}/messages`,
    params,
  )
}

// Rename conversation
export const renameConversation = (appId: string, conversationId: string, name: string) => {
  return post(`${prefix}/apps/${appId}/conversations/${conversationId}/name`, {
    body: { name },
  })
}

// Delete conversation
export const deleteConversation = (appId: string, conversationId: string) => {
  return del(`${prefix}/apps/${appId}/conversations/${conversationId}`)
}

// Stop message generation
export const stopChatMessageResponding = (appId: string, taskId: string) => {
  return post(`${prefix}/apps/${appId}/chat-messages/${taskId}/stop`, {
    body: {},
  })
}

// Feedback
export const updateFeedback = (
  appId: string,
  messageId: string,
  rating: 'like' | 'dislike' | null,
) => {
  return post(`${prefix}/apps/${appId}/messages/${messageId}/feedbacks`, {
    body: { rating },
  })
}

// Simple chat using configured models (for standalone chat page)
export const sendSimpleChatMessage = async (
  query: string,
  provider: string,
  model: string,
  history?: Array<{ type: 'user' | 'assistant', content: string }>,
  onData?: (data: string) => void,
  onError?: (error: string) => void,
  options?: { webSearch?: boolean },
) => {
  const requestBody = {
    query,
    provider,
    model,
    history,
    web_search: options?.webSearch || false,
  }
  
  console.log('[Simple Chat] Sending request:', {
    url: `${API_PREFIX}/simple-chat`,
    webSearch: options?.webSearch,
    body: requestBody,
  })
  
  const response = await fetch(`${API_PREFIX}/simple-chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      [CSRF_HEADER_NAME]: Cookies.get(CSRF_COOKIE_NAME()) || '',
    },
    credentials: 'include',
    body: JSON.stringify(requestBody),
  })
  
  console.log('[Simple Chat] Response status:', response.status, response.statusText)

  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`)
  }

  const reader = response.body?.getReader()
  const decoder = new TextDecoder()

  if (!reader)
    throw new Error('No response body')

  let buffer = ''

  while (true) {
    const { done, value } = await reader.read()
    buffer += decoder.decode(value, { stream: !done })

    const events = buffer.split('\n\n')
    buffer = events.pop() || ''

    for (const event of events) {
      const dataLines = event
        .split('\n')
        .filter(line => line.startsWith('data: '))
        .map(line => line.slice(6))

      if (!dataLines.length)
        continue

      const data = dataLines.join('\n')
      if (data === '[DONE]')
        return

      const parsed = JSON.parse(data)
      if (parsed.content) {
        onData?.(parsed.content)
      }
      else if (parsed.error) {
        onError?.(parsed.error)
        throw new Error(parsed.error)
      }
    }

    if (done)
      break
  }
}
