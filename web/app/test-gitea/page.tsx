'use client'

import { useState } from 'react'

export default function TestGiteaPage() {
  const [result, setResult] = useState('')
  const [loading, setLoading] = useState(false)

  const testGiteaAPI = async () => {
    setLoading(true)
    setResult('Testing...')
    
    try {
      const csrfToken = document.cookie.match(/csrf_token=([^;]+)/)?.[1] || ''
      console.log('CSRF Token:', csrfToken ? 'Found' : 'Not found')
      
      const url = 'http://localhost:5001/console/api/gitea/files?path='
      console.log('Calling:', url)
      
      const res = await fetch(url, {
        credentials: 'include',
        headers: {
          'X-CSRF-Token': csrfToken,
        },
      })
      
      console.log('Response status:', res.status)
      console.log('Response headers:', Object.fromEntries(res.headers.entries()))
      
      if (res.ok) {
        const data = await res.json()
        console.log('Response data:', data)
        setResult(`✓ Success!\n\nFiles: ${JSON.stringify(data, null, 2)}`)
      } else {
        const errorText = await res.text()
        console.error('Error response:', errorText)
        setResult(`✗ Error ${res.status}\n\n${errorText}`)
      }
    } catch (err) {
      console.error('Exception:', err)
      setResult(`✗ Exception: ${err instanceof Error ? err.message : String(err)}`)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold mb-4">Test Gitea API</h1>
      
      <button
        onClick={testGiteaAPI}
        disabled={loading}
        className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50"
      >
        {loading ? 'Testing...' : 'Test Gitea Files API'}
      </button>
      
      {result && (
        <pre className="mt-4 p-4 bg-gray-100 rounded whitespace-pre-wrap">
          {result}
        </pre>
      )}
      
      <div className="mt-8 p-4 bg-yellow-50 border border-yellow-200 rounded">
        <h2 className="font-bold mb-2">Debug Info:</h2>
        <p>CSRF Token: {document.cookie.match(/csrf_token=([^;]+)/)?.[1] ? 'Present' : 'Missing'}</p>
        <p>Cookies: {document.cookie || 'None'}</p>
      </div>
    </div>
  )
}
