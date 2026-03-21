#!/usr/bin/env python3
"""
Setup script for Gitea storage integration.
This script helps configure and test Gitea storage for CheersAI.
"""
import os
import sys
import requests
from pathlib import Path


def check_gitea_connection(url: str, token: str) -> bool:
    """Check if Gitea server is accessible."""
    try:
        headers = {"Authorization": f"token {token}"}
        response = requests.get(f"{url}/api/v1/user", headers=headers, timeout=5)
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Failed to connect to Gitea: {e}")
        return False


def check_repository_exists(url: str, token: str, owner: str, repo: str) -> bool:
    """Check if the storage repository exists."""
    try:
        headers = {"Authorization": f"token {token}"}
        response = requests.get(
            f"{url}/api/v1/repos/{owner}/{repo}",
            headers=headers,
            timeout=5
        )
        return response.status_code == 200
    except Exception:
        return False


def create_repository(url: str, token: str, owner: str, repo: str) -> bool:
    """Create the storage repository if it doesn't exist."""
    try:
        headers = {
            "Authorization": f"token {token}",
            "Content-Type": "application/json"
        }
        
        # Try to create user repository
        payload = {
            "name": repo,
            "description": "CheersAI file storage repository",
            "private": True,
            "auto_init": True,
        }
        
        response = requests.post(
            f"{url}/api/v1/user/repos",
            headers=headers,
            json=payload,
            timeout=10
        )
        
        if response.status_code == 201:
            print(f"✅ Created repository: {owner}/{repo}")
            return True
        elif response.status_code == 409:
            print(f"ℹ️  Repository already exists: {owner}/{repo}")
            return True
        else:
            print(f"❌ Failed to create repository: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error creating repository: {e}")
        return False


def test_file_upload(url: str, token: str, owner: str, repo: str) -> bool:
    """Test file upload to Gitea."""
    try:
        import base64
        
        headers = {
            "Authorization": f"token {token}",
            "Content-Type": "application/json"
        }
        
        # Create a test file
        test_content = b"This is a test file for CheersAI Gitea storage integration."
        content_base64 = base64.b64encode(test_content).decode("utf-8")
        
        payload = {
            "content": content_base64,
            "message": "Test upload from CheersAI setup script",
        }
        
        api_url = f"{url}/api/v1/repos/{owner}/{repo}/contents/test/setup_test.txt"
        
        response = requests.post(api_url, headers=headers, json=payload, timeout=10)
        
        if response.status_code in [200, 201]:
            print("✅ Test file upload successful")
            
            # Try to delete the test file
            result = response.json()
            sha = result.get("content", {}).get("sha")
            if sha:
                delete_payload = {
                    "message": "Delete test file",
                    "sha": sha
                }
                requests.delete(api_url, headers=headers, json=delete_payload, timeout=10)
                print("✅ Test file cleanup successful")
            
            return True
        else:
            print(f"❌ Test upload failed: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error during test upload: {e}")
        return False


def main():
    """Main setup function."""
    print("=" * 60)
    print("CheersAI Gitea Storage Setup")
    print("=" * 60)
    print()
    
    # Load environment variables
    gitea_url = os.getenv("GITEA_URL", "http://localhost:3000")
    gitea_token = os.getenv("GITEA_TOKEN", "")
    gitea_owner = os.getenv("GITEA_OWNER", "cheersai")
    gitea_repo = os.getenv("GITEA_REPO", "file-storage")
    
    # Check if token is provided
    if not gitea_token:
        print("❌ GITEA_TOKEN environment variable is not set!")
        print()
        print("Please set the following environment variables:")
        print("  - GITEA_URL (default: http://localhost:3000)")
        print("  - GITEA_TOKEN (required)")
        print("  - GITEA_OWNER (default: cheersai)")
        print("  - GITEA_REPO (default: file-storage)")
        print()
        print("Example:")
        print("  export GITEA_TOKEN=your_token_here")
        print("  python scripts/setup_gitea_storage.py")
        sys.exit(1)
    
    print(f"Configuration:")
    print(f"  Gitea URL: {gitea_url}")
    print(f"  Owner: {gitea_owner}")
    print(f"  Repository: {gitea_repo}")
    print(f"  Token: {'*' * 20}")
    print()
    
    # Step 1: Check Gitea connection
    print("Step 1: Checking Gitea connection...")
    if not check_gitea_connection(gitea_url, gitea_token):
        print("❌ Setup failed: Cannot connect to Gitea")
        sys.exit(1)
    print("✅ Gitea connection successful")
    print()
    
    # Step 2: Check/Create repository
    print("Step 2: Checking storage repository...")
    if not check_repository_exists(gitea_url, gitea_token, gitea_owner, gitea_repo):
        print(f"Repository {gitea_owner}/{gitea_repo} does not exist")
        print("Creating repository...")
        if not create_repository(gitea_url, gitea_token, gitea_owner, gitea_repo):
            print("❌ Setup failed: Cannot create repository")
            sys.exit(1)
    else:
        print(f"✅ Repository exists: {gitea_owner}/{gitea_repo}")
    print()
    
    # Step 3: Test file upload
    print("Step 3: Testing file upload...")
    if not test_file_upload(gitea_url, gitea_token, gitea_owner, gitea_repo):
        print("❌ Setup failed: File upload test failed")
        sys.exit(1)
    print()
    
    # Success
    print("=" * 60)
    print("✅ Gitea storage setup completed successfully!")
    print("=" * 60)
    print()
    print("Next steps:")
    print("1. Add the following to your api/.env file:")
    print()
    print(f"   USE_GITEA_STORAGE=true")
    print(f"   GITEA_URL={gitea_url}")
    print(f"   GITEA_TOKEN={gitea_token}")
    print(f"   GITEA_OWNER={gitea_owner}")
    print(f"   GITEA_REPO={gitea_repo}")
    print()
    print("2. Restart the CheersAI backend service")
    print("3. All file uploads will now use Gitea storage")
    print()


if __name__ == "__main__":
    main()
