import type { Tag } from './constant'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { ToastContext } from '@/app/components/base/toast'
import { createTag, fetchTagList } from '@/service/tag'
import TagManagementModal from './index'

const mockSetTagList = vi.fn()
const mockSetShowTagManagementModal = vi.fn()
const mockNotify = vi.fn()

const mockStoreState = {
  tagList: [] as Tag[],
  setTagList: mockSetTagList,
  setShowTagManagementModal: mockSetShowTagManagementModal,
}

vi.mock('@/service/tag', () => ({
  createTag: vi.fn(),
  fetchTagList: vi.fn(),
}))

vi.mock('@/context/app-context', () => ({
  useAppContext: () => ({
    canEditApps: true,
    canEditKnowledge: true,
  }),
}))

vi.mock('@/app/components/base/modal', () => ({
  default: ({ children, isShow }: { children: React.ReactNode, isShow: boolean }) => isShow ? <div>{children}</div> : null,
}))

vi.mock('./store', () => ({
  useStore: (selector: (state: typeof mockStoreState) => unknown) => selector(mockStoreState),
}))

vi.mock('./tag-item-editor', () => ({
  default: ({ tag }: { tag: { id: string } }) => <div data-testid={`tag-item-editor-${tag.id}`} />,
}))

const mockCreateTag = vi.mocked(createTag)
const mockFetchTagList = vi.mocked(fetchTagList)

const createDeferred = <T,>() => {
  let resolve!: (value: T) => void
  const promise = new Promise<T>((res) => {
    resolve = res
  })
  return { promise, resolve }
}

const renderModal = () => {
  render(
    <ToastContext.Provider value={{ notify: mockNotify, close: vi.fn() }}>
      <TagManagementModal show type="app" />
    </ToastContext.Provider>,
  )
}

describe('TagManagementModal', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockStoreState.tagList = []
    mockFetchTagList.mockResolvedValue([])
  })

  it('prevents duplicate create requests when submit is followed by blur', async () => {
    const deferred = createDeferred<{ id: string, name: string, type: 'app', binding_count: number }>()
    mockCreateTag.mockImplementation(() => deferred.promise)

    renderModal()

    const input = await screen.findByPlaceholderText('common.tag.addNew')
    fireEvent.change(input, { target: { value: 'New Tag' } })
    fireEvent.submit(input.closest('form') as HTMLFormElement)
    fireEvent.blur(input)

    expect(mockCreateTag).toHaveBeenCalledTimes(1)
    expect(mockCreateTag).toHaveBeenCalledWith('New Tag', 'app')

    deferred.resolve({ id: 'tag-1', name: 'New Tag', type: 'app', binding_count: 0 })

    await waitFor(() => {
      expect(mockNotify).toHaveBeenCalledWith({ type: 'success', message: 'common.tag.created' })
    })
  })

  it('trims name before creating a new tag', () => {
    mockCreateTag.mockImplementation(() => new Promise(() => {}))

    renderModal()

    const input = screen.getByPlaceholderText('common.tag.addNew')
    fireEvent.change(input, { target: { value: '  New Tag  ' } })
    fireEvent.submit(input.closest('form') as HTMLFormElement)

    expect(mockCreateTag).toHaveBeenCalledTimes(1)
    expect(mockCreateTag).toHaveBeenCalledWith('New Tag', 'app')
  })

  it('supports creating a new tag via explicit create action click', () => {
    mockCreateTag.mockImplementation(() => new Promise(() => {}))

    renderModal()

    const input = screen.getByPlaceholderText('common.tag.addNew')
    fireEvent.change(input, { target: { value: 'Common' } })
    fireEvent.click(screen.getByRole('button', { name: /common\.tag\.create/i }))

    expect(mockCreateTag).toHaveBeenCalledTimes(1)
    expect(mockCreateTag).toHaveBeenCalledWith('Common', 'app')
  })

  it('only renders tags matching the current type', () => {
    mockStoreState.tagList = [
      { id: 'app-1', name: '应用标签', type: 'app', binding_count: 0 },
      { id: 'knowledge-1', name: '知识标签', type: 'knowledge', binding_count: 0 },
    ]

    renderModal()

    expect(screen.getByTestId('tag-item-editor-app-1')).toBeInTheDocument()
    expect(screen.queryByTestId('tag-item-editor-knowledge-1')).not.toBeInTheDocument()
  })
})
