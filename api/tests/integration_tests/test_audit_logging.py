"""
审计日志集成测试
测试各操作是否能正确触发审计日志记录

运行方式: uv run pytest tests/integration_tests/test_audit_logging.py -v
"""

import pytest
import secrets
from datetime import datetime, timedelta
from flask.testing import FlaskClient
from sqlalchemy import text

from extensions.ext_database import db
from models import Account, Tenant, TenantAccountJoin
from models.model import OperationLog


class TestAuditLogging:
    """测试审计日志记录功能"""

    @pytest.fixture
    def test_tenant_account(self, flask_app):
        """创建测试租户和账户"""
        with flask_app.app_context():
            # 创建租户
            tenant = Tenant(
                id=secrets.token_hex(16),
                name="Test Tenant",
                status="normal",
            )
            db.session.add(tenant)

            # 创建账户
            account = Account(
                id=secrets.token_hex(16),
                email=f"audit_test_{secrets.token_hex(4)}@example.com",
                name="Audit Test User",
                password="",
                is_email_verified=True,
            )
            db.session.add(account)

            # 关联租户和账户
            join = TenantAccountJoin(
                tenant_id=tenant.id,
                account_id=account.id,
                role="owner",
                status="active",
            )
            db.session.add(join)
            db.session.commit()

            yield {"tenant": tenant, "account": account}

            # 清理
            db.session.query(OperationLog).filter(OperationLog.tenant_id == tenant.id).delete()
            db.session.query(TenantAccountJoin).filter(TenantAccountJoin.tenant_id == tenant.id).delete()
            db.session.query(Account).filter(Account.id == account.id).delete()
            db.session.query(Tenant).filter(Tenant.id == tenant.id).delete()
            db.session.commit()

    def test_login_audit_log(self, flask_app, test_tenant_account):
        """测试登录审计日志"""
        from services.audit_service import log_operation

        with flask_app.test_request_context():
            result = log_operation(
                action="login",
                operation_type="chat",
                content={"login_method": "password"},
            )
            assert result is not None, "登录审计日志应该成功创建"

        # 验证数据库记录
        with flask_app.app_context():
            log = (
                db.session.query(OperationLog)
                .filter(
                    OperationLog.action == "login",
                    OperationLog.tenant_id == test_tenant_account["tenant"].id,
                )
                .first()
            )
            assert log is not None, "登录日志应该存在于数据库"
            assert log.operation_type == "chat"
            print(f"✓ login 审计日志测试通过: {log.id}")

    def test_logout_audit_log(self, flask_app, test_tenant_account):
        """测试登出审计日志"""
        from services.audit_service import log_operation

        with flask_app.test_request_context():
            result = log_operation(
                action="logout",
                operation_type="chat",
                content={"reason": "user_initiated"},
            )
            assert result is not None, "登出审计日志应该成功创建"

        with flask_app.app_context():
            log = (
                db.session.query(OperationLog)
                .filter(
                    OperationLog.action == "logout",
                    OperationLog.tenant_id == test_tenant_account["tenant"].id,
                )
                .first()
            )
            assert log is not None, "登出日志应该存在于数据库"
            print(f"✓ logout 审计日志测试通过: {log.id}")

    def test_search_audit_log(self, flask_app, test_tenant_account):
        """测试搜索审计日志"""
        from services.audit_service import log_operation

        with flask_app.test_request_context():
            result = log_operation(
                action="search",
                operation_type="search",
                content={"query": "test query", "result_count": 5, "datasets": ["ds-1", "ds-2"]},
                request_content="test query",
            )
            assert result is not None, "搜索审计日志应该成功创建"

        with flask_app.app_context():
            log = (
                db.session.query(OperationLog)
                .filter(
                    OperationLog.action == "search",
                    OperationLog.tenant_id == test_tenant_account["tenant"].id,
                )
                .first()
            )
            assert log is not None, "搜索日志应该存在于数据库"
            assert log.operation_type == "search"
            print(f"✓ search 审计日志测试通过: {log.id}")

    def test_workflow_audit_log(self, flask_app, test_tenant_account):
        """测试工作流审计日志"""
        from services.audit_service import log_operation

        with flask_app.test_request_context():
            result = log_operation(
                action="workflow",
                operation_type="workflow",
                content={"app_id": "app-123", "mode": "advanced_chat"},
            )
            assert result is not None, "工作流审计日志应该成功创建"

        with flask_app.app_context():
            log = (
                db.session.query(OperationLog)
                .filter(
                    OperationLog.action == "workflow",
                    OperationLog.tenant_id == test_tenant_account["tenant"].id,
                )
                .first()
            )
            assert log is not None, "工作流日志应该存在于数据库"
            assert log.operation_type == "workflow"
            print(f"✓ workflow 审计日志测试通过: {log.id}")

    def test_file_mask_audit_log(self, flask_app, test_tenant_account):
        """测试文件脱敏审计日志"""
        from services.audit_service import log_operation

        with flask_app.test_request_context():
            result = log_operation(
                action="file_mask",
                content={"file_name": "test.txt", "size": 1024},
                resource_type="file",
            )
            assert result is not None, "文件脱敏审计日志应该成功创建"

        with flask_app.app_context():
            log = (
                db.session.query(OperationLog)
                .filter(
                    OperationLog.action == "file_mask",
                    OperationLog.tenant_id == test_tenant_account["tenant"].id,
                )
                .first()
            )
            assert log is not None, "文件脱敏日志应该存在于数据库"
            print(f"✓ file_mask 审计日志测试通过: {log.id}")

    def test_file_upload_audit_log(self, flask_app, test_tenant_account):
        """测试文件上传审计日志"""
        from services.audit_service import log_operation

        with flask_app.test_request_context():
            result = log_operation(
                action="file_upload",
                content={"file_name": "document.pdf", "size": 2048},
                resource_type="file",
            )
            assert result is not None, "文件上传审计日志应该成功创建"

        with flask_app.app_context():
            log = (
                db.session.query(OperationLog)
                .filter(
                    OperationLog.action == "file_upload",
                    OperationLog.tenant_id == test_tenant_account["tenant"].id,
                )
                .first()
            )
            assert log is not None, "文件上传日志应该存在于数据库"
            print(f"✓ file_upload 审计日志测试通过: {log.id}")

    def test_knowledge_sync_audit_log(self, flask_app, test_tenant_account):
        """测试知识同步审计日志"""
        from services.audit_service import log_operation

        with flask_app.test_context():
            result = log_operation(
                action="knowledge_sync",
                content={"dataset_id": "ds-1", "document_count": 10},
                resource_type="dataset",
            )
            assert result is not None, "知识同步审计日志应该成功创建"

        with flask_app.app_context():
            log = (
                db.session.query(OperationLog)
                .filter(
                    OperationLog.action == "knowledge_sync",
                    OperationLog.tenant_id == test_tenant_account["tenant"].id,
                )
                .first()
            )
            assert log is not None, "知识同步日志应该存在于数据库"
            print(f"✓ knowledge_sync 审计日志测试通过: {log.id}")

    def test_member_invite_audit_log(self, flask_app, test_tenant_account):
        """测试成员邀请审计日志"""
        from services.audit_service import log_operation

        with flask_app.test_request_context():
            result = log_operation(
                action="member_invite",
                content={"invited_email": "newuser@example.com", "role": "admin"},
                resource_type="member",
            )
            assert result is not None, "成员邀请审计日志应该成功创建"

        with flask_app.app_context():
            log = (
                db.session.query(OperationLog)
                .filter(
                    OperationLog.action == "member_invite",
                    OperationLog.tenant_id == test_tenant_account["tenant"].id,
                )
                .first()
            )
            assert log is not None, "成员邀请日志应该存在于数据库"
            print(f"✓ member_invite 审计日志测试通过: {log.id}")

    def test_chat_completion_audit_log(self, flask_app, test_tenant_account):
        """测试对话审计日志"""
        from services.audit_service import log_operation

        with flask_app.test_request_context():
            result = log_operation(
                action="chat_completion",
                operation_type="chat",
                content={"app_id": "app-1", "query": "hello"},
                request_content="hello",
                response_content="hi there",
            )
            assert result is not None, "对话审计日志应该成功创建"

        with flask_app.app_context():
            log = (
                db.session.query(OperationLog)
                .filter(
                    OperationLog.action == "chat_completion",
                    OperationLog.tenant_id == test_tenant_account["tenant"].id,
                )
                .first()
            )
            assert log is not None, "对话日志应该存在于数据库"
            assert log.operation_type == "chat"
            print(f"✓ chat_completion 审计日志测试通过: {log.id}")

    def test_document_delete_audit_log(self, flask_app, test_tenant_account):
        """测试文档删除审计日志"""
        from services.audit_service import log_operation

        with flask_app.test_request_context():
            result = log_operation(
                action="document_delete",
                content={"document_id": "doc-1", "reason": "user_request"},
                resource_type="document",
            )
            assert result is not None, "文档删除审计日志应该成功创建"

        with flask_app.app_context():
            log = (
                db.session.query(OperationLog)
                .filter(
                    OperationLog.action == "document_delete",
                    OperationLog.tenant_id == test_tenant_account["tenant"].id,
                )
                .first()
            )
            assert log is not None, "文档删除日志应该存在于数据库"
            print(f"✓ document_delete 审计日志测试通过: {log.id}")


class TestAuditLogTypes:
    """测试审计日志操作类型定义"""

    def test_operation_types_defined(self):
        """验证所有必需的操作类型都已定义"""
        from services.audit_service import OPERATION_TYPES

        required_types = [
            "chat",
            "search",
            "workflow",
        ]

        for op_type in required_types:
            assert op_type in OPERATION_TYPES, f"{op_type} 应该在 OPERATION_TYPES 中定义"

        print(f"✓ 操作类型定义正确: {OPERATION_TYPES}")

    def test_sync_statuses_defined(self):
        """验证同步状态定义"""
        from services.audit_service import SYNC_STATUSES

        required_statuses = ["pending", "synced", "failed"]
        for status in required_statuses:
            assert status in SYNC_STATUSES, f"{status} 应该在 SYNC_STATUSES 中定义"

        print(f"✓ 同步状态定义正确: {SYNC_STATUSES}")


class TestAuditLogQuery:
    """测试审计日志查询功能"""

    def test_query_by_action(self, flask_app):
        """测试按操作类型查询"""
        with flask_app.app_context():
            logs = db.session.query(OperationLog).filter(OperationLog.action == "login").all()
            assert isinstance(logs, list)
            print(f"✓ 查询 login 日志成功，共 {len(logs)} 条")

    def test_query_by_operation_type(self, flask_app):
        """测试按操作大类查询"""
        with flask_app.app_context():
            logs = db.session.query(OperationLog).filter(OperationLog.operation_type == "chat").all()
            assert isinstance(logs, list)
            print(f"✓ 查询 chat 类型日志成功，共 {len(logs)} 条")

    def test_query_by_date_range(self, flask_app):
        """测试按日期范围查询"""
        with flask_app.app_context():
            today = datetime.now()
            yesterday = today - timedelta(days=1)

            logs = db.session.query(OperationLog).filter(OperationLog.created_at >= yesterday).all()
            assert isinstance(logs, list)
            print(f"✓ 查询日期范围日志成功，共 {len(logs)} 条")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
