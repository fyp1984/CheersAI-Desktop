'use client'

import { useAppContext } from '@/context/app-context'

const useCanManageTags = (type: 'knowledge' | 'app') => {
  const { canEditApps, canEditKnowledge } = useAppContext()

  if (type === 'knowledge')
    return canEditKnowledge

  return canEditApps
}

export default useCanManageTags
