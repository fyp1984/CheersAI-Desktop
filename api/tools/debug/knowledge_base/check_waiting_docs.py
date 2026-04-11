#!/usr/bin/env python
"""Check for documents in waiting status."""

import sys
from pathlib import Path

API_ROOT = Path(__file__).resolve().parents[3]
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from extensions.ext_database import db
from models.dataset import Document

docs = db.session.query(Document).filter_by(
    dataset_id='36adfd03-f829-4eb6-a3b5-041064ef714a',
    indexing_status='waiting'
).order_by(Document.created_at.desc()).limit(10).all()

print(f'\nFound {len(docs)} documents in waiting status:\n')
for d in docs:
    print(f'ID: {d.id}')
    print(f'  Name: {d.name}')
    print(f'  Process Rule ID: {d.dataset_process_rule_id}')
    print(f'  Created: {d.created_at}')
    print(f'  Batch: {d.batch}')
    print()
