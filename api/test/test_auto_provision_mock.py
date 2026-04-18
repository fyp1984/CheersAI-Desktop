#!/usr/bin/env python3
"""Test auto-provision with mocked FileBay API."""
import sys
from pathlib import Path
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).parent))

import logging
from flask import Flask
from extensions.ext_database import db
from models.account import Account

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_username_generation():
    """Test username generation from email."""
    from services.filebay_auto_provision_service import FileBayAutoProvisionService
    
    logger.info("\n" + "=" * 80)
    logger.info("Test 1: Username Generation")
    logger.info("=" * 80)
    
    service = FileBayAutoProvisionService()
    
    test_cases = [
        ("test@example.com", "test_example_com_"),
        ("admin@1@qq.com", "admin_1_qq_com_"),
        ("user.name+tag@domain.co.uk", "user_name_tag_domain_co_uk_"),
        ("103456686@qq.com", "103456686_qq_com_"),
    ]
    
    for email, expected_prefix in test_cases:
        username = service.generate_username_from_email(email)
        logger.info(f"  {email:30} → {username}")
        
        # Verify format
        assert len(username) <= 39, f"Username too long: {len(username)}"
        assert username.startswith(expected_prefix), f"Unexpected prefix: {username}"
        assert "_" in username, "Username should contain underscore"
    
    logger.info("✓ All username generation tests passed")
    return True


def test_auto_provision_with_mock():
    """Test auto-provision with mocked FileBay API."""
    from configs import dify_config
    from services.filebay_auto_provision_service import FileBayAutoProvisionService
    
    logger.info("\n" + "=" * 80)
    logger.info("Test 2: Auto Provision with Mock")
    logger.info("=" * 80)
    
    # Create Flask app context
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = dify_config.SQLALCHEMY_DATABASE_URI
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = dify_config.SQLALCHEMY_ENGINE_OPTIONS
    
    db.init_app(app)
    
    with app.app_context():
        test_email = "mock_test@example.com"
        
        # Create test account
        logger.info(f"Creating test account: {test_email}")
        account = db.session.query(Account).filter_by(email=test_email).first()
        
        if not account:
            account = Account(
                name="Mock Test",
                email=test_email,
            )
            db.session.add(account)
            db.session.commit()
        else:
            account.custom_config_dict = {}
            db.session.commit()
        
        logger.info(f"✓ Account ready: {account.id}")
        
        # Mock FileBay API responses
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": 123,
            "username": "mock_user",
            "email": test_email,
        }
        
        mock_token_response = Mock()
        mock_token_response.status_code = 201
        mock_token_response.json.return_value = {
            "sha1": "mock_token_abc123def456ghi789jkl012mno345pqr678stu901vwx234yz",
        }
        
        with patch('requests.request') as mock_request:
            # Setup mock responses
            def mock_request_side_effect(*args, **kwargs):
                url = kwargs.get('url', '')
                method = kwargs.get('method', 'GET')
                
                logger.info(f"  Mock API call: {method} {url}")
                
                if '/tokens' in url:
                    return mock_token_response
                elif method == 'POST':
                    return mock_response
                else:
                    return mock_response
            
            mock_request.side_effect = mock_request_side_effect
            
            # Run auto-provision
            logger.info(f"\nRunning auto-provision for {test_email}...")
            service = FileBayAutoProvisionService()
            config = service.auto_provision(test_email)
            
            logger.info(f"\n✓ Auto-provision completed!")
            logger.info(f"  URL: {config['gitea_url']}")
            logger.info(f"  Owner: {config['gitea_owner']}")
            logger.info(f"  Repo: {config['gitea_repo']}")
            logger.info(f"  Token: {config['gitea_token'][:20]}...")
            
            # Save to database
            logger.info(f"\nSaving config to database...")
            account.custom_config_dict = config
            db.session.commit()
            
            # Verify
            db.session.refresh(account)
            saved_config = account.custom_config_dict
            
            assert saved_config.get('gitea_url') == config['gitea_url']
            assert saved_config.get('gitea_owner') == config['gitea_owner']
            assert saved_config.get('gitea_repo') == config['gitea_repo']
            assert saved_config.get('gitea_token') == config['gitea_token']
            
            logger.info("✓ Config verified in database")
            
    return True


def test_enterprise_api_logic():
    """Test enterprise API logic without actual HTTP calls."""
    from configs import dify_config
    
    logger.info("\n" + "=" * 80)
    logger.info("Test 3: Enterprise API Logic")
    logger.info("=" * 80)
    
    # Create Flask app context
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = dify_config.SQLALCHEMY_DATABASE_URI
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = dify_config.SQLALCHEMY_ENGINE_OPTIONS
    
    db.init_app(app)
    
    with app.app_context():
        # Test case 1: User with existing config
        logger.info("\nCase 1: User with existing config")
        test_email_1 = "existing_config@example.com"
        
        account_1 = db.session.query(Account).filter_by(email=test_email_1).first()
        if not account_1:
            account_1 = Account(name="Existing Config", email=test_email_1)
            db.session.add(account_1)
        
        account_1.custom_config_dict = {
            "gitea_url": "https://test.example.com",
            "gitea_owner": "test_user",
            "gitea_repo": "test_repo",
            "gitea_token": "test_token_123",
        }
        db.session.commit()
        
        # Verify config exists
        db.session.refresh(account_1)
        config = account_1.custom_config_dict
        
        assert config.get('gitea_url') == "https://test.example.com"
        logger.info("  ✓ Existing config retrieved correctly")
        
        # Test case 2: User without config
        logger.info("\nCase 2: User without config")
        test_email_2 = "no_config@example.com"
        
        account_2 = db.session.query(Account).filter_by(email=test_email_2).first()
        if not account_2:
            account_2 = Account(name="No Config", email=test_email_2)
            db.session.add(account_2)
        
        account_2.custom_config_dict = {}
        db.session.commit()
        
        # Verify no config
        db.session.refresh(account_2)
        config = account_2.custom_config_dict
        
        assert not config.get('gitea_url')
        logger.info("  ✓ No config detected correctly")
        
        # Test case 3: Save new config
        logger.info("\nCase 3: Save new config")
        new_config = {
            "gitea_url": "https://new.example.com",
            "gitea_owner": "new_user",
            "gitea_repo": "new_repo",
            "gitea_token": "new_token_456",
        }
        
        account_2.custom_config_dict = new_config
        db.session.commit()
        
        # Verify saved
        db.session.refresh(account_2)
        saved_config = account_2.custom_config_dict
        
        assert saved_config.get('gitea_url') == "https://new.example.com"
        assert saved_config.get('gitea_owner') == "new_user"
        logger.info("  ✓ New config saved correctly")
    
    return True


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("FileBay Auto Provision Mock Test Suite")
    print("=" * 80)
    
    results = []
    
    # Test 1: Username generation
    try:
        result1 = test_username_generation()
        results.append(("Username Generation", result1))
    except Exception as e:
        logger.error(f"Test 1 failed: {e}", exc_info=True)
        results.append(("Username Generation", False))
    
    # Test 2: Auto provision with mock
    try:
        result2 = test_auto_provision_with_mock()
        results.append(("Auto Provision (Mock)", result2))
    except Exception as e:
        logger.error(f"Test 2 failed: {e}", exc_info=True)
        results.append(("Auto Provision (Mock)", False))
    
    # Test 3: Enterprise API logic
    try:
        result3 = test_enterprise_api_logic()
        results.append(("Enterprise API Logic", result3))
    except Exception as e:
        logger.error(f"Test 3 failed: {e}", exc_info=True)
        results.append(("Enterprise API Logic", False))
    
    # Summary
    print("\n" + "=" * 80)
    print("Test Summary")
    print("=" * 80)
    for name, result in results:
        status = "✓ PASSED" if result else "✗ FAILED"
        print(f"{name:30} {status}")
    print("=" * 80)
    
    all_passed = all(result for _, result in results)
    sys.exit(0 if all_passed else 1)
