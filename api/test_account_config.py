"""Test if Account model has custom_config field."""
from extensions.ext_database import db
from models.account import Account
from app_factory import create_app

app = create_app()
with app.app_context():
    print('Testing Account model...')
    acc = db.session.query(Account).first()
    if acc:
        print(f'Account ID: {acc.id}')
        print(f'Account has custom_config attr: {hasattr(acc, "custom_config")}')
        print(f'Account has custom_config_dict attr: {hasattr(acc, "custom_config_dict")}')
        try:
            config = acc.custom_config
            print(f'custom_config value: {config}')
        except Exception as e:
            print(f'Error accessing custom_config: {e}')
    else:
        print('No accounts found')
