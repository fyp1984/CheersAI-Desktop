"""Test the gitea files endpoint with proper authentication."""
import sys
from app_factory import create_app
from models.account import Account
from extensions.ext_database import db
from flask import g
from flask_login import login_user

app = create_app()

with app.test_request_context():
    # Get the first account
    account = db.session.query(Account).filter_by(email='admin@cheersai.cloud').first()
    if not account:
        print('Account admin@cheersai.cloud not found, trying first account...')
        account = db.session.query(Account).first()
    
    if not account:
        print('No accounts found!')
        sys.exit(1)
    
    print(f'Testing with account: {account.email}')
    print(f'Account ID: {account.id}')
    
    # Simulate login
    login_user(account)
    
    # Import the endpoint
    from controllers.console.gitea_api.gitea_files import GiteaFileListApi
    
    # Create an instance and call the get method
    api = GiteaFileListApi()
    
    print('\nCalling GiteaFileListApi.get()...')
    try:
        result = api.get()
        print(f'Success! Result: {result}')
    except Exception as e:
        print(f'Error: {e}')
        import traceback
        traceback.print_exc()
