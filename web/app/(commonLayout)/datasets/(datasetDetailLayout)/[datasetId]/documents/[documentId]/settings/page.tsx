import * as React from 'react'
import Settings from '@/app/components/datasets/documents/detail/settings'
import RequireKnowledgeEdit from '@/app/components/datasets/require-knowledge-edit'

export type IProps = {
  params: Promise<{ datasetId: string, documentId: string }>
}

const DocumentSettings = async (props: IProps) => {
  const params = await props.params

  const {
    datasetId,
    documentId,
  } = params

  return (
    <RequireKnowledgeEdit fallbackHref={`/datasets/${datasetId}/documents`}>
      <Settings datasetId={datasetId} documentId={documentId} />
    </RequireKnowledgeEdit>
  )
}

export default DocumentSettings
