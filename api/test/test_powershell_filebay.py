#!/usr/bin/env python3
"""使用 PowerShell 调用 FileBay API"""
import sys
from pathlib import Path
import subprocess
import json
import base64

sys.path.insert(0, str(Path(__file__).parent))

FILEBAY_URL = "https://uat-filebay.cheersai.cloud"
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "3DIS9cqlR8@E"


def powershell_request(url, method="GET", body=None, headers=None):
    """使用 PowerShell 发送 HTTP 请求"""
    # 创建基本认证
    auth_string = f"{ADMIN_USERNAME}:{ADMIN_PASSWORD}"
    auth_bytes = auth_string.encode('utf-8')
    auth_b64 = base64.b64encode(auth_bytes).decode('utf-8')
    
    # 构建 PowerShell 命令
    ps_headers = {
        "Authorization": f"Basic {auth_b64}",
        "Content-Type": "application/json"
    }
    
    if headers:
        ps_headers.update(headers)
    
    # 构建 headers 字符串
    headers_str = "@{"
    for key, value in ps_headers.items():
        headers_str += f"'{key}'='{value}';"
    headers_str = headers_str.rstrip(';') + "}"
    
    # 构建命令
    if method == "GET":
        ps_command = f"""
        [System.Net.ServicePointManager]::ServerCertificateValidationCallback = {{$true}}
        $response = Invoke-WebRequest -Uri '{url}' -Method GET -Headers {headers_str} -UseBasicParsing
        $response.Content
        """
    else:
        body_json = json.dumps(body) if body else "{}"
        body_json_escaped = body_json.replace("'", "''").replace('"', '`"')
        ps_command = f"""
        [System.Net.ServicePointManager]::ServerCertificateValidationCallback = {{$true}}
        $body = '{body_json_escaped}'
        $response = Invoke-WebRequest -Uri '{url}' -Method {method} -Headers {headers_str} -Body $body -UseBasicParsing
        $response.Content
        """
    
    try:
        result = subprocess.run(
            ["powershell", "-Command", ps_command],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            return result.stdout.strip()
        else:
            print(f"PowerShell 错误: {result.stderr}")
            return None
    except Exception as e:
        print(f"执行失败: {e}")
        return None


def test_search_user(email):
    """搜索用户"""
    print("=" * 80)
    print(f"搜索用户: {email}")
    print("=" * 80)
    
    url = f"{FILEBAY_URL}/api/v1/admin/emails/search?q={email}&limit=10"
    
    result = powershell_request(url)
    
    if result:
        try:
            users = json.loads(result)
            print(f"✓ 搜索成功!")
            print(f"  找到用户数: {len(users) if isinstance(users, list) else 'N/A'}")
            
            if isinstance(users, list) and users:
                for user in users:
                    print(f"\n  用户信息:")
                    print(f"    邮箱: {user.get('email')}")
                    print(f"    用户名: {user.get('username') or user.get('login')}")
                    print(f"    ID: {user.get('id')}")
                
                return users[0]
        except json.JSONDecodeError as e:
            print(f"✗ JSON 解析失败: {e}")
            print(f"  响应: {result[:500]}")
    else:
        print(f"✗ 搜索失败")
    
    return None


def test_create_token(username):
    """创建 Token"""
    print()
    print("=" * 80)
    print(f"为用户创建 Token: {username}")
    print("=" * 80)
    
    url = f"{FILEBAY_URL}/api/v1/users/{username}/tokens"
    
    body = {
        "name": f"desktop-auto-{username}",
        "scopes": ["read:user", "read:repository", "write:repository"]
    }
    
    headers = {"Sudo": username}
    
    result = powershell_request(url, method="POST", body=body, headers=headers)
    
    if result:
        try:
            token_data = json.loads(result)
            token = token_data.get('sha1') or token_data.get('token')
            
            if token:
                print(f"✓ Token 创建成功!")
                print(f"  Token: {token[:20]}...{token[-10:]}")
                return token
            else:
                print(f"✗ Token 创建失败: 响应中没有 token")
                print(f"  响应: {result[:500]}")
        except json.JSONDecodeError as e:
            print(f"✗ JSON 解析失败: {e}")
            print(f"  响应: {result[:500]}")
    else:
        print(f"✗ Token 创建失败")
    
    return None


def save_to_database(email, username, repo, token):
    """保存到数据库"""
    print()
    print("=" * 80)
    print("保存配置到数据库")
    print("=" * 80)
    
    try:
        from flask import Flask
        from extensions.ext_database import db
        from models.account import Account
        from configs import dify_config
        
        app = Flask(__name__)
        app.config['SQLALCHEMY_DATABASE_URI'] = dify_config.SQLALCHEMY_DATABASE_URI
        app.config['SQLALCHEMY_ENGINE_OPTIONS'] = dify_config.SQLALCHEMY_ENGINE_OPTIONS
        
        db.init_app(app)
        
        with app.app_context():
            account = db.session.query(Account).filter_by(email=email).first()
            
            if not account:
                print(f"✗ 未找到账号: {email}")
                return False
            
            account.custom_config = {
                'gitea_url': FILEBAY_URL,
                'gitea_owner': username,
                'gitea_repo': repo,
                'gitea_token': token
            }
            
            db.session.commit()
            
            print(f"✓ 配置已保存!")
            print(f"  邮箱: {email}")
            print(f"  用户名: {username}")
            print(f"  仓库: {repo}")
            print(f"  Token: {token[:20]}...{token[-10:]}")
            
            return True
    except Exception as e:
        print(f"✗ 保存失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主函数"""
    print()
    print("=" * 80)
    print("使用 PowerShell 自动配置 FileBay")
    print("=" * 80)
    print()
    
    # 测试用户
    test_users = [
        "1@qq.com",
        "103456686@qq.com"
    ]
    
    for email in test_users:
        print()
        print("=" * 80)
        print(f"处理用户: {email}")
        print("=" * 80)
        print()
        
        # 1. 搜索用户
        user = test_search_user(email)
        
        if not user:
            print(f"✗ 未找到用户，跳过")
            continue
        
        username = user.get('username') or user.get('login')
        
        if not username:
            print(f"✗ 用户名为空，跳过")
            continue
        
        # 2. 创建 Token
        token = test_create_token(username)
        
        if not token:
            print(f"✗ Token 创建失败，跳过")
            continue
        
        # 3. 保存到数据库
        save_to_database(email, username, "workspace", token)
    
    print()
    print("=" * 80)
    print("处理完成")
    print("=" * 80)


if __name__ == "__main__":
    main()
