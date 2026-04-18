#!/usr/bin/env python
"""Reset setup status by clearing tenants and accounts."""

import psycopg2

conn_params = {
    'host': '127.0.0.1',
    'port': 5432,
    'database': 'dify',
    'user': 'postgres',
    'password': 'difyai123456'
}

try:
    conn = psycopg2.connect(**conn_params)
    cur = conn.cursor()
    
    # Delete all data to reset setup
    cur.execute("TRUNCATE TABLE accounts CASCADE;")
    cur.execute("TRUNCATE TABLE tenants CASCADE;")
    cur.execute("TRUNCATE TABLE dify_setups CASCADE;")
    
    conn.commit()
    print("✅ Successfully reset setup status")
    
    cur.close()
    conn.close()
    
except Exception as e:
    print(f"❌ Error: {e}")
