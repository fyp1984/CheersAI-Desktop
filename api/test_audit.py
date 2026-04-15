#!/usr/bin/env python3
"""
测试审计日志功能的脚本
"""

import os
import sys
import time

# 设置环境
os.chdir("/app")
sys.path.insert(0, "/app")

from extensions.ext_database import db
from models.account import Account
from models.model import OperationLog
from services.audit_service import log_operation
from sqlalchemy import select, func


def test_log_operation():
    """测试 log_operation 函数"""
    print("=" * 50)
    print("开始测试审计日志记录功能")
    print("=" * 50)

    # 获取当前数据库中的记录数
    with db.session() as session:
        count = session.query(func.count(OperationLog.id)).scalar()
        print(f"\n当前审计日志总数: {count}")

    # 获取一个测试账户
    with db.session() as session:
        result = session.execute(select(Account).limit(1)).scalar_one_or_none()

        if not result:
            print("ERROR: 没有找到测试账户")
            return

        account = result
        print(f"测试账户: {account.name} (ID: {account.id})")

        # 检查 tenant_id
        print(f"账户当前租户: {account.current_tenant_id}")

    # 模拟调用 log_operation - 使用 write_log 函数绕过登录检查
    from services.audit_service import write_log

    test_tenant_id = "1469d9d7-a37b-48ab-a8eb-a60a2040ff56"  # 使用已知存在的租户
    test_account_id = "19eff4de-7fd1-427b-9902-1235e3ea741c"  # C_Admin
    test_account_name = "C_Admin"

    print("\n测试 write_log 函数...")
    log_id = write_log(
        tenant_id=test_tenant_id,
        account_id=test_account_id,
        account_name=test_account_name,
        action="test_audit",
        operation_type="test",
        content={"test_key": "test_value", "message": "这是一个测试审计日志"},
    )

    if log_id:
        print(f"✓ 审计日志写入成功! Log ID: {log_id}")
    else:
        print("✗ 审计日志写入失败")
        return

    # 验证是否写入成功
    time.sleep(0.5)
    with db.session() as session:
        count = session.query(func.count(OperationLog.id)).scalar()
        print(f"\n写入后审计日志总数: {count}")

        # 查询刚刚写入的日志
        result = session.execute(select(OperationLog).where(OperationLog.id == log_id)).scalar_one_or_none()

        if result:
            print("\n" + "=" * 50)
            print("写入的审计日志详情:")
            print("=" * 50)
            print(f"  ID: {result.id}")
            print(f"  Action: {result.action}")
            print(f"  Content: {result.content}")
            print(f"  Tenant ID: {result.tenant_id}")
            print(f"  Account ID: {result.account_id}")
            print(f"  Account Name: {result.account_name}")
            print(f"  Created At: {result.created_at}")
            print(f"  Created IP: {result.created_ip}")
            print("=" * 50)
        else:
            print("✗ 无法查询到刚刚写入的日志")


if __name__ == "__main__":
    test_log_operation()
