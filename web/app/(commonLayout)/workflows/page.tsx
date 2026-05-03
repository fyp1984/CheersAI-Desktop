'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'

const WorkflowsPage = () => {
  const router = useRouter()

  useEffect(() => {
    router.replace('/apps?category=workflow')
  }, [router])

  return null
}

export default WorkflowsPage
