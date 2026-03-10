'use client'
import type { FC } from 'react'
import * as React from 'react'
import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { PlusIcon } from '@heroicons/react/24/outline'
import { XMarkIcon } from '@heroicons/react/24/solid'
import {
  RiCheckLine,
  RiEyeOffLine,
  RiMailLine,
  RiPhoneLine,
  RiShieldCheckLine,
  RiUserLine,
  RiIdCardLine,
} from '@remixicon/react'
import Button from '@/app/components/base/button'
import Modal from '@/app/components/base/modal'
import Input from '@/app/components/base/input'
import Select from '@/app/components/base/select'
import useDocumentTitle from '@/hooks/use-document-title'
import type { MaskingRule } from '@/service/data-masking'

const DataMaskingPage: FC = () => {
  const { t } = useTranslation()
  useDocumentTitle(t('menus.dataMasking', { ns: 'common' }))
  
  const [rules] = useState<MaskingRule[]>([])
  const isLoading = false
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [formData, setFormData] = useState({
    name: '',
    type: 'phone',
    pattern: '',
    maskChar: '*',
  })

  // 预设的正则表达式模板
  const patternTemplates = {
    phone: {
      name: '手机号',
      pattern: '1[3-9]\\d{9}',
      example: '13812345678',
      description: '匹配中国大陆手机号',
    },
    email: {
      name: '邮箱',
      pattern: '[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}',
      example: 'user@example.com',
      description: '匹配标准邮箱地址',
    },
    id_card: {
      name: '身份证',
      pattern: '[1-9]\\d{5}(18|19|20)\\d{2}(0[1-9]|1[0-2])(0[1-9]|[12]\\d|3[01])\\d{3}[0-9Xx]',
      example: '110101199001011234',
      description: '匹配18位身份证号',
    },
    bank_card: {
      name: '银行卡号',
      pattern: '\\d{16,19}',
      example: '6222021234567890123',
      description: '匹配16-19位银行卡号',
    },
    ip_address: {
      name: 'IP地址',
      pattern: '\\d{1,3}\\.\\d{1,3}\\.\\d{1,3}\\.\\d{1,3}',
      example: '192.168.1.1',
      description: '匹配IPv4地址',
    },
    address: {
      name: '地址',
      pattern: '.*省.*市.*区.*',
      example: '北京市朝阳区xxx街道',
      description: '匹配包含省市区的地址',
    },
    name: {
      name: '姓名',
      pattern: '[\\u4e00-\\u9fa5]{2,4}',
      example: '张三',
      description: '匹配2-4个中文字符的姓名',
    },
    custom: {
      name: '自定义',
      pattern: '',
      example: '',
      description: '自定义正则表达式',
    },
  }

  // 脱敏策略
  const maskingStrategies = [
    { value: 'partial', name: '部分脱敏', description: '保留部分字符，其余用*替换' },
    { value: 'full', name: '完全脱敏', description: '全部替换为*' },
    { value: 'hash', name: '哈希脱敏', description: '使用哈希算法加密' },
    { value: 'replace', name: '替换脱敏', description: '替换为固定文本' },
  ]

  const [maskingStrategy, setMaskingStrategy] = useState('partial')
  const [keepStart, setKeepStart] = useState(3)
  const [keepEnd, setKeepEnd] = useState(4)
  const [applyToApps, setApplyToApps] = useState<string[]>([])
  const [testInput, setTestInput] = useState('')

  // 脱敏预览函数
  const getMaskingPreview = (input: string, strategy: string) => {
    if (!input) return ''
    
    switch (strategy) {
      case 'partial':
        if (input.length <= keepStart + keepEnd) return input
        const start = input.substring(0, keepStart)
        const end = input.substring(input.length - keepEnd)
        const middle = '*'.repeat(input.length - keepStart - keepEnd)
        return `${start}${middle}${end}`
      case 'full':
        return '*'.repeat(input.length)
      case 'hash':
        return `[HASH:${input.length}位]`
      case 'replace':
        return '[已脱敏]'
      default:
        return input
    }
  }

  // 当规则类型改变时，自动填充对应的正则表达式
  const handleTypeChange = (type: string) => {
    const template = patternTemplates[type as keyof typeof patternTemplates]
    setFormData({
      ...formData,
      type,
      pattern: template.pattern,
      name: formData.name || template.name,
    })
  }

  const handleCreate = () => {
    // TODO: 调用后端 API 创建规则
    console.log('Creating rule:', formData)
    setShowCreateModal(false)
    // 重置表单
    setFormData({
      name: '',
      type: 'phone',
      pattern: '',
      maskChar: '*',
    })
  }

  return (
    <>
      <div className="flex flex-col h-full">
        {/* Header */}
        <div className="flex items-center justify-between px-12 pt-8 pb-4">
          <div>
            <h1 className="text-2xl font-semibold text-gray-900">
              {t('dataMasking.title', { ns: 'common' })}
            </h1>
            <p className="mt-1 text-sm text-gray-500">
              {t('dataMasking.description', { ns: 'common' })}
            </p>
          </div>
          <Button
            variant="primary"
            className="flex items-center gap-2"
            onClick={() => setShowCreateModal(true)}
          >
            <PlusIcon className="w-4 h-4" />
            {t('dataMasking.createRule', { ns: 'common' })}
          </Button>
        </div>

        <div className="flex-1 px-12 pb-8 overflow-y-auto">
          {/* 统计卡片 */}
          <div className="grid grid-cols-4 gap-4 mb-6">
            <div className="bg-white rounded-lg border border-gray-200 p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-500">总规则数</p>
                  <p className="text-2xl font-semibold text-gray-900 mt-1">{rules.length}</p>
                </div>
                <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                  <RiShieldCheckLine className="w-5 h-5 text-blue-600" />
                </div>
              </div>
            </div>

            <div className="bg-white rounded-lg border border-gray-200 p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-500">已启用</p>
                  <p className="text-2xl font-semibold text-green-600 mt-1">
                    {rules.filter(r => r.enabled).length}
                  </p>
                </div>
                <div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center">
                  <RiCheckLine className="w-5 h-5 text-green-600" />
                </div>
              </div>
            </div>

            <div className="bg-white rounded-lg border border-gray-200 p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-500">已禁用</p>
                  <p className="text-2xl font-semibold text-gray-400 mt-1">
                    {rules.filter(r => !r.enabled).length}
                  </p>
                </div>
                <div className="w-10 h-10 bg-gray-100 rounded-lg flex items-center justify-center">
                  <XMarkIcon className="w-5 h-5 text-gray-400" />
                </div>
              </div>
            </div>

            <div className="bg-white rounded-lg border border-gray-200 p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-500">本月脱敏</p>
                  <p className="text-2xl font-semibold text-purple-600 mt-1">1.2K</p>
                </div>
                <div className="w-10 h-10 bg-purple-100 rounded-lg flex items-center justify-center">
                  <RiEyeOffLine className="w-5 h-5 text-purple-600" />
                </div>
              </div>
            </div>
          </div>

          {/* 快速操作和使用指南 */}
          {rules.length === 0 && (
            <div className="grid grid-cols-3 gap-6 mb-6">
              {/* 快速创建模板 */}
              <div className="col-span-2 bg-gradient-to-br from-blue-50 to-indigo-50 rounded-lg border border-blue-200 p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">快速创建常用规则</h3>
                <div className="grid grid-cols-2 gap-3">
                  {[
                    { type: 'phone', name: '手机号脱敏', icon: RiPhoneLine, desc: '保护用户手机号隐私', bgColor: 'bg-blue-100', hoverBgColor: 'group-hover:bg-blue-200', iconColor: 'text-blue-600' },
                    { type: 'email', name: '邮箱脱敏', icon: RiMailLine, desc: '隐藏邮箱地址信息', bgColor: 'bg-green-100', hoverBgColor: 'group-hover:bg-green-200', iconColor: 'text-green-600' },
                    { type: 'id_card', name: '身份证脱敏', icon: RiIdCardLine, desc: '保护身份证号安全', bgColor: 'bg-purple-100', hoverBgColor: 'group-hover:bg-purple-200', iconColor: 'text-purple-600' },
                    { type: 'name', name: '姓名脱敏', icon: RiUserLine, desc: '隐藏真实姓名', bgColor: 'bg-orange-100', hoverBgColor: 'group-hover:bg-orange-200', iconColor: 'text-orange-600' },
                  ].map((template) => {
                    const IconComponent = template.icon
                    return (
                      <button
                        key={template.type}
                        onClick={() => {
                          handleTypeChange(template.type)
                          setShowCreateModal(true)
                        }}
                        className="flex items-start p-4 bg-white rounded-lg border border-gray-200 hover:border-blue-400 hover:shadow-md transition-all text-left group"
                      >
                        <div className={`w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0 mr-3 ${template.bgColor} ${template.hoverBgColor} transition-colors`}>
                          <IconComponent className={`w-5 h-5 ${template.iconColor}`} />
                        </div>
                        <div>
                          <p className="text-sm font-medium text-gray-900">{template.name}</p>
                          <p className="text-xs text-gray-500 mt-1">{template.desc}</p>
                        </div>
                      </button>
                    )
                  })}
                </div>
              </div>

              {/* 使用指南 */}
              <div className="bg-white rounded-lg border border-gray-200 p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">使用指南</h3>
                <div className="space-y-4">
                  <div className="flex items-start">
                    <div className="w-6 h-6 bg-blue-100 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                      <span className="text-xs font-semibold text-blue-600">1</span>
                    </div>
                    <div className="ml-3">
                      <p className="text-sm font-medium text-gray-900">创建规则</p>
                      <p className="text-xs text-gray-500 mt-1">选择数据类型并配置脱敏策略</p>
                    </div>
                  </div>
                  <div className="flex items-start">
                    <div className="w-6 h-6 bg-blue-100 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                      <span className="text-xs font-semibold text-blue-600">2</span>
                    </div>
                    <div className="ml-3">
                      <p className="text-sm font-medium text-gray-900">测试预览</p>
                      <p className="text-xs text-gray-500 mt-1">验证脱敏效果是否符合预期</p>
                    </div>
                  </div>
                  <div className="flex items-start">
                    <div className="w-6 h-6 bg-blue-100 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                      <span className="text-xs font-semibold text-blue-600">3</span>
                    </div>
                    <div className="ml-3">
                      <p className="text-sm font-medium text-gray-900">启用规则</p>
                      <p className="text-xs text-gray-500 mt-1">规则将自动应用到相关场景</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* 规则列表 */}
          {isLoading
            ? (
              <div className="flex items-center justify-center h-64">
                <div className="text-gray-400">
                  {t('loading', { ns: 'common' })}
                </div>
              </div>
              )
            : rules.length === 0
              ? (
                <div className="flex flex-col items-center justify-center h-48 bg-gray-50 rounded-lg border-2 border-dashed border-gray-200">
                  <RiShieldCheckLine className="w-12 h-12 text-gray-300 mb-4" />
                  <h3 className="text-sm font-medium text-gray-900">
                    {t('dataMasking.noRules', { ns: 'common' })}
                  </h3>
                  <p className="text-sm text-gray-500 mt-1">
                    {t('dataMasking.noRulesDescription', { ns: 'common' })}
                  </p>
                </div>
                )
              : (
                <div>
                  <h3 className="text-sm font-semibold text-gray-900 mb-4">脱敏规则列表</h3>
                  <div className="space-y-3">
                    {rules.map(rule => (
                      <div
                        key={rule.id}
                        className="p-4 bg-white rounded-lg border border-gray-200 hover:shadow-md transition-shadow"
                      >
                        <div className="flex items-center justify-between">
                          <div className="flex-1">
                            <div className="flex items-center gap-3">
                              <h3 className="text-sm font-medium text-gray-900">
                                {rule.name}
                              </h3>
                              <span className={`px-2 py-0.5 text-xs rounded ${rule.enabled ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'}`}>
                                {rule.enabled ? t('dataMasking.enabled', { ns: 'common' }) : t('dataMasking.disabled', { ns: 'common' })}
                              </span>
                            </div>
                            <p className="mt-1 text-xs text-gray-500">
                              {rule.type} • {rule.pattern}
                            </p>
                          </div>
                          <div className="flex items-center gap-2">
                            <Button variant="ghost" size="small">编辑</Button>
                            <Button variant="ghost" size="small">删除</Button>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
                )}
        </div>
      </div>

      {/* 创建规则弹窗 - 简化版 */}
      <Modal
        isShow={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        title={t('dataMasking.createRule', { ns: 'common' })}
        className="max-w-[520px]"
        closable
      >
        <div className="mt-6 space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              {t('dataMasking.ruleName', { ns: 'common' })}
            </label>
            <Input
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              placeholder="请输入规则名称"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              {t('dataMasking.ruleType', { ns: 'common' })}
            </label>
            <Select
              items={[
                { value: 'phone', name: '手机号' },
                { value: 'email', name: '邮箱' },
                { value: 'id_card', name: '身份证' },
                { value: 'bank_card', name: '银行卡号' },
                { value: 'ip_address', name: 'IP地址' },
                { value: 'address', name: '地址' },
                { value: 'name', name: '姓名' },
                { value: 'custom', name: '自定义' },
              ]}
              defaultValue={formData.type}
              onSelect={(item) => handleTypeChange(item.value as string)}
            />
            {formData.type !== 'custom' && patternTemplates[formData.type as keyof typeof patternTemplates] && (
              <div className="mt-2 p-3 bg-blue-50 rounded-lg">
                <p className="text-xs text-blue-600">
                  <span className="font-medium">示例：</span>
                  {patternTemplates[formData.type as keyof typeof patternTemplates].example}
                </p>
              </div>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              {t('dataMasking.pattern', { ns: 'common' })}
            </label>
            <Input
              value={formData.pattern}
              onChange={(e) => setFormData({ ...formData, pattern: e.target.value })}
              placeholder={formData.type === 'custom' ? '请输入正则表达式' : '已自动填充'}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              脱敏策略
            </label>
            <Select
              items={maskingStrategies.map(s => ({ value: s.value, name: s.name }))}
              defaultValue={maskingStrategy}
              onSelect={(item) => setMaskingStrategy(item.value as string)}
            />
          </div>

          {maskingStrategy === 'partial' && (
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  保留前几位
                </label>
                <Input
                  type="number"
                  value={keepStart}
                  onChange={(e) => setKeepStart(Number(e.target.value))}
                  min={0}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  保留后几位
                </label>
                <Input
                  type="number"
                  value={keepEnd}
                  onChange={(e) => setKeepEnd(Number(e.target.value))}
                  min={0}
                />
              </div>
            </div>
          )}

          {/* 脱敏预览 */}
          {testInput && (
            <div className="p-4 bg-gray-50 rounded-lg border border-gray-200">
              <p className="text-xs text-gray-500 mb-2">预览效果</p>
              <div className="flex items-center gap-2">
                <span className="text-sm font-mono text-gray-900">{testInput}</span>
                <span className="text-gray-400">→</span>
                <span className="text-sm font-mono text-blue-600">{getMaskingPreview(testInput, maskingStrategy)}</span>
              </div>
            </div>
          )}

          <div className="flex justify-end gap-2 mt-6 pt-4 border-t">
            <Button
              variant="secondary"
              onClick={() => setShowCreateModal(false)}
            >
              <XMarkIcon className="w-4 h-4 mr-1" />
              {t('operation.cancel', { ns: 'common' })}
            </Button>
            <Button
              variant="primary"
              onClick={handleCreate}
              disabled={!formData.name || !formData.pattern}
            >
              <PlusIcon className="w-4 h-4 mr-1" />
              {t('operation.create', { ns: 'common' })}
            </Button>
          </div>
        </div>
      </Modal>
    </>
  )
}

export default React.memo(DataMaskingPage)
