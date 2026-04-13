from datetime import datetime
from io import BytesIO

import xlsxwriter
from flask import Blueprint, Response
from flask_login import current_user
from flask_restx import Resource, fields
from sqlalchemy import desc, func, or_
from sqlalchemy.orm import Session

from controllers.console import console_ns
from controllers.console.wraps import account_initialization_required, require_workspace_capabilities
from extensions.ext_database import db
from libs.desktop_auth import has_role_capability
from libs.helper import TimestampField
from libs.login import login_required
from models.account import Account
from models.model import OperationLog

operation_log_model = console_ns.model(
    "OperationLog",
    {
        "id": fields.String(description="Log ID"),
        "tenant_id": fields.String(description="Tenant ID"),
        "account_id": fields.String(description="Account ID"),
        "account_name": fields.String(description="Account name"),
        "account_email": fields.String(description="Account email"),
        "action": fields.String(description="Action type"),
        "content": fields.Raw(description="Action content"),
        "created_at": TimestampField(description="Created time"),
        "created_ip": fields.String(description="IP address"),
        "operation_type": fields.String(description="Operation type"),
        "request_content": fields.String(description="Request content"),
        "response_content": fields.String(description="Response content"),
        "desensitize_status": fields.String(description="Desensitize status"),
        "device_info": fields.String(description="Device info"),
        "duration": fields.Integer(description="Duration (ms)"),
        "sync_status": fields.String(description="Sync status"),
        "sync_time": TimestampField(description="Sync time"),
        "is_expired": fields.Boolean(description="Is expired"),
        "error_message": fields.String(description="Error message"),
    },
)

operation_log_list_model = console_ns.model(
    "OperationLogList",
    {
        "data": fields.List(fields.Nested(operation_log_model)),
        "total": fields.Integer(description="Total count"),
        "page": fields.Integer(description="Current page"),
        "limit": fields.Integer(description="Page size"),
        "has_more": fields.Boolean(description="Has more data"),
    },
)

stats_model = console_ns.model(
    "OperationLogStats",
    {
        "today_count": fields.Integer(description="Today's operation count"),
        "total_count": fields.Integer(description="Total operation count"),
        "verified_count": fields.Integer(description="Verified operation count"),
        "failed_count": fields.Integer(description="Failed operation count"),
    },
)

operation_logs_bp = Blueprint("operation_logs", __name__, url_prefix="/console/api")


@console_ns.route("/operation-logs")
class OperationLogListApi(Resource):
    @login_required
    @account_initialization_required
    @require_workspace_capabilities("desktop_audit_view")
    @console_ns.marshal_with(operation_log_list_model)
    def get(self):
        """Get operation logs list with pagination and filters"""
        parser = console_ns.parser()
        parser.add_argument("page", type=int, default=1, location="args")
        parser.add_argument("limit", type=int, default=20, location="args")
        parser.add_argument("action", type=str, location="args")
        parser.add_argument("account_id", type=str, location="args")
        parser.add_argument("account_name", type=str, location="args")
        parser.add_argument("keyword", type=str, location="args")
        parser.add_argument("start_date", type=str, location="args")
        parser.add_argument("end_date", type=str, location="args")
        parser.add_argument("operation_type", type=str, location="args")
        parser.add_argument("sync_status", type=str, location="args")
        args = parser.parse_args()

        page = max(1, args["page"])
        limit = min(100, max(1, args["limit"]))
        offset = (page - 1) * limit

        # Get tenant_id from user's tenant joins if current_tenant_id is None
        tenant_id = current_user.current_tenant_id
        if not tenant_id:
            from models.account import TenantAccountJoin

            join = session.query(TenantAccountJoin).filter(TenantAccountJoin.account_id == str(current_user.id)).first()
            if join:
                tenant_id = join.tenant_id

        if not tenant_id:
            return {"data": [], "total": 0, "page": page, "limit": limit, "has_more": False}

        with Session(db.engine) as session:
            query = (
                session.query(OperationLog, Account)
                .join(Account, OperationLog.account_id == Account.id)
                .filter(OperationLog.tenant_id == tenant_id)
            )

            if args.get("action"):
                query = query.filter(OperationLog.action == args["action"])

            if args.get("account_id"):
                query = query.filter(OperationLog.account_id == args["account_id"])

            if args.get("account_name"):
                query = query.filter(Account.name.ilike(f"%{args['account_name']}%"))

            if args.get("keyword"):
                keyword = f"%{args['keyword']}%"
                query = query.filter(
                    or_(
                        Account.name.ilike(keyword),
                        Account.email.ilike(keyword),
                        OperationLog.action.ilike(keyword),
                    )
                )

            if args.get("start_date") and args["start_date"]:
                try:
                    start = datetime.strptime(args["start_date"], "%Y-%m-%d")
                    query = query.filter(OperationLog.created_at >= start)
                except (ValueError, TypeError):
                    pass

            if args.get("end_date") and args["end_date"]:
                try:
                    end = datetime.strptime(args["end_date"], "%Y-%m-%d")
                    end = end.replace(hour=23, minute=59, second=59)
                    query = query.filter(OperationLog.created_at <= end)
                except (ValueError, TypeError):
                    pass

            if args.get("operation_type"):
                query = query.filter(OperationLog.operation_type == args["operation_type"])

            if args.get("sync_status"):
                query = query.filter(OperationLog.sync_status == args["sync_status"])

            total = query.count()

            results = query.order_by(desc(OperationLog.created_at)).offset(offset).limit(limit).all()

            data = []
            for log, account in results:
                data.append(
                    {
                        "id": log.id,
                        "tenant_id": log.tenant_id,
                        "account_id": log.account_id,
                        "account_name": log.account_name or account.name,
                        "account_email": account.email,
                        "action": log.action,
                        "content": log.content,
                        "created_at": int(log.created_at.timestamp() * 1000),
                        "created_ip": log.created_ip,
                        "operation_type": log.operation_type,
                        "request_content": log.request_content,
                        "response_content": log.response_content,
                        "desensitize_status": log.desensitize_status,
                        "device_info": log.device_info,
                        "duration": log.duration,
                        "sync_status": log.sync_status,
                        "sync_time": int(log.sync_time.timestamp()) if log.sync_time else None,
                        "is_expired": log.is_expired,
                        "error_message": log.error_message,
                    }
                )

            return {
                "data": data,
                "total": total,
                "page": page,
                "limit": limit,
                "has_more": total > page * limit,
            }


@console_ns.route("/operation-logs/stats")
class OperationLogStatsApi(Resource):
    @login_required
    @account_initialization_required
    @require_workspace_capabilities("desktop_audit_view")
    @console_ns.marshal_with(stats_model)
    def get(self):
        """Get operation logs statistics"""
        # Get tenant_id from user context
        tenant_id = current_user.current_tenant_id
        if not tenant_id:
            from models.account import TenantAccountJoin

            join = (
                db.session.query(TenantAccountJoin).filter(TenantAccountJoin.account_id == str(current_user.id)).first()
            )
            if join:
                tenant_id = join.tenant_id

        if not tenant_id:
            return {"today_count": 0, "total_count": 0, "verified_count": 0, "failed_count": 0}

        with Session(db.engine) as session:
            today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            today_count = (
                session.query(func.count(OperationLog.id))
                .filter(
                    OperationLog.tenant_id == tenant_id,
                    OperationLog.created_at >= today_start,
                )
                .scalar()
            )

            total_count = (
                session.query(func.count(OperationLog.id)).filter(OperationLog.tenant_id == tenant_id).scalar()
            )

            verified_actions = ["login", "create", "update", "delete"]
            verified_count = (
                session.query(func.count(OperationLog.id))
                .filter(
                    OperationLog.tenant_id == tenant_id,
                    OperationLog.action.in_(verified_actions),
                )
                .scalar()
            )

            failed_count = (
                session.query(func.count(OperationLog.id))
                .filter(
                    OperationLog.tenant_id == tenant_id,
                    OperationLog.action.like("%fail%"),
                )
                .scalar()
            )

            return {
                "today_count": today_count or 0,
                "total_count": total_count or 0,
                "verified_count": verified_count or 0,
                "failed_count": failed_count or 0,
            }


@console_ns.route("/operation-logs/actions")
class OperationLogActionsApi(Resource):
    @login_required
    @account_initialization_required
    @require_workspace_capabilities("desktop_audit_view")
    def get(self):
        """Get all unique action types"""
        # Get tenant_id from user context
        tenant_id = current_user.current_tenant_id
        if not tenant_id:
            from models.account import TenantAccountJoin

            join = (
                db.session.query(TenantAccountJoin).filter(TenantAccountJoin.account_id == str(current_user.id)).first()
            )
            if join:
                tenant_id = join.tenant_id

        if not tenant_id:
            return {"actions": []}

        with Session(db.engine) as session:
            actions = session.query(OperationLog.action).filter(OperationLog.tenant_id == tenant_id).distinct().all()

            return {"actions": [action[0] for action in actions]}


@console_ns.route("/operation-logs/export")
class OperationLogExportApi(Resource):
    @login_required
    @account_initialization_required
    @require_workspace_capabilities("desktop_audit_view")
    def post(self):
        """Export operation logs to Excel or PDF"""
        if not has_role_capability(current_user.role, "desktop_audit_view"):
            return {"error": "Permission denied"}, 403

        parser = console_ns.parser()
        parser.add_argument("format", type=str, default="excel", location="json")
        parser.add_argument("action", type=str, location="json")
        parser.add_argument("account_id", type=str, location="json")
        parser.add_argument("account_name", type=str, location="json")
        parser.add_argument("keyword", type=str, location="json")
        parser.add_argument("start_date", type=str, location="json")
        parser.add_argument("end_date", type=str, location="json")
        parser.add_argument("operation_type", type=str, location="json")
        parser.add_argument("sync_status", type=str, location="json")
        args = parser.parse_args()

        with Session(db.engine) as session:
            query = (
                session.query(OperationLog, Account)
                .join(Account, OperationLog.account_id == Account.id)
                .filter(OperationLog.tenant_id == current_user.current_tenant_id)
            )

            if args.get("action"):
                query = query.filter(OperationLog.action == args["action"])

            if args.get("account_id"):
                query = query.filter(OperationLog.account_id == args["account_id"])

            if args.get("account_name"):
                query = query.filter(Account.name.ilike(f"%{args['account_name']}%"))

            if args.get("keyword"):
                keyword = f"%{args['keyword']}%"
                query = query.filter(
                    or_(
                        Account.name.ilike(keyword),
                        Account.email.ilike(keyword),
                        OperationLog.action.ilike(keyword),
                    )
                )

            if args.get("start_date") and args["start_date"]:
                try:
                    start = datetime.strptime(args["start_date"], "%Y-%m-%d")
                    query = query.filter(OperationLog.created_at >= start)
                except (ValueError, TypeError):
                    pass

            if args.get("end_date") and args["end_date"]:
                try:
                    end = datetime.strptime(args["end_date"], "%Y-%m-%d")
                    end = end.replace(hour=23, minute=59, second=59)
                    query = query.filter(OperationLog.created_at <= end)
                except (ValueError, TypeError):
                    pass

            if args.get("operation_type"):
                query = query.filter(OperationLog.operation_type == args["operation_type"])

            if args.get("sync_status"):
                query = query.filter(OperationLog.sync_status == args["sync_status"])

            results = query.order_by(desc(OperationLog.created_at)).all()

            if args.get("format") == "excel":
                return self._export_excel(results)
            else:
                return self._export_excel(results)

    def _export_excel(self, results):
        """Export to Excel format"""
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output, {"in_memory": True})
        worksheet = workbook.add_worksheet("审计日志")

        headers = [
            "时间",
            "操作类型",
            "操作行为",
            "账户名称",
            "IP地址",
            "设备信息",
            "执行耗时(ms)",
            "脱敏状态",
            "同步状态",
            "错误信息",
        ]
        for col, header in enumerate(headers):
            worksheet.write(0, col, header)

        for row, (log, account) in enumerate(results, start=1):
            worksheet.write(row, 0, log.created_at.strftime("%Y-%m-%d %H:%M:%S") if log.created_at else "")
            worksheet.write(row, 1, log.operation_type or "")
            worksheet.write(row, 2, log.action or "")
            worksheet.write(row, 3, log.account_name or account.name if account else "")
            worksheet.write(row, 4, log.created_ip or "")
            worksheet.write(row, 5, log.device_info or "")
            worksheet.write(row, 6, log.duration or 0)
            worksheet.write(row, 7, log.desensitize_status or "")
            worksheet.write(row, 8, log.sync_status or "")
            worksheet.write(row, 9, log.error_message or "")

        workbook.close()
        output.seek(0)

        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        filename = f"CheersAI审计日志_{timestamp}.xlsx"

        return Response(
            output.getvalue(),
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )
