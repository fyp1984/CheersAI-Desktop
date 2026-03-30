/**
 * 测试设置文件
 * Test Setup File
 */

import { webcrypto } from 'node:crypto'
import { afterAll, afterEach, beforeAll } from 'vitest'
import 'fake-indexeddb/auto'

type LocalStorageMock = {
  getItem: (key: string) => string | null
  setItem: (key: string, value: string) => void
  removeItem: (key: string) => void
  clear: () => void
}

// Mock localStorage
const localStorageMock: LocalStorageMock = (() => {
  let store: Record<string, string> = {}

  return {
    getItem: (key: string) => store[key] || null,
    setItem: (key: string, value: string) => {
      store[key] = value.toString()
    },
    removeItem: (key: string) => {
      delete store[key]
    },
    clear: () => {
      store = {}
    },
  }
})()

Object.defineProperty(globalThis, 'localStorage', {
  value: localStorageMock,
  writable: true,
})

// Mock window.crypto for Web Crypto API
if (typeof globalThis.crypto === 'undefined') {
  Object.defineProperty(globalThis, 'crypto', {
    value: {
      getRandomValues: (arr: Uint8Array) => {
        const bytes = webcrypto.getRandomValues(new Uint8Array(arr.length))
        arr.set(bytes)
        return arr
      },
      subtle: webcrypto.subtle,
    } satisfies Crypto,
    writable: true,
  })
}

// 全局测试设置
beforeAll(() => {
  // 初始化测试环境
})

afterEach(() => {
  // 每个测试后清理
  localStorageMock.clear()
})

afterAll(() => {
  // 清理测试环境
})
