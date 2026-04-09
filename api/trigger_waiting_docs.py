#!/usr/bin/env python
"""
触发等待中的文档进行索引
"""
import sys
sys.path.insert(0, '/app')

from app_factory import create_app
from extensions.ext_database import db
from models.dataset import Document
from services.document_indexing_proxy.document_indexing_task_proxy import DocumentIndexingTaskProxy

app = create_app()

with app.app_context():
    # 查找等待中的文档
    dataset_id = '36adfd03-f829-4eb6-a3b5-041064ef714a'
    
    waiting_docs = db.session.query(Document).filter(
        Document.dataset_id == dataset_id,
        Document.indexing_status == 'waiting'
    ).all()
    
    if not waiting_docs:
        print('No waiting documents found')
        sys.exit(0)
    
    print(f'Found {len(waiting_docs)} waiting documents:')
    for doc in waiting_docs:
        print(f'  - {doc.name} (ID: {doc.id})')
    
    # 触发索引
    print('\nTriggering indexing...')
    for doc in waiting_docs:
        try:
            DocumentIndexingTaskProxy(doc.tenant_id, doc.dataset_id, [doc.id]).delay()
            print(f'  ✓ Triggered: {doc.name}')
        except Exception as e:
            print(f'  ✗ Failed: {doc.name} - {e}')
    
    print('\nDone! Check Celery Worker logs for processing status.')
