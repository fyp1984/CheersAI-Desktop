import type { CommonNodeType } from '@/app/components/workflow/types'
import { useCallback } from 'react'
import { useNodeDataUpdate } from '@/app/components/workflow/hooks'

const useNodeCrud = <T>(id: string, data: CommonNodeType<T>) => {
  const { handleNodeDataUpdateWithSyncDraft } = useNodeDataUpdate()

  const setInputs = useCallback((newInputs: CommonNodeType<T>) => {
    handleNodeDataUpdateWithSyncDraft({
      id,
      data: newInputs,
    })
  }, [handleNodeDataUpdateWithSyncDraft, id])

  return {
    inputs: data,
    setInputs,
  }
}

export default useNodeCrud
