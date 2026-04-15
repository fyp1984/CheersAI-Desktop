'use client'

import { useState } from 'react'
import { API_PREFIX } from '@/config'

export default function TestGiteaPage() {
  const [result, setResult] = useState('')
  const [loading, setLoading] = useState(false)
  const csrfTokenStatus = document.cookie.match(/csrf_token=([^;]+)/)?.[1] ? 'Present' : 'Missing'
  const cookieText = document.cookie || 'None'

  const testGiteaAPI = async () => {
    setLoading(true)
    setResult('Testing...')

    try {
      const csrfToken = document.cookie.match(/csrf_token=([^;]+)/)?.[1] || ''
      const url = `${API_PREFIX}/gitea/files?path=`

      const res = await fetch(url, {
        credentials: 'include',
        headers: {
          'X-CSRF-Token': csrfToken,
        },
      })

      if (res.ok) {
        const data = await res.json()
        setResult(`✓ Success!\n\nFiles: ${JSON.stringify(data, null, 2)}`)
      }
      else {
        const errorText = await res.text()
        console.error('Error response:', errorText)
        setResult(`✗ Error ${res.status}\n\n${errorText}`)
      }
    }
    catch (err) {
      console.error('Exception:', err)
      setResult(`✗ Exception: ${err instanceof Error ? err.message : String(err)}`)
    }
    finally {
      setLoading(false)
    }
  }

  return (
    <div className="p-8">
      <h1 className="mb-4 text-2xl font-bold">Test Gitea API</h1>

      <button
        className="rounded bg-blue-500 px-4 py-2 text-white hover:bg-blue-600 disabled:opacity-50"
        disabled={loading}
        onClick={testGiteaAPI}
      >
        {loading ? 'Testing...' : 'Test Gitea Files API'}
      </button>

      {result && (
        <pre className="mt-4 whitespace-pre-wrap rounded bg-gray-100 p-4">
          {result}
        </pre>
      )}

      <div className="mt-8 rounded border border-yellow-200 bg-yellow-50 p-4">
        <h2 className="mb-2 font-bold">Debug Info:</h2>
        <p>
          CSRF Token:
          {' '}
          {csrfTokenStatus}
        </p>
        <p>
          Cookies:
          {' '}
          {cookieText}
        </p>
      </div>
    </div>
  )
}
