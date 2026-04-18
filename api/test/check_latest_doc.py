#!/usr/bin/env python
"""Check the latest document status."""

from extensions.ext_database import db
from models.dataset import Document

# Get the latest document
doc = db.session.query(Document).filter_by(
    dataset_id='36adfd03-f829-4eb6-a3b5-041064ef714a'
).order_by(Document.created_at.desc()).first()

if doc:
    print('\nLatest document:')
    print(f'  ID: {doc.id}')
    print(f'  Name: {doc.name}')
    print(f'  Status: {doc.indexing_status}')
    print(f'  Process Rule ID: {doc.dataset_process_rule_id}')
    print(f'  Created: {doc.created_at}')
    print(f'  Batch: {doc.batch}')
    print(f'  Data Source Type: {doc.data_source_type}')
else:
    print('No documents found')
