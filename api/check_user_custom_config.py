"""检查用户的 custom_config"""
import json
from extensions.ext_database import db
from models.account import Account
from app import create_app

app = create_app()

with app.app_context():
    email = '103456686@qq.com'
    account = db.session.query(Account).filter_by(email=email).first()
    
    if account:
        print(f'\n找到用户: {account.email}')
        print(f'用户 ID: {account.id}')
        print(f'用户名: {account.name}')
        
        if account.custom_config:
            try:
                custom_config = json.loads(account.custom_config)
                print(f'\ncustom_config 内容:')
                print(json.dumps(custom_config, indent=2, ensure_ascii=False))
                
                if 'filebay' in custom_config:
                    print(f'\n✅ 找到 FileBay 配置!')
                    filebay_config = custom_config['filebay']
                    print(f'  - gitea_url: {filebay_config.get("gitea_url", "未设置")}')
                    print(f'  - gitea_owner: {filebay_config.get("gitea_owner", "未设置")}')
                    print(f'  - gitea_repo: {filebay_config.get("gitea_repo", "未设置")}')
                    token = filebay_config.get("gitea_token", "")
                    if token:
                        print(f'  - gitea_token: {token[:4]}...{token[-4:]} (长度: {len(token)})')
                    else:
                        print(f'  - gitea_token: 未设置')
                else:
                    print(f'\n❌ custom_config 中没有 filebay 配置')
            except json.JSONDecodeError as e:
                print(f'\n❌ 解析 custom_config 失败: {e}')
                print(f'原始内容: {account.custom_config}')
        else:
            print(f'\n❌ custom_config 为空')
    else:
        print(f'\n❌ 未找到用户: {email}')
