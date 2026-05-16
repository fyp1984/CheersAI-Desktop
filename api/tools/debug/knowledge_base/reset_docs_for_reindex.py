"""Reset documents for reindexing using direct SQL"""

import sys
from pathlib import Path

API_ROOT = Path(__file__).resolve().parents[3]
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

import json
import os

import psycopg2

# Database connection
db_url = os.getenv('DB_URI', 'postgresql://postgres:difyai123456@localhost:5432/dify')
conn = psycopg2.connect(db_url)
cur = conn.cursor()

dataset_id = '36adfd03-f829-4eb6-a3b5-041064ef714a'

# Find documents with segments that have no embeddings
cur.execute("""
    SELECT DISTINCT d.id, d.name, d.data_source_info
    FROM documents d
    INNER JOIN document_segments ds ON d.id = ds.document_id
    WHERE d.dataset_id = %s
    AND d.indexing_status = 'completed'
    AND ds.index_node_id IS NULL
""", (dataset_id,))

docs = cur.fetchall()

if not docs:
    print('✓ All completed documents have embeddings!')
    cur.close()
    conn.close()
    exit(0)

print(f'\n发现 {len(docs)} 个文档需要重新索引:')
for doc in docs:
    print(f'  - {doc[1]} (ID: {doc[0]})')

print('\n开始重置文档...')

for doc_id, doc_name, data_source_info_str in docs:
    try:
        # Delete segments
        cur.execute("DELETE FROM document_segments WHERE document_id = %s", (doc_id,))
        deleted = cur.rowcount
        print(f'  删除 {deleted} 个分段: {doc_name}')
        
        # Modify data_source_info
        data_source_info = json.loads(data_source_info_str) if data_source_info_str else {}
        data_source_info["use_builtin_extractor"] = True
        data_source_info["bypass_dify_extractor"] = True
        data_source_info["force_text_extraction"] = True
        
        # Remove plugin config
        data_source_info.pop("plugin_id", None)
        data_source_info.pop("plugin_config", None)
        
        # Reset document
        cur.execute("""
            UPDATE documents
            SET indexing_status = 'waiting',
                error = NULL,
                completed_at = NULL,
                word_count = 0,
                tokens = 0,
                data_source_info = %s
            WHERE id = %s
        """, (json.dumps(data_source_info), doc_id))
        
        print(f'  ✓ 已重置: {doc_name}')
        
    except Exception as e:
        print(f'  ✗ 失败: {doc_name} - {e}')
        conn.rollback()
        continue

conn.commit()
cur.close()
conn.close()

print('\n完成！文档已重置为 waiting 状态。')
print('自动修复任务会在2分钟内触发索引。')
