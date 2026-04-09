import { render } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { describe, expect, it, vi } from 'vitest'
import { ProviderContextProvider } from './provider-context'

const { mockUseModelProviders } = vi.hoisted(() => ({
  mockUseModelProviders: vi.fn((enabled?: boolean) => ({ data: undefined, enabled })),
}))

vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string) => key,
  }),
}))

vi.mock('@/context/app-context', () => ({
  useSelector: (selector: (state: { currentWorkspace: { capabilities: string[] } }) => unknown) =>
    selector({ currentWorkspace: { capabilities: ['desktop_app_view'] } }),
}))

vi.mock('@/service/use-common', () => ({
  useModelProviders: mockUseModelProviders,
  useModelListByType: () => ({ data: undefined }),
  useSupportRetrievalMethods: () => ({ data: undefined }),
}))

vi.mock('@/service/use-education', () => ({
  useEducationStatus: () => ({
    data: undefined,
    isLoading: false,
    isFetching: false,
    isFetchedAfterMount: false,
  }),
}))

vi.mock('@/service/billing', () => ({
  fetchCurrentPlanInfo: vi.fn(() => new Promise(() => {})),
}))

vi.mock('@/app/components/base/toast', () => ({
  default: {
    notify: vi.fn(),
  },
}))

vi.mock('@/app/components/base/zendesk/utils', () => ({
  setZendeskConversationFields: vi.fn(),
}))

describe('ProviderContextProvider', () => {
  it('does not fetch model providers for users without model management capability', () => {
    const queryClient = new QueryClient()

    render(
      <QueryClientProvider client={queryClient}>
        <ProviderContextProvider>
          <div>child</div>
        </ProviderContextProvider>
      </QueryClientProvider>,
    )

    expect(mockUseModelProviders).toHaveBeenCalledWith(false)
  })
})
