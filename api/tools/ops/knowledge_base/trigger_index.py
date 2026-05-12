import sys
from pathlib import Path

API_ROOT = Path(__file__).resolve().parents[3]
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from extensions.ext_database import db
from models.account import Tenant, TenantAccountJoin
from tasks.document_indexing_task import normal_document_indexing_task

# 获取tenant_id
tenant = db.session.query(Tenant).join(TenantAccountJoin).first()
if tenant:
    tenant_id = str(tenant.id)
    dataset_id = '36adfd03-f829-4eb6-a3b5-041064ef714a'
    document_ids = ['351646be-af4b-4e45-b916-678002cb3f3b']
    
    print(f'Triggering indexing task for tenant: {tenant_id}, dataset: {dataset_id}, documents: {document_ids}')
    normal_document_indexing_task.delay(tenant_id, dataset_id, document_ids)
    print('Task triggered successfully')
else:
    print('No tenant found')
