import { useState } from 'react'
import Button from '@/app/components/base/button'

type WechatAuthProps = {
  disabled?: boolean
}

export default function WechatAuth(props: WechatAuthProps) {
  const [qrCodeUrl, setQrCodeUrl] = useState<string>('')
  const [showQrCode, setShowQrCode] = useState(false)

  const handleWechatLogin = async () => {
    try {
      setShowQrCode(true)
      // 这里应该调用后端API获取微信二维码
      // const response = await fetch(getOAuthLink('/oauth/wechat/qrcode'))
      // const data = await response.json()
      // setQrCodeUrl(data.qrCodeUrl)

      // 临时模拟二维码URL
      setQrCodeUrl('https://via.placeholder.com/200x200?text=WeChat+QR+Code')
    }
    catch (error) {
      console.error('获取微信二维码失败:', error)
    }
  }

  return (
    <div className="w-full">
      {!showQrCode
        ? (
            <Button
              disabled={props.disabled}
              className="w-full bg-green-500 text-white hover:bg-green-600"
              onClick={handleWechatLogin}
            >
              <div className="flex items-center justify-center">
                <svg className="mr-2 h-5 w-5" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M8.691 2.188C3.891 2.188 0 5.476 0 9.53c0 2.212 1.17 4.203 3.002 5.55a.59.59 0 0 1 .213.665l-.39 1.48c-.019.07-.048.141-.048.213 0 .163.13.295.29.295a.326.326 0 0 0 .167-.054l1.903-1.114a.864.864 0 0 1 .717-.098 10.16 10.16 0 0 0 2.837.403c.276 0 .543-.027.811-.05-.857-2.578.157-4.972 1.932-6.446 1.703-1.415 4.882-1.900 7.852.24-.71-3.842-4.493-6.616-8.596-6.616z" />
                  <path d="M23.999 14.191c0-3.297-2.993-5.977-6.686-5.977-3.694 0-6.686 2.68-6.686 5.977s2.992 5.977 6.686 5.977a7.785 7.785 0 0 0 2.334-.351.71.71 0 0 1 .590.081l1.579.922a.264.264 0 0 0 .138.044c.134 0 .24-.108.24-.240 0-.06-.024-.115-.04-.171l-.324-1.224a.487.487 0 0 1 .176-.549c1.519-1.117 2.493-2.764 2.493-4.589z" />
                </svg>
                <span className="truncate leading-normal">微信登录</span>
              </div>
            </Button>
          )
        : (
            <div className="w-full rounded-lg border border-gray-200 bg-white p-4">
              <div className="mb-3 text-center">
                <h3 className="text-sm font-medium text-gray-900">微信扫码登录</h3>
                <p className="mt-1 text-xs text-gray-500">请使用微信扫描下方二维码</p>
              </div>
              <div className="mb-3 flex justify-center">
                {qrCodeUrl
                  ? (
                      <img src={qrCodeUrl} alt="微信登录二维码" className="h-32 w-32 border border-gray-200" />
                    )
                  : (
                      <div className="flex h-32 w-32 items-center justify-center border border-gray-200 bg-gray-100">
                        <div className="h-8 w-8 animate-spin rounded-full border-b-2 border-green-500"></div>
                      </div>
                    )}
              </div>
              <div className="text-center">
                <button
                  onClick={() => setShowQrCode(false)}
                  className="text-xs text-blue-600 hover:text-blue-700"
                >
                  返回登录方式选择
                </button>
              </div>
            </div>
          )}
    </div>
  )
}
