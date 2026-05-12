"""
查询所有账号及其 Gitea 配置信息
"""
import json

from app import create_app
from extensions.ext_database import db
from models.account import Account

app = create_app()

with app.app_context():
    # 查询所有账号
    accounts = db.session.query(Account).order_by(Account.created_at.desc()).all()
    
    print(f'\n{"=" * 80}')
    print(f'系统账号列表（共 {len(accounts)} 个账号）')
    print(f'{"=" * 80}\n')
    
    for idx, account in enumerate(accounts, 1):
        print(f'【账号 {idx}】')
        print(f'  邮箱: {account.email}')
        print(f'  用户名: {account.name}')
        print(f'  账号 ID: {account.id}')
        print(f'  状态: {account.status}')
        print(f'  是否设置密码: {"是" if account.password else "否"}')
        
        if account.password:
            print(f'  密码哈希: {account.password[:20]}...')
        
        print(f'  创建时间: {account.created_at}')
        print(f'  最后登录: {account.last_login_at or "从未登录"}')
        
        # 检查 Gitea 配置
        if account.custom_config_dict:
            config = account.custom_config_dict
            
            # 检查是否有 Gitea 配置
            if config.get('gitea_url'):
                print('\n  ✅ Gitea 配置:')
                print(f'    - URL: {config.get("gitea_url")}')
                print(f'    - Owner: {config.get("gitea_owner")}')
                print(f'    - Repo: {config.get("gitea_repo")}')
                
                token = config.get('gitea_token', '')
                if token:
                    masked = token[:4] + '****' + token[-4:] if len(token) > 8 else '****'
                    print(f'    - Token: {masked} (长度: {len(token)})')
                else:
                    print('    - Token: 未设置')
            else:
                print('\n  ❌ 无 Gitea 配置')
                if config:
                    print(f'  custom_config 内容: {json.dumps(config, ensure_ascii=False)}')
        else:
            print('\n  ❌ custom_config 为空')
        
        print(f'\n{"-" * 80}\n')
    
    # 统计信息
    print(f'\n{"=" * 80}')
    print('统计信息')
    print(f'{"=" * 80}')
    
    total = len(accounts)
    with_password = sum(1 for a in accounts if a.password)
    with_gitea = sum(1 for a in accounts if a.custom_config_dict and a.custom_config_dict.get('gitea_url'))
    active = sum(1 for a in accounts if a.status == 'active')
    
    print(f'  总账号数: {total}')
    print(f'  已设置密码: {with_password}')
    print(f'  已配置 Gitea: {with_gitea}')
    print(f'  活跃账号: {active}')
    print(f'{"=" * 80}\n')
