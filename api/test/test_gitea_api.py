#!/usr/bin/env python3
"""Test Gitea API endpoints."""
import requests
from dotenv import load_dotenv

load_dotenv()

# Test the config test endpoint
url = "http://localhost:5001/console/api/gitea/config/test"
data = {
    "gitea_url": "https://uat-filebay.cheersai.cloud",
    "gitea_token": "c260c56115d2a9e32494927672c55eb84cd54d23",
    "gitea_owner": "beta_20260415162204_example_com_9838ca",
    "gitea_repo": "workspace"
}

print("Testing Gitea connection via API...")
print(f"URL: {url}")
print(f"Data: {data}")
print("-" * 60)

try:
    response = requests.post(url, json=data, timeout=30)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
except Exception as e:
    print(f"Error: {e}")
