'use client'

import { useState, useEffect, useCallback } from 'react'
import { MagnifyingGlassIcon, XMarkIcon } from '@heroicons/react/24/outline'
import Modal from '@/app/components/base/modal'

interface SearchResult {
  messageId: string
  conversationId: string
  content: string
  timestamp: Date
  isUser: boolean
  matchIndex: number
  matchLength: number
}

interface ChatSearchProps {
  isOpen: boolean
  onClose: () => void
  onSearch: (query: string, filters?: any) => Promise<SearchResult[]>
  onResultSelect: (result: SearchResult) => void
}

export function ChatSearch({ isOpen, onClose, onSearch, onResultSelect }: ChatSearchProps) {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<SearchResult[]>([])
  const [isSearching, setIsSearching] = useState(false)
  const [filters, setFilters] = useState({
    messageType: 'all',
  })

  const performSearch = useCallback(async (searchQuery: string) => {
    if (!searchQuery.trim()) {
      setResults([])
      return
    }

    setIsSearching(true)
    try {
      const searchResults = await onSearch(searchQuery, filters)
      setResults(searchResults)
    } catch (error) {
      console.error('搜索失败:', error)
      setResults([])
    } finally {
      setIsSearching(false)
    }
  }, [onSearch, filters])

  useEffect(() => {
    const timer = setTimeout(() => {
      performSearch(query)
    }, 300)

    return () => clearTimeout(timer)
  }, [query, performSearch])

  const handleClose = () => {
    setQuery('')
    setResults([])
    onClose()
  }

  const handleResultClick = (result: SearchResult) => {
    onResultSelect(result)
    handleClose()
  }

  const highlightText = (text: string, searchQuery: string) => {
    if (!searchQuery.trim()) return text

    const regex = new RegExp(`(${searchQuery.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi')
    const parts = text.split(regex)
    
    return parts.map((part, index) => 
      regex.test(part) ? (
        <mark key={index} className="bg-yellow-200 text-yellow-900 rounded px-1">
          {part}
        </mark>
      ) : part
    )
  }

  const formatTime = (date: Date) => {
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

  return (
    <Modal isShow={isOpen} onClose={handleClose} className="!max-w-2xl">
      <div className="p-6">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-lg font-semibold text-gray-900">搜索对话记录</h2>
          <button
            onClick={handleClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <XMarkIcon className="w-5 h-5" />
          </button>
        </div>

        <div className="relative mb-4">
          <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="输入关键词搜索对话内容..."
            className="w-full pl-10 pr-4 py-3 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            autoFocus
          />
        </div>

        <div className="flex items-center gap-4 mb-6">
          <span className="text-sm text-gray-600">消息类型:</span>
          <div className="flex items-center gap-2">
            {[
              { value: 'all', label: '全部' },
              { value: 'user', label: '用户消息' },
              { value: 'ai', label: 'AI回复' },
            ].map((option) => (
              <button
                key={option.value}
                onClick={() => setFilters(prev => ({ ...prev, messageType: option.value }))}
                className={`px-3 py-1 text-xs rounded-full transition-colors ${
                  filters.messageType === option.value
                    ? 'bg-blue-100 text-blue-700 border border-blue-200'
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                }`}
              >
                {option.label}
              </button>
            ))}
          </div>
        </div>

        <div className="max-h-96 overflow-y-auto">
          {isSearching ? (
            <div className="flex items-center justify-center py-8">
              <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-500"></div>
              <span className="ml-2 text-sm text-gray-600">搜索中...</span>
            </div>
          ) : query.trim() && results.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              <MagnifyingGlassIcon className="w-12 h-12 mx-auto mb-2 text-gray-300" />
              <p className="text-sm">未找到相关对话</p>
            </div>
          ) : results.length > 0 ? (
            <div className="space-y-3">
              {results.map((result, index) => (
                <div
                  key={`${result.conversationId}-${result.messageId}-${index}`}
                  onClick={() => handleResultClick(result)}
                  className="p-3 border border-gray-200 rounded-lg hover:bg-gray-50 cursor-pointer transition-colors"
                >
                  <div className="flex items-start justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <div className={`w-2 h-2 rounded-full ${
                        result.isUser ? 'bg-blue-500' : 'bg-green-500'
                      }`} />
                      <span className="text-xs text-gray-500">
                        {result.isUser ? '用户' : 'AI'}
                      </span>
                    </div>
                    <span className="text-xs text-gray-400">
                      {formatTime(result.timestamp)}
                    </span>
                  </div>
                  <div className="text-sm text-gray-700 line-clamp-3">
                    {highlightText(result.content, query)}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8 text-gray-500">
              <MagnifyingGlassIcon className="w-12 h-12 mx-auto mb-2 text-gray-300" />
              <p className="text-sm">输入关键词开始搜索</p>
            </div>
          )}
        </div>

        {query.trim() && results.length > 0 && (
          <div className="mt-4 pt-4 border-t border-gray-200">
            <p className="text-xs text-gray-500 text-center">
              找到 {results.length} 条相关消息
            </p>
          </div>
        )}
      </div>
    </Modal>
  )
}
