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
from libs.desktop_auth import has_any_workspace_capability
from libs.helper import TimestampField
from libs.login import login_required
from models.account import Account, TenantAccountJoin
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

SYSTEM_AUDIT_CAPABILITIES = ("desktop_system_admin",)
TEAM_AUDIT_CAPABILITIES = ("desktop_team_manage", "desktop_member_manage")


def _resolve_current_tenant_id(session: Session) -> str | None:
    tenant_id = current_user.current_tenant_id
    if tenant_id:
        return tenant_id

    join = (
        session.query(TenantAccountJoin)
        .filter(TenantAccountJoin.account_id == str(current_user.id))
        .order_by(TenantAccountJoin.current.desc(), TenantAccountJoin.id.asc())
        .first()
    )
    return join.tenant_id if join else None


def _resolve_audit_scope(session: Session) -> tuple[str | None, bool, bool]:
    tenant_id = _resolve_current_tenant_id(session)
    can_view_system = bool(
        tenant_id
        and has_any_workspace_capability(current_user, SYSTEM_AUDIT_CAPABILITIES, tenant_id)
    )
    can_view_team = can_view_system or bool(
        tenant_id
        and has_any_workspace_capability(current_user, TEAM_AUDIT_CAPABILITIES, tenant_id)
    )
    return tenant_id, can_view_system, can_view_team


def _apply_common_filters(query, args: dict):
    if args.get("action"):
        query = query.filter(OperationLog.action == args["action"])

    if args.get("keyword"):
        keyword = f"%{args['keyword']}%"
        query = query.filter(
            or_(
                OperationLog.action.ilike(keyword),
                OperationLog.operation_type.ilike(keyword),
                OperationLog.created_ip.ilike(keyword),
                OperationLog.error_message.ilike(keyword),
                Account.name.ilike(keyword),
                Account.email.ilike(keyword),
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

    return query


def _apply_user_scope_filters(query, args: dict, *, can_view_team: bool):
    if not can_view_team:
        return query.filter(OperationLog.account_id == str(current_user.id))

    if args.get("account_id"):
        query = query.filter(OperationLog.account_id == args["account_id"])

    if args.get("account_name"):
        account_name = f"%{args['account_name']}%"
        query = query.filter(
            or_(
                Account.name.ilike(account_name),
                Account.email.ilike(account_name),
            )
        )

    if args.get("user_keyword"):
        user_keyword = f"%{args['user_keyword']}%"
        query = query.filter(
            or_(
                Account.name.ilike(user_keyword),
                Account.email.ilike(user_keyword),
            )
        )

    return query


def _build_operation_log_query(session: Session, args: dict):
    tenant_id, can_view_system, can_view_team = _resolve_audit_scope(session)

    query = session.query(OperationLog, Account).join(Account, OperationLog.account_id == Account.id)

    if not can_view_system:
        if not tenant_id:
            return None, tenant_id, can_view_system, can_view_team
        query = query.filter(OperationLog.tenant_id == tenant_id)

    query = _apply_common_filters(query, args)
    query = _apply_user_scope_filters(query, args, can_view_team=can_view_team)
    return query, tenant_id, can_view_system, can_view_team


def _build_operation_log_scope_query(session: Session):
    tenant_id, can_view_system, can_view_team = _resolve_audit_scope(session)
    query = session.query(OperationLog)

    if not can_view_system:
        if not tenant_id:
            return None, tenant_id, can_view_system, can_view_team
        query = query.filter(OperationLog.tenant_id == tenant_id)

    if not can_view_team:
        query = query.filter(OperationLog.account_id == str(current_user.id))

    return query, tenant_id, can_view_system, can_view_team


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
        parser.add_argument("user_keyword", type=str, location="args")
        parser.add_argument("keyword", type=str, location="args")
        parser.add_argument("start_date", type=str, location="args")
        parser.add_argument("end_date", type=str, location="args")
        parser.add_argument("operation_type", type=str, location="args")
        parser.add_argument("sync_status", type=str, location="args")
        args = parser.parse_args()

        page = max(1, args["page"])
        limit = min(100, max(1, args["limit"]))
        offset = (page - 1) * limit

        with Session(db.engine) as session:
            query, _tenant_id, _can_view_system, _can_view_team = _build_operation_log_query(session, args)
            if query is None:
                return {"data": [], "total": 0, "page": page, "limit": limit, "has_more": False}

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
        with Session(db.engine) as session:
            base_query, _tenant_id, _can_view_system, _can_view_team = _build_operation_log_scope_query(session)
            if base_query is None:
                return {"today_count": 0, "total_count": 0, "verified_count": 0, "failed_count": 0}

            today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            today_count = base_query.filter(OperationLog.created_at >= today_start).count()

            total_count = base_query.count()

            verified_actions = ["login", "create", "update", "delete"]
            verified_count = base_query.filter(OperationLog.action.in_(verified_actions)).count()

            failed_count = base_query.filter(
                or_(
                    OperationLog.action.like("%fail%"),
                    OperationLog.error_message.is_not(None),
                    OperationLog.sync_status == "failed",
                )
            ).count()

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
        with Session(db.engine) as session:
            base_query, _tenant_id, _can_view_system, _can_view_team = _build_operation_log_scope_query(session)
            if base_query is None:
                return {"actions": []}

            actions = base_query.with_entities(OperationLog.action).distinct().all()

            return {"actions": [action[0] for action in actions]}


@console_ns.route("/operation-logs/export")
class OperationLogExportApi(Resource):
    @login_required
    @account_initialization_required
    @require_workspace_capabilities("desktop_audit_view")
    def post(self):
        """Export operation logs to Excel or PDF"""
        import logging

        logger = logging.getLogger(__name__)

        parser = console_ns.parser()
        parser.add_argument("format", type=str, default="excel", location="json")
        parser.add_argument("action", type=str, location="json")
        parser.add_argument("account_id", type=str, location="json")
        parser.add_argument("account_name", type=str, location="json")
        parser.add_argument("user_keyword", type=str, location="json")
        parser.add_argument("keyword", type=str, location="json")
        parser.add_argument("start_date", type=str, location="json")
        parser.add_argument("end_date", type=str, location="json")
        parser.add_argument("operation_type", type=str, location="json")
        parser.add_argument("sync_status", type=str, location="json")
        args = parser.parse_args()

        with Session(db.engine) as session:
            tenant_id = _resolve_current_tenant_id(session)
            if not has_any_workspace_capability(current_user, ["desktop_audit_view"], tenant_id):
                logger.error("[EXPORT] Permission denied for current user")
                return {"error": "Permission denied"}, 403

            query, _tenant_id, _can_view_system, _can_view_team = _build_operation_log_query(session, args)
            if query is None:
                return {"error": "No accessible audit scope"}, 403

            results = query.order_by(desc(OperationLog.created_at)).all()

            if args.get("format") == "excel":
                return self._export_excel(results)
            else:
                return self._export_excel(results)

    def _export_excel(self, results):
        """Export to Excel format"""
        import logging

        logger = logging.getLogger(__name__)

        try:
            output = BytesIO()
            workbook = xlsxwriter.Workbook(output, {"in_memory": True})
            worksheet = workbook.add_worksheet("Audit Logs")

            headers = [
                "Time",
                "Operation Type",
                "Action",
                "User",
                "User Email",
                "IP Address",
                "Device Info",
                "Duration (ms)",
                "Desensitize Status",
                "Sync Status",
                "Error Message",
            ]
            for col, header in enumerate(headers):
                worksheet.write(0, col, header)

            for row, (log, account) in enumerate(results, start=1):
                worksheet.write(row, 0, log.created_at.strftime("%Y-%m-%d %H:%M:%S") if log.created_at else "")
                worksheet.write(row, 1, log.operation_type or "")
                worksheet.write(row, 2, log.action or "")
                worksheet.write(row, 3, log.account_name or account.name if account else "")
                worksheet.write(row, 4, account.email if account else "")
                worksheet.write(row, 5, log.created_ip or "")
                worksheet.write(row, 6, log.device_info or "")
                worksheet.write(row, 7, log.duration or 0)
                worksheet.write(row, 8, log.desensitize_status or "")
                worksheet.write(row, 9, log.sync_status or "")
                worksheet.write(row, 10, log.error_message or "")

            workbook.close()
            output.seek(0)

            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            filename = f"CheersAI_AuditLogs_{timestamp}.xlsx"

            return Response(
                output.getvalue(),
                mimetype="application/octet-stream",
                headers={"Content-Disposition": f"attachment; filename={filename}"},
            )
        except Exception as e:
            logger.error(f"[EXPORT] Error: {e}")
            return {"error": str(e)}, 500
