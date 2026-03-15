// Chat API service
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
