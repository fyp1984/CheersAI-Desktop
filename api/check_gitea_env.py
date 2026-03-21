"""Check Gitea environment variables."""
import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

print("Checking Gitea environment variables...")
print("=" * 50)

gitea_url = os.getenv('GITEA_URL', '')
gitea_owner = os.getenv('GITEA_OWNER', '')
gitea_repo = os.getenv('GITEA_REPO', '')
gitea_token = os.getenv('GITEA_TOKEN', '')

print(f"GITEA_URL:   {gitea_url or '(not set)'}")
print(f"GITEA_OWNER: {gitea_owner or '(not set)'}")
print(f"GITEA_REPO:  {gitea_repo or '(not set)'}")
print(f"GITEA_TOKEN: {'*' * 10 if gitea_token else '(not set)'}")

print("=" * 50)

if not all([gitea_url, gitea_owner, gitea_repo, gitea_token]):
    print("\n⚠️  Gitea is NOT configured!")
    print("\nTo configure Gitea, add these to your .env file:")
    print("\nGITEA_URL=http://localhost:8080")
    print("GITEA_OWNER=root")
    print("GITEA_REPO=cheersAI")
    print("GITEA_TOKEN=your_token_here")
    print("\nOr configure via the web UI in 'Data Security' settings.")
else:
    print("\n✓ Gitea is configured!")
    print("\nNow test the connection:")
    print("1. Make sure Gitea is running at", gitea_url)
    print("2. Make sure the repository exists:", f"{gitea_owner}/{gitea_repo}")
    print("3. Make sure the token is valid")
