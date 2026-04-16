#!/usr/bin/env python3
"""Final test of GiteaStorageService with SSL fix."""
import os
from dotenv import load_dotenv

load_dotenv()

# Configure SSL before importing services
from core.ssl_config import configure_ssl_backend
ssl_configured = configure_ssl_backend()
print(f"SSL Backend configured: {ssl_configured}")
print("-" * 60)

# Now import and test the service
from services.gitea_storage_service import GiteaStorageService

# Test with direct connection (should work with pyOpenSSL)
print("\n1. Testing DIRECT connection to FileBay...")
os.environ['GITEA_PROXY_URL'] = ''  # Disable proxy
os.environ['GITEA_OWNER'] = 'beta_20260415162204_example_com_9838ca'
os.environ['GITEA_REPO'] = 'workspace'
service = GiteaStorageService()
print(f"   URL: {service.gitea_url}")
print(f"   Owner: {service.gitea_owner}")
print(f"   Repo: {service.gitea_repo}")
print(f"   Using proxy: {bool(service.gitea_proxy_url)}")

try:
    files = service.list_files('')
    print(f"   ✓ Success! Found {len(files)} files")
    for f in files[:3]:
        print(f"     - {f['name']}")
except Exception as e:
    print(f"   ✗ Failed: {e}")

# Test with proxy
print("\n2. Testing via PROXY...")
os.environ['GITEA_PROXY_URL'] = 'http://localhost:39091'
service2 = GiteaStorageService()
print(f"   URL: {service2.request_base_url}")

try:
    files = service2.list_files('')
    print(f"   ✓ Success! Found {len(files)} files")
    for f in files[:3]:
        print(f"     - {f['name']}")
except Exception as e:
    print(f"   ✗ Failed: {e}")

print("\n" + "=" * 60)
print("SSL Fix Status: WORKING ✓" if ssl_configured else "SSL Fix Status: NOT CONFIGURED ✗")
print("=" * 60)
