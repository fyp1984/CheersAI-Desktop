"""Check document segment embedding status"""
import os

from sqlalchemy import create_engine, text

# Get database URL from environment
db_url = os.getenv('DB_URI', 'postgresql://postgres:difyai123456@localhost:5432/dify')

# Create engine
engine = create_engine(db_url)

# Query all documents with their segment details
with engine.connect() as conn:
    result = conn.execute(text("""
        SELECT 
            d.id,
            d.name,
            d.indexing_status as doc_status,
            ds.id as segment_id,
            ds.status as segment_status,
            ds.index_node_id,
            ds.index_node_hash,
            ds.error as segment_error
        FROM documents d
        LEFT JOIN document_segments ds ON d.id = ds.document_id
        WHERE d.dataset_id = '36adfd03-f829-4eb6-a3b5-041064ef714a'
        ORDER BY d.created_at DESC, ds.position
    """))
    
    current_doc = None
    print("\n文档和分段嵌入状态:")
    print("=" * 120)
    
    for row in result:
        if current_doc != row[0]:
            current_doc = row[0]
            print(f"\n文档: {row[1]}")
            print(f"  文档状态: {row[2]}")
        
        if row[3]:  # Has segment
            print(f"  分段 {str(row[3])[:8]}...")
            print(f"    状态: {row[4]}")
            print(f"    index_node_id: {row[5]}")
            print(f"    index_node_hash: {row[6]}")
            if row[7]:
                print(f"    错误: {row[7]}")
        else:
            print("  ⚠ 没有分段")
    
    print("=" * 120)
