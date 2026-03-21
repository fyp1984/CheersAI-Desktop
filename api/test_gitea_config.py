"""Test Gitea configuration API."""
import os
import sys

# Add the api directory to the path
sys.path.insert(0, os.path.dirname(__file__))

from app_factory import create_app

app = create_app()

with app.app_context():
    # Test the Gitea config endpoint
    print("Testing Gitea configuration API...")
    
    # Set test environment variables
    os.environ['GITEA_URL'] = 'http://localhost:8080'
    os.environ['GITEA_OWNER'] = 'root'
    os.environ['GITEA_REPO'] = 'cheersAI'
    os.environ['GITEA_TOKEN'] = 'test_token_12345'
    
    from services.gitea_storage_service import GiteaStorageService
    
    try:
        gitea_service = GiteaStorageService()
        print(f"✓ Gitea service initialized")
        print(f"  URL: {os.getenv('GITEA_URL')}")
        print(f"  Owner: {os.getenv('GITEA_OWNER')}")
        print(f"  Repo: {os.getenv('GITEA_REPO')}")
        
        # Try to list files
        try:
            files = gitea_service.list_files('')
            print(f"✓ Successfully connected! Found {len(files)} items")
        except Exception as e:
            print(f"✗ Connection test failed: {str(e)}")
            print(f"  Error type: {type(e).__name__}")
            
    except Exception as e:
        print(f"✗ Failed to initialize Gitea service: {str(e)}")
        import traceback
        traceback.print_exc()
