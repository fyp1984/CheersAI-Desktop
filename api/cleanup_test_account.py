"""
删除测试账号并显示真实账号信息
"""
from extensions.ext_database import db
from models.account import Account
from app import create_app

app = create_app()

with app.app_context():
    # 删除测试账号
    test_account = db.session.query(Account).filter_by(email='test_eacm9wzq@test.com').first()
    if test_account:
        print(f'删除测试账号: {test_account.email}')
        db.session.delete(test_account)
        db.session.commit()
        print('✅ 测试账号已删除\n')
    else:
        print('测试账号不存在\n')
    
    # 显示真实账号
    print('='*80)
    print('真实账号列表')
    print('='*80)
    
    accounts = db.session.query(Account).order_by(Account.created_at).all()
    
    for idx, account in enumerate(accounts, 1):
        print(f'\n【账号 {idx}】')
        print(f'  邮箱: {account.email}')
        print(f'  用户名: {account.name}')
        print(f'  账号 ID: {account.id}')
        print(f'  状态: {account.status}')
        print(f'  是否设置密码: {"是" if account.password else "否"}')
        print(f'  创建时间: {account.created_at}')
        print(f'  最后登录: {account.last_login_at or "从未登录"}')
        
        if account.custom_config_dict:
            config = account.custom_config_dict
            if config.get('gitea_url'):
                print(f'\n  ✅ Gitea 配置:')
                print(f'    - URL: {config.get("gitea_url")}')
                print(f'    - Owner: {config.get("gitea_owner")}')
                print(f'    - Repo: {config.get("gitea_repo")}')
                token = config.get('gitea_token', '')
                if token:
                    masked = token[:8] + '...' + token[-8:] if len(token) > 16 else '****'
                    print(f'    - Token: {masked}')
                else:
                    print(f'    - Token: 未设置')
            else:
                print(f'\n  ❌ 无 Gitea 配置')
        else:
            print(f'\n  ❌ custom_config 为空')
        
        print('-'*80)
