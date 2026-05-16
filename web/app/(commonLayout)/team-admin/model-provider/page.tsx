'use client'

import type { TeamModelConfigItem, TeamModelConfigPayload } from '@/service/use-common'
import Link from 'next/link'
import { RiFlashlightLine, RiSettings3Line } from '@remixicon/react'
import { useQueryClient } from '@tanstack/react-query'
import { useEffect, useMemo, useState } from 'react'
import Drawer from '@/app/components/base/drawer'
import Input from '@/app/components/base/input'
import Toast from '@/app/components/base/toast'
import Button from '@/app/components/base/button'
import useDocumentTitle from '@/hooks/use-document-title'
import { useSaveTeamModelConfig, useTeamModelConfigs } from '@/service/use-common'

type FormState = {
  api_key: string
  base_url: string
  max_concurrent: string
  max_qps: string
}

const emptyForm: FormState = {
  api_key: '',
  base_url: '',
  max_concurrent: '',
  max_qps: '',
}

const TeamAdminModelProviderPage = () => {
  useDocumentTitle('团队模型供应商')

  const queryClient = useQueryClient()
  const { data, isLoading } = useTeamModelConfigs(true)
  const saveMutation = useSaveTeamModelConfig()
  const items = data?.data ?? []
  const [selectedItem, setSelectedItem] = useState<TeamModelConfigItem | null>(null)
  const [form, setForm] = useState<FormState>(emptyForm)

  useEffect(() => {
    if (!selectedItem) {
      setForm(emptyForm)
      return
    }

    setForm({
      api_key: '',
      base_url: selectedItem.base_url ?? '',
      max_concurrent: selectedItem.max_concurrent ? String(selectedItem.max_concurrent) : '',
      max_qps: selectedItem.max_qps ? String(selectedItem.max_qps) : '',
    })
  }, [selectedItem])

  const validationMessage = useMemo(() => {
    if (!selectedItem)
      return ''
    if (!selectedItem.configured && !form.api_key.trim())
      return '首次配置时必须填写 API Key'
    if (!form.base_url.trim())
      return 'Base URL 不能为空'
    if (!/^https?:\/\/.+/i.test(form.base_url.trim()))
      return 'Base URL 格式不正确'
    if (form.api_key.trim() && !/^[^\s].*[^\s]$|^[^\s]$/.test(form.api_key.trim()))
      return 'API Key 格式不正确'
    if (form.max_concurrent && (!/^\d+$/.test(form.max_concurrent) || Number(form.max_concurrent) < 1))
      return '并发限额必须为大于 0 的整数'
    if (form.max_qps && (!/^\d+$/.test(form.max_qps) || Number(form.max_qps) < 1))
      return 'QPS 限额必须为大于 0 的整数'
    return ''
  }, [form, selectedItem])

  const handleSave = async () => {
    if (!selectedItem)
      return
    if (validationMessage) {
      Toast.notify({ type: 'error', message: validationMessage })
      return
    }

    const trimmedApiKey = form.api_key.trim()
    const payload: TeamModelConfigPayload = {
      plugin_code: selectedItem.plugin_code,
      base_url: form.base_url.trim(),
      max_concurrent: form.max_concurrent ? Number(form.max_concurrent) : null,
      max_qps: form.max_qps ? Number(form.max_qps) : null,
      ...(trimmedApiKey ? { api_key: trimmedApiKey } : {}),
    }

    try {
      await saveMutation.mutateAsync(payload)
      Toast.notify({ type: 'success', message: '团队模型配置已保存，成员将自动复用该配置' })
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ['common', 'team-model-configs'] }),
        queryClient.invalidateQueries({ queryKey: ['common', 'model-providers'] }),
        queryClient.invalidateQueries({ queryKey: ['common', 'model-list'] }),
        queryClient.invalidateQueries({ queryKey: ['common', 'default-model'] }),
      ])
      setSelectedItem(null)
    }
    catch (error) {
      Toast.notify({
        type: 'error',
        message: error instanceof Error ? error.message : '团队模型配置保存失败',
      })
    }
  }

  return (
    <div className="relative flex h-0 shrink-0 grow flex-col overflow-y-auto bg-background-body">
      <div className="sticky top-0 z-10 flex items-center justify-between bg-background-body px-12 pb-4 pt-7">
        <div>
          <h2 className="text-lg font-semibold text-text-primary">团队模型供应商</h2>
          <div className="mt-1 text-sm text-text-tertiary">
            系统管理员先完成全局插件安装，团队管理员再在此为当前团队配置 API Key、Base URL 与限流参数。
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Link
            href="/plugins"
            className="inline-flex items-center rounded-lg border border-divider-regular px-4 py-2 text-sm font-medium text-text-secondary transition-colors hover:bg-state-base-hover"
          >
            查看工具插件
          </Link>
        </div>
      </div>
      <div className="px-12 pb-8">
        <div className="mb-4 rounded-xl border border-components-panel-border bg-components-panel-bg shadow-xs">
          <div className="flex items-start justify-between gap-4 border-b border-divider-subtle px-4 py-4">
            <div>
              <div className="system-md-semibold text-text-primary">团队模型配置</div>
              <div className="system-xs-regular mt-1 text-text-tertiary">
                团队管理员在这里为全团队统一配置共享模型服务的 API Key、Base URL 与限流参数。
              </div>
            </div>
            <div className="flex items-center gap-1 rounded-full bg-state-base-hover px-3 py-1 text-xs text-text-secondary">
              <RiFlashlightLine className="h-3.5 w-3.5" />
              仅当前团队生效
            </div>
          </div>
          <div className="space-y-3 p-4">
            {!items.length && !isLoading && (
              <div className="rounded-lg border border-dashed border-divider-subtle px-4 py-6 text-sm text-text-tertiary">
                暂无可配置的大模型服务，请先由系统管理员在工具插件中完成安装。
              </div>
            )}
            {items.map(item => (
              <div key={item.plugin_code} className="rounded-xl border border-divider-subtle bg-components-panel-bg px-4 py-4">
                <div className="flex items-start justify-between gap-4">
                  <div className="min-w-0">
                    <div className="flex items-center gap-2">
                      <div className="system-sm-semibold text-text-primary">{item.name}</div>
                      <div className="rounded-full bg-state-base-hover px-2 py-0.5 text-xs text-text-tertiary">
                        v{item.version}
                      </div>
                      <div
                        className={`rounded-full px-2 py-0.5 text-xs ${item.configured
                          ? 'bg-green-50 text-green-700'
                          : 'bg-amber-50 text-amber-700'}`}
                      >
                        {item.configured ? '已配置' : '待配置'}
                      </div>
                    </div>
                    <div className="system-xs-regular mt-1 text-text-tertiary">
                      {item.description || '系统管理员安装后，全团队可见；仅当前团队配置完成后可调用。'}
                    </div>
                    <div className="system-xs-regular mt-2 text-text-secondary">
                      {item.base_url ? `Base URL: ${item.base_url}` : '尚未配置 Base URL'}
                    </div>
                  </div>
                  <Button variant="secondary" onClick={() => setSelectedItem(item)}>
                    <RiSettings3Line className="mr-1 h-4 w-4" />
                    配置
                  </Button>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
      <Drawer
        isOpen={!!selectedItem}
        onClose={() => setSelectedItem(null)}
        onCancel={() => setSelectedItem(null)}
        onOk={handleSave}
        showClose
        title={selectedItem ? `配置 ${selectedItem.name}` : ''}
        description="提交后将覆盖当前团队在该模型服务上的统一凭据，普通成员会自动复用。"
        panelClassName="!max-w-[520px]"
      >
        <div className="mt-4 space-y-4">
          <div>
            <div className="mb-2 text-sm font-medium text-text-primary">API Key *</div>
            <Input
              type="password"
              value={form.api_key}
              placeholder={selectedItem?.configured ? '如需更新请重新输入 API Key' : '请输入 API Key'}
              onChange={e => setForm(prev => ({ ...prev, api_key: e.target.value }))}
            />
          </div>
          <div>
            <div className="mb-2 text-sm font-medium text-text-primary">Base URL *</div>
            <Input
              type="url"
              value={form.base_url}
              placeholder="https://api.example.com/v1"
              onChange={e => setForm(prev => ({ ...prev, base_url: e.target.value }))}
            />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <div className="mb-2 text-sm font-medium text-text-primary">并发限额</div>
              <Input
                type="number"
                min={1}
                value={form.max_concurrent}
                placeholder="例如 10"
                onChange={e => setForm(prev => ({ ...prev, max_concurrent: e.target.value }))}
              />
            </div>
            <div>
              <div className="mb-2 text-sm font-medium text-text-primary">QPS 限额</div>
              <Input
                type="number"
                min={1}
                value={form.max_qps}
                placeholder="例如 5"
                onChange={e => setForm(prev => ({ ...prev, max_qps: e.target.value }))}
              />
            </div>
          </div>
          {validationMessage && (
            <div className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
              {validationMessage}
            </div>
          )}
        </div>
      </Drawer>
    </div>
  )
}

export default TeamAdminModelProviderPage
