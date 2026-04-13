import logging
from uuid import uuid4

from configs import dify_config
from extensions.ext_database import db
from extensions.ext_mail import mail
from models.beta_application_notification import BetaApplicationNotification
from tasks.mail_inner_task import send_inner_email, send_inner_email_task

logger = logging.getLogger(__name__)


class BetaApplicationNotificationService:
    """Dispatch beta application notification emails."""

    @classmethod
    def send_submitted_email(
        cls,
        *,
        application_id: str | None,
        to: str,
        name: str | None,
        language: str | None,
        sync: bool = False,
    ) -> bool:
        subject, body = cls._build_submitted_message(language)
        return cls._dispatch_email(
            application_id=application_id,
            event="submitted",
            to=to,
            subject=subject,
            body=body,
            substitutions={"name": name or ""},
            sync=sync,
        )

    @classmethod
    def send_rejected_email(
        cls,
        *,
        application_id: str | None,
        to: str,
        name: str | None,
        language: str | None,
        reason: str,
        sync: bool = False,
    ) -> bool:
        subject, body = cls._build_rejected_message(language)
        return cls._dispatch_email(
            application_id=application_id,
            event="rejected",
            to=to,
            subject=subject,
            body=body,
            substitutions={
                "name": name or "",
                "reason": reason,
            },
            sync=sync,
        )

    @classmethod
    def send_provision_success_email(
        cls,
        *,
        application_id: str | None,
        to: str,
        name: str | None,
        language: str | None,
        sso_username: str | None,
        sso_initial_password: str | None,
        filebay_repo: str | None,
        sync: bool = False,
    ) -> bool:
        subject, body = cls._build_success_message(language)
        return cls._dispatch_email(
            application_id=application_id,
            event="provision_success",
            to=to,
            subject=subject,
            body=body,
            substitutions={
                "name": name or "",
                "sso_username": sso_username or "",
                "sso_initial_password": sso_initial_password or "",
                "has_sso_initial_password": "1" if sso_initial_password else "",
                "filebay_repo": filebay_repo or "",
                "desktop_url": cls._get_desktop_url(),
                "sso_login_url": cls._get_sso_login_url(),
            },
            sync=sync,
        )

    @classmethod
    def send_provision_failed_email(
        cls,
        *,
        application_id: str | None,
        to: str,
        name: str | None,
        language: str | None,
        error_message: str,
        sync: bool = False,
    ) -> bool:
        subject, body = cls._build_failed_message(language)
        return cls._dispatch_email(
            application_id=application_id,
            event="provision_failed",
            to=to,
            subject=subject,
            body=body,
            substitutions={
                "name": name or "",
                "error_message": error_message,
            },
            sync=sync,
        )

    @classmethod
    def _dispatch_email(
        cls,
        *,
        application_id: str | None,
        event: str,
        to: str,
        subject: str,
        body: str,
        substitutions: dict[str, str],
        sync: bool = False,
    ) -> bool:
        if not to:
            return False
        notification = cls._create_notification(
            application_id=application_id,
            event=event,
            receiver=to,
        )
        if not mail.is_inited():
            logger.warning("Skip beta application mail for %s because mail client is not initialized", to)
            cls._mark_notification_failed(notification, error_message="Mail client is not initialized.")
            return False
        try:
            if sync:
                send_inner_email(to=[to], subject=subject, body=body, substitutions=substitutions)
                provider_message_id = None
            else:
                task = send_inner_email_task.delay(to=[to], subject=subject, body=body, substitutions=substitutions)
                provider_message_id = getattr(task, "id", None)
            cls._mark_notification_sent(notification, provider_message_id=provider_message_id)
            return True
        except Exception:
            logger.exception("Failed to enqueue beta application mail for %s", to)
            cls._mark_notification_failed(notification, error_message="Failed to enqueue mail task.")
            return False

    @classmethod
    def _create_notification(
        cls,
        *,
        application_id: str | None,
        event: str,
        receiver: str,
    ) -> BetaApplicationNotification | None:
        if not application_id:
            return None

        notification = BetaApplicationNotification(
            id=str(uuid4()),
            application_id=application_id,
            channel="email",
            event=event,
            receiver=receiver,
            status="pending",
        )
        db.session.add(notification)
        db.session.commit()
        return notification

    @classmethod
    def _mark_notification_sent(
        cls,
        notification: BetaApplicationNotification | None,
        *,
        provider_message_id: str | None = None,
    ):
        if not notification:
            return
        notification.status = "sent"
        notification.provider_message_id = provider_message_id
        notification.error_message = None
        db.session.add(notification)
        db.session.commit()

    @classmethod
    def _mark_notification_failed(cls, notification: BetaApplicationNotification | None, *, error_message: str):
        if not notification:
            return
        notification.status = "failed"
        notification.error_message = error_message[:5000]
        db.session.add(notification)
        db.session.commit()

    @classmethod
    def _get_desktop_url(cls) -> str:
        return dify_config.BETA_NOTIFICATION_DESKTOP_URL or dify_config.CONSOLE_WEB_URL or ""

    @classmethod
    def _get_sso_login_url(cls) -> str:
        configured = dify_config.BETA_NOTIFICATION_SSO_LOGIN_URL
        if configured:
            return configured
        base_url = (dify_config.SSO_API_URL or "").rstrip("/")
        base_url = base_url.removesuffix("/api")
        owner = dify_config.SSO_PROVISION_OWNER or "CheersAI"
        return f"{base_url}/login/{owner}" if base_url else ""

    @classmethod
    def _build_submitted_message(cls, language: str | None) -> tuple[str, str]:
        if language == "zh-Hans":
            return (
                "内测申请已提交",
                """
                <p>您好 {{ name or '用户' }}，</p>
                <p>您的内测申请已经提交成功，当前状态为“待审核”。</p>
                <p>审核完成后，我们会通过邮件通知您结果。</p>
                """,
            )
        return (
            "Your beta application has been submitted",
            """
            <p>Hello {{ name or 'there' }},</p>
            <p>Your beta application has been submitted successfully and is now pending review.</p>
            <p>We will notify you by email once the review is complete.</p>
            """,
        )

    @classmethod
    def _build_rejected_message(cls, language: str | None) -> tuple[str, str]:
        if language == "zh-Hans":
            return (
                "内测申请审核未通过",
                """
                <p>您好 {{ name or '用户' }}，</p>
                <p>很抱歉，您的内测申请本次未通过审核。</p>
                <p>原因：{{ reason }}</p>
                <p>如需重新申请，请根据原因调整后再提交。</p>
                """,
            )
        return (
            "Your beta application was not approved",
            """
            <p>Hello {{ name or 'there' }},</p>
            <p>We are sorry to let you know that your beta application was not approved this time.</p>
            <p>Reason: {{ reason }}</p>
            <p>You may submit a new application after addressing the issue.</p>
            """,
        )

    @classmethod
    def _build_success_message(cls, language: str | None) -> tuple[str, str]:
        if language == "zh-Hans":
            return (
                "内测账号已开通",
                """
                <p>您好 {{ name or '用户' }}，</p>
                <p>您的内测申请已经审核通过，相关账号和资源已开通完成。</p>
                <p>Desktop 入口：<a href="{{ desktop_url }}">{{ desktop_url }}</a></p>
                <p>SSO 登录入口：<a href="{{ sso_login_url }}">{{ sso_login_url }}</a></p>
                <p>SSO 用户名：{{ sso_username }}</p>
                {% if has_sso_initial_password %}
                <p>SSO 初始密码：{{ sso_initial_password }}</p>
                <p>首次登录后请立即修改密码并妥善保管。</p>
                {% else %}
                <p>SSO 密码：沿用您当前密码；如忘记请联系管理员重置。</p>
                {% endif %}
                <p>FileBay 私有仓库：{{ filebay_repo }}</p>
                <p>安全提醒：请勿共享账号，不要上传映射文件到 FileBay。</p>
                """,
            )
        return (
            "Your beta account is ready",
            """
            <p>Hello {{ name or 'there' }},</p>
            <p>Your beta application has been approved and your access is ready.</p>
            <p>Desktop entry: <a href="{{ desktop_url }}">{{ desktop_url }}</a></p>
            <p>SSO login: <a href="{{ sso_login_url }}">{{ sso_login_url }}</a></p>
            <p>SSO username: {{ sso_username }}</p>
            {% if has_sso_initial_password %}
            <p>SSO temporary password: {{ sso_initial_password }}</p>
            <p>Please change your password immediately after first login.</p>
            {% else %}
            <p>SSO password: use your current password; contact admin if you need a reset.</p>
            {% endif %}
            <p>FileBay repository: {{ filebay_repo }}</p>
            <p>Please do not share your account or upload mapping files to FileBay.</p>
            """,
        )

    @classmethod
    def _build_failed_message(cls, language: str | None) -> tuple[str, str]:
        if language == "zh-Hans":
            return (
                "内测账号开通处理中",
                """
                <p>您好 {{ name or '用户' }}，</p>
                <p>您的内测申请已审核通过，但系统在自动开通时遇到异常，管理员正在处理。</p>
                <p>当前异常：{{ error_message }}</p>
                <p>请先不要重复提交申请，处理完成后我们会继续通知您。</p>
                """,
            )
        return (
            "Your beta account is still being provisioned",
            """
            <p>Hello {{ name or 'there' }},</p>
            <p>Your beta application has been approved, but we hit an error while provisioning your access.</p>
            <p>Current error: {{ error_message }}</p>
            <p>Please do not submit a duplicate application.</p>
            <p>We are working on it and will notify you once it is resolved.</p>
            """,
        )
