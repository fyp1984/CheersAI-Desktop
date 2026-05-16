#!/usr/bin/env python
"""Check all documents status."""

import sys
from pathlib import Path

API_ROOT = Path(__file__).resolve().parents[3]
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from sqlalchemy import func

from app_factory import create_app
from extensions.ext_database import db
from models.dataset import Document

app = create_app()

with app.app_context():
    # Get document status counts
    status_counts = (
        db.session.query(Document.indexing_status, func.count(Document.id))
        .filter_by(dataset_id='36adfd03-f829-4eb6-a3b5-041064ef714a')
        .group_by(Document.indexing_status)
        .all()
    )

    print('\nDocument status summary:')
    for status, count in status_counts:
        print(f'  {status}: {count}')

    # Get error documents
    error_docs = (
        db.session.query(Document)
        .filter_by(
            dataset_id='36adfd03-f829-4eb6-a3b5-041064ef714a',
            indexing_status='error'
        )
        .order_by(Document.created_at.desc())
        .limit(5)
        .all()
    )

    if error_docs:
        print('\nRecent error documents:')
        for doc in error_docs:
            print(f'  - {doc.name}')
            print(f'    Error: {doc.error}')
            print(f'    Created: {doc.created_at}')
