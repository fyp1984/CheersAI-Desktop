#!/usr/bin/env python
"""Check successful document details."""

import psycopg2

conn = psycopg2.connect(
    host="127.0.0.1",
    port=5432,
    database="dify",
    user="postgres",
    password="difyai123456"
)

cur = conn.cursor()

# Check the successful document
cur.execute("""
    SELECT id, name, indexing_status, data_source_type, doc_form, created_at
    FROM documents
    WHERE dataset_id = '36adfd03-f829-4eb6-a3b5-041064ef714a'
    AND indexing_status = 'completed'
""")

row = cur.fetchone()
if row:
    print('\nSuccessful document:')
    print(f'  Name: {row[1]}')
    print(f'  Status: {row[2]}')
    print(f'  Data source type: {row[3]}')
    print(f'  Doc form: {row[4]}')
    print(f'  Created: {row[5]}')
else:
    print('No successful documents found')

cur.close()
conn.close()
