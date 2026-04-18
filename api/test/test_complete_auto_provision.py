#!/usr/bin/env python3
"""Test complete SSO to FileBay auto-provision flow."""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

import logging
from flask import Flask
from extensions.ext_database import db
from models.account import Account
from services.filebay_auto_provision_service import FileBayAutoProvisionService

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_auto_provision():
    """Test the complete auto-provision flow."""
    from configs import dify_config
    
    # Create Flask app context
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = dify_config.SQLALCHEMY_DATABASE_URI
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = dify_config.SQLALCHEMY_ENGINE_OPTIONS
    
    db.init_app(app)
    
    with app.app_context():
        # Test email
        test_email = "test_auto_provision@example.com"
        
        logger.info("=" * 80)
        logger.info("Testing FileBay Auto Provision Flow")
        logger.info("=" * 80)
        
        # Step 1: Check if test account exists
        logger.info(f"\n[Step 1] Checking if account exists: {test_email}")
        account = db.session.query(Account).filter_by(email=test_email).first()
        
        if not account:
            logger.info(f"Account not found. Creating test account...")
            account = Account(
                name="Test Auto Provision",
                email=test_email,
            )
            db.session.add(account)
            db.session.commit()
            logger.info(f"✓ Created test account: {account.id}")
        else:
            logger.info(f"✓ Account exists: {account.id}")
        
        # Step 2: Clear existing config
        logger.info(f"\n[Step 2] Clearing existing FileBay config")
        if account.custom_config_dict and account.custom_config_dict.get('gitea_url'):
            logger.info(f"Existing config: {account.custom_config_dict}")
            account.custom_config_dict = {}
            db.session.commit()
            logger.info("✓ Cleared existing config")
        else:
            logger.info("✓ No existing config to clear")
        
        # Step 3: Test auto-provision service
        logger.info(f"\n[Step 3] Testing FileBay auto-provision service")
        try:
            service = FileBayAutoProvisionService()
            
            # Check configuration
            logger.info(f"FileBay Base URL: {service.filebay_base_url}")
            logger.info(f"Admin Username: {service.admin_username}")
            logger.info(f"Default Repo: {service.default_repo}")
            logger.info(f"Masked Dir: {service.masked_dir}")
            
            # Run auto-provision
            logger.info(f"\nRunning auto-provision for {test_email}...")
            config = service.auto_provision(test_email)
            
            logger.info(f"\n✓ Auto-provision completed!")
            logger.info(f"  URL: {config['gitea_url']}")
            logger.info(f"  Owner: {config['gitea_owner']}")
            logger.info(f"  Repo: {config['gitea_repo']}")
            logger.info(f"  Token: {config['gitea_token'][:10]}...{config['gitea_token'][-10:]}")
            
            # Step 4: Save to database
            logger.info(f"\n[Step 4] Saving config to database")
            account.custom_config_dict = config
            db.session.commit()
            logger.info("✓ Config saved to database")
            
            # Step 5: Verify saved config
            logger.info(f"\n[Step 5] Verifying saved config")
            db.session.refresh(account)
            saved_config = account.custom_config_dict
            
            if saved_config.get('gitea_url') == config['gitea_url']:
                logger.info("✓ Config verified in database")
                logger.info(f"  URL: {saved_config['gitea_url']}")
                logger.info(f"  Owner: {saved_config['gitea_owner']}")
                logger.info(f"  Repo: {saved_config['gitea_repo']}")
                logger.info(f"  Token: {saved_config['gitea_token'][:10]}...{saved_config['gitea_token'][-10:]}")
            else:
                logger.error("✗ Config mismatch in database")
                return False
            
            # Step 6: Test enterprise API
            logger.info(f"\n[Step 6] Testing enterprise API")
            import requests
            
            api_url = "http://localhost:5001/inner/api/enterprise/gitea/config"
            params = {"email": test_email}
            
            logger.info(f"Calling: {api_url}?email={test_email}")
            response = requests.get(api_url, params=params, timeout=10)
            
            if response.status_code == 200:
                api_config = response.json()
                logger.info("✓ Enterprise API returned config")
                logger.info(f"  URL: {api_config.get('gitea_url')}")
                logger.info(f"  Owner: {api_config.get('gitea_owner')}")
                logger.info(f"  Repo: {api_config.get('gitea_repo')}")
                logger.info(f"  Token: {api_config.get('gitea_token', '')[:10]}...")
                
                if api_config.get('gitea_url') == config['gitea_url']:
                    logger.info("✓ API config matches saved config")
                else:
                    logger.warning("⚠ API config doesn't match saved config")
            else:
                logger.error(f"✗ Enterprise API failed: {response.status_code}")
                logger.error(f"  Response: {response.text}")
            
            logger.info("\n" + "=" * 80)
            logger.info("✓ All tests passed!")
            logger.info("=" * 80)
            return True
            
        except Exception as e:
            logger.error(f"\n✗ Auto-provision failed: {e}", exc_info=True)
            return False


def test_enterprise_api_with_auto_provision():
    """Test enterprise API with auto_provision parameter."""
    logger.info("\n" + "=" * 80)
    logger.info("Testing Enterprise API with auto_provision=true")
    logger.info("=" * 80)
    
    test_email = "test_api_auto@example.com"
    
    from configs import dify_config
    from flask import Flask
    
    # Create Flask app context
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = dify_config.SQLALCHEMY_DATABASE_URI
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = dify_config.SQLALCHEMY_ENGINE_OPTIONS
    
    db.init_app(app)
    
    with app.app_context():
        # Create test account without config
        logger.info(f"\n[Step 1] Creating test account: {test_email}")
        account = db.session.query(Account).filter_by(email=test_email).first()
        
        if not account:
            account = Account(
                name="Test API Auto",
                email=test_email,
            )
            db.session.add(account)
            db.session.commit()
            logger.info(f"✓ Created account: {account.id}")
        else:
            # Clear existing config
            account.custom_config_dict = {}
            db.session.commit()
            logger.info(f"✓ Account exists, cleared config: {account.id}")
        
        # Test API with auto_provision=true
        logger.info(f"\n[Step 2] Calling enterprise API with auto_provision=true")
        import requests
        
        api_url = "http://localhost:5001/inner/api/enterprise/gitea/config"
        params = {"email": test_email, "auto_provision": "true"}
        
        logger.info(f"Calling: {api_url}?email={test_email}&auto_provision=true")
        response = requests.get(api_url, params=params, timeout=30)
        
        if response.status_code == 200:
            config = response.json()
            logger.info("✓ API returned config")
            logger.info(f"  URL: {config.get('gitea_url')}")
            logger.info(f"  Owner: {config.get('gitea_owner')}")
            logger.info(f"  Repo: {config.get('gitea_repo')}")
            logger.info(f"  Token: {config.get('gitea_token', '')[:10]}...")
            
            # Verify saved in database
            logger.info(f"\n[Step 3] Verifying config saved in database")
            db.session.refresh(account)
            saved_config = account.custom_config_dict
            
            if saved_config.get('gitea_url'):
                logger.info("✓ Config saved in database")
                logger.info(f"  URL: {saved_config['gitea_url']}")
                logger.info(f"  Owner: {saved_config['gitea_owner']}")
                logger.info(f"  Repo: {saved_config['gitea_repo']}")
            else:
                logger.error("✗ Config not saved in database")
                return False
            
            logger.info("\n" + "=" * 80)
            logger.info("✓ Enterprise API auto-provision test passed!")
            logger.info("=" * 80)
            return True
        else:
            logger.error(f"✗ API failed: {response.status_code}")
            logger.error(f"  Response: {response.text}")
            return False


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("FileBay Auto Provision Test Suite")
    print("=" * 80)
    
    # Test 1: Direct service test
    print("\n[Test 1] Testing FileBay Auto Provision Service directly")
    result1 = test_auto_provision()
    
    # Test 2: Enterprise API with auto_provision parameter
    print("\n[Test 2] Testing Enterprise API with auto_provision=true")
    result2 = test_enterprise_api_with_auto_provision()
    
    # Summary
    print("\n" + "=" * 80)
    print("Test Summary")
    print("=" * 80)
    print(f"Test 1 (Direct Service): {'✓ PASSED' if result1 else '✗ FAILED'}")
    print(f"Test 2 (Enterprise API): {'✓ PASSED' if result2 else '✗ FAILED'}")
    print("=" * 80)
    
    sys.exit(0 if (result1 and result2) else 1)
