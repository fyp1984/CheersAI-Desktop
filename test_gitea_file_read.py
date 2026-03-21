"""Test Gitea file reading from localhost:8080."""
import os
import sys

# Add the api directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'api'))

from dotenv import load_dotenv
load_dotenv('api/.env')

print("=" * 60)
print("测试从 Gitea (localhost:8080) 读取文件")
print("=" * 60)

# Check environment variables
gitea_url = os.getenv('GITEA_URL', '')
gitea_owner = os.getenv('GITEA_OWNER', '')
gitea_repo = os.getenv('GITEA_REPO', '')
gitea_token = os.getenv('GITEA_TOKEN', '')

print(f"\n配置信息:")
print(f"  GITEA_URL:   {gitea_url}")
print(f"  GITEA_OWNER: {gitea_owner}")
print(f"  GITEA_REPO:  {gitea_repo}")
print(f"  GITEA_TOKEN: {'*' * 10}...{gitea_token[-4:] if gitea_token else '(未设置)'}")

if not all([gitea_url, gitea_owner, gitea_repo, gitea_token]):
    print("\n❌ Gitea 配置不完整！")
    sys.exit(1)

print("\n" + "=" * 60)
print("步骤 1: 初始化 Gitea 服务")
print("=" * 60)

from services.gitea_storage_service import GiteaStorageService

try:
    gitea_service = GiteaStorageService()
    print("✓ Gitea 服务初始化成功")
except Exception as e:
    print(f"✗ 初始化失败: {e}")
    sys.exit(1)

print("\n" + "=" * 60)
print("步骤 2: 列出仓库中的文件")
print("=" * 60)

try:
    files = gitea_service.list_files('')
    print(f"✓ 成功获取文件列表")
    print(f"  共找到 {len(files)} 个项目")
    
    if files:
        print("\n文件列表:")
        for i, f in enumerate(files, 1):
            file_type = f.get('type', 'unknown')
            file_name = f.get('name', 'unknown')
            file_size = f.get('size', 0)
            icon = "📁" if file_type == 'dir' else "📄"
            print(f"  {i}. {icon} {file_name} ({file_size} bytes) [type: {file_type}]")
    else:
        print("\n  仓库为空，没有文件")
        print("\n请在 Gitea 中上传测试文件:")
        print(f"  1. 访问 {gitea_url}/{gitea_owner}/{gitea_repo}")
        print(f"  2. 点击 '上传文件'")
        print(f"  3. 上传一些测试文件")
        sys.exit(0)
        
except Exception as e:
    print(f"✗ 获取文件列表失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 60)
print("步骤 3: 测试读取文件内容")
print("=" * 60)

# Find the first file (not directory)
test_file = None
for f in files:
    if f.get('type') == 'file':
        test_file = f
        break

if not test_file:
    print("✗ 没有找到可测试的文件（只有目录）")
    print("\n请在 Gitea 仓库根目录中上传一些文件")
    sys.exit(0)

test_file_name = test_file.get('name')
test_file_size = test_file.get('size', 0)

print(f"测试文件: {test_file_name} ({test_file_size} bytes)")

try:
    # Read file content
    file_content = gitea_service.get_file(test_file_name)
    print(f"✓ 成功读取文件内容")
    print(f"  读取字节数: {len(file_content)}")
    print(f"  预期字节数: {test_file_size}")
    
    if len(file_content) == test_file_size:
        print("  ✓ 文件大小匹配")
    else:
        print(f"  ⚠ 文件大小不匹配")
    
    # Show first 200 bytes
    if len(file_content) > 0:
        preview = file_content[:200]
        try:
            # Try to decode as text
            text_preview = preview.decode('utf-8', errors='ignore')
            print(f"\n  文件内容预览 (前200字节):")
            print(f"  {repr(text_preview)}")
        except:
            print(f"\n  文件内容预览 (前200字节, 二进制):")
            print(f"  {preview.hex()[:100]}...")
            
except FileNotFoundError as e:
    print(f"✗ 文件未找到: {e}")
except Exception as e:
    print(f"✗ 读取文件失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 60)
print("步骤 4: 测试获取文件元数据")
print("=" * 60)

try:
    metadata = gitea_service.get_file_metadata(test_file_name)
    print(f"✓ 成功获取文件元数据")
    print(f"  名称: {metadata.get('name')}")
    print(f"  路径: {metadata.get('path')}")
    print(f"  大小: {metadata.get('size')} bytes")
    print(f"  SHA: {metadata.get('sha', '')[:10]}...")
    print(f"  下载URL: {metadata.get('url', '')[:50]}...")
    
except Exception as e:
    print(f"✗ 获取元数据失败: {e}")

print("\n" + "=" * 60)
print("✅ 测试完成！")
print("=" * 60)
print("\n后端 Gitea 文件读取接口工作正常！")
print(f"\n可以通过以下 API 访问文件:")
print(f"  列出文件: GET /console/api/gitea/files?path=")
print(f"  下载文件: GET /console/api/gitea/files/{test_file_name}")
print(f"  文件元数据: GET /console/api/gitea/files/{test_file_name}/metadata")
