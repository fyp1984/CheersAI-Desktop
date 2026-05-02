'use client'

import type { AppDetailResponse } from '@/models/app'
import {
  RiCloseLine,
  RiDownload2Line,
  RiFileCopyLine,
  RiQrCodeLine,
} from '@remixicon/react'
import { toPng } from 'html-to-image'
import { QRCodeCanvas as QRCode } from 'qrcode.react'
import { useMemo, useRef, useState } from 'react'
import AppIcon from '@/app/components/base/app-icon'
import Button from '@/app/components/base/button'
import Modal from '@/app/components/base/modal'
import Toast from '@/app/components/base/toast'
import { downloadUrl } from '@/utils/download'
import { basePath } from '@/utils/var'

type SharePosterModalProps = {
  isShow: boolean
  appInfo: AppDetailResponse
  onClose: () => void
}

const OFFICIAL_SITE_URL = 'https://www.cheersai.cloud/'
const OFFICIAL_ACCOUNT_NAME = 'CheersAI'
const OFFICIAL_ACCOUNT_QR_IMAGE = `${basePath}/logo/wechat-official-account-qr.jpg`
const PRODUCT_LOGO_IMAGE = `${basePath}/logo/CheersAI.png`

const clampText = (text: string, maxLength: number) => {
  const cleanText = text.trim()
  return cleanText.length > maxLength ? `${cleanText.slice(0, maxLength)}...` : cleanText
}

const SharePosterModal = ({
  isShow,
  appInfo,
  onClose,
}: SharePosterModalProps) => {
  const posterRef = useRef<HTMLDivElement>(null)
  const [isRendering, setIsRendering] = useState(false)
  const posterTitle = appInfo.site?.title || appInfo.name
  const agentDescription = useMemo(
    () => clampText(appInfo.description || appInfo.site?.description || '这个智能体可以帮助你更高效地完成业务咨询、内容生成和知识协作。', 128),
    [appInfo.description, appInfo.site?.description],
  )

  const renderPoster = async () => {
    if (!posterRef.current)
      return ''

    setIsRendering(true)
    try {
      return await toPng(posterRef.current, {
        cacheBust: true,
        pixelRatio: 2,
        backgroundColor: '#f7f9fc',
      })
    }
    finally {
      setIsRendering(false)
    }
  }

  const handleDownload = async () => {
    const dataUrl = await renderPoster()
    if (!dataUrl)
      return
    downloadUrl({ url: dataUrl, fileName: `${posterTitle}-分享海报.png` })
    Toast.notify({ type: 'success', message: '海报已导出为图片' })
  }

  const handleCopyImage = async () => {
    const dataUrl = await renderPoster()
    if (!dataUrl)
      return

    try {
      const blob = await (await fetch(dataUrl)).blob()
      await navigator.clipboard.write([new ClipboardItem({ [blob.type]: blob })])
      Toast.notify({ type: 'success', message: '海报图片已复制' })
    }
    catch {
      Toast.notify({ type: 'warning', message: '当前环境不支持复制图片，请先保存海报' })
    }
  }

  return (
    <Modal
      isShow={isShow}
      onClose={onClose}
      className="max-h-[88vh] max-w-[960px] !p-0"
      containerClassName="p-6"
      clickOutsideNotClose
    >
      <div className="flex max-h-[88vh] flex-col overflow-hidden rounded-2xl">
        <div className="flex shrink-0 items-start justify-between border-b border-divider-subtle px-6 py-5">
          <div>
            <div className="text-xl font-semibold leading-7 text-text-primary">智能体分享海报</div>
            <div className="mt-1 text-sm leading-5 text-text-tertiary">生成一张可转发到微信、朋友圈和社群的智能体介绍图。</div>
          </div>
          <button
            type="button"
            className="flex h-8 w-8 items-center justify-center rounded-lg text-text-tertiary hover:bg-state-base-hover hover:text-text-primary"
            onClick={onClose}
          >
            <RiCloseLine className="h-5 w-5" />
          </button>
        </div>

        <div className="grid min-h-0 flex-1 grid-cols-[430px_1fr] overflow-hidden">
          <div className="flex min-h-0 justify-center overflow-y-auto bg-[#edf4f7] px-8 py-5">
            <div className="flex min-h-full items-center">
              <div
                ref={posterRef}
                className="relative h-[604px] w-[340px] overflow-hidden bg-[#f8fbff] text-[#12202f] shadow-[0_24px_60px_rgba(18,32,47,0.18)]"
              >
                <div className="absolute inset-x-0 top-0 h-[244px] bg-[linear-gradient(145deg,#eef7ff_0%,#f7fbff_52%,#edf8f1_100%)]" />
                <div className="absolute inset-x-0 top-0 h-[244px] opacity-45 [background-image:linear-gradient(rgba(46,94,170,0.09)_1px,transparent_1px),linear-gradient(90deg,rgba(46,94,170,0.09)_1px,transparent_1px)] [background-size:28px_28px]" />
                <div className="absolute right-[-48px] top-[-40px] h-[168px] w-[168px] rotate-12 bg-[linear-gradient(135deg,rgba(44,111,255,0.18),rgba(36,190,139,0.12))]" />
                <div className="relative flex h-full flex-col px-7 pb-0 pt-6">
                  <div className="flex items-center gap-2 opacity-80">
                    <img
                      src={PRODUCT_LOGO_IMAGE}
                      alt="CheersAI"
                      className="h-8 w-8 rounded-lg object-cover shadow-[0_6px_14px_rgba(47,107,255,0.18)]"
                    />
                    <div className="min-w-0">
                      <div className="text-[10px] font-semibold leading-[14px] text-[#476071]">CheersAI Desktop</div>
                      <div className="truncate text-[8px] leading-[12px] text-[#6f8291]">智享 AI · 安全随行</div>
                    </div>
                  </div>

                  <div className="mt-11 flex items-start gap-3">
                    <div className="shrink-0">
                      <div className="flex h-[52px] w-[52px] items-center justify-center rounded-[15px] border border-[#8fb2ff] bg-[rgba(255,255,255,0.18)] shadow-[0_10px_22px_rgba(47,107,255,0.16),inset_0_0_0_1px_rgba(255,255,255,0.45)] backdrop-blur">
                        <AppIcon
                          size="xl"
                          iconType={appInfo.site?.icon_type || appInfo.icon_type}
                          icon={appInfo.site?.icon || appInfo.icon}
                          background={appInfo.site?.icon_background || appInfo.icon_background}
                          imageUrl={appInfo.site?.icon_url || appInfo.icon_url}
                          className="border-0"
                        />
                      </div>
                    </div>
                    <div className="min-w-0 flex-1 pt-0.5">
                      <div className="text-[11px] font-semibold leading-[16px] text-[#2f6bff]">
                        智能体
                      </div>
                      <div className="mt-1 line-clamp-2 text-[24px] font-semibold leading-[31px] text-[#101828]">
                        {posterTitle}
                      </div>
                      <div className="mt-3 h-[3px] w-10 bg-[#2f6bff]" />
                    </div>
                  </div>

                  <div className="mt-7 h-[178px] bg-white/90 px-5 py-5 shadow-[0_12px_32px_rgba(18,32,47,0.08)]">
                    <div className="flex items-center gap-2">
                      <div className="h-4 w-[3px] bg-[#2f6bff]" />
                      <div className="text-[12px] font-semibold leading-none text-[#2364d2]">智能体介绍</div>
                    </div>
                    <div className="mt-4 line-clamp-5 text-[14px] leading-[25px] text-[#344054]">{agentDescription}</div>
                  </div>

                  <div className="mx-[-28px] mt-auto border-t border-[#dce8f3] bg-[#f7fbff] px-7 pb-5 pt-5">
                    <div className="flex items-center justify-between">
                      <div className="text-[11px] font-semibold leading-4 text-[#2f6bff]">CheersAI</div>
                      <div className="text-[9px] leading-[13px] text-[#7890a4]">官网与公众号</div>
                    </div>
                    <div className="mt-4 grid grid-cols-2 gap-4">
                      <div className="min-w-0 bg-white px-3 py-3 shadow-[0_8px_22px_rgba(18,32,47,0.06)]">
                        <div className="flex h-[76px] w-[76px] items-center justify-center bg-white">
                          <QRCode size={72} value={OFFICIAL_SITE_URL} />
                        </div>
                        <div className="mt-2 text-[11px] font-semibold leading-[15px] text-[#101828]">官网</div>
                        <div className="mt-0.5 text-[9px] leading-[13px] text-[#66788a]">了解产品与方案</div>
                      </div>
                      <div className="min-w-0 bg-white px-3 py-3 shadow-[0_8px_22px_rgba(18,32,47,0.06)]">
                        <div className="flex h-[76px] w-[76px] items-center justify-center bg-white">
                          <img
                            src={OFFICIAL_ACCOUNT_QR_IMAGE}
                            alt="CheersAI 公众号二维码"
                            className="h-[72px] w-[72px] object-contain"
                          />
                        </div>
                        <div className="mt-2 text-[11px] font-semibold leading-[15px] text-[#101828]">公众号</div>
                        <div className="mt-0.5 text-[9px] leading-[13px] text-[#66788a]">
                          关注
                          {' '}
                          {OFFICIAL_ACCOUNT_NAME}
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div className="flex min-w-0 flex-col overflow-y-auto bg-components-panel-bg px-7 py-6">
            <div>
              <div className="text-sm font-semibold leading-5 text-text-primary">海报内容</div>
              <div className="mt-3 border-y border-divider-subtle py-4">
                <div className="system-sm-semibold text-text-primary">智能体介绍</div>
                <div className="system-xs-regular mt-2 text-text-tertiary">{agentDescription}</div>
                <div className="system-xs-regular mt-2 text-text-quaternary">海报内最多展示 4 行，超出自动省略。</div>
              </div>
            </div>

            <div className="mt-6 border-y border-divider-subtle py-4">
              <div className="flex items-center gap-2 text-sm font-semibold text-text-primary">
                <RiQrCodeLine className="h-4 w-4" />
                二维码配置
              </div>
              <div className="mt-4 space-y-3 text-xs leading-5 text-text-tertiary">
                <div className="flex justify-between gap-3">
                  <span>官网二维码</span>
                  <span className="text-text-secondary">{OFFICIAL_SITE_URL}</span>
                </div>
                <div className="flex justify-between gap-3">
                  <span>公众号二维码</span>
                  <span className="text-text-secondary">{OFFICIAL_ACCOUNT_NAME}</span>
                </div>
                <div className="flex justify-between gap-3">
                  <span>展示方式</span>
                  <span className="text-text-secondary">底部并排展示</span>
                </div>
              </div>
            </div>

            <div className="mt-auto flex shrink-0 items-center justify-between border-t border-divider-subtle pt-5">
              <div className="text-xs leading-5 text-text-tertiary">
                建议保存后转发到微信或朋友圈。
              </div>
              <div className="flex items-center gap-2">
                <Button onClick={handleCopyImage} disabled={isRendering}>
                  <RiFileCopyLine className="mr-1 h-4 w-4" />
                  复制图片
                </Button>
                <Button variant="primary" onClick={handleDownload} loading={isRendering}>
                  <RiDownload2Line className="mr-1 h-4 w-4" />
                  保存海报
                </Button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </Modal>
  )
}

export default SharePosterModal
