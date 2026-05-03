'use client'

import { useAppContext } from '@/context/app-context'

const useCanManageTags = (type: 'knowledge' | 'app') => {
  const { isCurrentWorkspaceManager, isCurrentWorkspaceOwner } = useAppContext()

  void type
  return isCurrentWorkspaceManager || isCurrentWorkspaceOwner
}

export default useCanManageTags
