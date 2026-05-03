export const dynamic = 'force-static'

const cleanupServiceWorkerScript = `
self.addEventListener('install', (event) => {
  event.waitUntil(self.skipWaiting())
})

self.addEventListener('activate', (event) => {
  event.waitUntil((async () => {
    const cacheNames = await caches.keys()
    await Promise.all(cacheNames.map(cacheName => caches.delete(cacheName)))
    await self.registration.unregister()
    const clientsList = await self.clients.matchAll({ type: 'window', includeUncontrolled: true })
    clientsList.forEach((client) => {
      if ('navigate' in client)
        client.navigate(client.url)
    })
  })())
})

self.addEventListener('fetch', () => {})
`.trim()

export async function GET(
  _request: Request,
  { params }: { params: Promise<{ path: string }> },
) {
  const { path } = await params

  if (path !== 'sw.js')
    return new Response('', { status: 404 })

  return new Response(cleanupServiceWorkerScript, {
    headers: {
      'Content-Type': 'application/javascript; charset=utf-8',
      'Cache-Control': 'no-store, no-cache, must-revalidate, proxy-revalidate',
      'Service-Worker-Allowed': '/',
    },
  })
}
