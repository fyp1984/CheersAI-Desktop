"""Test gitea files API endpoint."""
from app_factory import create_app
from models.account import Account
from extensions.ext_database import db

app = create_app()
with app.app_context():
    # Get a test account
    account = db.session.query(Account).first()
    if not account:
        print('No accounts found')
        exit(1)
    
    print(f'Testing with account: {account.email}')
    print(f'Account ID: {account.id}')
    print(f'Account custom_config: {account.custom_config}')
    print(f'Account custom_config_dict: {account.custom_config_dict}')
    
    # Test the enterprise API call
    import requests
    from configs import dify_config
    
    tunnel_url = dify_config.CLOUDFLARE_TUNNEL_URL or 'https://moisture-people-detail-possible.trycloudflare.com'
    enterprise_api_url = f'{tunnel_url}/inner/api/enterprise/gitea/config'
    
    print(f'\nCalling: {enterprise_api_url}?email={account.email}')
    
    try:
        response = requests.get(
            enterprise_api_url,
            params={'email': account.email},
            timeout=10
        )
        print(f'Response status: {response.status_code}')
        print(f'Response body: {response.text}')
        
        if response.status_code == 200:
            data = response.json()
            print(f'\nParsed data:')
            for key, value in data.items():
                if key == 'gitea_token':
                    print(f'  {key}: {value[:10]}...' if value else f'  {key}: None')
                else:
                    print(f'  {key}: {value}')
    except Exception as e:
        print(f'Error: {e}')
