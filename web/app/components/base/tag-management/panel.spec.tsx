import type { Tag } from './constant'
import { fireEvent, render, screen } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { ToastContext } from '@/app/components/base/toast'
import { createTag } from '@/service/tag'
import Panel from './panel'

const mockSetTagList = vi.fn()
const mockSetShowTagManagementModal = vi.fn()
const mockNotify = vi.fn()

const mockStoreState = {
  tagList: [] as Tag[],
  setTagList: mockSetTagList,
  setShowTagManagementModal: mockSetShowTagManagementModal,
}

vi.mock('ahooks', () => ({
  useUnmount: vi.fn(),
}))

vi.mock('@/context/app-context', () => ({
  useAppContext: () => ({
    canEditApps: true,
    canEditKnowledge: true,
  }),
}))

vi.mock('@/service/tag', () => ({
  createTag: vi.fn(),
  bindTag: vi.fn(),
  unBindTag: vi.fn(),
}))

vi.mock('@/app/components/base/input', () => ({
  default: ({ value, placeholder, onChange, onKeyDown }: { value: string, placeholder?: string, onChange: (event: { target: { value: string } }) => void, onKeyDown?: (event: { key: string, nativeEvent: { isComposing?: boolean }, preventDefault: () => void, stopPropagation: () => void }) => void }) => (
    <input
      value={value}
      placeholder={placeholder}
      onChange={event => onChange({ target: { value: event.target.value } })}
      onKeyDown={event => onKeyDown?.({
        key: event.key,
        nativeEvent: { isComposing: (event.nativeEvent as KeyboardEvent).isComposing },
        preventDefault: () => event.preventDefault(),
        stopPropagation: () => event.stopPropagation(),
      })}
    />
  ),
}))

vi.mock('@/app/components/base/checkbox', () => ({
  default: () => <div />,
}))

vi.mock('@/app/components/base/divider', () => ({
  default: () => <div />,
}))

vi.mock('./store', () => ({
  useStore: (selector: (state: typeof mockStoreState) => unknown) => selector(mockStoreState),
}))

const mockCreateTag = vi.mocked(createTag)

describe('TagManagementPanel', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockStoreState.tagList = []
  })

  it('prevents duplicate create requests when create action is clicked repeatedly', () => {
    mockCreateTag.mockImplementation(() => new Promise(() => {}))

    render(
      <ToastContext.Provider value={{ notify: mockNotify, close: vi.fn() }}>
        <Panel
          targetID="app-1"
          type="app"
          value={[]}
          selectedTags={[]}
          onCacheUpdate={vi.fn()}
          onCreate={vi.fn()}
        />
      </ToastContext.Provider>,
    )

    fireEvent.change(screen.getByPlaceholderText('common.tag.selectorPlaceholder'), { target: { value: 'New Tag' } })

    const createAction = screen.getByText('common.tag.create')
    fireEvent.click(createAction)
    fireEvent.click(createAction)

    expect(mockCreateTag).toHaveBeenCalledTimes(1)
    expect(mockCreateTag).toHaveBeenCalledWith('New Tag', 'app')
  })

  it('submits create request when enter is pressed in the input', () => {
    mockCreateTag.mockImplementation(() => new Promise(() => {}))

    render(
      <ToastContext.Provider value={{ notify: mockNotify, close: vi.fn() }}>
        <Panel
          targetID="app-1"
          type="app"
          value={[]}
          selectedTags={[]}
          onCacheUpdate={vi.fn()}
          onCreate={vi.fn()}
        />
      </ToastContext.Provider>,
    )

    const input = screen.getByPlaceholderText('common.tag.selectorPlaceholder')
    fireEvent.change(input, { target: { value: '  Enter Tag  ' } })
    fireEvent.keyDown(input, { key: 'Enter' })

    expect(mockCreateTag).toHaveBeenCalledTimes(1)
    expect(mockCreateTag).toHaveBeenCalledWith('Enter Tag', 'app')
  })

  it('still allows creating app tags when store contains tags of other types', () => {
    mockStoreState.tagList = [
      { id: 'knowledge-1', name: '知识标签', type: 'knowledge', binding_count: 0 },
    ]
    mockCreateTag.mockImplementation(() => new Promise(() => {}))

    render(
      <ToastContext.Provider value={{ notify: mockNotify, close: vi.fn() }}>
        <Panel
          targetID="app-1"
          type="app"
          value={[]}
          selectedTags={[]}
          onCacheUpdate={vi.fn()}
          onCreate={vi.fn()}
        />
      </ToastContext.Provider>,
    )

    fireEvent.change(screen.getByPlaceholderText('common.tag.selectorPlaceholder'), { target: { value: '跨类型标签' } })

    expect(screen.getByText('common.tag.create')).toBeInTheDocument()
  })
})
