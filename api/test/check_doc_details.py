#!/usr/bin/env python
"""Check document details."""

import psycopg2

conn = psycopg2.connect(
    host="127.0.0.1",
    port=5432,
    database="dify",
    user="postgres",
    password="difyai123456"
)

cur = conn.cursor()

# Check completed documents
cur.execute("""
    SELECT id, name, indexing_status, created_at
    FROM documents
    WHERE dataset_id = '36adfd03-f829-4eb6-a3b5-041064ef714a'
    ORDER BY created_at DESC
""")

print('\nAll documents:')
for row in cur.fetchall():
    print(f'  - {row[1]}: {row[2]} (created: {row[3]})')

cur.close()
conn.close()
