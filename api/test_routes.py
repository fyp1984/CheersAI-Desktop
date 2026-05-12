#!/usr/bin/env python
"""Test script to list all registered routes."""
import sys
sys.path.insert(0, '.')

from app import app

print("=== All Registered Routes ===")
for rule in sorted(app.url_map.iter_rules(), key=lambda r: str(r)):
    if 'filebay' in str(rule).lower():
        print(f"✓ {rule} [{', '.join(rule.methods - {'HEAD', 'OPTIONS'})}]")

print("\n=== FileBay Routes ===")
filebay_routes = [str(rule) for rule in app.url_map.iter_rules() if 'filebay' in str(rule).lower()]
for route in sorted(filebay_routes):
    print(f"  {route}")

if not filebay_routes:
    print("  ❌ No FileBay routes found!")
