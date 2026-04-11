"""Auto-fix documents without process rules"""
import logging

from celery import shared_task

from extensions.ext_database import db
from models.dataset import Dataset, DatasetProcessRule, Document
from services.document_indexing_proxy.document_indexing_task_proxy import DocumentIndexingTaskProxy

logger = logging.getLogger(__name__)


@shared_task(queue="dataset", bind=True)
def auto_fix_documents_process_rule_task(self):
    """
    Automatically fix documents that are missing process rules.
    This task runs periodically to ensure all waiting documents have process rules assigned.
    """
    try:
        # Find documents without process rules that are waiting
        documents = (
            db.session.query(Document)
            .filter(
                Document.dataset_process_rule_id.is_(None),
                Document.indexing_status == "waiting",
            )
            .all()
        )

        if not documents:
            logger.info("No documents need fixing")
            return {"fixed": 0, "triggered": 0}

        # Group by dataset
        datasets_docs = {}
        for doc in documents:
            if doc.dataset_id not in datasets_docs:
                datasets_docs[doc.dataset_id] = []
            datasets_docs[doc.dataset_id].append(doc)

        fixed_count = 0
        triggered_count = 0

        for ds_id, docs in datasets_docs.items():
            # Get latest process rule for this dataset
            process_rule = (
                db.session.query(DatasetProcessRule)
                .filter_by(dataset_id=ds_id)
                .order_by(DatasetProcessRule.created_at.desc())
                .first()
            )

            if not process_rule:
                logger.warning(f"No process rule found for dataset {ds_id}, skipping {len(docs)} documents")
                continue

            # Update documents
            doc_ids = []
            for doc in docs:
                doc.dataset_process_rule_id = process_rule.id
                db.session.add(doc)
                doc_ids.append(str(doc.id))
                fixed_count += 1

            db.session.commit()
            logger.info(f"Fixed {len(docs)} documents in dataset {ds_id}")

            # Trigger indexing
            dataset = db.session.query(Dataset).filter_by(id=ds_id).first()
            if dataset and doc_ids:
                try:
                    DocumentIndexingTaskProxy(
                        tenant_id=str(dataset.tenant_id), dataset_id=ds_id, document_ids=doc_ids
                    ).delay()
                    triggered_count += len(doc_ids)
                    logger.info(f"Triggered indexing for {len(doc_ids)} documents in dataset {ds_id}")
                except Exception as e:
                    logger.error("Failed to trigger indexing for dataset %s: %s", ds_id, e)

        return {"fixed": fixed_count, "triggered": triggered_count}

    except Exception as e:
        logger.error("Error in auto_fix_documents_process_rule_task: %s", e)
        raise
