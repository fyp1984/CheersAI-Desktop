"""Upload a test file to Gitea repository."""
import os
import sys
import requests
import base64

from dotenv import load_dotenv
load_dotenv('api/.env')

print("=" * 60)
print("上传测试文件到 Gitea")
print("=" * 60)

# Get Gitea configuration
gitea_url = os.getenv('GITEA_URL', '')
gitea_owner = os.getenv('GITEA_OWNER', '')
gitea_repo = os.getenv('GITEA_REPO', '')
gitea_token = os.getenv('GITEA_TOKEN', '')

print(f"\nGitea 配置:")
print(f"  URL: {gitea_url}")
print(f"  仓库: {gitea_owner}/{gitea_repo}")

if not all([gitea_url, gitea_owner, gitea_repo, gitea_token]):
    print("\n❌ Gitea 配置不完整！")
    sys.exit(1)

# Create test file content
test_content = """这是一个测试文件
用于验证 Gitea 文件读取功能

测试内容:
- 中文字符
- English characters
- 数字: 123456
- 特殊符号: !@#$%^&*()

测试时间: 2026-03-21
"""

print(f"\n创建测试文件内容 ({len(test_content.encode('utf-8'))} 字节)")

# Encode content to base64
content_base64 = base64.b64encode(test_content.encode('utf-8')).decode('utf-8')

# Upload file to Gitea
file_name = "test_file.txt"
api_url = f"{gitea_url}/api/v1/repos/{gitea_owner}/{gitea_repo}/contents/{file_name}"

print(f"\n上传文件到 Gitea:")
print(f"  文件名: {file_name}")
print(f"  API URL: {api_url}")

headers = {
    "Authorization": f"token {gitea_token}",
    "Content-Type": "application/json"
}

data = {
    "content": content_base64,
    "message": f"Add test file: {file_name}"
}

try:
    # Check if file already exists
    check_response = requests.get(api_url, headers=headers)
    
    if check_response.status_code == 200:
        print(f"\n文件已存在，删除后重新创建...")
        existing_data = check_response.json()
        # Delete existing file
        delete_data = {
            "message": f"Delete old test file: {file_name}",
            "sha": existing_data.get("sha")
        }
        delete_response = requests.delete(api_url, headers=headers, json=delete_data)
        if delete_response.status_code not in [200, 204]:
            print(f"⚠ 删除文件失败: {delete_response.status_code}")
    
    # Create new file
    response = requests.post(
        f"{gitea_url}/api/v1/repos/{gitea_owner}/{gitea_repo}/contents/{file_name}",
        headers=headers,
        json=data
    )
    
    if response.status_code in [200, 201]:
        print(f"✓ 文件上传成功！")
        result = response.json()
        print(f"\n文件信息:")
        print(f"  名称: {result.get('content', {}).get('name')}")
        print(f"  路径: {result.get('content', {}).get('path')}")
        print(f"  大小: {result.get('content', {}).get('size')} bytes")
        print(f"  SHA: {result.get('content', {}).get('sha', '')[:10]}...")
    else:
        print(f"✗ 上传失败: {response.status_code}")
        print(f"  错误: {response.text}")
        sys.exit(1)
        
except Exception as e:
    print(f"✗ 上传异常: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 60)
print("现在运行测试脚本验证读取功能:")
print("=" * 60)
print("\npython test_gitea_file_read.py")
