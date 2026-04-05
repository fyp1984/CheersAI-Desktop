#!/usr/bin/env python
"""Fix admin account role back to owner"""

from app_factory import create_app
from extensions.ext_database import db
from models.account import Account, TenantAccountJoin

app = create_app()

with app.app_context():
    # List all accounts
    print("=== All Accounts ===")
    accounts = db.session.query(Account).all()
    for account in accounts:
        print(f"ID: {account.id}")
        print(f"Email: {account.email}")
        print(f"Name: {account.name}")
        
        # Get tenant join info
        tenant_joins = db.session.query(TenantAccountJoin).filter_by(
            account_id=account.id
        ).all()
        
        for tj in tenant_joins:
            print(f"  Workspace: {tj.tenant_id}, Role: {tj.role}")
        print()
    
    # Find admin account (you can modify the email if needed)
    admin_email = input("Enter admin email to restore (or press Enter to skip): ").strip()
    
    if admin_email:
        admin_account = db.session.query(Account).filter_by(email=admin_email).first()
        
        if admin_account:
            print(f"\nFound account: {admin_account.name} ({admin_account.email})")
            
            # Update all tenant joins to owner
            tenant_joins = db.session.query(TenantAccountJoin).filter_by(
                account_id=admin_account.id
            ).all()
            
            for tj in tenant_joins:
                old_role = tj.role
                tj.role = 'owner'
                print(f"Updated role from '{old_role}' to 'owner' in workspace {tj.tenant_id}")
            
            db.session.commit()
            print("\n✅ Admin role restored to owner!")
        else:
            print(f"\n❌ Account not found: {admin_email}")
