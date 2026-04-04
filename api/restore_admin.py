#!/usr/bin/env python
"""Restore admin account to owner role"""

from extensions.ext_database import db
from models.account import Account, TenantAccountJoin
from app_factory import create_app

app = create_app()

with app.app_context():
    admin_email = "admin@example.com"
    
    admin_account = db.session.query(Account).filter_by(email=admin_email).first()
    
    if admin_account:
        print(f"Found account: {admin_account.name} ({admin_account.email})")
        print(f"Account ID: {admin_account.id}")
        
        # Get all tenant joins
        tenant_joins = db.session.query(TenantAccountJoin).filter_by(
            account_id=admin_account.id
        ).all()
        
        print(f"\nWorkspaces: {len(tenant_joins)}")
        
        for tj in tenant_joins:
            print(f"\nWorkspace ID: {tj.tenant_id}")
            print(f"Current Role: {tj.role}")
            
            if tj.role != 'owner':
                tj.role = 'owner'
                print(f"✅ Updated to owner")
            else:
                print(f"✅ Already owner")
        
        db.session.commit()
        print("\n✅ Admin account verified/restored!")
    else:
        print(f"❌ Account not found: {admin_email}")
