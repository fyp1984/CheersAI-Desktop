#!/usr/bin/env python3
"""Test if SSL configuration works in Flask context."""
import sys
sys.path.insert(0, '.')

from app_factory import create_app
from services.gitea_storage_service import GiteaStorageService

print("Creating Flask app...")
app = create_app()

print("\nTesting GiteaStorageService in Flask context...")
with app.app_context():
    try:
        service = GiteaStorageService()
        print(f"Service URL: {service.request_base_url}")
        print(f"Owner: {service.gitea_owner}")
        print(f"Repo: {service.gitea_repo}")
        
        files = service.list_files('')
        print(f"✓ Success! Found {len(files)} files")
        for f in files[:3]:
            print(f"  - {f['name']}")
    except Exception as e:
        print(f"✗ Failed: {e}")
        import traceback
        traceback.print_exc()
