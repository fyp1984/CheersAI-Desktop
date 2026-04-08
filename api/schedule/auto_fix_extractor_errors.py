"""
Auto-fix documents that fail due to dify_extractor connection errors.

This task automatically detects documents that failed due to dify_extractor
plugin issues and re-triggers indexing without the plugin.
"""

import json
import logging

from celery import shared_task
from sqlalchemy import and_

from extensions.ext_database import db
from models.dataset import Document, DocumentSegment
from services.document_indexing_proxy.document_indexing_task_proxy import DocumentIndexingTaskProxy

logger = logging.getLogger(__name__)


@shared_task(queue="dataset")
def auto_fix_extractor_errors_task():
    """
    Automatically fix documents that failed due to dify_extractor errors.
    
    Strategy:
    1. Find documents with dify_extractor connection errors
    2. Delete any incomplete segments
    3. Modify data_source_info to bypass plugin
    4. Reset document status to 'waiting'
    5. Trigger normal indexing (will use built-in extractors)
    """
    logger.info("Starting auto-fix extractor errors task")
    
    try:
        # Find documents with dify_extractor errors
        error_documents = (
            db.session.query(Document)
            .filter(
                and_(
                    Document.indexing_status == "error",
                    Document.enabled == True,
                    Document.error.like("%dify_extractor%"),
                    Document.error.like("%Connection refused%"),
                )
            )
            .all()
        )
        
        if not error_documents:
            logger.info("No documents with dify_extractor errors found")
            return {"fixed": 0, "failed": 0, "skipped": 0}
        
        logger.info(f"Found {len(error_documents)} documents with dify_extractor errors")
        
        fixed_count = 0
        failed_count = 0
        skipped_count = 0
        
        for doc in error_documents:
            try:
                logger.info(f"Processing document {doc.id}: {doc.name}")
                
                # Delete any existing segments
                deleted_segments = db.session.query(DocumentSegment).filter_by(document_id=doc.id).delete()
                if deleted_segments > 0:
                    logger.info(f"Deleted {deleted_segments} incomplete segments")
                
                # Modify data_source_info to bypass dify_extractor
                data_source_info = json.loads(doc.data_source_info) if doc.data_source_info else {}
                
                # Add markers to force built-in extractor usage
                data_source_info["use_builtin_extractor"] = True
                data_source_info["bypass_dify_extractor"] = True
                data_source_info["force_text_extraction"] = True
                
                # Remove any plugin-related configuration
                if "plugin_id" in data_source_info:
                    del data_source_info["plugin_id"]
                if "plugin_config" in data_source_info:
                    del data_source_info["plugin_config"]
                
                doc.data_source_info = json.dumps(data_source_info)
                
                # Reset document status to waiting
                doc.indexing_status = "waiting"
                doc.error = None
                doc.completed_at = None
                doc.word_count = 0
                doc.tokens = 0
                
                db.session.commit()
                
                # Trigger indexing using normal flow
                logger.info(f"Triggering indexing for document {doc.id}")
                DocumentIndexingTaskProxy(doc.tenant_id, doc.dataset_id, [doc.id]).delay()
                
                logger.info(f"✓ Successfully reset and triggered indexing for document {doc.id}: {doc.name}")
                fixed_count += 1
                
            except Exception as e:
                logger.error(f"Error fixing document {doc.id}: {str(e)}", exc_info=True)
                db.session.rollback()
                failed_count += 1
        
        result = {"fixed": fixed_count, "failed": failed_count, "skipped": skipped_count}
        logger.info(f"Auto-fix extractor errors task completed: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Error in auto-fix extractor errors task: {str(e)}", exc_info=True)
        db.session.rollback()
        return {"error": str(e)}
