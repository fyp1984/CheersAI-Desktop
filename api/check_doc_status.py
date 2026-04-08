#!/usr/bin/env python
"""Check document status."""

import psycopg2

conn = psycopg2.connect(
    host="127.0.0.1",
    port=5432,
    database="dify",
    user="postgres",
    password="difyai123456"
)

cur = conn.cursor()

cur.execute("""
    SELECT id, name, indexing_status, error
    FROM documents
    WHERE id = '8c2eb51f-927c-4ede-8c2c-02613045f904'
""")

doc = cur.fetchone()
if doc:
    print(f'Document: {doc[1]}')
    print(f'  Status: {doc[2]}')
    print(f'  Error: {doc[3]}')

cur.close()
conn.close()
