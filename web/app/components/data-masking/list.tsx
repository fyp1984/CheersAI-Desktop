'use client'
import type { FC } from 'react'
import type { MaskingRule } from '@/lib/data-masking/types'
import { useTranslation } from '#i18n'
import { PlusIcon } from '@heroicons/react/24/outline'
import { useEffect, useState } from 'react'
import Button from '@/app/components/base/button'
import { rulesManager } from '@/lib/data-masking/rules-manager'
import { RuleForm } from './rule-form'

const DataMaskingList: FC = () => {
  const { t } = useTranslation('dataMasking')
  const [rules, setRules] = useState<MaskingRule[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [showRuleForm, setShowRuleForm] = useState(false)
  const [editingRule, setEditingRule] = useState<MaskingRule | undefined>(undefined)

  const loadRules = async () => {
    setIsLoading(true)
    try {
      const allRules = await rulesManager.getAllRules()
      setRules(allRules)
    }
    catch (error) {
      console.error('Failed to load rules:', error)
    }
    finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    loadRules()
  }, [])

  const handleCreateRule = () => {
    setEditingRule(undefined)
    setShowRuleForm(true)
  }

  const handleEditRule = (rule: MaskingRule) => {
    setEditingRule(rule)
    setShowRuleForm(true)
  }

  const handleDeleteRule = async (id: string) => {
    // eslint-disable-next-line no-alert
    if (confirm(t('common.deleteConfirm') || '确认删除？')) {
      await rulesManager.deleteRule(id)
      loadRules()
    }
  }

  const handleSaveRule = async (data: Omit<MaskingRule, 'id' | 'createdAt' | 'updatedAt'>) => {
    try {
      if (editingRule) {
        await rulesManager.updateRule(editingRule.id, data)
      }
      else {
        await rulesManager.createRule(data)
      }
      setShowRuleForm(false)
      loadRules()
    }
    catch (error) {
      console.error('Failed to save rule:', error)
      // eslint-disable-next-line no-alert
      alert(t('common.error') || '发生错误')
    }
  }

  return (
    <div className="flex h-full flex-col">
      <div className="flex items-center justify-between px-12 pb-4 pt-8">
        <div>
          <h1 className="text-2xl font-semibold text-gray-900">
            {t('rules.title')}
          </h1>
          <p className="mt-1 text-sm text-gray-500">
            {t('description')}
          </p>
        </div>
        <Button
          variant="primary"
          className="flex items-center gap-2"
          onClick={handleCreateRule}
        >
          <PlusIcon className="h-4 w-4" />
          {t('rules.createRule')}
        </Button>
      </div>

      <div className="flex-1 overflow-y-auto px-12 pb-8">
        {isLoading
          ? (
              <div className="flex h-64 items-center justify-center">
                <div className="text-gray-400">
                  {t('common.loading') || '加载中...'}
                </div>
              </div>
            )
          : rules.length === 0
            ? (
                <div className="flex h-64 flex-col items-center justify-center rounded-lg border-2 border-dashed border-gray-200 bg-gray-50">
                  <div className="text-center">
                    <h3 className="text-sm font-medium text-gray-900">
                      {t('rules.noRules')}
                    </h3>
                    <p className="mt-1 text-sm text-gray-500">
                      {t('rules.noRulesDescription')}
                    </p>
                    <div className="mt-6">
                      <Button
                        variant="primary"
                        className="flex items-center gap-2"
                        onClick={handleCreateRule}
                      >
                        <PlusIcon className="h-4 w-4" />
                        {t('rules.createFirstRule')}
                      </Button>
                    </div>
                  </div>
                </div>
              )
            : (
                <div className="space-y-4">
                  {rules.map(rule => (
                    <div
                      key={rule.id}
                      className="cursor-pointer rounded-lg border border-gray-200 bg-white p-4 transition-shadow hover:shadow-md"
                      onClick={() => handleEditRule(rule)}
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex-1">
                          <h3 className="text-sm font-medium text-gray-900">
                            {rule.name}
                          </h3>
                          <p className="mt-1 text-xs text-gray-500">
                            {rule.strategy.type}
                            {' • '}
                            {rule.pattern instanceof RegExp ? rule.pattern.source : rule.pattern}
                          </p>
                        </div>
                        <div className="flex items-center gap-2">
                          <span className={`rounded px-2 py-1 text-xs ${rule.enabled ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'}`}>
                            {rule.enabled ? t('rules.enabled') : t('rules.disabled')}
                          </span>
                          <button
                            onClick={(e) => {
                              e.stopPropagation()
                              handleDeleteRule(rule.id)
                            }}
                            className="px-2 text-gray-400 hover:text-red-500"
                          >
                            {t('common.delete') || '删除'}
                          </button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
      </div>

      {showRuleForm && (
        <RuleForm
          rule={editingRule}
          onSave={handleSaveRule}
          onCancel={() => setShowRuleForm(false)}
        />
      )}
    </div>
  )
}

export default DataMaskingList
