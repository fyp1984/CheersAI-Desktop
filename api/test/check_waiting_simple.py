"""Check waiting documents"""
import os

from sqlalchemy import create_engine, text

# Get database URL from environment
db_url = os.getenv('DB_URI', 'postgresql://postgres:difyai123456@localhost:5432/dify')

# Create engine
engine = create_engine(db_url)

# Query waiting documents
with engine.connect() as conn:
    result = conn.execute(text("""
        SELECT id, name, indexing_status, dataset_process_rule_id, data_source_type, created_at
        FROM documents
        WHERE dataset_id = '36adfd03-f829-4eb6-a3b5-041064ef714a'
        AND indexing_status = 'pending'
        ORDER BY created_at DESC
    """))
    
    rows = list(result)
    
    if not rows:
        print("\n✓ 没有排队中的文档！")
    else:
        print(f"\n发现 {len(rows)} 个排队中的文档:")
        print("=" * 120)
        for row in rows:
            print(f"\nID: {row[0]}")
            print(f"名称: {row[1]}")
            print(f"状态: {row[2]}")
            print(f"处理规则ID: {row[3]}")
            print(f"数据源类型: {row[4]}")
            print(f"创建时间: {row[5]}")
            print("=" * 120)
