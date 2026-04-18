#!/usr/bin/env python
"""Check document status counts."""

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
    SELECT indexing_status, COUNT(*)
    FROM documents
    WHERE dataset_id = '36adfd03-f829-4eb6-a3b5-041064ef714a'
    GROUP BY indexing_status
""")

print('\nDocument status counts:')
for status, count in cur.fetchall():
    print(f'  {status}: {count}')

cur.close()
conn.close()
