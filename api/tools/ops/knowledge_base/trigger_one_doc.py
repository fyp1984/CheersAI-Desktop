#!/usr/bin/env python
"""Trigger indexing for one document by resetting its status."""

import sys
from pathlib import Path

API_ROOT = Path(__file__).resolve().parents[3]
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

import psycopg2

# Connect to database
conn = psycopg2.connect(
    host="127.0.0.1",
    port=5432,
    database="dify",
    user="postgres",
    password="difyai123456"
)

cur = conn.cursor()

# Get one error document
cur.execute("""
    SELECT id, name, indexing_status, error
    FROM documents
    WHERE dataset_id = '36adfd03-f829-4eb6-a3b5-041064ef714a'
    AND indexing_status = 'error'
    LIMIT 1
""")

doc = cur.fetchone()

if doc:
    doc_id, name, status, error = doc
    print(f'Found document: {name}')
    print(f'  ID: {doc_id}')
    print(f'  Status: {status}')
    print(f'  Error: {error}')
    
    # Reset to waiting
    cur.execute("""
        UPDATE documents
        SET indexing_status = 'waiting',
            error = NULL,
            updated_at = NOW()
        WHERE id = %s
    """, (doc_id,))
    
    conn.commit()
    print(f'\nReset document {doc_id} to waiting status')
    print('The Celery Worker should pick it up automatically')
else:
    print('No error documents found')

cur.close()
conn.close()
