#!/usr/bin/env python3
"""Test SSO login flow with FileBay auto-provision"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_sso_login():
    """Test the complete SSO login flow"""
    from flask import Flask
    from extensions.ext_database import db
    from models.account import Account
    
    # Create Flask app
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:difyai123456@127.0.0.1:5432/dify'
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_size': 30,
        'max_overflow': 10,
        'pool_recycle': 3600,
        'pool_pre_ping': True,
    }
    db.init_app(app)
    
    with app.app_context():
        # Test email
        test_email = "test_sso_user@example.com"
        
        print(f"\n{'='*60}")
        print(f"Testing SSO Login Flow")
        print(f"{'='*60}\n")
        
        # Step 1: Check if account exists
        print(f"[Step 1] Checking if account exists: {test_email}")
        account = db.session.query(Account).filter_by(email=test_email).first()
        
        if account:
            print(f"  ✓ Account exists: {account.id}")
            print(f"  Name: {account.name}")
            print(f"  Status: {account.status}")
            
            # Check custom_config_dict
            print(f"\n[Step 2] Checking custom_config_dict property")
            try:
                config = account.custom_config_dict
                print(f"  ✓ custom_config_dict accessible")
                print(f"  Type: {type(config)}")
                print(f"  Content: {config}")
                
                if config.get('gitea_url'):
                    print(f"\n  ✓ FileBay config exists:")
                    print(f"    URL:   {config.get('gitea_url')}")
                    print(f"    Owner: {config.get('gitea_owner')}")
                    print(f"    Repo:  {config.get('gitea_repo')}")
                    print(f"    Token: {'***' if config.get('gitea_token') else 'None'}")
                else:
                    print(f"\n  ℹ No FileBay config yet")
                    
            except Exception as e:
                print(f"  ✗ Error accessing custom_config_dict: {e}")
                import traceback
                traceback.print_exc()
                return False
                
        else:
            print(f"  ℹ Account does not exist (will be created on first SSO login)")
        
        # Step 3: Test resolve_filebay_config
        print(f"\n[Step 3] Testing resolve_filebay_config")
        try:
            from services.filebay_config_service import resolve_filebay_config
            
            print(f"  Calling resolve_filebay_config with auto_provision=True...")
            config = resolve_filebay_config(
                test_email,
                auto_provision=True,
                mask_token=True
            )
            
            print(f"  ✓ Config resolved:")
            print(f"    URL:   {config.gitea_url}")
            print(f"    Owner: {config.gitea_owner}")
            print(f"    Repo:  {config.gitea_repo}")
            print(f"    Token: {config.gitea_token}")
            
        except Exception as e:
            print(f"  ✗ Error resolving config: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        print(f"\n{'='*60}")
        print(f"✓ All tests passed!")
        print(f"{'='*60}\n")
        return True

if __name__ == "__main__":
    success = test_sso_login()
    sys.exit(0 if success else 1)
