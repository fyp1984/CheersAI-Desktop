#!/usr/bin/env python
"""Check existing accounts in database."""

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
    
    cur.execute('SELECT email, name, status FROM accounts LIMIT 5')
    print('Accounts:')
    for row in cur.fetchall():
        print(f'  Email: {row[0]}, Name: {row[1]}, Status: {row[2]}')
    
    cur.close()
    conn.close()
    
except Exception as e:
    print(f"Error: {e}")
