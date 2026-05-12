#!/usr/bin/env python3
"""生成创建 FileBay Token 的命令和配置"""
import json
import sys
from pathlib import Path
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).parent))

from flask import Flask

from configs import dify_config
from extensions.ext_database import db
from models.account import Account


def generate_token_name(email: str) -> str:
    """生成 token 名称"""
    return f"desktop-{email.split('@')[0]}-{uuid4().hex[:8]}"


def generate_commands_for_user(email: str):
    """为用户生成创建 token 的命令"""
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = dify_config.SQLALCHEMY_DATABASE_URI
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = dify_config.SQLALCHEMY_ENGINE_OPTIONS
    
    db.init_app(app)
    
    with app.app_context():
        account = db.session.query(Account).filter_by(email=email).first()
        
        if not account:
            print(f"✗ 未找到账号: {email}")
            return
        
        print("=" * 80)
        print(f"为用户创建 FileBay Token: {email}")
        print("=" * 80)
        print()
        
        # 假设 FileBay 用户名与邮箱前缀相关
        # 你需要替换为实际的 FileBay 用户名
        username_suggestion = email.split('@')[0].replace('.', '_')
        token_name = generate_token_name(email)
        
        print("账号信息:")
        print(f"  邮箱: {account.email}")
        print(f"  姓名: {account.name}")
        print(f"  ID:   {account.id}")
        print()
        
        print("建议的配置:")
        print(f"  FileBay 用户名: {username_suggestion} (请确认实际用户名)")
        print(f"  Token 名称: {token_name}")
        print("  仓库名称: workspace")
        print()
        
        # 生成 curl 命令
        print("-" * 80)
        print("方法 1: 使用 curl 命令（在可以连接 FileBay 的环境中执行）")
        print("-" * 80)
        print()
        
        # 步骤 1: 查找用户
        print("# 步骤 1: 查找用户信息")
        print('curl -k -u "admin:3DIS9cqlR8@E" \\')
        print(f'  "https://uat-filebay.cheersai.cloud/api/v1/admin/emails/search?q={email}"')
        print()
        
        # 步骤 2: 创建 token
        print("# 步骤 2: 为用户创建 Token（替换 <username> 为实际用户名）")
        token_payload = {
            "name": token_name,
            "scopes": ["read:user", "read:repository", "write:repository"]
        }
        print('curl -k -X POST -u "admin:3DIS9cqlR8@E" \\')
        print('  -H "Content-Type: application/json" \\')
        print('  -H "Sudo: <username>" \\')
        print(f"  -d '{json.dumps(token_payload)}' \\")
        print('  "https://uat-filebay.cheersai.cloud/api/v1/users/<username>/tokens"')
        print()
        
        # 生成 Postman 配置
        print("-" * 80)
        print("方法 2: Postman 配置")
        print("-" * 80)
        print()
        print("请求 1: 查找用户")
        print("  Method: GET")
        print("  URL: https://uat-filebay.cheersai.cloud/api/v1/admin/emails/search")
        print("  Query Params:")
        print(f"    q: {email}")
        print("    limit: 10")
        print("  Auth: Basic Auth")
        print("    Username: admin")
        print("    Password: 3DIS9cqlR8@E")
        print()
        
        print("请求 2: 创建 Token")
        print("  Method: POST")
        print("  URL: https://uat-filebay.cheersai.cloud/api/v1/users/<username>/tokens")
        print("  Headers:")
        print("    Content-Type: application/json")
        print("    Sudo: <username>")
        print("  Auth: Basic Auth")
        print("    Username: admin")
        print("    Password: 3DIS9cqlR8@E")
        print("  Body (JSON):")
        print(f"    {json.dumps(token_payload, indent=4)}")
        print()
        
        # 生成保存命令
        print("-" * 80)
        print("步骤 3: 保存 Token 到数据库")
        print("-" * 80)
        print()
        print("获取到 Token 后，执行以下命令保存:")
        print()
        print(f'python save_filebay_token.py "{email}" "<username>" "workspace" "<token>"')
        print()
        print("或使用交互模式:")
        print('python save_filebay_token.py')
        print()
        
        # 生成 Python 代码
        print("-" * 80)
        print("方法 3: 直接使用 Python 代码保存（如果你已经有 Token）")
        print("-" * 80)
        print()
        print("```python")
        print("from flask import Flask")
        print("from extensions.ext_database import db")
        print("from models.account import Account")
        print("from configs import dify_config")
        print()
        print("app = Flask(__name__)")
        print("app.config['SQLALCHEMY_DATABASE_URI'] = dify_config.SQLALCHEMY_DATABASE_URI")
        print("app.config['SQLALCHEMY_ENGINE_OPTIONS'] = dify_config.SQLALCHEMY_ENGINE_OPTIONS")
        print("db.init_app(app)")
        print()
        print("with app.app_context():")
        print(f"    account = db.session.query(Account).filter_by(email='{email}').first()")
        print("    account.custom_config = {")
        print("        'gitea_url': 'https://uat-filebay.cheersai.cloud',")
        print("        'gitea_owner': '<username>',  # 替换为实际用户名")
        print("        'gitea_repo': 'workspace',")
        print("        'gitea_token': '<token>'  # 替换为实际 Token")
        print("    }")
        print("    db.session.commit()")
        print("    print('✓ 配置已保存')")
        print("```")
        print()
        
        print("=" * 80)


def main():
    print()
    print("=" * 80)
    print("FileBay Token 创建命令生成器")
    print("=" * 80)
    print()
    
    # 为两个真实用户生成命令
    users = ["1@qq.com", "103456686@qq.com"]
    
    for email in users:
        generate_commands_for_user(email)
        print()
        print()
    
    print("=" * 80)
    print("总结")
    print("=" * 80)
    print()
    print("1. 使用上面的命令在可以连接 FileBay 的环境中创建 Token")
    print("2. 或者在浏览器中访问 FileBay Swagger API 手动创建")
    print("3. 获取到 Token 后使用 save_filebay_token.py 保存到数据库")
    print("4. 使用 check_accounts_filebay.py 验证配置")
    print()
    print("提示: 如果你可以直接访问 FileBay 数据库，也可以直接查询用户信息")
    print()


if __name__ == "__main__":
    main()
