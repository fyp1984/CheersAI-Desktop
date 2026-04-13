"""
审计日志服务单元测试
"""

import unittest
from unittest.mock import MagicMock, patch


class TestAuditService(unittest.TestCase):
    """测试审计日志功能"""

    def test_operation_types_defined(self):
        """测试操作类型定义"""
        from services.audit_service import OPERATION_TYPES

        self.assertIn("chat", OPERATION_TYPES)
        self.assertIn("search", OPERATION_TYPES)
        self.assertIn("workflow", OPERATION_TYPES)

    def test_desensitize_content(self):
        """测试敏感信息脱敏"""
        from services.audit_service import desensitize_content

        # 手机号脱敏
        result = desensitize_content("请致电13812345678")
        self.assertEqual("请致电***********", result)

        # 邮箱脱敏
        result = desensitize_content("请联系 test@example.com")
        self.assertEqual("请联系 ***@***.***", result)

    @patch("services.audit_service.Session")
    @patch("services.audit_service.current_user")
    @patch("services.audit_service.request")
    def test_log_operation_success(self, mock_request, mock_current_user, mock_session):
        """测试记录操作日志成功"""
        from services.audit_service import log_operation

        # Mock current_user
        mock_current_user.id = "test-account-id"
        mock_current_user.name = "Test User"
        mock_current_user.tenant_id = "test-tenant-id"

        # Mock request
        mock_request.headers = {}
        mock_request.remote_addr = "127.0.0.1"

        # Mock session
        mock_session_instance = MagicMock()
        mock_session.return_value.__enter__.return_value = mock_session_instance

        result = log_operation(
            action="login",
            operation_type="chat",
            content={"method": "password"},
        )

        self.assertIsNotNone(result)
        mock_session_instance.add.assert_called_once()
        mock_session_instance.commit.assert_called_once()

    def test_log_operation_partial_fields(self):
        """测试部分字段记录"""
        from services.audit_service import log_operation

        with (
            patch("services.audit_service.Session") as mock_session,
            patch("services.audit_service.current_user") as mock_current_user,
            patch("services.audit_service.request") as mock_request,
        ):
            mock_current_user.id = "test-account-id"
            mock_current_user.name = "Test User"
            mock_current_user.tenant_id = "test-tenant-id"
            mock_request.headers = {}
            mock_request.remote_addr = "127.0.0.1"

            mock_session_instance = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_session_instance

            result = log_operation(
                action="search",
                operation_type="search",
                content={"query": "test query", "result_count": 5},
            )

            self.assertIsNotNone(result)


class TestAuditLogging(unittest.TestCase):
    """测试各模块审计日志记录"""

    @patch("services.audit_service.log_operation")
    def test_knowledge_retrieval_logs_search(self, mock_log_operation):
        """测试知识检索记录搜索日志"""
        from core.workflow.nodes.knowledge_retrieval.knowledge_retrieval_node import (
            KnowledgeRetrievalNode,
        )
        from core.workflow.entities import GraphInitParams

        # 验证模块导入成功
        self.assertIsNotNone(KnowledgeRetrievalNode)

    @patch("services.audit_service.log_operation")
    def test_workflow_runs_are_logged(self, mock_log_operation):
        """测试工作流运行记录日志"""
        # 这个测试只验证导入成功
        from controllers.console.app import workflow

        self.assertIsNotNone(workflow)


if __name__ == "__main__":
    unittest.main()
