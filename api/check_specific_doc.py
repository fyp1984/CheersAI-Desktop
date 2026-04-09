"""Check specific document details including segments"""
import os
from sqlalchemy import create_engine, text

# Get database URL from environment
db_url = os.getenv('DB_URI', 'postgresql://postgres:difyai123456@localhost:5432/dify')

# Create engine
engine = create_engine(db_url)

# Query the first document (most recent)
with engine.connect() as conn:
    # Get document details
    result = conn.execute(text("""
        SELECT id, name, indexing_status, error, word_count, tokens, 
               data_source_type, data_source_info, doc_form
        FROM documents
        WHERE dataset_id = '36adfd03-f829-4eb6-a3b5-041064ef714a'
        ORDER BY created_at DESC
        LIMIT 1
    """))
    
    doc = result.fetchone()
    
    if doc:
        print("\n最新文档详情:")
        print("=" * 120)
        print(f"ID: {doc[0]}")
        print(f"名称: {doc[1]}")
        print(f"索引状态: {doc[2]}")
        print(f"错误: {doc[3]}")
        print(f"字数: {doc[4]}")
        print(f"Tokens: {doc[5]}")
        print(f"数据源类型: {doc[6]}")
        print(f"数据源信息: {doc[7]}")
        print(f"文档形式: {doc[8]}")
        print("=" * 120)
        
        # Check segments
        seg_result = conn.execute(text("""
            SELECT id, position, status, word_count, tokens, error, enabled
            FROM document_segments
            WHERE document_id = :doc_id
            ORDER BY position
        """), {"doc_id": doc[0]})
        
        segments = list(seg_result)
        
        if segments:
            print(f"\n文档分段 ({len(segments)} 个):")
            print("-" * 120)
            for seg in segments:
                print(f"分段 {seg[1]}: 状态={seg[2]}, 字数={seg[3]}, tokens={seg[4]}, 启用={seg[6]}, 错误={seg[5]}")
        else:
            print("\n⚠ 没有找到文档分段！")
