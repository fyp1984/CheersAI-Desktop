import type { ReactNode } from 'react'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { ToastContext } from '@/app/components/base/toast'
import { deleteTag, updateTag } from '@/service/tag'
import TagItemEditor from './tag-item-editor'

const mockSetTagList = vi.fn()
const mockNotify = vi.fn()

const mockStoreState = {
  tagList: [
    { id: 'tag-1', name: '常用', type: 'app' as const, binding_count: 0 },
  ],
  setTagList: mockSetTagList,
}

vi.mock('ahooks', () => ({
  useDebounceFn: (fn: (...args: unknown[]) => unknown) => ({
    run: (...args: unknown[]) => fn(...args),
  }),
}))

vi.mock('@/context/app-context', () => ({
  useAppContext: () => ({
    isCurrentWorkspaceEditor: true,
  }),
}))

vi.mock('@/service/tag', () => ({
  updateTag: vi.fn(),
  deleteTag: vi.fn(),
}))

vi.mock('@/app/components/base/tooltip', () => ({
  default: ({ children }: { children: ReactNode }) => <>{children}</>,
}))

vi.mock('@/app/components/base/confirm', () => ({
  default: () => null,
}))

vi.mock('./store', () => ({
  useStore: (selector: (state: typeof mockStoreState) => unknown) => selector(mockStoreState),
}))

const mockUpdateTag = vi.mocked(updateTag)
const mockDeleteTag = vi.mocked(deleteTag)

describe('TagItemEditor', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockStoreState.tagList = [
      { id: 'tag-1', name: '常用', type: 'app', binding_count: 0 },
    ]
  })

  it('does not submit while IME composition is active', () => {
    render(
      <ToastContext.Provider value={{ notify: mockNotify, close: vi.fn() }}>
        <TagItemEditor tag={mockStoreState.tagList[0]} />
      </ToastContext.Provider>,
    )

    fireEvent.click(document.querySelector('.group\\/edit') as Element)
    const input = screen.getByDisplayValue('常用')
    fireEvent.change(input, { target: { value: '常用标签' } })
    fireEvent.keyDown(input, { key: 'Enter', isComposing: true, keyCode: 229, which: 229 })

    expect(mockUpdateTag).not.toHaveBeenCalled()
    expect(screen.getByDisplayValue('常用标签')).toBeInTheDocument()
  })

  it('submits only once on enter followed by blur and passes type', async () => {
    mockUpdateTag.mockImplementation(() => new Promise(() => {}))

    render(
      <ToastContext.Provider value={{ notify: mockNotify, close: vi.fn() }}>
        <TagItemEditor tag={mockStoreState.tagList[0]} />
      </ToastContext.Provider>,
    )

    fireEvent.click(document.querySelector('.group\\/edit') as Element)
    const input = screen.getByDisplayValue('常用')
    fireEvent.change(input, { target: { value: '  新标签名  ' } })
    fireEvent.keyDown(input, { key: 'Enter', nativeEvent: { isComposing: false } })
    fireEvent.blur(input)

    await waitFor(() => {
      expect(mockUpdateTag).toHaveBeenCalledTimes(1)
    })
    expect(mockUpdateTag).toHaveBeenCalledWith('tag-1', '新标签名', 'app')
  })

  it('deletes tag immediately when binding count is zero', async () => {
    mockDeleteTag.mockResolvedValue(undefined)

    render(
      <ToastContext.Provider value={{ notify: mockNotify, close: vi.fn() }}>
        <TagItemEditor tag={mockStoreState.tagList[0]} />
      </ToastContext.Provider>,
    )

    fireEvent.click(document.querySelector('.group\\/remove') as Element)

    await waitFor(() => {
      expect(mockDeleteTag).toHaveBeenCalledTimes(1)
    })
    expect(mockDeleteTag).toHaveBeenCalledWith('tag-1')
  })
})
