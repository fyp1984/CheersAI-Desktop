import { FileBayConfigDownload } from '../components/filebay-config-download'

export default function FileBayDownloadPage() {
  return (
    <div className="min-h-screen bg-gray-50 py-12">
      <div className="max-w-2xl mx-auto px-4">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-4">
            FileBay 配置管理
          </h1>
          <p className="text-gray-600">
            下载 FileBay 配置文件，用于 Desktop App 的文件上传功能
          </p>
        </div>
        
        <FileBayConfigDownload />
        
        <div className="mt-8 p-6 bg-blue-50 border border-blue-200 rounded-lg">
          <h3 className="text-lg font-semibold text-blue-900 mb-3">
            💡 配置文件说明
          </h3>
          <div className="text-blue-800 space-y-2">
            <p><strong>文件名:</strong> filebay-config.json</p>
            <p><strong>包含信息:</strong></p>
            <ul className="list-disc list-inside ml-4 space-y-1">
              <li>FileBay 服务器地址</li>
              <li>用户名和仓库名</li>
              <li>用户邮箱 (用于企业配置)</li>
              <li>下载时间和版本信息</li>
            </ul>
            <p className="mt-3">
              <strong>安全说明:</strong> 配置文件不包含敏感的 API Token，仅包含连接信息。
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}