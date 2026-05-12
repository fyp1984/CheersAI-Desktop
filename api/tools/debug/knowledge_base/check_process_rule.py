"""Check dataset process rule configuration"""

import sys
from pathlib import Path

API_ROOT = Path(__file__).resolve().parents[3]
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

import os

from sqlalchemy import create_engine, text

# Get database URL from environment
db_url = os.getenv('DB_URI', 'postgresql://postgres:difyai123456@localhost:5432/dify')

# Create engine
engine = create_engine(db_url)

# Query process rule
with engine.connect() as conn:
    result = conn.execute(text("""
        SELECT id, mode, rules
        FROM dataset_process_rules
        WHERE id = '7d56c869-3a88-4a2f-af6e-40f3a1dc62b5'
    """))
    
    row = result.fetchone()
    
    if row:
        print("\n处理规则详情:")
        print("=" * 120)
        print(f"ID: {row[0]}")
        print(f"模式: {row[1]}")
        print(f"规则: {row[2]}")
        print("=" * 120)
