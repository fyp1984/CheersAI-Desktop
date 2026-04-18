#!/usr/bin/env python3
"""测试 FileBay Config Service（带 SSL 修复）"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

# 加载环境变量
from dotenv import load_dotenv
load_dotenv()

from flask import Flask
from extensions.ext_database import db
from services.filebay_config_service import resolve_filebay_config


def print_separator(char="=", length=80):
    """打印分隔线"""
    print(char * length)


def test_real_users():
    """测试真实用户"""
    from configs import dify_config
    
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = dify_config.SQLALCHEMY_DATABASE_URI
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = dify_config.SQLALCHEMY_ENGINE_OPTIONS
    
    db.init_app(app)
    
    with app.app_context():
        print_separator()
        print("测试 FileBay Config Service - 真实用户")
        print_separator()
        
        # 测试用户列表
        test_users = [
            "1@qq.com",
            "103456686@qq.com",
        ]
        
        for email in test_users:
            print(f"\n测试用户: {email}")
            print("-" * 80)
            
            try:
                config = resolve_filebay_config(
                    email,
                    allow_global_fallback=False,
                    mask_token=False
                )
                
                print(f"✓ 配置解析成功")
                print(f"  URL:   {config.gitea_url}")
                print(f"  Owner: {config.gitea_owner}")
                print(f"  Repo:  {config.gitea_repo}")
                print(f"  Token: {config.gitea_token[:20]}...{config.gitea_token[-10:]}")
                
                # 测试 Token 是否有效
                import requests
                import urllib3
                urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
                
                test_url = f"{config.gitea_url}/api/v1/user"
                response = requests.get(
                    test_url,
                    headers={"Authorization": f"token {config.gitea_token}"},
                    verify=False,
                    timeout=10
                )
                
                if response.status_code == 200:
                    user_info = response.json()
                    print(f"✓ Token 验证成功")
                    print(f"  用户名: {user_info.get('login')}")
                    print(f"  用户ID: {user_info.get('id')}")
                else:
                    print(f"✗ Token 验证失败: {response.status_code}")
                    print(f"  响应: {response.text[:200]}")
                
            except LookupError as e:
                print(f"✗ 查找失败: {e}")
            except Exception as e:
                print(f"✗ 错误: {e}")
                import traceback
                traceback.print_exc()
        
        print_separator()


def test_ssl_connection():
    """测试 SSL 连接"""
    print_separator()
    print("测试 SSL 连接")
    print_separator()
    
    from services.filebay_config_service import _create_session_with_ssl_workaround
    
    session = _create_session_with_ssl_workaround()
    
    try:
        response = session.get(
            "https://uat-filebay.cheersai.cloud/api/v1/version",
            verify=False,
            timeout=10
        )
        
        print(f"✓ SSL 连接成功")
        print(f"  状态码: {response.status_code}")
        print(f"  响应: {response.text[:200]}")
        
    except Exception as e:
        print(f"✗ SSL 连接失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()
    
    print_separator()


def test_admin_api():
    """测试 Admin API"""
    print_separator()
    print("测试 Admin API")
    print_separator()
    
    from services.filebay_config_service import _filebay_admin_request
    
    try:
        # 测试获取版本信息
        response = _filebay_admin_request(
            method="GET",
            path="/api/v1/version"
        )
        
        print(f"✓ Admin API 调用成功")
        print(f"  状态码: {response.status_code}")
        print(f"  响应: {response.text[:200]}")
        
        # 测试搜索用户
        response = _filebay_admin_request(
            method="GET",
            path="/api/v1/admin/emails/search",
            params={"q": "1@qq.com", "limit": 10}
        )
        
        print(f"\n✓ 用户搜索成功")
        print(f"  状态码: {response.status_code}")
        
        if response.status_code == 200:
            users = response.json()
            print(f"  找到用户数: {len(users) if isinstance(users, list) else 'N/A'}")
            if isinstance(users, list) and users:
                for user in users[:3]:
                    print(f"    - {user.get('email')} ({user.get('username')})")
        
    except Exception as e:
        print(f"✗ Admin API 调用失败: {e}")
        import traceback
        traceback.print_exc()
    
    print_separator()


if __name__ == "__main__":
    # 测试 SSL 连接
    test_ssl_connection()
    
    # 测试 Admin API
    test_admin_api()
    
    # 测试真实用户
    test_real_users()
