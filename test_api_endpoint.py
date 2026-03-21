"""Test Gitea API endpoint directly."""
import requests

print("Testing Gitea API endpoint...")
print("=" * 50)

# Test the files endpoint
url = "http://localhost:5001/console/api/gitea/files?path="

print(f"URL: {url}")
print("\nSending request...")

try:
    response = requests.get(url)
    print(f"Status Code: {response.status_code}")
    print(f"Headers: {dict(response.headers)}")
    
    if response.status_code == 200:
        print("\n✓ Success!")
        data = response.json()
        print(f"Response: {data}")
        
        if 'files' in data:
            files = data['files']
            print(f"\nFound {len(files)} files:")
            for f in files:
                print(f"  - {f}")
    else:
        print(f"\n✗ Error: {response.status_code}")
        print(f"Response: {response.text}")
        
except Exception as e:
    print(f"\n✗ Exception: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 50)
print("\nNote: 401 error is expected (requires authentication)")
print("The important thing is that the endpoint exists and responds")
