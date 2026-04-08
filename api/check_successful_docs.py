#!/usr/bin/env python
"""Check successful documents to see how they were uploaded."""

from extensions.ext_database import db
from models.dataset import Document

# Get completed documents
completed_docs = (
    db.session.query(Document)
    .filter_by(
        dataset_id='36adfd03-f829-4eb6-a3b5-041064ef714a',
        indexing_status='completed'
    )
    .order_by(Document.created_at.desc())
    .limit(5)
    .all()
)

print(f'\nFound {len(completed_docs)} completed documents:\n')
for doc in completed_docs:
    print(f'Name: {doc.name}')
    print(f'  Data Source Type: {doc.data_source_type}')
    print(f'  Created: {doc.created_at}')
    print(f'  Batch: {doc.batch}')
    print()
