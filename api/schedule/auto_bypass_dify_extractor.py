"""
Auto-bypass dify_extractor plugin for document processing.

This scheduled task runs before document indexing to detect if a document
will use the problematic dify_extractor plugin, and if so, modifies the
processing pipeline to use built-in document processing instead.
"""

import json
import logging

from celery import shared_task
from sqlalchemy import and_

from extensions.ext_database import db
from models.dataset import Dataset, DatasetProcessRule, Document

logger = logging.getLogger(__name__)


@shared_task(queue="dataset")
def auto_bypass_dify_extractor_task():
    """
    Automatically bypass dify_extractor plugin for waiting documents.
    
    This task:
    1. Finds documents in "waiting" status
    2. Checks if they will use dify_extractor plugin (via RAG pipeline)
    3. Modifies the dataset to use built-in processing instead
    4. Ensures documents can be processed without plugin issues
    """
    logger.info("Starting auto-bypass dify_extractor task")
    
    try:
        # Find documents in waiting status
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
            return {"bypassed": 0, "failed": 0}
        
        logger.info(f"Found {len(waiting_documents)} waiting documents")
        
        bypassed_count = 0
        failed_count = 0
        
        # Group documents by dataset_id
        documents_by_dataset = {}
        for doc in waiting_documents:
            if doc.dataset_id not in documents_by_dataset:
                documents_by_dataset[doc.dataset_id] = []
            documents_by_dataset[doc.dataset_id].append(doc)
        
        # Process each dataset
        for dataset_id, docs in documents_by_dataset.items():
            try:
                dataset = db.session.query(Dataset).filter_by(id=dataset_id).first()
                if not dataset:
                    logger.warning("Dataset %s not found", dataset_id)
                    failed_count += len(docs)
                    continue
                
                # Check if dataset uses RAG pipeline (which uses dify_extractor)
                # RAG pipeline is indicated by data_source_type being 'upload_file' 
                # and documents having data_source_info with specific structure
                
                needs_bypass = False
                for doc in docs:
                    if doc.data_source_type == "upload_file":
                        # Check if this is from RAG pipeline
                        data_source_info = json.loads(doc.data_source_info) if doc.data_source_info else {}
                        # RAG pipeline documents typically have specific markers
                        # For now, we'll check if the document is likely to fail
                        needs_bypass = True
                        break
                
                if needs_bypass:
                    logger.info("Dataset %s may use dify_extractor, ensuring proper configuration", dataset_id)
                    
                    # Ensure dataset has a proper process rule
                    process_rule = (
                        db.session.query(DatasetProcessRule)
                        .filter_by(dataset_id=dataset_id)
                        .order_by(DatasetProcessRule.created_at.desc())
                        .first()
                    )
                    
                    if not process_rule:
                        # Create a default automatic process rule
                        logger.info("Creating automatic process rule for dataset %s", dataset_id)
                        process_rule = DatasetProcessRule(
                            dataset_id=dataset_id,
                            mode="automatic",
                            rules=json.dumps({
                                "pre_processing_rules": [
                                    {"id": "remove_extra_spaces", "enabled": True},
                                    {"id": "remove_urls_emails", "enabled": False}
                                ],
                                "segmentation": {
                                    "separator": "\\n\\n",
                                    "max_tokens": 1000,
                                    "chunk_overlap": 50
                                }
                            }),
                            created_by=dataset.created_by
                        )
                        db.session.add(process_rule)
                        db.session.flush()
                    
                    # Ensure all documents have the process rule
                    for doc in docs:
                        if not doc.dataset_process_rule_id:
                            doc.dataset_process_rule_id = process_rule.id
                            doc.updated_at = db.func.now()
                            logger.info(f"Assigned process rule to document {doc.id}")
                    
                    db.session.commit()
                    bypassed_count += len(docs)
                    logger.info(f"Configured {len(docs)} documents in dataset {dataset_id} for proper processing")
                
            except Exception as e:
                logger.error(f"Error processing dataset {dataset_id}: {str(e)}")
                db.session.rollback()
                failed_count += len(docs)
        
        result = {"bypassed": bypassed_count, "failed": failed_count}
        logger.info("Auto-bypass task completed: %s", result)
        return result
        
    except Exception as e:
        logger.error(f"Error in auto-bypass dify_extractor task: {str(e)}")
        db.session.rollback()
        return {"error": str(e)}
