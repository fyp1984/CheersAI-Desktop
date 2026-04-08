import * as React from 'react'
import CreateFromPipeline from '@/app/components/datasets/documents/create-from-pipeline'
import RequireKnowledgeEdit from '@/app/components/datasets/require-knowledge-edit'

type IProps = {
  params: Promise<{ datasetId: string }>
}

const CreateFromPipelinePage = async (props: IProps) => {
  const params = await props.params
  const { datasetId } = params

  return (
    <RequireKnowledgeEdit fallbackHref={`/datasets/${datasetId}/documents`}>
      <CreateFromPipeline />
    </RequireKnowledgeEdit>
  )
}

export default CreateFromPipelinePage
