#!/usr/bin/env python
"""Reset all error documents to waiting status."""

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

# Get count of error documents
cur.execute("""
    SELECT COUNT(*)
    FROM documents
    WHERE dataset_id = '36adfd03-f829-4eb6-a3b5-041064ef714a'
    AND indexing_status = 'error'
""")

count = cur.fetchone()[0]
print(f'Found {count} error documents')

if count > 0:
    # Reset all to waiting
    cur.execute("""
        UPDATE documents
        SET indexing_status = 'waiting',
            error = NULL,
            updated_at = NOW()
        WHERE dataset_id = '36adfd03-f829-4eb6-a3b5-041064ef714a'
        AND indexing_status = 'error'
    """)
    
    conn.commit()
    print(f'Reset {count} documents to waiting status')
    print('\n请在知识库界面点击"重新索引"按钮来触发处理')
else:
    print('No error documents found')

cur.close()
conn.close()
