#!/usr/bin/env python
"""Check dify_extractor tool configuration."""

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

# First check the table structure
cur.execute("""
    SELECT column_name, data_type
    FROM information_schema.columns
    WHERE table_name = 'tool_installations'
""")

print("tool_installations table structure:")
for row in cur.fetchall():
    print(f"  - {row[0]}: {row[1]}")

# Check tool_installations for dify_extractor
cur.execute("""
    SELECT *
    FROM tool_installations
    WHERE provider LIKE '%dify_extractor%' OR plugin_id LIKE '%dify_extractor%'
    LIMIT 1
""")

rows = cur.fetchall()
if rows:
    print(f"\nFound dify_extractor installation:")
    print(rows[0])
else:
    print("\nNo dify_extractor installations found")

cur.close()
conn.close()
