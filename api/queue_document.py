#!/usr/bin/env python
"""Queue a document for indexing."""

import psycopg2
from celery import Celery

# Setup Celery
celery_app = Celery('app')
celery_app.config_from_object('celery_config')

# Connect to database
conn = psycopg2.connect(
    host="127.0.0.1",
    port=5432,
    database="dify",
    user="postgres",
    password="difyai123456"
)

cur = conn.cursor()

# Get document info
cur.execute("""
    SELECT d.id, d.name, d.dataset_id, d.tenant_id
    FROM documents d
    WHERE d.id = '8c2eb51f-927c-4ede-8c2c-02613045f904'
""")

doc = cur.fetchone()

if doc:
    doc_id, name, dataset_id, tenant_id = doc
    print(f'Queueing document: {name}')
    print(f'  ID: {doc_id}')
    print(f'  Dataset: {dataset_id}')
    print(f'  Tenant: {tenant_id}')
    
    # Queue the indexing task
    from tasks.document_indexing_task import document_indexing_task
    
    task = document_indexing_task.apply_async(
        queue='dataset',
        kwargs={
            'dataset_id': dataset_id,
            'document_ids': [doc_id]
        }
    )
    
    print(f'\nQueued task: {task.id}')
    print('Check Celery Worker logs for processing')
else:
    print('Document not found')

cur.close()
conn.close()
