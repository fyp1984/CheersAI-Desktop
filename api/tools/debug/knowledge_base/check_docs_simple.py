"""Simple script to check document status without loading full app"""

import sys
from pathlib import Path

API_ROOT = Path(__file__).resolve().parents[3]
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

import os
import sys
from sqlalchemy import create_engine, text

# Get database URL from environment
db_url = os.getenv('DB_URI', 'postgresql://postgres:difyai123456@localhost:5432/dify')

# Create engine
engine = create_engine(db_url)

# Query documents
with engine.connect() as conn:
    result = conn.execute(text("""
        SELECT id, name, indexing_status, error, word_count, tokens
        FROM documents
        WHERE dataset_id = '36adfd03-f829-4eb6-a3b5-041064ef714a'
        ORDER BY created_at DESC
    """))
    
    print("\nDocuments in knowledge base:")
    print("-" * 100)
    for row in result:
        print(f"ID: {row[0]}")
        print(f"Name: {row[1]}")
        print(f"Status: {row[2]}")
        print(f"Error: {row[3] if row[3] else 'None'}")
        print(f"Word count: {row[4]}")
        print(f"Tokens: {row[5]}")
        print("-" * 100)
