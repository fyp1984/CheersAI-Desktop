#!/usr/bin/env python3
"""
CheersAI SQLite Database Initialization Script
"""
import sqlite3
import os
from pathlib import Path


def init_database(db_path: str = "cheersai.db", sql_file: str = "init_sqlite.sql"):
    """
    Initialize SQLite database with schema from SQL file.
    
    Args:
        db_path: Path to SQLite database file
        sql_file: Path to SQL initialization file
    """
    # Get absolute paths
    script_dir = Path(__file__).parent
    db_file = script_dir / db_path
    sql_file_path = script_dir / sql_file
    
    # Check if SQL file exists
    if not sql_file_path.exists():
        raise FileNotFoundError(f"SQL file not found: {sql_file_path}")
    
    # Remove existing database if it exists
    if db_file.exists():
        print(f"Removing existing database: {db_file}")
        os.remove(db_file)
    
    # Create database connection
    print(f"Creating new database: {db_file}")
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    try:
        # Read and execute SQL file
        print(f"Reading SQL file: {sql_file_path}")
        with open(sql_file_path, 'r', encoding='utf-8') as f:
            sql_script = f.read()
        
        print("Executing SQL script...")
        cursor.executescript(sql_script)
        conn.commit()
        
        # Verify tables were created
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = cursor.fetchall()
        
        print("\n✅ Database initialized successfully!")
        print(f"\n📊 Created {len(tables)} tables:")
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
            count = cursor.fetchone()[0]
            print(f"  - {table[0]}: {count} rows")
        
        # Verify views
        cursor.execute("SELECT name FROM sqlite_master WHERE type='view' ORDER BY name")
        views = cursor.fetchall()
        print(f"\n👁️  Created {len(views)} views:")
        for view in views:
            print(f"  - {view[0]}")
        
        # Verify triggers
        cursor.execute("SELECT name FROM sqlite_master WHERE type='trigger' ORDER BY name")
        triggers = cursor.fetchall()
        print(f"\n⚡ Created {len(triggers)} triggers:")
        for trigger in triggers:
            print(f"  - {trigger[0]}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error initializing database: {e}")
        conn.rollback()
        return False
        
    finally:
        conn.close()


def test_database(db_path: str = "cheersai.db"):
    """
    Test database by performing basic queries.
    
    Args:
        db_path: Path to SQLite database file
    """
    script_dir = Path(__file__).parent
    db_file = script_dir / db_path
    
    if not db_file.exists():
        print(f"❌ Database not found: {db_file}")
        return False
    
    print(f"\n🧪 Testing database: {db_file}\n")
    
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    try:
        # Test 1: Check membership plans
        print("Test 1: Membership Plans")
        cursor.execute("SELECT code, name, price_monthly FROM membership_plans ORDER BY sort_order")
        plans = cursor.fetchall()
        for plan in plans:
            print(f"  - {plan[1]} ({plan[0]}): ¥{plan[2] or 'Custom'}/month")
        
        # Test 2: Insert test user
        print("\nTest 2: Insert Test User")
        cursor.execute("""
            INSERT INTO users (email, username, password_hash, nickname)
            VALUES ('test@example.com', 'testuser', 'hashed_password', 'Test User')
        """)
        user_id = cursor.lastrowid
        print(f"  ✅ Created user with ID: {cursor.execute('SELECT id FROM users WHERE email = ?', ('test@example.com',)).fetchone()[0]}")
        
        # Test 3: Create subscription for test user
        print("\nTest 3: Create Subscription")
        cursor.execute("""
            INSERT INTO subscriptions (user_id, plan_code, start_date, end_date, status)
            SELECT id, 'pro', date('now'), date('now', '+1 year'), 'active'
            FROM users WHERE email = 'test@example.com'
        """)
        print(f"  ✅ Created subscription")
        
        # Test 4: Query active subscriptions view
        print("\nTest 4: Active Subscriptions View")
        cursor.execute("SELECT email, plan_name, end_date FROM v_active_subscriptions")
        subs = cursor.fetchall()
        for sub in subs:
            print(f"  - {sub[0]}: {sub[1]} (expires: {sub[2]})")
        
        # Test 5: Insert feedback
        print("\nTest 5: Insert Feedback")
        cursor.execute("""
            INSERT INTO feedbacks (user_id, type, title, content, status, priority)
            SELECT id, 'feature', 'Test Feature Request', 'This is a test feedback', 'pending', 'medium'
            FROM users WHERE email = 'test@example.com'
        """)
        print(f"  ✅ Created feedback")
        
        # Test 6: Insert announcement
        print("\nTest 6: Insert Announcement")
        cursor.execute("""
            INSERT INTO announcements (type, title, content, status, created_by, publish_at)
            SELECT 'update', 'Test Announcement', 'This is a test announcement', 'published', id, datetime('now')
            FROM users WHERE email = 'test@example.com'
        """)
        print(f"  ✅ Created announcement")
        
        # Test 7: Query published announcements view
        print("\nTest 7: Published Announcements View")
        cursor.execute("SELECT title, creator_name FROM v_published_announcements")
        announcements = cursor.fetchall()
        for ann in announcements:
            print(f"  - {ann[0]} (by {ann[1]})")
        
        # Test 8: Audit log
        print("\nTest 8: Insert Audit Log")
        cursor.execute("""
            INSERT INTO audit_logs (log_type, action, operator_id, operator_name, target_type, result)
            SELECT 'user', 'create', id, username, 'user', 'success'
            FROM users WHERE email = 'test@example.com'
        """)
        print(f"  ✅ Created audit log entry")
        
        conn.commit()
        print("\n✅ All tests passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        conn.rollback()
        return False
        
    finally:
        conn.close()


if __name__ == "__main__":
    print("=" * 60)
    print("CheersAI SQLite Database Initialization")
    print("=" * 60)
    
    # Initialize database
    if init_database():
        # Run tests
        test_database()
    
    print("\n" + "=" * 60)
    print("Done!")
    print("=" * 60)
