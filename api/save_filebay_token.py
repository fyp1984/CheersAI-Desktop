#!/usr/bin/env python3
"""手动保存 FileBay Token 到数据库"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from flask import Flask

from configs import dify_config
from extensions.ext_database import db
from models.account import Account


def save_token(email: str, username: str, repo: str, token: str):
    """保存 FileBay Token 到账号配置"""
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = dify_config.SQLALCHEMY_DATABASE_URI
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = dify_config.SQLALCHEMY_ENGINE_OPTIONS
    
    db.init_app(app)
    
    with app.app_context():
        account = db.session.query(Account).filter_by(email=email).first()
        
        if not account:
            print(f"✗ 未找到账号: {email}")
            return False
        
        print(f"找到账号: {account.email} ({account.name})")
        print(f"账号 ID: {account.id}")
        
        # 保存配置
        account.custom_config = {
            'gitea_url': 'https://uat-filebay.cheersai.cloud',
            'gitea_owner': username,
            'gitea_repo': repo,
            'gitea_token': token
        }
        
        db.session.commit()
        
        print("\n✓ FileBay 配置已保存:")
        print("  URL:   https://uat-filebay.cheersai.cloud")
        print(f"  Owner: {username}")
        print(f"  Repo:  {repo}")
        print(f"  Token: {token[:10]}...{token[-10:]}")
        
        return True


def main():
    print("=" * 80)
    print("FileBay Token 手动保存工具")
    print("=" * 80)
    print()
    
    if len(sys.argv) == 5:
        # 命令行参数模式
        email = sys.argv[1]
        username = sys.argv[2]
        repo = sys.argv[3]
        token = sys.argv[4]
    else:
        # 交互模式
        print("请输入以下信息:")
        print()
        
        email = input("账号邮箱 (例如: 1@qq.com): ").strip()
        if not email:
            print("✗ 邮箱不能为空")
            return
        
        username = input("FileBay 用户名 (例如: user1): ").strip()
        if not username:
            print("✗ 用户名不能为空")
            return
        
        repo = input("FileBay 仓库名 (默认: workspace): ").strip() or "workspace"
        
        token = input("FileBay Token: ").strip()
        if not token:
            print("✗ Token 不能为空")
            return
        
        print()
        print("-" * 80)
        print("确认信息:")
        print(f"  邮箱:   {email}")
        print(f"  用户名: {username}")
        print(f"  仓库:   {repo}")
        print(f"  Token:  {token[:10]}...{token[-10:] if len(token) > 20 else ''}")
        print("-" * 80)
        
        confirm = input("\n确认保存? (y/n): ").strip().lower()
        if confirm != 'y':
            print("✗ 已取消")
            return
    
    print()
    success = save_token(email, username, repo, token)
    
    if success:
        print()
        print("=" * 80)
        print("下一步:")
        print("=" * 80)
        print("1. 验证配置:")
        print(f"   python check_accounts_filebay.py check {email}")
        print()
        print("2. 测试 Enterprise API:")
        print(f'   curl "http://localhost:5001/inner/api/enterprise/gitea/config?email={email}"')
        print()


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] in ['-h', '--help']:
        print("用法:")
        print("  交互模式:")
        print("    python save_filebay_token.py")
        print()
        print("  命令行模式:")
        print("    python save_filebay_token.py <email> <username> <repo> <token>")
        print()
        print("示例:")
        print('    python save_filebay_token.py 1@qq.com user1 workspace "abc123..."')
    else:
        main()
