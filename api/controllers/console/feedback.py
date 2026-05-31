from datetime import datetime

from flask import request
from flask_restx import Resource
from pydantic import BaseModel, Field
from sqlalchemy import desc, func, or_, select
from werkzeug.exceptions import NotFound

from controllers.common.schema import register_schema_models
from controllers.console import console_ns
from controllers.console.admin import admin_required
from extensions.ext_database import db
from libs.datetime_utils import naive_utc_now
from libs.helper import extract_remote_ip
from models import UserFeedback, UserFeedbackMessage


class FeedbackListQuery(BaseModel):
    page: int = Field(default=1, ge=1)
    limit: int = Field(default=20, ge=1, le=100)
    status: str | None = None
    tenant_id: str | None = None
    account_id: str | None = None
    q: str | None = None


class FeedbackReplyPayload(BaseModel):
    content: str = Field(..., min_length=1, max_length=5000)
    sender_type: str = Field(default="external", max_length=32)
    sender_id: str | None = Field(default=None, max_length=255)
    sender_name: str | None = Field(default=None, max_length=255)
    is_internal: bool = False
    status: str | None = Field(default=None, max_length=32)
    metadata: dict | None = None


class FeedbackUpdatePayload(BaseModel):
    status: str | None = Field(default=None, max_length=32)
    priority: str | None = Field(default=None, max_length=16)
    assigned_to: str | None = None
    resolution: str | None = None


register_schema_models(console_ns, FeedbackListQuery, FeedbackReplyPayload, FeedbackUpdatePayload)


def _timestamp(value: datetime | None) -> int | None:
    return int(value.timestamp()) if value else None


def _serialize_message(message: UserFeedbackMessage) -> dict:
    return {
        "id": message.id,
        "feedback_id": message.feedback_id,
        "content": message.content,
        "sender_type": message.sender_type,
        "sender_id": message.sender_id,
        "sender_name": message.sender_name,
        "is_internal": message.is_internal,
        "metadata": message.extra_metadata,
        "created_at": _timestamp(message.created_at),
    }


def _serialize_feedback(feedback: UserFeedback, include_messages: bool = False) -> dict:
    payload = {
        "id": feedback.id,
        "ticket_no": feedback.ticket_no,
        "tenant_id": feedback.tenant_id,
        "account_id": feedback.account_id,
        "user_name": feedback.user_name,
        "user_email": feedback.user_email,
        "source": feedback.source,
        "channel": feedback.channel,
        "category": feedback.category,
        "title": feedback.title,
        "content": feedback.content,
        "status": feedback.status,
        "priority": feedback.priority,
        "assigned_to": feedback.assigned_to,
        "resolved_at": _timestamp(feedback.resolved_at),
        "closed_at": _timestamp(feedback.closed_at),
        "resolution": feedback.resolution,
        "page_url": feedback.page_url,
        "app_id": feedback.app_id,
        "conversation_id": feedback.conversation_id,
        "message_id": feedback.message_id,
        "contact_allowed": feedback.contact_allowed,
        "metadata": feedback.extra_metadata,
        "created_at": _timestamp(feedback.created_at),
        "updated_at": _timestamp(feedback.updated_at),
    }
    if include_messages:
        messages = db.session.scalars(
            select(UserFeedbackMessage)
            .where(UserFeedbackMessage.feedback_id == feedback.id)
            .order_by(UserFeedbackMessage.created_at.asc())
        ).all()
        payload["messages"] = [_serialize_message(message) for message in messages]
    return payload


def _get_feedback(feedback_id: str) -> UserFeedback:
    feedback = db.session.scalar(select(UserFeedback).where(UserFeedback.id == feedback_id))
    if not feedback:
        raise NotFound("Feedback not found.")
    return feedback


@console_ns.route("/admin/feedbacks")
class AdminFeedbackListApi(Resource):
    @console_ns.expect(console_ns.models[FeedbackListQuery.__name__])
    @admin_required
    def get(self):
        args = FeedbackListQuery.model_validate(request.args.to_dict())
        stmt = select(UserFeedback)

        if args.status:
            stmt = stmt.where(UserFeedback.status == args.status)
        if args.tenant_id:
            stmt = stmt.where(UserFeedback.tenant_id == args.tenant_id)
        if args.account_id:
            stmt = stmt.where(UserFeedback.account_id == args.account_id)
        if args.q:
            keyword = f"%{args.q.strip()}%"
            stmt = stmt.where(
                or_(
                    UserFeedback.ticket_no.ilike(keyword),
                    UserFeedback.title.ilike(keyword),
                    UserFeedback.content.ilike(keyword),
                    UserFeedback.user_email.ilike(keyword),
                    UserFeedback.user_name.ilike(keyword),
                )
            )

        total = db.session.scalar(select(func.count()).select_from(stmt.subquery())) or 0
        items = db.session.scalars(
            stmt.order_by(desc(UserFeedback.created_at)).offset((args.page - 1) * args.limit).limit(args.limit)
        ).all()
        return {
            "data": [_serialize_feedback(feedback) for feedback in items],
            "total": total,
            "page": args.page,
            "limit": args.limit,
            "has_more": args.page * args.limit < total,
        }


@console_ns.route("/admin/feedbacks/<uuid:feedback_id>")
class AdminFeedbackApi(Resource):
    @admin_required
    def get(self, feedback_id):
        return {"data": _serialize_feedback(_get_feedback(str(feedback_id)), include_messages=True)}

    @console_ns.expect(console_ns.models[FeedbackUpdatePayload.__name__])
    @admin_required
    def patch(self, feedback_id):
        feedback = _get_feedback(str(feedback_id))
        args = FeedbackUpdatePayload.model_validate(console_ns.payload or {})

        if args.status:
            feedback.status = args.status
            if args.status == "resolved" and not feedback.resolved_at:
                feedback.resolved_at = naive_utc_now()
            if args.status in {"closed", "resolved"} and not feedback.closed_at:
                feedback.closed_at = naive_utc_now()
        if args.priority:
            feedback.priority = args.priority
        if args.assigned_to is not None:
            feedback.assigned_to = args.assigned_to or None
        if args.resolution is not None:
            feedback.resolution = args.resolution

        db.session.commit()
        return {"result": "success", "data": _serialize_feedback(feedback)}


@console_ns.route("/admin/feedbacks/<uuid:feedback_id>/messages")
class AdminFeedbackMessageListApi(Resource):
    @console_ns.expect(console_ns.models[FeedbackReplyPayload.__name__])
    @admin_required
    def post(self, feedback_id):
        feedback = _get_feedback(str(feedback_id))
        args = FeedbackReplyPayload.model_validate(console_ns.payload or {})

        metadata = dict(args.metadata or {})
        metadata.setdefault("remote_ip", extract_remote_ip(request))
        metadata.setdefault("user_agent", request.headers.get("User-Agent"))

        message = UserFeedbackMessage(
            feedback_id=feedback.id,
            content=args.content.strip(),
            sender_type=args.sender_type,
            sender_id=args.sender_id,
            sender_name=args.sender_name,
            is_internal=args.is_internal,
            extra_metadata=metadata,
        )
        db.session.add(message)

        if args.status:
            feedback.status = args.status
            if args.status == "resolved" and not feedback.resolved_at:
                feedback.resolved_at = naive_utc_now()
            if args.status in {"closed", "resolved"} and not feedback.closed_at:
                feedback.closed_at = naive_utc_now()
        elif feedback.status == "open":
            feedback.status = "in_progress"

        message_id = message.id
        db.session.commit()

        return {
            "result": "success",
            "data": _serialize_message(db.session.get(UserFeedbackMessage, message_id) or message),
        }, 201
