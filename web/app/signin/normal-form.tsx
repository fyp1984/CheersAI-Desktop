import { RiContractLine, RiDoorLockLine, RiErrorWarningFill } from '@remixicon/react'
import Link from 'next/link'
import { useRouter, useSearchParams } from 'next/navigation'
import { useCallback, useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import Toast from '@/app/components/base/toast'
import { useGlobalPublicStore } from '@/context/global-public-context'
import { isDesktopSSOEnabled } from '@/service/sso-desktop-auth'
import { useIsLogin } from '@/service/use-common'
import { LicenseStatus } from '@/types/feature'
import Loading from '../components/base/loading'
import SSOAuth from './components/sso-auth'
import { resolvePostLoginRedirect } from './utils/post-login-redirect'

const NormalForm = () => {
  const { t } = useTranslation()
  const router = useRouter()
  const searchParams = useSearchParams()
  const { isLoading: isCheckLoading, data: loginData } = useIsLogin()
  const isLoggedIn = loginData?.logged_in
  const message = searchParams.get('message') || ''
  const [isInitCheckLoading, setInitCheckLoading] = useState(true)
  const [isRedirecting, setIsRedirecting] = useState(false)
  const isLoading = isCheckLoading || isInitCheckLoading || isRedirecting
  const { systemFeatures } = useGlobalPublicStore()
  const legalUrl = 'https://cheersai.cloud'

  const init = useCallback(async () => {
    try {
      if (isLoggedIn) {
        setIsRedirecting(true)
        const redirectUrl = resolvePostLoginRedirect(searchParams)
        // Prevent redirect loop if the target is also signin page
        if (redirectUrl && (redirectUrl.includes('/signin') || redirectUrl.includes('/login'))) {
          router.replace('/apps')
        }
        else {
          router.replace(redirectUrl || '/apps')
        }
        return
      }

      if (message) {
        Toast.notify({
          type: 'error',
          message,
        })
      }
    }
    catch (error) {
      console.error(error)
    }
    finally { setInitCheckLoading(false) }
  }, [isLoggedIn, message, router, searchParams])
  useEffect(() => {
    init()
  }, [init])
  if (isLoading) {
    return (
      <div className="signin-loading">
        <Loading type="area" />
      </div>
    )
  }
  if (systemFeatures.license?.status === LicenseStatus.LOST) {
    return (
      <div className="mx-auto mt-8 w-full">
        <div className="relative">
          <div className="rounded-lg bg-gradient-to-r from-workflow-workflow-progress-bg-1 to-workflow-workflow-progress-bg-2 p-4">
            <div className="shadows-shadow-lg relative mb-2 flex h-10 w-10 items-center justify-center rounded-xl bg-components-card-bg shadow">
              <RiContractLine className="h-5 w-5" />
              <RiErrorWarningFill className="absolute -right-1 -top-1 h-4 w-4 text-text-warning-secondary" />
            </div>
            <p className="system-sm-medium text-text-primary">{t('licenseLost', { ns: 'login' })}</p>
            <p className="system-xs-regular mt-1 text-text-tertiary">{t('licenseLostTip', { ns: 'login' })}</p>
          </div>
        </div>
      </div>
    )
  }
  if (systemFeatures.license?.status === LicenseStatus.EXPIRED) {
    return (
      <div className="mx-auto mt-8 w-full">
        <div className="relative">
          <div className="rounded-lg bg-gradient-to-r from-workflow-workflow-progress-bg-1 to-workflow-workflow-progress-bg-2 p-4">
            <div className="shadows-shadow-lg relative mb-2 flex h-10 w-10 items-center justify-center rounded-xl bg-components-card-bg shadow">
              <RiContractLine className="h-5 w-5" />
              <RiErrorWarningFill className="absolute -right-1 -top-1 h-4 w-4 text-text-warning-secondary" />
            </div>
            <p className="system-sm-medium text-text-primary">{t('licenseExpired', { ns: 'login' })}</p>
            <p className="system-xs-regular mt-1 text-text-tertiary">{t('licenseExpiredTip', { ns: 'login' })}</p>
          </div>
        </div>
      </div>
    )
  }
  if (systemFeatures.license?.status === LicenseStatus.INACTIVE) {
    return (
      <div className="mx-auto mt-8 w-full">
        <div className="relative">
          <div className="rounded-lg bg-gradient-to-r from-workflow-workflow-progress-bg-1 to-workflow-workflow-progress-bg-2 p-4">
            <div className="shadows-shadow-lg relative mb-2 flex h-10 w-10 items-center justify-center rounded-xl bg-components-card-bg shadow">
              <RiContractLine className="h-5 w-5" />
              <RiErrorWarningFill className="absolute -right-1 -top-1 h-4 w-4 text-text-warning-secondary" />
            </div>
            <p className="system-sm-medium text-text-primary">{t('licenseInactive', { ns: 'login' })}</p>
            <p className="system-xs-regular mt-1 text-text-tertiary">{t('licenseInactiveTip', { ns: 'login' })}</p>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="signin-main">
      <h2 className="signin-main__title">{t('signinRefresh.formTitle', { ns: 'login' })}</h2>
      <div className="signin-main__form">
        {isDesktopSSOEnabled() && (
          <SSOAuth protocol="" />
        )}

        {!isDesktopSSOEnabled() && (
          <div className="signin-main__status" role="alert">
            <div className="signin-main__status-title">
              <RiDoorLockLine className="mr-2 h-5 w-5 text-red-500" />
              <p>{t('signinRefresh.ssoUnavailableTitle', { ns: 'login' })}</p>
            </div>
            <p className="signin-main__status-copy">{t('signinRefresh.ssoUnavailableDescription', { ns: 'login' })}</p>
          </div>
        )}
      </div>
      <div className="signin-main__footer">
        <p>
          {t('signup.noAccount', { ns: 'login' })}
          <Link
            className="signin-main__link"
            href="/signup"
            prefetch={false}
          >
            {t('signinRefresh.applyTrial', { ns: 'login' })}
          </Link>
        </p>
        {!systemFeatures.branding.enabled && (
          <p className="signin-main__legal-copy">
            <span>{t('signinRefresh.termsPrefix', { ns: 'login' })}</span>
            <Link
              className="signin-main__link signin-main__legal-link"
              target="_blank"
              rel="noopener noreferrer"
              href={legalUrl}
            >
              {t('signinRefresh.termsServiceLabel', { ns: 'login' })}
            </Link>
            <span>{t('signinRefresh.termsJoiner', { ns: 'login' })}</span>
            <Link
              className="signin-main__link signin-main__legal-link"
              target="_blank"
              rel="noopener noreferrer"
              href={legalUrl}
            >
              {t('signinRefresh.privacyPolicyLabel', { ns: 'login' })}
            </Link>
          </p>
        )}
      </div>
    </div>
  )
}

export default NormalForm
