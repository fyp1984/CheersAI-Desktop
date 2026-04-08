import * as React from 'react'
import DatasetUpdateForm from '@/app/components/datasets/create'
import RequireKnowledgeEdit from '@/app/components/datasets/require-knowledge-edit'

export type IProps = {
  params: Promise<{ datasetId: string }>
}

const Create = async (props: IProps) => {
  const params = await props.params

  const {
    datasetId,
  } = params

  return (
    <RequireKnowledgeEdit fallbackHref={`/datasets/${datasetId}/documents`}>
      <DatasetUpdateForm datasetId={datasetId} />
    </RequireKnowledgeEdit>
  )
}

export default Create
