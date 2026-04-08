'use client'

import { useEffect, useRef } from 'react'
import { useTranslation } from 'react-i18next'
import Loading from '@/app/components/base/loading'
import { useSelector as useAppContextWithSelector } from '@/context/app-context'
import { useDatasetList, useInvalidDatasetList } from '@/service/knowledge/use-dataset'
import { hasWorkspaceCapability, WORKSPACE_CAPABILITIES } from '@/utils/workspace-capabilities'
import DatasetCard from './dataset-card'
import NewDatasetCard from './new-dataset-card'

type Props = {
  tags: string[]
  keywords: string
  includeAll: boolean
}

const Datasets = ({
  tags,
  keywords,
  includeAll,
}: Props) => {
  const { t } = useTranslation()
  const currentWorkspace = useAppContextWithSelector(state => state.currentWorkspace)
  const canEditKnowledge = hasWorkspaceCapability(currentWorkspace, WORKSPACE_CAPABILITIES.knowledgeEdit)
  const {
    data: datasetList,
    fetchNextPage,
    hasNextPage,
    isFetching,
    isFetchingNextPage,
  } = useDatasetList({
    initialPage: 1,
    tag_ids: tags,
    limit: 30,
    include_all: includeAll,
    keyword: keywords,
  })
  const invalidDatasetList = useInvalidDatasetList()
  const anchorRef = useRef<HTMLDivElement>(null)
  const observerRef = useRef<IntersectionObserver>(null)

  useEffect(() => {
    document.title = `${t('knowledge', { ns: 'dataset' })} - CheersAI`
  }, [t])

  useEffect(() => {
    if (anchorRef.current) {
      observerRef.current = new IntersectionObserver((entries) => {
        if (entries[0].isIntersecting && hasNextPage && !isFetching)
          fetchNextPage()
      }, {
        rootMargin: '100px',
      })
      observerRef.current.observe(anchorRef.current)
    }
    return () => observerRef.current?.disconnect()
  }, [anchorRef, hasNextPage, isFetching, fetchNextPage])

  return (
    <>
      <nav className="grid grow grid-cols-1 content-start gap-3 px-12 pt-2 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4">
        {canEditKnowledge && <NewDatasetCard />}
        {datasetList?.pages.map(({ data: datasets }) => datasets.map(dataset => (
          <DatasetCard key={dataset.id} dataset={dataset} onSuccess={invalidDatasetList} />),
        ))}
        {isFetchingNextPage && <Loading />}
        <div ref={anchorRef} className="h-0" />
      </nav>
    </>
  )
}

export default Datasets
