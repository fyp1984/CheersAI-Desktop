'use client'

import type { AppInstruction, AppInstructionSource } from '@/service/app-instruction'
import { RiQuestionLine } from '@remixicon/react'
import { useEffect, useState } from 'react'
import ActionButton, { ActionButtonState } from '@/app/components/base/action-button'
import { Markdown } from '@/app/components/base/markdown'
import Modal from '@/app/components/base/modal'
import Tooltip from '@/app/components/base/tooltip'
import { fetchAppInstruction } from '@/service/app-instruction'
import { cn } from '@/utils/classnames'

type Props = {
  appId?: string
  source: AppInstructionSource
  className?: string
}

const AppInstructionHelpButton = ({
  appId,
  source,
  className,
}: Props) => {
  const [instruction, setInstruction] = useState<AppInstruction | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [isShow, setIsShow] = useState(false)

  useEffect(() => {
    let ignore = false
    const loadInstruction = async () => {
      if (!appId) {
        setInstruction(null)
        return
      }
      setIsLoading(true)
      try {
        const res = await fetchAppInstruction(appId, source)
        if (!ignore)
          setInstruction(res.instruction)
      }
      catch {
        if (!ignore)
          setInstruction(null)
      }
      finally {
        if (!ignore)
          setIsLoading(false)
      }
    }
    loadInstruction()
    return () => {
      ignore = true
    }
  }, [appId, source])

  const hasInstruction = !!instruction?.content

  return (
    <>
      <Tooltip popupContent={hasInstruction ? '查看使用说明' : '暂无使用说明'}>
        <div className={className}>
          <ActionButton
            size="l"
            state={hasInstruction ? ActionButtonState.Default : ActionButtonState.Disabled}
            disabled={!hasInstruction || isLoading}
            onClick={() => setIsShow(true)}
          >
            <RiQuestionLine className="h-[18px] w-[18px]" />
          </ActionButton>
        </div>
      </Tooltip>
      {isShow && hasInstruction && (
        <Modal
          isShow
          onClose={() => setIsShow(false)}
          title={instruction?.title || '使用说明'}
          className="max-w-[760px] p-0"
        >
          <div className="max-h-[70vh] overflow-y-auto px-6 py-5">
            <Markdown
              content={instruction.content}
              className={cn(
                'text-sm leading-6',
                '[&_a]:text-text-accent',
                '[&_pre]:bg-background-section-burn',
                '[&_code]:text-text-primary',
              )}
            />
          </div>
        </Modal>
      )}
    </>
  )
}

export default AppInstructionHelpButton
