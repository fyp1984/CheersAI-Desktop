#!/usr/bin/env python3
"""测试集成的自动配置功能"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

from flask import Flask
from extensions.ext_database import db
from services.filebay_config_service import resolve_filebay_config


def print_separator(char="=", length=80):
    """打印分隔线"""
    print(char * length)


def test_auto_provision():
    """测试自动配置"""
    from configs import dify_config
    
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = dify_config.SQLALCHEMY_DATABASE_URI
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = dify_config.SQLALCHEMY_ENGINE_OPTIONS
    
    db.init_app(app)
    
    with app.app_context():
        print_separator()
        print("测试 FileBay 自动配置（集成版）")
        print_separator()
        
        # 测试用户
        test_users = [
            "1@qq.com",
            "103456686@qq.com",
        ]
        
        for email in test_users:
            print(f"\n测试用户: {email}")
            print("-" * 80)
            
            try:
                # 尝试自动配置
                config = resolve_filebay_config(
                    email,
                    allow_global_fallback=False,
                    auto_provision=True,  # 启用自动配置
                    mask_token=False
                )
                
                print(f"✓ 配置成功")
                print(f"  URL:   {config.gitea_url}")
                print(f"  Owner: {config.gitea_owner}")
                print(f"  Repo:  {config.gitea_repo}")
                print(f"  Token: {config.gitea_token[:20]}...{config.gitea_token[-10:]}")
                
                # 验证配置
                print(f"\n验证配置:")
                
                # 1. 检查数据库
                from models.account import Account
                account = db.session.query(Account).filter_by(email=email).first()
                if account and account.custom_config_dict:
                    print(f"  ✓ 配置已保存到数据库")
                    print(f"    URL:   {account.custom_config_dict.get('gitea_url')}")
                    print(f"    Owner: {account.custom_config_dict.get('gitea_owner')}")
                    print(f"    Repo:  {account.custom_config_dict.get('gitea_repo')}")
                else:
                    print(f"  ✗ 配置未保存到数据库")
                
                # 2. 测试 Token（如果 SSL 可用）
                try:
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
                        print(f"  ✓ Token 验证成功")
                        print(f"    用户名: {user_info.get('login')}")
                        print(f"    用户ID: {user_info.get('id')}")
                    else:
                        print(f"  ✗ Token 验证失败: {response.status_code}")
                except Exception as e:
                    print(f"  ⚠ 无法验证 Token (SSL 问题): {str(e)[:100]}")
                
            except Exception as e:
                print(f"✗ 配置失败: {e}")
                import traceback
                traceback.print_exc()
        
        print_separator()


def test_workflow():
    """测试完整工作流程"""
    print_separator()
    print("FileBay 自动配置工作流程")
    print_separator()
    print()
    
    print("配置解析策略（4-tier）:")
    print("  1. Account.custom_config_dict（已保存的配置）")
    print("  2. 查找 FileBay 已有用户 + 动态生成 Token")
    print("  3. 自动创建新用户、仓库和 Token ⭐ 新增")
    print("  4. 全局环境变量（fallback）")
    print()
    
    print("自动配置流程:")
    print("  1. 从邮箱生成唯一用户名")
    print("  2. 检查用户是否存在，不存在则创建")
    print("  3. 检查仓库是否存在，不存在则创建")
    print("  4. 为用户生成访问 Token")
    print("  5. 初始化 masked 目录")
    print("  6. 保存配置到数据库")
    print()
    
    print("优点:")
    print("  ✓ 完全自动化，无需手动操作")
    print("  ✓ 每个用户独立的 FileBay 账号和仓库")
    print("  ✓ 配置持久化到数据库")
    print("  ✓ 支持 SSL workaround")
    print()
    
    print("注意事项:")
    print("  ⚠ 需要 FileBay 管理员权限")
    print("  ⚠ 如果 SSL 连接失败，自动配置会失败")
    print("  ⚠ 建议先解决 SSL 问题再使用自动配置")
    print()
    
    print_separator()


if __name__ == "__main__":
    # 显示工作流程
    test_workflow()
    
    # 测试自动配置
    print()
    print("开始测试...")
    print()
    test_auto_provision()
