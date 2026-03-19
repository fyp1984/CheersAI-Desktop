'use client'
import Link from 'next/link'
import { useCallback, useState } from 'react'
import { useTranslation } from 'react-i18next'
import Button from '@/app/components/base/button'
import Input from '@/app/components/base/input'
import Toast from '@/app/components/base/toast'
import Split from '@/app/signin/split'
import { emailRegex } from '@/config'
import { useGlobalPublicStore } from '@/context/global-public-context'
import { useLocale } from '@/context/i18n'
import { applyForBeta } from '@/service/common'

export default function Form() {
  const { t } = useTranslation()
  const [email, setEmail] = useState('')
  const [name, setName] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [submitted, setSubmitted] = useState(false)
  const locale = useLocale()
  const { systemFeatures } = useGlobalPublicStore()

  const handleSubmit = useCallback(async () => {
    if (isLoading)
      return

    if (!email) {
      Toast.notify({ type: 'error', message: t('error.emailEmpty', { ns: 'login' }) })
      return
    }
    if (!emailRegex.test(email)) {
      Toast.notify({
        type: 'error',
        message: t('error.emailInValid', { ns: 'login' }),
      })
      return
    }
    if (!name?.trim()) {
      Toast.notify({ type: 'error', message: '请输入您的姓名' })
      return
    }

    try {
      setIsLoading(true)
      const res = await applyForBeta({ email, name, language: locale })
      if (res.result === 'success') {
        setSubmitted(true)
        Toast.notify({ type: 'success', message: '申请已提交，请等待管理员审核' })
      }
      else {
        Toast.notify({ type: 'error', message: res.data || '申请失败，请重试' })
      }
    }
    catch (error: any) {
      Toast.notify({ type: 'error', message: error.message || '申请失败，请重试' })
    }
    finally {
      setIsLoading(false)
    }
  }, [email, name, locale, isLoading, t])

  if (submitted) {
    return (
      <div className="text-center">
        <div className="mb-6 rounded-lg bg-green-50 border border-green-200 p-6">
          <div className="mb-4 text-4xl">✓</div>
          <h3 className="text-lg font-semibold text-green-800 mb-2">申请已提交</h3>
          <p className="text-sm text-green-700">
            我们已收到您的内测申请，管理员将尽快审核。
            <br />
            审核通过后，您将收到邮件通知。
          </p>
        </div>
        <Link
          className="text-text-accent hover:underline"
          href="/signin"
        >
          返回登录页面
        </Link>
      </div>
    )
  }

  return (
    <form onSubmit={(e) => {
      e.preventDefault()
      handleSubmit()
    }}
    >
      <div className="mb-3">
        <label htmlFor="name" className="system-md-semibold my-2 text-text-secondary">
          姓名
        </label>
        <div className="mt-1">
          <Input
            value={name}
            onChange={e => setName(e.target.value)}
            id="name"
            type="text"
            autoComplete="name"
            placeholder="请输入您的姓名"
            tabIndex={1}
          />
        </div>
      </div>
      <div className="mb-3">
        <label htmlFor="email" className="system-md-semibold my-2 text-text-secondary">
          {t('email', { ns: 'login' })}
        </label>
        <div className="mt-1">
          <Input
            value={email}
            onChange={e => setEmail(e.target.value)}
            id="email"
            type="email"
            autoComplete="email"
            placeholder={t('emailPlaceholder', { ns: 'login' }) || ''}
            tabIndex={2}
          />
        </div>
      </div>
      <div className="mb-2">
        <Button
          tabIndex={3}
          variant="primary"
          type="submit"
          disabled={isLoading || !email || !name}
          className="w-full"
        >
          {isLoading ? '提交中...' : '申请加入内测'}
        </Button>
      </div>
      <Split className="mb-5 mt-4" />

      <div className="text-[13px] font-medium leading-4 text-text-secondary">
        <span>{t('signup.haveAccount', { ns: 'login' })}</span>
        <Link
          className="text-text-accent"
          href="/signin"
        >
          {t('signup.signIn', { ns: 'login' })}
        </Link>
      </div>

      {!systemFeatures.branding.enabled && (
        <>
          <div className="system-xs-regular mt-3 block w-full text-text-tertiary">
            {t('tosDesc', { ns: 'login' })}
            &nbsp;
            <Link
              className="system-xs-medium text-text-secondary hover:underline"
              target="_blank"
              rel="noopener noreferrer"
              href="https://cheersai.cloud"
            >
              {t('tos', { ns: 'login' })}
            </Link>
            &nbsp;&&nbsp;
            <Link
              className="system-xs-medium text-text-secondary hover:underline"
              target="_blank"
              rel="noopener noreferrer"
              href="https://cheersai.cloud"
            >
              {t('pp', { ns: 'login' })}
            </Link>
          </div>
        </>
      )}

    </form>
  )
}
