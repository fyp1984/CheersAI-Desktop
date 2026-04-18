#!/usr/bin/env python
"""Add custom_config column to accounts table if it doesn't exist."""

import psycopg2

# Database connection parameters
conn_params = {
    'host': '127.0.0.1',
    'port': 5432,
    'database': 'dify',
    'user': 'postgres',
    'password': 'difyai123456'
}

try:
    # Connect to database
    conn = psycopg2.connect(**conn_params)
    cur = conn.cursor()
    
    # Add custom_config column if it doesn't exist
    cur.execute("""
        ALTER TABLE accounts 
        ADD COLUMN IF NOT EXISTS custom_config TEXT;
    """)
    
    conn.commit()
    print("✅ Successfully added custom_config column to accounts table")
    
    cur.close()
    conn.close()
    
except Exception as e:
    print(f"❌ Error: {e}")
