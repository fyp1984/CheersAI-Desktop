#!/usr/bin/env python
"""Re-index all error documents."""

import sys
from pathlib import Path

API_ROOT = Path(__file__).resolve().parents[3]
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

import os

from app_factory import create_flask_app
from extensions.ext_database import db
from models.dataset import Document
from tasks.document_indexing_task import document_indexing_task

# Create Flask app context
app = create_flask_app()

with app.app_context():
    # Get all error documents
    docs = (
        db.session.query(Document)
        .filter_by(
            dataset_id='36adfd03-f829-4eb6-a3b5-041064ef714a',
            indexing_status='error'
        )
        .all()
    )
    
    print(f'Found {len(docs)} error documents')
    
    for doc in docs:
        print(f'\nProcessing: {doc.name}')
        
        # Reset status
        doc.indexing_status = 'waiting'
        doc.error = None
        db.session.commit()
        
        # Queue the task
        task = document_indexing_task.apply_async(
            queue='dataset',
            kwargs={
                'dataset_id': doc.dataset_id,
                'document_ids': [doc.id]
            }
        )
        
        print(f'  Queued task: {task.id}')
    
    print(f'\nReset and queued {len(docs)} documents')
    print('Check Celery Worker logs for processing')

