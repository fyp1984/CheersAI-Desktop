#!/usr/bin/env python
"""Check dify_extractor plugin configuration."""

import sys
from pathlib import Path

API_ROOT = Path(__file__).resolve().parents[3]
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

import psycopg2
import json

conn = psycopg2.connect(
    host="127.0.0.1",
    port=5432,
    database="dify_plugin",
    user="postgres",
    password="difyai123456"
)

cur = conn.cursor()

# Check if there's a plugin configuration table
cur.execute("""
    SELECT table_name 
    FROM information_schema.tables 
    WHERE table_schema = 'public'
""")

print("Tables in dify_plugin database:")
for table in cur.fetchall():
    print(f"  - {table[0]}")

cur.close()
conn.close()
