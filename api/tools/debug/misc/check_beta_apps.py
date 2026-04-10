#!/usr/bin/env python3
"""Check beta applications in database."""

import sys
from pathlib import Path

API_ROOT = Path(__file__).resolve().parents[3]
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from app import create_app
from extensions.ext_database import db
from models.beta_application import BetaApplication

app = create_app()

with app.app_context():
    apps = db.session.query(BetaApplication).all()
    print(f"\n✅ Total beta applications: {len(apps)}\n")
    
    for app_record in apps:
        print(f"📧 Email: {app_record.email}")
        print(f"👤 Name: {app_record.name}")
        print(f"🏢 Company: {app_record.company}")
        print(f"💡 Use Case: {app_record.use_case}")
        print(f"📍 Status: {app_record.status}")
        print(f"🌐 IP: {app_record.ip_address}")
        print(f"📅 Created: {app_record.created_at}")
        print("-" * 60)
