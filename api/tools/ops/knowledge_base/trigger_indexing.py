#!/usr/bin/env python
"""Manually trigger indexing for waiting documents."""

import sys
from pathlib import Path

API_ROOT = Path(__file__).resolve().parents[3]
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from extensions.ext_database import db
from models.dataset import Dataset, Document
from services.document_indexing_proxy.document_indexing_task_proxy import DocumentIndexingTaskProxy

# Find the waiting document
doc = db.session.query(Document).filter_by(
    id='13bf7d6d-271a-43ee-a2eb-7c1284ab27eb'
).first()

if doc:
    print(f'Found document: {doc.name}')
    print(f'  Status: {doc.indexing_status}')
    print(f'  Process Rule ID: {doc.dataset_process_rule_id}')
    print(f'  Dataset ID: {doc.dataset_id}')
    
    # Get dataset
    dataset = db.session.query(Dataset).filter_by(id=doc.dataset_id).first()
    if dataset:
        print(f'  Tenant ID: {dataset.tenant_id}')
        
        # Trigger indexing
        print('\nTriggering indexing task...')
        DocumentIndexingTaskProxy(dataset.tenant_id, doc.dataset_id, [doc.id]).delay()
        print('Indexing task triggered successfully!')
    else:
        print('ERROR: Dataset not found!')
else:
    print('ERROR: Document not found!')
