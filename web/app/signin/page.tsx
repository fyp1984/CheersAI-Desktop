'use client'
import { useSearchParams } from 'next/navigation'
import { useEffect } from 'react'
import usePSInfo from '../components/billing/partner-stack/use-ps-info'
import NormalForm from './normal-form'
import OneMoreStep from './one-more-step'

const SignIn = () => {
  const searchParams = useSearchParams()
  const step = searchParams.get('step')
  const { saveOrUpdate } = usePSInfo()

  useEffect(() => {
    saveOrUpdate()
  }, [])

  if (step === 'next')
    return <OneMoreStep />
  
  // 确保 basePath 是有效的
  const basePath = process.env.NEXT_PUBLIC_BASE_PATH || ''
  
  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-gray-50 py-12 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        <img
          className="mx-auto h-12 w-auto"
          src={`${basePath}/logo/logo-site.png`}
          alt="CheersAI"
        />
        <NormalForm />
      </div>
    </div>
  )
}

export default SignIn
