#!/usr/bin/env python
"""Test document indexing with one document."""

import sys
from pathlib import Path

API_ROOT = Path(__file__).resolve().parents[3]
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from app_factory import create_app
from extensions.ext_database import db
from models.dataset import Document
from services.document_indexing_proxy.document_indexing_task_proxy import DocumentIndexingTaskProxy

app = create_app()

with app.app_context():
    # Get one error document
    doc = (
        db.session.query(Document)
        .filter_by(
            dataset_id='36adfd03-f829-4eb6-a3b5-041064ef714a',
            indexing_status='error'
        )
        .first()
    )
    
    if doc:
        print(f'Testing document: {doc.name}')
        print(f'  ID: {doc.id}')
        print(f'  Status: {doc.indexing_status}')
        print(f'  Previous error: {doc.error}')
        
        # Reset status to waiting
        doc.indexing_status = 'waiting'
        doc.error = None
        db.session.commit()
        
        # Trigger indexing
        DocumentIndexingTaskProxy(doc.tenant_id, doc.dataset_id, [doc.id]).delay()
        print(f'\nTriggered indexing for document {doc.id}')
        print('Check Celery Worker logs to see if it processes successfully')
    else:
        print('No error documents found')
