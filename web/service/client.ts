import type { ContractRouterClient } from '@orpc/contract'
import type { JsonifiedClient } from '@orpc/openapi-client'
import { createORPCClient, onError } from '@orpc/client'
import { OpenAPILink } from '@orpc/openapi-client/fetch'
import { createTanstackQueryUtils } from '@orpc/tanstack-query'
import {
  API_PREFIX,
  APP_VERSION,
  IS_MARKETPLACE,
  MARKETPLACE_API_PREFIX,
} from '@/config'
import {
  consoleRouterContract,
  marketplaceRouterContract,
} from '@/contract/router'
import { request } from './base'

const MARKETPLACE_REQUEST_TIMEOUT = 8000

const marketplaceFetch = (request: Request | URL | string, init?: RequestInit) => {
  // If marketplace is not configured, reject immediately
  if (!MARKETPLACE_API_PREFIX || MARKETPLACE_API_PREFIX === 'http://localhost:5002/api') {
    return Promise.reject(new Error('Marketplace is not configured'))
  }

  const controller = new AbortController()
  const timeoutId = globalThis.setTimeout(() => {
    controller.abort()
  }, MARKETPLACE_REQUEST_TIMEOUT)

  const abortListener = () => controller.abort()

  if (init?.signal) {
    if (init.signal.aborted)
      controller.abort()
    else
      init.signal.addEventListener('abort', abortListener, { once: true })
  }

  return globalThis.fetch(request, {
    ...init,
    cache: 'no-store',
    signal: controller.signal,
  }).finally(() => {
    globalThis.clearTimeout(timeoutId)
    init?.signal?.removeEventListener('abort', abortListener)
  })
}

const getMarketplaceHeaders = () => new Headers({
  'X-Dify-Version': !IS_MARKETPLACE ? APP_VERSION : '999.0.0',
})

const shouldLogClientError = (error: unknown) => {
  if (error instanceof Response)
    return error.status >= 500

  return true
}

const marketplaceLink = new OpenAPILink(marketplaceRouterContract, {
  url: MARKETPLACE_API_PREFIX,
  headers: () => (getMarketplaceHeaders()),
  fetch: (request, init) => {
    return marketplaceFetch(request, init)
  },
  interceptors: [
    onError((error) => {
      if (shouldLogClientError(error))
        console.error(error)
    }),
  ],
})

export const marketplaceClient: JsonifiedClient<ContractRouterClient<typeof marketplaceRouterContract>> = createORPCClient(marketplaceLink)
export const marketplaceQuery = createTanstackQueryUtils(marketplaceClient, { path: ['marketplace'] })

const consoleLink = new OpenAPILink(consoleRouterContract, {
  url: API_PREFIX,
  fetch: (input, init) => {
    return request(
      input.url,
      init,
      {
        fetchCompat: true,
        request: input,
      },
    )
  },
  interceptors: [
    onError((error) => {
      if (shouldLogClientError(error))
        console.error(error)
    }),
  ],
})

export const consoleClient: JsonifiedClient<ContractRouterClient<typeof consoleRouterContract>> = createORPCClient(consoleLink)
export const consoleQuery = createTanstackQueryUtils(consoleClient, { path: ['console'] })
