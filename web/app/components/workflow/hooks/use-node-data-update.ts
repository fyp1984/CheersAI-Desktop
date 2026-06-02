import type { SyncCallback } from './use-nodes-sync-draft'
import { isEqual } from 'es-toolkit/predicate'
import { produce } from 'immer'
import { useCallback } from 'react'
import { useStoreApi } from 'reactflow'
import { useNodesSyncDraft } from './use-nodes-sync-draft'
import { useNodesReadOnly } from './use-workflow'

type NodeDataUpdatePayload = {
  id: string
  data: Record<string, any>
}

export const useNodeDataUpdate = () => {
  const store = useStoreApi()
  const { handleSyncWorkflowDraft } = useNodesSyncDraft()
  const { getNodesReadOnly } = useNodesReadOnly()

  const handleNodeDataUpdate = useCallback(({ id, data }: NodeDataUpdatePayload) => {
    const {
      getNodes,
      setNodes,
    } = store.getState()
    const nodes = getNodes()
    const targetNode = nodes.find(node => node.id === id)
    if (!targetNode)
      return

    const nextData = { ...targetNode.data, ...data }
    if (isEqual(targetNode.data, nextData))
      return

    const newNodes = produce(nodes, (draft) => {
      const currentNode = draft.find(node => node.id === id)!

      if (currentNode)
        currentNode.data = nextData
    })
    setNodes(newNodes)
  }, [store])

  const handleNodeDataUpdateWithSyncDraft = useCallback((
    payload: NodeDataUpdatePayload,
    options?: {
      sync?: boolean
      notRefreshWhenSyncError?: boolean
      callback?: SyncCallback
    },
  ) => {
    if (getNodesReadOnly())
      return

    handleNodeDataUpdate(payload)
    handleSyncWorkflowDraft(options?.sync, options?.notRefreshWhenSyncError, options?.callback)
  }, [handleSyncWorkflowDraft, handleNodeDataUpdate, getNodesReadOnly])

  return {
    handleNodeDataUpdate,
    handleNodeDataUpdateWithSyncDraft,
  }
}
