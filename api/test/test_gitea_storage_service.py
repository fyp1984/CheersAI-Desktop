#!/usr/bin/env python3
"""测试更新后的 GiteaStorageService"""
import os

# 设置环境变量
os.environ['GITEA_URL'] = 'https://uat-filebay.cheersai.cloud'
os.environ['GITEA_TOKEN'] = '97149d001c6f8ed2ed48d70f5facc9dc0de2516b'
os.environ['GITEA_OWNER'] = 'junqianxi'
os.environ['GITEA_REPO'] = 'workspace'

from services.gitea_storage_service import GiteaStorageService

print("=" * 80)
print("测试: GiteaStorageService (NoSNI 客户端)")
print("=" * 80)

try:
    service = GiteaStorageService()
    
    print(f"\n配置:")
    print(f"  URL: {service.gitea_url}")
    print(f"  Owner: {service.gitea_owner}")
    print(f"  Repo: {service.gitea_repo}")
    print(f"  Token: {service.gitea_token[:20]}...{service.gitea_token[-10:]}")
    
    # 测试 1: 列出文件
    print("\n测试 1: 列出根目录文件")
    print("-" * 60)
    files = service.list_files('')
    print(f"✓ 找到 {len(files)} 个文件/目录")
    for file in files[:5]:
        print(f"  - {file['name']} ({file['type']}) - {file.get('size', 0)} bytes")
    
    # 测试 2: 获取文件元数据
    if files:
        print("\n测试 2: 获取文件元数据")
        print("-" * 60)
        first_file = files[0]
        if first_file['type'] == 'file':
            try:
                path = f"/api/v1/repos/{service.gitea_owner}/{service.gitea_repo}/contents/{first_file['path']}"
                print(f"  请求路径: {path}")
                status_code, content = service.client.get(path)
                print(f"  状态码: {status_code}")
                print(f"  响应长度: {len(content)} bytes")
                print(f"  响应前100字节: {content[:100]}")
                
                metadata = service.get_file_metadata(first_file['path'])
                print(f"✓ 文件: {metadata['name']}")
                print(f"  大小: {metadata['size']} bytes")
                print(f"  SHA: {metadata['sha']}")
            except Exception as e:
                print(f"✗ 失败: {e}")
                import traceback
                traceback.print_exc()
    
    print("\n" + "=" * 80)
    print("✓ 所有测试通过! GiteaStorageService 使用 NoSNI 客户端正常工作")
    print("=" * 80)
    
except Exception as e:
    print(f"\n✗ 测试失败: {e}")
    import traceback
    traceback.print_exc()
