import { RiContractLine, RiDoorLockLine, RiErrorWarningFill } from '@remixicon/react'
import Link from 'next/link'
import { useRouter, useSearchParams } from 'next/navigation'
import * as React from 'react'
import { useCallback, useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import Toast from '@/app/components/base/toast'
import { IS_CE_EDITION } from '@/config'
import { useGlobalPublicStore } from '@/context/global-public-context'
import { invitationCheck } from '@/service/common'
import { isDesktopSSOEnabled } from '@/service/sso-desktop-auth'
import { useIsLogin } from '@/service/use-common'
import { LicenseStatus } from '@/types/feature'
import { cn } from '@/utils/classnames'
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
  const invite_token = searchParams.get('invite_token') || ''
  const [isInitCheckLoading, setInitCheckLoading] = useState(true)
  const [isRedirecting, setIsRedirecting] = useState(false)
  const isLoading = isCheckLoading || isInitCheckLoading || isRedirecting
  const { systemFeatures } = useGlobalPublicStore()
  const [, setWorkSpaceName] = useState('')

  const isInviteLink = Boolean(invite_token && invite_token !== 'null')

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
      if (isInviteLink) {
        const checkRes = await invitationCheck({
          url: '/activate/check',
          params: {
            token: invite_token,
          },
        })
        setWorkSpaceName(checkRes?.data?.workspace_name || '')
      }
    }
    catch (error) {
      console.error(error)
    }
    finally { setInitCheckLoading(false) }
  }, [invite_token, isInviteLink, isLoggedIn, message, router, searchParams])
  useEffect(() => {
    init()
  }, [init])
  if (isLoading) {
    return (
      <div className={
        cn(
          'flex w-full grow flex-col items-center justify-center',
          'px-6',
          'md:px-[108px]',
        )
      }
      >
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
    <>
      <div className="w-full">
        {/* 标题 */}
        <div className="mb-8 text-center">
          <h2 className="text-2xl font-bold text-gray-900">
            欢迎回来
          </h2>
        </div>

        {/* SSO 登录按钮 */}
        <div className="space-y-4">
          {isDesktopSSOEnabled() && (
            <SSOAuth protocol="" />
          )}

          {!isDesktopSSOEnabled() && (
            <div className="rounded-lg border border-red-200 bg-red-50 p-4">
              <div className="mb-2 flex items-center">
                <RiDoorLockLine className="mr-2 h-5 w-5 text-red-500" />
                <p className="text-sm font-medium text-red-800">SSO 登录未配置</p>
              </div>
              <p className="text-sm text-red-700">请联系管理员配置 SSO 登录</p>
            </div>
          )}
        </div>

        {/* 底部提示 */}
        <div className="mt-6 space-y-3 text-center text-xs text-gray-500">
          <p>
            还没有账号？
            <Link
              className="ml-1 text-blue-600 hover:text-blue-700"
              href="/signup"
            >
              申请试用
            </Link>
          </p>

          {!systemFeatures.branding.enabled && (
            <>
              <p>
                登录即表示您同意我们的
                <Link
                  className="mx-1 text-blue-600 hover:text-blue-700"
                  target="_blank"
                  rel="noopener noreferrer"
                  href="https://cheersai.cloud"
                >
                  服务条款
                </Link>
                和
                <Link
                  className="ml-1 text-blue-600 hover:text-blue-700"
                  target="_blank"
                  rel="noopener noreferrer"
                  href="https://cheersai.cloud"
                >
                  隐私政策
                </Link>
              </p>
              {IS_CE_EDITION && (
                <p>
                  需要初始化系统？
                  <Link
                    className="ml-1 text-blue-600 hover:text-blue-700"
                    href="/install"
                  >
                    设置管理员账户
                  </Link>
                </p>
              )}
            </>
          )}
        </div>
      </div>
    </>
  )
}

export default NormalForm
