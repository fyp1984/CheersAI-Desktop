#!/usr/bin/env python
"""Test Gitea connection with current configuration."""
import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

print("=" * 60)
print("Testing Gitea Connection")
print("=" * 60)

print(f"\nConfiguration:")
print(f"  GITEA_URL: {os.getenv('GITEA_URL')}")
print(f"  GITEA_OWNER: {os.getenv('GITEA_OWNER')}")
print(f"  GITEA_REPO: {os.getenv('GITEA_REPO')}")
print(f"  GITEA_TOKEN: {'*' * 20 if os.getenv('GITEA_TOKEN') else 'Not set'}")
print(f"  GITEA_VERIFY_SSL: {os.getenv('GITEA_VERIFY_SSL')}")
print(f"  BETA_PROVISION_SSL_VERIFY: {os.getenv('BETA_PROVISION_SSL_VERIFY')}")

print(f"\nTesting GiteaStorageService...")
try:
    from services.gitea_storage_service import GiteaStorageService
    
    service = GiteaStorageService()
    print(f"  Service created successfully")
    print(f"  verify_ssl = {service.verify_ssl}")
    
    print(f"\nAttempting to list files...")
    files = service.list_files('')
    print(f"  ✓ Success! Found {len(files)} items")
    for f in files[:5]:
        print(f"    - {f.get('name')} ({f.get('type')})")
    if len(files) > 5:
        print(f"    ... and {len(files) - 5} more")
        
except FileNotFoundError as e:
    print(f"  ✓ Connection successful but directory not found: {e}")
except Exception as e:
    print(f"  ✗ Error: {e}")
    import traceback
    traceback.print_exc()

print(f"\nTesting BetaApplicationProvisioningService...")
try:
    from services.beta_application_provisioning_service import BetaApplicationProvisioningService
    
    service = BetaApplicationProvisioningService()
    print(f"  Service created successfully")
    print(f"  ssl_verify = {service.ssl_verify}")
    print(f"  filebay_base_url = {service.filebay_base_url}")
    
except Exception as e:
    print(f"  ✗ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
