"""
Reindex completed documents that don't have embeddings (index_node_id is None)
"""

import sys
from pathlib import Path

API_ROOT = Path(__file__).resolve().parents[3]
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from app_factory import create_app
from extensions.ext_database import db
from models.dataset import Document, DocumentSegment
from services.document_indexing_proxy.document_indexing_task_proxy import DocumentIndexingTaskProxy
import json

app = create_app()

with app.app_context():
    dataset_id = '36adfd03-f829-4eb6-a3b5-041064ef714a'
    
    # Find completed documents with segments that have no embeddings
    docs_to_reindex = []
    
    docs = db.session.query(Document).filter(
        Document.dataset_id == dataset_id,
        Document.indexing_status == 'completed'
    ).all()
    
    for doc in docs:
        segments = db.session.query(DocumentSegment).filter(
            DocumentSegment.document_id == doc.id,
            DocumentSegment.index_node_id == None
        ).first()
        
        if segments:
            docs_to_reindex.append(doc)
    
    if not docs_to_reindex:
        print('✓ All completed documents have embeddings!')
        sys.exit(0)
    
    print(f'\n发现 {len(docs_to_reindex)} 个文档需要重新索引（缺少嵌入）:')
    for doc in docs_to_reindex:
        print(f'  - {doc.name} (ID: {doc.id})')
    
    # Reset and reindex
    print('\n开始重新索引...')
    for doc in docs_to_reindex:
        try:
            # Delete segments
            deleted = db.session.query(DocumentSegment).filter_by(document_id=doc.id).delete()
            print(f'  删除 {deleted} 个分段: {doc.name}')
            
            # Modify data_source_info to bypass plugin
            data_source_info = json.loads(doc.data_source_info) if doc.data_source_info else {}
            data_source_info["use_builtin_extractor"] = True
            data_source_info["bypass_dify_extractor"] = True
            data_source_info["force_text_extraction"] = True
            
            # Remove plugin config
            if "plugin_id" in data_source_info:
                del data_source_info["plugin_id"]
            if "plugin_config" in data_source_info:
                del data_source_info["plugin_config"]
            
            doc.data_source_info = json.dumps(data_source_info)
            
            # Reset status
            doc.indexing_status = 'waiting'
            doc.error = None
            doc.completed_at = None
            doc.word_count = 0
            doc.tokens = 0
            
            db.session.commit()
            
            # Trigger indexing
            DocumentIndexingTaskProxy(doc.tenant_id, doc.dataset_id, [doc.id]).delay()
            print(f'  ✓ 已触发重新索引: {doc.name}')
            
        except Exception as e:
            print(f'  ✗ 失败: {doc.name} - {e}')
            db.session.rollback()
    
    print('\n完成！请检查 Celery Worker 日志查看处理状态。')
