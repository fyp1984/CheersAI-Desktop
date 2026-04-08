"""
Auto-fix documents missing dataset_process_rule_id and trigger indexing.

This scheduled task runs periodically to find documents that are stuck in "waiting" status
because they don't have a dataset_process_rule_id assigned or haven't been triggered for indexing,
and automatically fixes them by assigning the latest process rule and triggering indexing.
"""

import logging
import time

from celery import shared_task
from sqlalchemy import and_

from extensions.ext_database import db
from models.dataset import Dataset, DatasetProcessRule, Document

logger = logging.getLogger(__name__)


@shared_task(queue="dataset")
def auto_fix_documents_process_rule_task():
    """
    Automatically fix documents missing dataset_process_rule_id and trigger indexing.
    
    This task:
    1. Finds documents in "waiting" status (with or without dataset_process_rule_id)
    2. For documents without process rule, assigns the latest process rule from their dataset
    3. Triggers indexing for ALL waiting documents
    """
    logger.info("Starting auto-fix documents process rule task")
    
    try:
        # Find ALL documents in waiting status (regardless of process rule)
        waiting_documents = (
            db.session.query(Document)
            .filter(
                and_(
                    Document.indexing_status == "waiting",
                    Document.enabled == True,
                )
            )
            .all()
        )
        
        if not waiting_documents:
            logger.info("No waiting documents found")
            return {"fixed": 0, "failed": 0, "triggered": 0}
        
        logger.info(f"Found {len(waiting_documents)} waiting documents")
        
        fixed_count = 0
        failed_count = 0
        triggered_count = 0
        
        # Group documents by dataset_id for efficiency
        documents_by_dataset = {}
        for doc in waiting_documents:
            if doc.dataset_id not in documents_by_dataset:
                documents_by_dataset[doc.dataset_id] = []
            documents_by_dataset[doc.dataset_id].append(doc)
        
        # Process each dataset's documents
        for dataset_id, docs in documents_by_dataset.items():
            try:
                # Get the latest process rule for this dataset
                process_rule = (
                    db.session.query(DatasetProcessRule)
                    .filter_by(dataset_id=dataset_id)
                    .order_by(DatasetProcessRule.created_at.desc())
                    .first()
                )
                
                if not process_rule:
                    logger.warning(f"No process rule found for dataset {dataset_id}, skipping {len(docs)} documents")
                    failed_count += len(docs)
                    continue
                
                # Separate documents that need process rule fix
                docs_needing_fix = []
                docs_ready_to_index = []
                
                for doc in docs:
                    if not doc.dataset_process_rule_id:
                        docs_needing_fix.append(doc)
                        doc.dataset_process_rule_id = process_rule.id
                        doc.updated_at = db.func.now()
                    else:
                        docs_ready_to_index.append(doc)
                
                if docs_needing_fix:
                    db.session.commit()
                    logger.info(f"Fixed {len(docs_needing_fix)} documents for dataset {dataset_id} with process rule {process_rule.id}")
                    fixed_count += len(docs_needing_fix)
                
                # Trigger indexing for ALL documents (both fixed and already having process rule)
                all_document_ids = [doc.id for doc in docs]
                
                if all_document_ids:
                    from services.document_indexing_proxy.document_indexing_task_proxy import DocumentIndexingTaskProxy
                    
                    dataset = db.session.query(Dataset).filter_by(id=dataset_id).first()
                    if dataset:
                        DocumentIndexingTaskProxy(dataset.tenant_id, dataset_id, all_document_ids).delay()
                        logger.info(f"Triggered indexing for {len(all_document_ids)} documents in dataset {dataset_id}")
                        triggered_count += len(all_document_ids)
                
            except Exception as e:
                logger.error(f"Error processing documents for dataset {dataset_id}: {str(e)}")
                db.session.rollback()
                failed_count += len(docs)
        
        result = {"fixed": fixed_count, "failed": failed_count, "triggered": triggered_count}
        logger.info(f"Auto-fix task completed: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Error in auto-fix documents process rule task: {str(e)}")
        db.session.rollback()
        return {"error": str(e)}
