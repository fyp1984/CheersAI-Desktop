"""
为 admin@cheersai.cloud 创建 beta_application 记录的脚本
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from extensions.ext_database import db
from models.beta_application import BetaApplication
from app import create_flask_app

def add_admin_beta_application():
    """为 admin 用户添加 beta application 记录"""
    app = create_flask_app()
    
    with app.app_context():
        # 检查是否已存在
        existing = BetaApplication.query.filter_by(email='admin@cheersai.cloud').first()
        
        if existing:
            print(f'✓ Beta application already exists for admin@cheersai.cloud')
            print(f'  Status: {existing.status}')
            print(f'  FileBay Username: {existing.filebay_username}')
            print(f'  FileBay Repo: {existing.filebay_repo}')
            
            # 更新状态为 success
            if existing.status != 'success':
                existing.status = 'success'
                db.session.commit()
                print(f'✓ Updated status to success')
            
            return
        
        # 创建新记录
        beta_app = BetaApplication(
            email='admin@cheersai.cloud',
            name='Admin User',
            company='CheersAI',
            use_case='System Administration',
            status='success',
            filebay_username='admin_cheersai_cloud_admin',
            filebay_repo='workspace',
        )
        
        db.session.add(beta_app)
        db.session.commit()
        
        print(f'✓ Created beta application for admin@cheersai.cloud')
        print(f'  FileBay Username: {beta_app.filebay_username}')
        print(f'  FileBay Repo: {beta_app.filebay_repo}')
        print(f'  Status: {beta_app.status}')

if __name__ == '__main__':
    add_admin_beta_application()
