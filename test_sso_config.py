#!/usr/bin/env python3
"""
测试 SSO 配置是否正确加载
"""
import sys
import os

# 切换到 api 目录
api_dir = os.path.join(os.path.dirname(__file__), 'api')
os.chdir(api_dir)

# 添加 api 目录到 Python 路径
sys.path.insert(0, api_dir)

try:
    from configs import dify_config
    
    print("=" * 60)
    print("SSO 配置检查")
    print("=" * 60)
    
    print(f"\n✓ SSO_API_URL: {dify_config.SSO_API_URL}")
    print(f"✓ DESKTOP_SSO_CLIENT_ID: {dify_config.DESKTOP_SSO_CLIENT_ID}")
    
    if dify_config.DESKTOP_SSO_CLIENT_SECRET:
        # 只显示前几个字符，保护密钥
        secret_preview = dify_config.DESKTOP_SSO_CLIENT_SECRET[:8] + "..." if len(dify_config.DESKTOP_SSO_CLIENT_SECRET) > 8 else "***"
        print(f"✓ DESKTOP_SSO_CLIENT_SECRET: {secret_preview}")
    else:
        print("✗ DESKTOP_SSO_CLIENT_SECRET: 未设置")
        print("\n⚠️  警告：需要设置 DESKTOP_SSO_CLIENT_SECRET")
        print("   请在 api/.env 文件中添加：")
        print("   DESKTOP_SSO_CLIENT_SECRET=你的客户端密钥")
    
    print("\n" + "=" * 60)
    
    if not dify_config.SSO_API_URL:
        print("✗ 错误：SSO_API_URL 未设置")
        sys.exit(1)
    
    if not dify_config.DESKTOP_SSO_CLIENT_ID:
        print("✗ 错误：DESKTOP_SSO_CLIENT_ID 未设置")
        sys.exit(1)
    
    if not dify_config.DESKTOP_SSO_CLIENT_SECRET:
        print("⚠️  警告：DESKTOP_SSO_CLIENT_SECRET 未设置，SSO 登录将失败")
        sys.exit(1)
    
    print("✓ 所有 SSO 配置项已正确设置")
    print("\n可以开始测试 SSO 登录了！")
    
except Exception as e:
    print(f"✗ 错误：{e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
