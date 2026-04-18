#!/usr/bin/env python3
"""Check if custom_config column exists in accounts table"""
import sys
from sqlalchemy import create_engine, text

# Database connection
DB_URI = "postgresql://postgres:difyai123456@127.0.0.1:5432/dify"

try:
    engine = create_engine(DB_URI)
    with engine.connect() as conn:
        result = conn.execute(text(
            "SELECT column_name, data_type "
            "FROM information_schema.columns "
            "WHERE table_name='accounts' AND column_name='custom_config'"
        ))
        rows = result.fetchall()
        
        if rows:
            print("✓ custom_config column EXISTS in accounts table")
            for row in rows:
                print(f"  Column: {row[0]}, Type: {row[1]}")
        else:
            print("✗ custom_config column DOES NOT EXIST in accounts table")
            sys.exit(1)
            
except Exception as e:
    print(f"✗ Error checking database: {e}")
    sys.exit(1)
