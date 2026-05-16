"""为用户设置 FileBay 配置"""
import json

from app import create_app
from extensions.ext_database import db
from models.account import Account

app = create_app()

with app.app_context():
    email = '103456686@qq.com'
    account = db.session.query(Account).filter_by(email=email).first()
    
    if account:
        print(f'\n找到用户: {account.email}')
        
        # 准备 FileBay 配置
        filebay_config = {
            'gitea_url': 'https://uat-filebay.cheersai.cloud',
            'gitea_owner': 'junqianxi',
            'gitea_repo': 'CheersAI-Desktop',
            'gitea_token': 'test_token_12345678'  # 这里应该是真实的 token
        }
        
        # 获取现有的 custom_config 或创建新的
        if account.custom_config:
            try:
                custom_config = json.loads(account.custom_config)
            except json.JSONDecodeError:
                custom_config = {}
        else:
            custom_config = {}
        
        # 添加 FileBay 配置
        custom_config['filebay'] = filebay_config
        
        # 保存回数据库
        account.custom_config = json.dumps(custom_config, ensure_ascii=False)
        db.session.commit()
        
        print('\n✅ 成功保存 FileBay 配置到 custom_config!')
        print('\n配置内容:')
        print(json.dumps(filebay_config, indent=2, ensure_ascii=False))
    else:
        print(f'\n❌ 未找到用户: {email}')
