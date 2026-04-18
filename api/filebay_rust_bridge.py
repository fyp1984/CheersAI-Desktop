#!/usr/bin/env python3
"""使用 Rust 工具作为桥接来访问 FileBay API"""
import json
import subprocess
from pathlib import Path
from typing import Optional

# Rust 工具路径
RUST_TOOL_PATH = Path(__file__).parent.parent / "cheersai-desktop" / "src-tauri" / "target" / "release" / "filebay_token_tool.exe"


def search_user(email: str) -> Optional[dict]:
    """搜索用户"""
    try:
        result = subprocess.run(
            [str(RUST_TOOL_PATH), "search_user", email],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            users = json.loads(result.stdout)
            if isinstance(users, list) and users:
                return users[0]
        else:
            print(f"搜索用户失败: {result.stderr}")
    except Exception as e:
        print(f"调用 Rust 工具失败: {e}")
    
    return None


def create_token(username: str, token_name: Optional[str] = None) -> Optional[str]:
    """创建 Token"""
    try:
        args = [str(RUST_TOOL_PATH), "create_token", username]
        if token_name:
            args.append(token_name)
        
        result = subprocess.run(
            args,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            token_data = json.loads(result.stdout)
            return token_data.get('sha1') or token_data.get('token')
        else:
            print(f"创建 Token 失败: {result.stderr}")
    except Exception as e:
        print(f"调用 Rust 工具失败: {e}")
    
    return None


def auto_provision_user(email: str) -> Optional[dict]:
    """自动配置用户"""
    print(f"开始为用户配置 FileBay: {email}")
    
    # 1. 搜索用户
    print(f"  1. 搜索用户...")
    user = search_user(email)
    
    if not user:
        print(f"  ✗ 未找到用户")
        return None
    
    username = user.get('username') or user.get('login')
    user_id = user.get('id')
    
    print(f"  ✓ 找到用户: {username} (ID: {user_id})")
    
    # 2. 创建 Token
    print(f"  2. 创建 Token...")
    token_name = f"desktop-auto-{username}"
    token = create_token(username, token_name)
    
    if not token:
        print(f"  ✗ Token 创建失败")
        return None
    
    print(f"  ✓ Token 创建成功: {token[:20]}...{token[-10:]}")
    
    # 3. 返回配置
    config = {
        'gitea_url': 'https://uat-filebay.cheersai.cloud',
        'gitea_owner': username,
        'gitea_repo': 'workspace',
        'gitea_token': token
    }
    
    print(f"  ✓ 配置完成")
    return config


def save_config_to_database(email: str, config: dict) -> bool:
    """保存配置到数据库"""
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
            
            account.custom_config = config
            db.session.commit()
            
            print(f"✓ 配置已保存到数据库")
            return True
    except Exception as e:
        print(f"✗ 保存失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("用法:")
        print("  python filebay_rust_bridge.py <email>")
        print()
        print("示例:")
        print("  python filebay_rust_bridge.py 1@qq.com")
        sys.exit(1)
    
    email = sys.argv[1]
    
    print("=" * 80)
    print(f"使用 Rust 桥接自动配置 FileBay")
    print("=" * 80)
    print()
    
    # 检查 Rust 工具是否存在
    if not RUST_TOOL_PATH.exists():
        print(f"✗ Rust 工具不存在: {RUST_TOOL_PATH}")
        print()
        print("请先编译 Rust 工具:")
        print(f"  cd {RUST_TOOL_PATH.parent}")
        print(f"  rustc --edition 2021 filebay_token_tool.rs -o filebay_token_tool.exe")
        sys.exit(1)
    
    # 自动配置
    config = auto_provision_user(email)
    
    if config:
        print()
        print("=" * 80)
        print("配置信息")
        print("=" * 80)
        print(f"URL:   {config['gitea_url']}")
        print(f"Owner: {config['gitea_owner']}")
        print(f"Repo:  {config['gitea_repo']}")
        print(f"Token: {config['gitea_token'][:20]}...{config['gitea_token'][-10:]}")
        print()
        
        # 保存到数据库
        if save_config_to_database(email, config):
            print()
            print("=" * 80)
            print("✓ 配置完成!")
            print("=" * 80)
        else:
            print()
            print("=" * 80)
            print("⚠ 配置获取成功，但保存到数据库失败")
            print("=" * 80)
            print()
            print("手动保存命令:")
            print(f'python save_filebay_token.py "{email}" "{config["gitea_owner"]}" "{config["gitea_repo"]}" "{config["gitea_token"]}"')
    else:
        print()
        print("=" * 80)
        print("✗ 配置失败")
        print("=" * 80)
        sys.exit(1)
