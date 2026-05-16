#!/usr/bin/env python
"""Check dify_extractor plugin declaration."""

import sys
from pathlib import Path

API_ROOT = Path(__file__).resolve().parents[3]
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

import json

import psycopg2

conn = psycopg2.connect(
    host="127.0.0.1",
    port=5432,
    database="dify_plugin",
    user="postgres",
    password="difyai123456"
)

cur = conn.cursor()

# Check plugin_declarations for dify_extractor
cur.execute("""
    SELECT id, plugin_unique_identifier, declaration
    FROM plugin_declarations
    WHERE plugin_unique_identifier LIKE '%dify_extractor%'
""")

rows = cur.fetchall()
if rows:
    for row in rows:
        print(f"Plugin: {row[1]}")
        declaration = json.loads(row[2]) if row[2] else {}
        
        # Check for credentials schema
        if 'tools' in declaration:
            for tool in declaration['tools']:
                print(f"\nTool: {tool.get('identity', {}).get('name')}")
                if 'parameters' in tool:
                    print("Parameters:")
                    for param in tool['parameters']:
                        print(f"  - {param.get('name')}: {param.get('type')} (required: {param.get('required', False)})")
else:
    print("No dify_extractor declarations found")

cur.close()
conn.close()
