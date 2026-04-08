import * as React from 'react'
import ExternalKnowledgeBaseConnector from '@/app/components/datasets/external-knowledge-base/connector'
import RequireKnowledgeEdit from '@/app/components/datasets/require-knowledge-edit'

const ExternalKnowledgeBaseCreation = () => {
  return (
    <RequireKnowledgeEdit>
      <ExternalKnowledgeBaseConnector />
    </RequireKnowledgeEdit>
  )
}

export default ExternalKnowledgeBaseCreation
