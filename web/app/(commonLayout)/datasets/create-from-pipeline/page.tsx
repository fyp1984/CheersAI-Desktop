import * as React from 'react'
import CreateFromPipeline from '@/app/components/datasets/create-from-pipeline'
import RequireKnowledgeEdit from '@/app/components/datasets/require-knowledge-edit'

const DatasetCreation = async () => {
  return (
    <RequireKnowledgeEdit>
      <CreateFromPipeline />
    </RequireKnowledgeEdit>
  )
}

export default DatasetCreation
