import * as React from 'react'
import DatasetUpdateForm from '@/app/components/datasets/create'
import RequireKnowledgeEdit from '@/app/components/datasets/require-knowledge-edit'

const DatasetCreation = async () => {
  return (
    <RequireKnowledgeEdit>
      <DatasetUpdateForm />
    </RequireKnowledgeEdit>
  )
}

export default DatasetCreation
