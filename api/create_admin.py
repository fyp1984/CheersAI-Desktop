#!/usr/bin/env python3
"""Create an admin account for CheersAI."""
from app import create_app
from extensions.ext_database import db
from models.account import Account, AccountStatus
from werkzeug.security import generate_password_hash
import uuid

app = create_app()

with app.app_context():
    # Check if admin already exists
    admin = db.session.query(Account).filter_by(email='admin@cheersai.com').first()
    
    if admin:
        print(f"Admin account already exists: {admin.email}")
        print(f"Status: {admin.status}")
        
        # Update to active if pending
        if admin.status == AccountStatus.PENDING:
            admin.status = AccountStatus.ACTIVE
            db.session.commit()
            print("✅ Updated admin status to ACTIVE")
    else:
        # Create new admin account
        admin = Account(
            name='Admin',
            email='admin@cheersai.com',
            password=generate_password_hash('admin123'),
            password_salt='',
            status=AccountStatus.ACTIVE,
        )
        
        db.session.add(admin)
        db.session.commit()
        
        print("✅ Admin account created successfully!")
        print(f"Email: admin@cheersai.com")
        print(f"Password: admin123")
        print(f"Status: {admin.status}")
