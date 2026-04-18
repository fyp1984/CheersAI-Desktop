#!/usr/bin/env python3
"""Test Redis connection"""
import sys
import redis

try:
    # Connect to Redis
    r = redis.Redis(
        host='127.0.0.1',
        port=6700,
        password='difyai123456',
        db=0,
        decode_responses=True
    )
    
    # Test connection
    r.ping()
    print("✓ Redis connection successful!")
    
    # Test set/get
    r.set('test_key', 'test_value')
    value = r.get('test_key')
    
    if value == 'test_value':
        print("✓ Redis read/write works!")
    else:
        print("✗ Redis read/write failed")
        sys.exit(1)
    
    # Clean up
    r.delete('test_key')
    
    print("\n✓ All Redis tests passed!")
    
except redis.exceptions.AuthenticationError as e:
    print(f"✗ Redis authentication failed: {e}")
    sys.exit(1)
except redis.exceptions.ConnectionError as e:
    print(f"✗ Redis connection failed: {e}")
    sys.exit(1)
except Exception as e:
    print(f"✗ Unexpected error: {e}")
    sys.exit(1)
