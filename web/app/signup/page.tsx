'use client'
import { useRouter, useSearchParams } from 'next/navigation'
import { useCallback } from 'react'
import { useTranslation } from 'react-i18next'
import MailForm from './components/input-mail'

const Signup = () => {
  const router = useRouter()
  const searchParams = useSearchParams()
  const { t } = useTranslation()

  return (
    <div className="mx-auto mt-8 w-full">
      <div className="mx-auto mb-10 w-full">
        <h2 className="title-4xl-semi-bold text-text-primary">申请加入内测</h2>
        <p className="body-md-regular mt-2 text-text-tertiary">填写您的信息，我们将尽快审核您的申请</p>
      </div>
      <MailForm />
    </div>
  )
}

export default Signup
