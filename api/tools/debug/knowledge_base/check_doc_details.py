#!/usr/bin/env python
"""Check document details."""

import sys
from pathlib import Path

API_ROOT = Path(__file__).resolve().parents[3]
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

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
