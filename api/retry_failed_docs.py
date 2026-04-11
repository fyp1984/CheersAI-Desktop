#!/usr/bin/env python
"""Retry failed documents."""

from extensions.ext_database import db
from models.dataset import Dataset, Document
from tasks.retry_document_indexing_task import retry_document_indexing_task

# Get error documents
error_docs = (
    db.session.query(Document)
    .filter_by(
        dataset_id='36adfd03-f829-4eb6-a3b5-041064ef714a',
        indexing_status='error'
    )
    .order_by(Document.created_at.desc())
    .limit(3)
    .all()
)

print(f'\nFound {len(error_docs)} error documents\n')

for doc in error_docs:
    print(f'Retrying: {doc.name}')
    
    # Get dataset
    dataset = db.session.query(Dataset).filter_by(id=doc.dataset_id).first()
    if dataset:
        # Trigger retry with correct parameters: (dataset_id, document_ids list, user_id)
        retry_document_indexing_task.delay(dataset.id, [doc.id], doc.created_by)
        print('  ✓ Retry task triggered')
    else:
        print('  ✗ Dataset not found')
    print()

print('All retry tasks have been triggered!')
