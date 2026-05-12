#!/usr/bin/env python
"""Fix documents without process rule by assigning the latest dataset process rule"""

import sys
from pathlib import Path

API_ROOT = Path(__file__).resolve().parents[3]
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

import click

from app_factory import create_app
from extensions.ext_database import db
from models.dataset import Dataset, DatasetProcessRule, Document

app = create_app()


@click.command()
@click.option('--dataset-id', help='Specific dataset ID to fix (optional)')
@click.option('--auto-trigger', is_flag=True, help='Automatically trigger indexing for fixed documents')
def fix_process_rules(dataset_id, auto_trigger):
    """Fix documents without process rules"""
    with app.app_context():
        query = db.session.query(Document).filter(
            Document.dataset_process_rule_id.is_(None),
            Document.indexing_status == 'waiting'
        )
        
        if dataset_id:
            query = query.filter(Document.dataset_id == dataset_id)
        
        documents = query.all()
        
        if not documents:
            click.echo('No documents need fixing')
            return
        
        # Group by dataset
        datasets_docs = {}
        for doc in documents:
            if doc.dataset_id not in datasets_docs:
                datasets_docs[doc.dataset_id] = []
            datasets_docs[doc.dataset_id].append(doc)
        
        fixed_count = 0
        for ds_id, docs in datasets_docs.items():
            # Get latest process rule for this dataset
            process_rule = db.session.query(DatasetProcessRule).filter_by(
                dataset_id=ds_id
            ).order_by(DatasetProcessRule.created_at.desc()).first()
            
            if not process_rule:
                click.echo(f'No process rule found for dataset {ds_id}, skipping {len(docs)} documents')
                continue
            
            # Update documents
            for doc in docs:
                doc.dataset_process_rule_id = process_rule.id
                db.session.add(doc)
                fixed_count += 1
            
            click.echo(f'Fixed {len(docs)} documents in dataset {ds_id}')
        
        db.session.commit()
        click.echo(f'Total fixed: {fixed_count} documents')
        
        if auto_trigger and fixed_count > 0:
            from tasks.document_indexing_task import normal_document_indexing_task
            
            for ds_id, docs in datasets_docs.items():
                dataset = db.session.query(Dataset).filter_by(id=ds_id).first()
                if dataset:
                    doc_ids = [str(doc.id) for doc in docs]
                    normal_document_indexing_task.delay(
                        tenant_id=str(dataset.tenant_id),
                        dataset_id=ds_id,
                        document_ids=doc_ids
                    )
                    click.echo(f'Triggered indexing for {len(doc_ids)} documents in dataset {ds_id}')


if __name__ == '__main__':
    fix_process_rules()
