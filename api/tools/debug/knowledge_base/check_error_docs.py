"""Check error documents in detail"""

import sys
from pathlib import Path

API_ROOT = Path(__file__).resolve().parents[3]
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

import os
from sqlalchemy import create_engine, text

# Get database URL from environment
db_url = os.getenv('DB_URI', 'postgresql://postgres:difyai123456@localhost:5432/dify')

# Create engine
engine = create_engine(db_url)

# Query error documents
with engine.connect() as conn:
    result = conn.execute(text("""
        SELECT id, name, indexing_status, error, data_source_type, data_source_info
        FROM documents
        WHERE dataset_id = '36adfd03-f829-4eb6-a3b5-041064ef714a'
        AND indexing_status = 'error'
        ORDER BY created_at DESC
    """))
    
    rows = list(result)
    
    if not rows:
        print("\n✓ 没有错误文档！")
    else:
        print(f"\n发现 {len(rows)} 个错误文档:")
        print("=" * 120)
        for row in rows:
            print(f"\nID: {row[0]}")
            print(f"名称: {row[1]}")
            print(f"状态: {row[2]}")
            print(f"数据源类型: {row[3]}")
            print(f"数据源信息: {row[4]}")
            print(f"\n错误信息:")
            print(row[5])
            print("=" * 120)
