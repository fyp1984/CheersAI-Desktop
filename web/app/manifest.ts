import { MetadataRoute } from 'next'

export default function manifest(): MetadataRoute.Manifest {
  const basePath = process.env.NEXT_PUBLIC_BASE_PATH || ''

  return {
    name: 'CheersAI',
    short_name: 'CheersAI',
    description: 'Build Production Ready Agentic AI Solutions',
    start_url: `${basePath}/`,
    scope: `${basePath}/`,
    display: 'standalone',
    background_color: '#ffffff',
    theme_color: '#1C64F2',
    icons: [
      {
        src: `${basePath}/icon-192x192.png`,
        sizes: '192x192',
        type: 'image/png',
        purpose: 'any',
      },
      {
        src: `${basePath}/icon-192x192.png`,
        sizes: '192x192',
        type: 'image/png',
        purpose: 'maskable',
      },
      {
        src: `${basePath}/icon-256x256.png`,
        sizes: '256x256',
        type: 'image/png',
      },
      {
        src: `${basePath}/icon-384x384.png`,
        sizes: '384x384',
        type: 'image/png',
      },
      {
        src: `${basePath}/icon-512x512.png`,
        sizes: '512x512',
        type: 'image/png',
      },
    ],
    shortcuts: [
      {
        name: 'Apps',
        short_name: 'Apps',
        url: `${basePath}/apps`,
        icons: [{ src: `${basePath}/icon-96x96.png`, sizes: '96x96' }],
      },
      {
        name: 'Datasets',
        short_name: 'Datasets',
        url: `${basePath}/datasets`,
        icons: [{ src: `${basePath}/icon-96x96.png`, sizes: '96x96' }],
      },
    ],
  }
}
