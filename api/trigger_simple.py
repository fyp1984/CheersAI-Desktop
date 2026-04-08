#!/usr/bin/env python
"""
简单触发文档索引
"""
import psycopg2
from celery import Celery

# 连接数据库
conn = psycopg2.connect(
    host='127.0.0.1',
    port=5432,
    database='dify',
    user='postgres',
    password='difyai123456'
)
cur = conn.cursor()

# 查找等待中的文档
dataset_id = '36adfd03-f829-4eb6-a3b5-041064ef714a'

cur.execute('''
    SELECT id, name, tenant_id, dataset_id
    FROM documents
    WHERE dataset_id = %s
    AND indexing_status = 'waiting'
''', (dataset_id,))

docs = cur.fetchall()

if not docs:
    print('No waiting documents found')
    cur.close()
    conn.close()
    exit(0)

print(f'Found {len(docs)} waiting documents:')
for doc in docs:
    print(f'  - {doc[1]} (ID: {doc[0]})')

# 创建 Celery 应用
celery_app = Celery('app', broker='redis://127.0.0.1:6379/1', backend='redis://127.0.0.1:6379/1')

# 触发索引任务
print('\nTriggering indexing tasks...')
for doc in docs:
    doc_id, name, tenant_id, dataset_id = doc
    try:
        # 发送任务到 dataset 队列
        result = celery_app.send_task(
            'tasks.document_indexing_task.normal_document_indexing_task',
            kwargs={
                'tenant_id': tenant_id,
                'dataset_id': dataset_id,
                'document_ids': [doc_id]
            },
            queue='dataset'
        )
        print(f'  ✓ Triggered: {name} (task_id: {result.id})')
    except Exception as e:
        print(f'  ✗ Failed: {name} - {e}')

cur.close()
conn.close()

print('\nDone! Check Celery Worker logs for processing status.')
