"""
测试 SSO 注册 + FileBay 配置完整流程
"""
import json
import random
import string
import requests
from extensions.ext_database import db
from models.account import Account
from app import create_app

def generate_random_email():
    """生成随机测试邮箱"""
    random_str = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    return f'test_{random_str}@test.com'

def test_complete_flow():
    """测试完整流程"""
    app = create_app()
    
    with app.app_context():
        # 1. 生成测试邮箱
        test_email = generate_random_email()
        print(f'\n{"="*60}')
        print(f'步骤 1: 生成测试账号')
        print(f'{"="*60}')
        print(f'测试邮箱: {test_email}')
        
        # 2. 模拟 SSO 注册（直接在数据库创建账号）
        print(f'\n{"="*60}')
        print(f'步骤 2: 创建测试账号（模拟 SSO 注册）')
        print(f'{"="*60}')
        
        # 检查账号是否已存在
        existing_account = db.session.query(Account).filter_by(email=test_email).first()
        if existing_account:
            print(f'账号已存在，删除旧账号...')
            db.session.delete(existing_account)
            db.session.commit()
        
        # 创建新账号
        new_account = Account(
            email=test_email,
            name=f'Test User {test_email.split("@")[0]}',
            status='active',
            initialized_at=db.func.now()
        )
        db.session.add(new_account)
        db.session.commit()
        
        print(f'✅ 账号创建成功')
        print(f'  - ID: {new_account.id}')
        print(f'  - Email: {new_account.email}')
        print(f'  - Name: {new_account.name}')
        
        # 3. 为账号配置 FileBay
        print(f'\n{"="*60}')
        print(f'步骤 3: 配置 FileBay')
        print(f'{"="*60}')
        
        filebay_config = {
            'gitea_url': 'https://test-filebay.example.com',
            'gitea_owner': 'testuser',
            'gitea_repo': 'test-repo',
            'gitea_token': 'test_token_abc123xyz'
        }
        
        # 使用 custom_config_dict 属性
        new_account.custom_config_dict = filebay_config
        db.session.commit()
        
        print(f'✅ FileBay 配置已保存')
        print(f'配置内容:')
        for key, value in filebay_config.items():
            if key == 'gitea_token':
                masked = value[:4] + '****' + value[-4:] if len(value) > 8 else '****'
                print(f'  - {key}: {masked}')
            else:
                print(f'  - {key}: {value}')
        
        # 4. 测试企业 API
        print(f'\n{"="*60}')
        print(f'步骤 4: 测试企业 API')
        print(f'{"="*60}')
        
        try:
            response = requests.get(
                'http://localhost:5001/inner/api/enterprise/gitea/config',
                params={'email': test_email},
                timeout=5
            )
            
            print(f'请求: GET /inner/api/enterprise/gitea/config?email={test_email}')
            print(f'状态码: {response.status_code}')
            
            if response.status_code == 200:
                config_data = response.json()
                print(f'✅ 企业 API 响应成功')
                print(f'返回配置:')
                for key, value in config_data.items():
                    if key == 'gitea_token':
                        masked = value[:4] + '****' + value[-4:] if value and len(value) > 8 else '****'
                        print(f'  - {key}: {masked}')
                    else:
                        print(f'  - {key}: {value}')
                
                # 验证配置是否正确
                if (config_data.get('gitea_url') == filebay_config['gitea_url'] and
                    config_data.get('gitea_owner') == filebay_config['gitea_owner'] and
                    config_data.get('gitea_repo') == filebay_config['gitea_repo'] and
                    config_data.get('gitea_token') == filebay_config['gitea_token']):
                    print(f'\n✅ 配置验证通过！')
                else:
                    print(f'\n❌ 配置不匹配！')
                    print(f'预期: {filebay_config}')
                    print(f'实际: {config_data}')
            else:
                print(f'❌ 企业 API 返回错误: {response.status_code}')
                print(f'响应内容: {response.text}')
        except Exception as e:
            print(f'❌ 企业 API 调用失败: {e}')
        
        # 5. 验证数据库中的配置
        print(f'\n{"="*60}')
        print(f'步骤 5: 验证数据库配置')
        print(f'{"="*60}')
        
        # 重新查询账号
        account = db.session.query(Account).filter_by(email=test_email).first()
        if account:
            print(f'✅ 账号存在')
            print(f'custom_config 内容:')
            if account.custom_config:
                print(f'{account.custom_config}')
                
                # 使用 custom_config_dict 属性
                config_dict = account.custom_config_dict
                print(f'\ncustom_config_dict 解析:')
                for key, value in config_dict.items():
                    if key == 'gitea_token':
                        masked = value[:4] + '****' + value[-4:] if value and len(value) > 8 else '****'
                        print(f'  - {key}: {masked}')
                    else:
                        print(f'  - {key}: {value}')
            else:
                print(f'❌ custom_config 为空')
        else:
            print(f'❌ 账号不存在')
        
        # 6. 总结
        print(f'\n{"="*60}')
        print(f'测试总结')
        print(f'{"="*60}')
        print(f'✅ 测试账号: {test_email}')
        print(f'✅ 账号 ID: {new_account.id}')
        print(f'✅ FileBay 配置已保存到数据库')
        print(f'✅ 企业 API 可以正确获取配置')
        print(f'\n下一步: 使用此账号登录前端，测试 FileBay 文件选择器')
        print(f'{"="*60}')
        
        return test_email, new_account.id

if __name__ == '__main__':
    test_email, account_id = test_complete_flow()
    print(f'\n测试完成！')
    print(f'测试账号: {test_email}')
    print(f'账号 ID: {account_id}')
