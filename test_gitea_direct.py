"""Direct test of Gitea API."""
import os
import sys

# Add the api directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'api'))

from dotenv import load_dotenv
load_dotenv('api/.env')

print("Testing Gitea connection directly...")
print("=" * 50)

# Check environment variables
gitea_url = os.getenv('GITEA_URL', '')
gitea_owner = os.getenv('GITEA_OWNER', '')
gitea_repo = os.getenv('GITEA_REPO', '')
gitea_token = os.getenv('GITEA_TOKEN', '')

print(f"GITEA_URL:   {gitea_url}")
print(f"GITEA_OWNER: {gitea_owner}")
print(f"GITEA_REPO:  {gitea_repo}")
print(f"GITEA_TOKEN: {'*' * 10 if gitea_token else '(not set)'}")
print("=" * 50)

if not all([gitea_url, gitea_owner, gitea_repo, gitea_token]):
    print("\n❌ Gitea is NOT configured in .env file!")
    sys.exit(1)

# Test Gitea connection
from services.gitea_storage_service import GiteaStorageService

try:
    print("\nInitializing Gitea service...")
    gitea_service = GiteaStorageService()
    print("✓ Gitea service initialized")
    
    print("\nTesting connection by listing files...")
    files = gitea_service.list_files('')
    print(f"✓ Successfully connected!")
    print(f"  Found {len(files)} items in repository")
    
    if files:
        print("\nFiles in repository:")
        for f in files[:10]:  # Show first 10 files
            print(f"  - {f.get('name', 'unknown')} ({f.get('size', 0)} bytes)")
    else:
        print("\n  Repository is empty")
        
except FileNotFoundError as e:
    print(f"✗ Repository not found: {str(e)}")
    print("\nPlease create the repository in Gitea:")
    print(f"  1. Visit {gitea_url}")
    print(f"  2. Create repository: {gitea_owner}/{gitea_repo}")
except Exception as e:
    print(f"✗ Connection failed: {str(e)}")
    print(f"  Error type: {type(e).__name__}")
    import traceback
    traceback.print_exc()
