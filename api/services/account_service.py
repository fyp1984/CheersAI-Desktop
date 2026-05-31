import base64
import json
import logging
import secrets
import uuid
from datetime import UTC, datetime, timedelta
from hashlib import sha256
from typing import Any, cast

from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from sqlalchemy.orm.exc import StaleDataError
from werkzeug.exceptions import Unauthorized

from configs import dify_config
from constants.languages import get_valid_language, language_timezone_mapping
from events.tenant_event import tenant_was_created
from extensions.ext_database import db
from extensions.ext_redis import redis_client, redis_fallback
from libs.datetime_utils import naive_utc_now
from libs.helper import RateLimiter, TokenManager
from libs.passport import PassportService
from libs.password import compare_password, hash_password, valid_password
from libs.rsa import generate_key_pair
from libs.token import generate_csrf_token
from models.account import (
    Account,
    AccountIntegrate,
    AccountInviteCode,
    AccountPointRedemption,
    AccountPointTransaction,
    AccountStatus,
    Tenant,
    TenantAccountJoin,
    TenantAccountRole,
    TenantPluginAutoUpgradeStrategy,
    TenantStatus,
)
from models.model import DifySetup
from services.billing_service import BillingService
from services.errors.account import (
    AccountAlreadyInTenantError,
    AccountLoginError,
    AccountNotLinkTenantError,
    AccountPasswordError,
    AccountRegisterError,
    CannotOperateSelfError,
    CurrentPasswordIncorrectError,
    InvalidActionError,
    LinkAccountIntegrateError,
    MemberNotInTenantError,
    NoPermissionError,
    RoleAlreadyAssignedError,
    TenantNotFoundError,
)
from services.errors.workspace import WorkSpaceNotAllowedCreateError, WorkspacesLimitExceededError
from services.feature_service import FeatureService
from tasks.delete_account_task import delete_account_task
from tasks.mail_account_deletion_task import send_account_deletion_verification_code
from tasks.mail_change_mail_task import (
    send_change_mail_completed_notification_task,
    send_change_mail_task,
)
from tasks.mail_email_code_login import send_email_code_login_mail_task
from tasks.mail_invite_member_task import send_invite_member_mail_task
from tasks.mail_owner_transfer_task import (
    send_new_owner_transfer_notify_email_task,
    send_old_owner_transfer_notify_email_task,
    send_owner_transfer_confirm_task,
)
from tasks.mail_register_task import send_email_register_mail_task, send_email_register_mail_task_when_account_exist
from tasks.mail_reset_password_task import (
    send_reset_password_mail_task,
    send_reset_password_mail_task_when_account_not_exist,
)

logger = logging.getLogger(__name__)


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    csrf_token: str


REFRESH_TOKEN_PREFIX = "refresh_token:"
ACCOUNT_REFRESH_TOKEN_PREFIX = "account_refresh_token:"
REFRESH_TOKEN_EXPIRY = timedelta(days=dify_config.REFRESH_TOKEN_EXPIRE_DAYS)


class AccountService:
    reset_password_rate_limiter = RateLimiter(prefix="reset_password_rate_limit", max_attempts=1, time_window=60 * 1)
    email_register_rate_limiter = RateLimiter(prefix="email_register_rate_limit", max_attempts=1, time_window=60 * 1)
    email_code_login_rate_limiter = RateLimiter(
        prefix="email_code_login_rate_limit", max_attempts=3, time_window=300 * 1
    )
    email_code_account_deletion_rate_limiter = RateLimiter(
        prefix="email_code_account_deletion_rate_limit", max_attempts=1, time_window=60 * 1
    )
    change_email_rate_limiter = RateLimiter(prefix="change_email_rate_limit", max_attempts=1, time_window=60 * 1)
    owner_transfer_rate_limiter = RateLimiter(prefix="owner_transfer_rate_limit", max_attempts=1, time_window=60 * 1)

    LOGIN_MAX_ERROR_LIMITS = 5
    FORGOT_PASSWORD_MAX_ERROR_LIMITS = 5
    CHANGE_EMAIL_MAX_ERROR_LIMITS = 5
    OWNER_TRANSFER_MAX_ERROR_LIMITS = 5
    EMAIL_REGISTER_MAX_ERROR_LIMITS = 5

    @staticmethod
    def _get_refresh_token_key(refresh_token: str) -> str:
        return f"{REFRESH_TOKEN_PREFIX}{refresh_token}"

    @staticmethod
    def _get_account_refresh_token_key(account_id: str) -> str:
        return f"{ACCOUNT_REFRESH_TOKEN_PREFIX}{account_id}"

    @staticmethod
    def _store_refresh_token(refresh_token: str, account_id: str):
        redis_client.setex(AccountService._get_refresh_token_key(refresh_token), REFRESH_TOKEN_EXPIRY, account_id)
        redis_client.setex(
            AccountService._get_account_refresh_token_key(account_id), REFRESH_TOKEN_EXPIRY, refresh_token
        )

    @staticmethod
    def _delete_refresh_token(refresh_token: str, account_id: str):
        redis_client.delete(AccountService._get_refresh_token_key(refresh_token))
        redis_client.delete(AccountService._get_account_refresh_token_key(account_id))

    @staticmethod
    def load_user(user_id: str) -> None | Account:
        account = db.session.query(Account).filter_by(id=user_id).first()
        if not account:
            return None

        if account.status == AccountStatus.BANNED:
            raise Unauthorized("Account is banned.")

        now = naive_utc_now()
        current_tenant = db.session.query(TenantAccountJoin).filter_by(account_id=account.id, current=True).first()
        if current_tenant:
            account.set_tenant_id(current_tenant.tenant_id)
        else:
            available_ta = (
                db.session.query(TenantAccountJoin)
                .filter_by(account_id=account.id)
                .order_by(TenantAccountJoin.id.asc())
                .first()
            )
            if not available_ta:
                return None

            account.set_tenant_id(available_ta.tenant_id)
            try:
                with Session(db.engine, expire_on_commit=False) as session:
                    join_to_update = session.query(TenantAccountJoin).filter_by(id=available_ta.id).first()
                    if join_to_update:
                        join_to_update.current = True
                        session.add(join_to_update)
                        session.commit()
            except StaleDataError:
                logger.warning(
                    "Skipping current tenant persistence for account %s because tenant membership changed concurrently",
                    account.id,
                    exc_info=True,
                )

        if account.email == "admin@example.com":
            try:
                with Session(db.engine, expire_on_commit=False) as session:
                    join_to_update = (
                        session.query(TenantAccountJoin)
                        .filter_by(account_id=account.id, tenant_id=account.current_tenant_id)
                        .first()
                    )
                    if join_to_update and join_to_update.role != TenantAccountRole.OWNER:
                        join_to_update.role = TenantAccountRole.OWNER
                        session.add(join_to_update)
                        session.commit()
                        account.role = TenantAccountRole.OWNER
            except Exception:
                logger.warning("Failed to restore admin account role", exc_info=True)

        if now - account.last_active_at > timedelta(minutes=10):
            try:
                with Session(db.engine, expire_on_commit=False) as session:
                    account_to_update = session.query(Account).filter_by(id=account.id).first()
                    if account_to_update:
                        account_to_update.last_active_at = now
                        session.add(account_to_update)
                        session.commit()
                account.last_active_at = now
            except StaleDataError:
                logger.warning(
                    "Skipping last_active update for account %s because account row changed concurrently",
                    account.id,
                    exc_info=True,
                )
        # NOTE: make sure account is accessible outside of a db session
        # This ensures that it will work correctly after upgrading to Flask version 3.1.2
        db.session.close()
        return account

    @staticmethod
    def get_account_jwt_token(account: Account) -> str:
        exp_dt = datetime.now(UTC) + timedelta(minutes=dify_config.ACCESS_TOKEN_EXPIRE_MINUTES)
        exp = int(exp_dt.timestamp())
        payload = {
            "user_id": account.id,
            "exp": exp,
            "iss": dify_config.EDITION,
            "sub": "Console API Passport",
        }

        token: str = PassportService().issue(payload)
        return token

    @staticmethod
    def authenticate(email: str, password: str, invite_token: str | None = None) -> Account:
        """authenticate account with email and password"""

        account = db.session.query(Account).filter_by(email=email).first()
        if not account:
            raise AccountPasswordError("Invalid email or password.")

        if account.status == AccountStatus.BANNED:
            raise AccountLoginError("Account is banned.")

        if password and invite_token and account.password is None:
            # if invite_token is valid, set password and password_salt
            salt = secrets.token_bytes(16)
            base64_salt = base64.b64encode(salt).decode()
            password_hashed = hash_password(password, salt)
            base64_password_hashed = base64.b64encode(password_hashed).decode()
            account.password = base64_password_hashed
            account.password_salt = base64_salt

        if account.password is None or not compare_password(password, account.password, account.password_salt):
            raise AccountPasswordError("Invalid email or password.")

        if account.status == AccountStatus.PENDING:
            account.status = AccountStatus.ACTIVE
            account.initialized_at = naive_utc_now()

        db.session.commit()

        return account

    @staticmethod
    def update_account_password(account, password, new_password):
        """update account password"""
        if account.password and not compare_password(password, account.password, account.password_salt):
            raise CurrentPasswordIncorrectError("Current password is incorrect.")

        # may be raised
        valid_password(new_password)

        # generate password salt
        salt = secrets.token_bytes(16)
        base64_salt = base64.b64encode(salt).decode()

        # encrypt password with salt
        password_hashed = hash_password(new_password, salt)
        base64_password_hashed = base64.b64encode(password_hashed).decode()
        account.password = base64_password_hashed
        account.password_salt = base64_salt
        db.session.add(account)
        db.session.commit()
        return account

    @staticmethod
    def create_account(
        email: str,
        name: str,
        interface_language: str,
        password: str | None = None,
        interface_theme: str = "light",
        is_setup: bool | None = False,
    ) -> Account:
        """create account"""
        if not FeatureService.get_system_features().is_allow_register and not is_setup:
            from controllers.console.error import AccountNotFound

            raise AccountNotFound()

        if dify_config.BILLING_ENABLED and BillingService.is_email_in_freeze(email):
            raise AccountRegisterError(
                description=(
                    "This email account has been deleted within the past "
                    "30 days and is temporarily unavailable for new account registration"
                )
            )

        password_to_set = None
        salt_to_set = None
        if password:
            valid_password(password)

            # generate password salt
            salt = secrets.token_bytes(16)
            base64_salt = base64.b64encode(salt).decode()

            # encrypt password with salt
            password_hashed = hash_password(password, salt)
            base64_password_hashed = base64.b64encode(password_hashed).decode()

            password_to_set = base64_password_hashed
            salt_to_set = base64_salt

        account = Account(
            name=name,
            email=email,
            password=password_to_set,
            password_salt=salt_to_set,
            interface_language=interface_language,
            interface_theme=interface_theme,
            timezone=language_timezone_mapping.get(interface_language, "UTC"),
        )

        db.session.add(account)
        db.session.commit()
        return account

    @staticmethod
    def create_account_and_tenant(
        email: str, name: str, interface_language: str, password: str | None = None
    ) -> Account:
        """create account"""
        account = AccountService.create_account(
            email=email, name=name, interface_language=interface_language, password=password
        )

        TenantService.create_owner_tenant_if_not_exist(account=account)
        AccountInviteCodeService.ensure_invite_codes(account)

        return account

    @staticmethod
    def generate_account_deletion_verification_code(account: Account) -> tuple[str, str]:
        code = "".join([str(secrets.randbelow(exclusive_upper_bound=10)) for _ in range(6)])
        token = TokenManager.generate_token(
            account=account, token_type="account_deletion", additional_data={"code": code}
        )
        return token, code

    @classmethod
    def send_account_deletion_verification_email(cls, account: Account, code: str):
        email = account.email
        if cls.email_code_account_deletion_rate_limiter.is_rate_limited(email):
            from controllers.console.auth.error import EmailCodeAccountDeletionRateLimitExceededError

            raise EmailCodeAccountDeletionRateLimitExceededError(
                int(cls.email_code_account_deletion_rate_limiter.time_window / 60)
            )

        send_account_deletion_verification_code.delay(to=email, code=code)

        cls.email_code_account_deletion_rate_limiter.increment_rate_limit(email)

    @staticmethod
    def verify_account_deletion_code(token: str, code: str) -> bool:
        token_data = TokenManager.get_token_data(token, "account_deletion")
        if token_data is None:
            return False

        if token_data["code"] != code:
            return False

        return True

    @staticmethod
    def delete_account(account: Account):
        """Delete account. This method only adds a task to the queue for deletion."""
        delete_account_task.delay(account.id)

    @staticmethod
    def link_account_integrate(provider: str, open_id: str, account: Account):
        """Link account integrate"""
        try:
            # Query whether there is an existing binding record for the same provider
            account_integrate: AccountIntegrate | None = (
                db.session.query(AccountIntegrate).filter_by(account_id=account.id, provider=provider).first()
            )

            if account_integrate:
                # If it exists, update the record
                account_integrate.open_id = open_id
                account_integrate.encrypted_token = ""  # todo
                account_integrate.updated_at = naive_utc_now()
            else:
                # If it does not exist, create a new record
                account_integrate = AccountIntegrate(
                    account_id=account.id, provider=provider, open_id=open_id, encrypted_token=""
                )
                db.session.add(account_integrate)

            db.session.commit()
            logger.info("Account %s linked %s account %s.", account.id, provider, open_id)
        except Exception as e:
            logger.exception("Failed to link %s account %s to Account %s", provider, open_id, account.id)
            raise LinkAccountIntegrateError("Failed to link account.") from e

    @staticmethod
    def close_account(account: Account):
        """Close account"""
        account.status = AccountStatus.CLOSED
        db.session.commit()

    @staticmethod
    def update_account(account, **kwargs):
        """Update account fields"""
        account = db.session.merge(account)
        for field, value in kwargs.items():
            if hasattr(account, field):
                setattr(account, field, value)
            else:
                raise AttributeError(f"Invalid field: {field}")

        db.session.commit()
        return account

    @staticmethod
    def update_account_email(account: Account, email: str) -> Account:
        """Update account email"""
        account.email = email
        account_integrate = db.session.query(AccountIntegrate).filter_by(account_id=account.id).first()
        if account_integrate:
            db.session.delete(account_integrate)
        db.session.add(account)
        db.session.commit()
        return account

    @staticmethod
    def update_login_info(account: Account, *, ip_address: str):
        """Update last login time and ip"""
        account.last_login_at = naive_utc_now()
        account.last_login_ip = ip_address
        db.session.add(account)
        db.session.commit()

    @staticmethod
    def login(account: Account, *, ip_address: str | None = None) -> TokenPair:
        if ip_address:
            try:
                AccountService.update_login_info(account=account, ip_address=ip_address)
            except StaleDataError:
                # Some local/dev databases have a duplicated physical account row; keep login working.
                db.session.rollback()
                logger.warning(
                    "Skipping login info update for account %s because account row changed concurrently",
                    account.id,
                    exc_info=True,
                )

        if account.status == AccountStatus.PENDING:
            account.status = AccountStatus.ACTIVE
            db.session.commit()

        access_token = AccountService.get_account_jwt_token(account=account)
        refresh_token = _generate_refresh_token()
        csrf_token = generate_csrf_token(account.id)

        AccountService._store_refresh_token(refresh_token, account.id)

        return TokenPair(access_token=access_token, refresh_token=refresh_token, csrf_token=csrf_token)

    @staticmethod
    def logout(*, account: Account):
        refresh_token = redis_client.get(AccountService._get_account_refresh_token_key(account.id))
        if refresh_token:
            AccountService._delete_refresh_token(refresh_token.decode("utf-8"), account.id)

    @staticmethod
    def refresh_token(refresh_token: str) -> TokenPair:
        # Verify the refresh token
        account_id = redis_client.get(AccountService._get_refresh_token_key(refresh_token))
        if not account_id:
            raise ValueError("Invalid refresh token")

        account = AccountService.load_user(account_id.decode("utf-8"))
        if not account:
            raise ValueError("Invalid account")

        # Generate new access token and refresh token
        new_access_token = AccountService.get_account_jwt_token(account)
        new_refresh_token = _generate_refresh_token()

        AccountService._delete_refresh_token(refresh_token, account.id)
        AccountService._store_refresh_token(new_refresh_token, account.id)
        csrf_token = generate_csrf_token(account.id)

        return TokenPair(access_token=new_access_token, refresh_token=new_refresh_token, csrf_token=csrf_token)

    @staticmethod
    def load_logged_in_account(*, account_id: str):
        return AccountService.load_user(account_id)

    @classmethod
    def send_reset_password_email(
        cls,
        account: Account | None = None,
        email: str | None = None,
        language: str = "en-US",
        is_allow_register: bool = False,
    ):
        account_email = account.email if account else email
        if account_email is None:
            raise ValueError("Email must be provided.")

        if cls.reset_password_rate_limiter.is_rate_limited(account_email):
            from controllers.console.auth.error import PasswordResetRateLimitExceededError

            raise PasswordResetRateLimitExceededError(int(cls.reset_password_rate_limiter.time_window / 60))

        code, token = cls.generate_reset_password_token(account_email, account)

        if account:
            send_reset_password_mail_task.delay(
                language=language,
                to=account_email,
                code=code,
            )
        else:
            send_reset_password_mail_task_when_account_not_exist.delay(
                language=language,
                to=account_email,
                is_allow_register=is_allow_register,
            )
        cls.reset_password_rate_limiter.increment_rate_limit(account_email)
        return token

    @classmethod
    def send_email_register_email(
        cls,
        account: Account | None = None,
        email: str | None = None,
        language: str = "en-US",
    ):
        account_email = account.email if account else email
        if account_email is None:
            raise ValueError("Email must be provided.")

        if cls.email_register_rate_limiter.is_rate_limited(account_email):
            from controllers.console.auth.error import EmailRegisterRateLimitExceededError

            raise EmailRegisterRateLimitExceededError(int(cls.email_register_rate_limiter.time_window / 60))

        code, token = cls.generate_email_register_token(account_email)

        if account:
            send_email_register_mail_task_when_account_exist.delay(
                language=language,
                to=account_email,
                account_name=account.name,
            )

        else:
            send_email_register_mail_task.delay(
                language=language,
                to=account_email,
                code=code,
            )
        cls.email_register_rate_limiter.increment_rate_limit(account_email)
        return token

    @classmethod
    def send_change_email_email(
        cls,
        account: Account | None = None,
        email: str | None = None,
        old_email: str | None = None,
        language: str = "en-US",
        phase: str | None = None,
    ):
        account_email = account.email if account else email
        if account_email is None:
            raise ValueError("Email must be provided.")
        if not phase:
            raise ValueError("phase must be provided.")

        if cls.change_email_rate_limiter.is_rate_limited(account_email):
            from controllers.console.auth.error import EmailChangeRateLimitExceededError

            raise EmailChangeRateLimitExceededError(int(cls.change_email_rate_limiter.time_window / 60))

        code, token = cls.generate_change_email_token(account_email, account, old_email=old_email)

        send_change_mail_task.delay(
            language=language,
            to=account_email,
            code=code,
            phase=phase,
        )
        cls.change_email_rate_limiter.increment_rate_limit(account_email)
        return token

    @classmethod
    def send_change_email_completed_notify_email(
        cls,
        account: Account | None = None,
        email: str | None = None,
        language: str = "en-US",
    ):
        account_email = account.email if account else email
        if account_email is None:
            raise ValueError("Email must be provided.")

        send_change_mail_completed_notification_task.delay(
            language=language,
            to=account_email,
        )

    @classmethod
    def send_owner_transfer_email(
        cls,
        account: Account | None = None,
        email: str | None = None,
        language: str = "en-US",
        workspace_name: str | None = "",
    ):
        account_email = account.email if account else email
        if account_email is None:
            raise ValueError("Email must be provided.")

        if cls.owner_transfer_rate_limiter.is_rate_limited(account_email):
            from controllers.console.auth.error import OwnerTransferRateLimitExceededError

            raise OwnerTransferRateLimitExceededError(int(cls.owner_transfer_rate_limiter.time_window / 60))

        code, token = cls.generate_owner_transfer_token(account_email, account)
        workspace_name = workspace_name or ""

        send_owner_transfer_confirm_task.delay(
            language=language,
            to=account_email,
            code=code,
            workspace=workspace_name,
        )
        cls.owner_transfer_rate_limiter.increment_rate_limit(account_email)
        return token

    @classmethod
    def send_old_owner_transfer_notify_email(
        cls,
        account: Account | None = None,
        email: str | None = None,
        language: str = "en-US",
        workspace_name: str | None = "",
        new_owner_email: str = "",
    ):
        account_email = account.email if account else email
        if account_email is None:
            raise ValueError("Email must be provided.")
        workspace_name = workspace_name or ""

        send_old_owner_transfer_notify_email_task.delay(
            language=language,
            to=account_email,
            workspace=workspace_name,
            new_owner_email=new_owner_email,
        )

    @classmethod
    def send_new_owner_transfer_notify_email(
        cls,
        account: Account | None = None,
        email: str | None = None,
        language: str = "en-US",
        workspace_name: str | None = "",
    ):
        account_email = account.email if account else email
        if account_email is None:
            raise ValueError("Email must be provided.")
        workspace_name = workspace_name or ""

        send_new_owner_transfer_notify_email_task.delay(
            language=language,
            to=account_email,
            workspace=workspace_name,
        )

    @classmethod
    def generate_reset_password_token(
        cls,
        email: str,
        account: Account | None = None,
        code: str | None = None,
        additional_data: dict[str, Any] = {},
    ):
        if not code:
            code = "".join([str(secrets.randbelow(exclusive_upper_bound=10)) for _ in range(6)])
        additional_data["code"] = code
        token = TokenManager.generate_token(
            account=account, email=email, token_type="reset_password", additional_data=additional_data
        )
        return code, token

    @classmethod
    def generate_email_register_token(
        cls,
        email: str,
        code: str | None = None,
        additional_data: dict[str, Any] = {},
    ):
        if not code:
            code = "".join([str(secrets.randbelow(exclusive_upper_bound=10)) for _ in range(6)])
        additional_data["code"] = code
        token = TokenManager.generate_token(email=email, token_type="email_register", additional_data=additional_data)
        return code, token

    @classmethod
    def generate_change_email_token(
        cls,
        email: str,
        account: Account | None = None,
        code: str | None = None,
        old_email: str | None = None,
        additional_data: dict[str, Any] = {},
    ):
        if not code:
            code = "".join([str(secrets.randbelow(exclusive_upper_bound=10)) for _ in range(6)])
        additional_data["code"] = code
        additional_data["old_email"] = old_email
        token = TokenManager.generate_token(
            account=account, email=email, token_type="change_email", additional_data=additional_data
        )
        return code, token

    @classmethod
    def generate_owner_transfer_token(
        cls,
        email: str,
        account: Account | None = None,
        code: str | None = None,
        additional_data: dict[str, Any] = {},
    ):
        if not code:
            code = "".join([str(secrets.randbelow(exclusive_upper_bound=10)) for _ in range(6)])
        additional_data["code"] = code
        token = TokenManager.generate_token(
            account=account, email=email, token_type="owner_transfer", additional_data=additional_data
        )
        return code, token

    @classmethod
    def revoke_reset_password_token(cls, token: str):
        TokenManager.revoke_token(token, "reset_password")

    @classmethod
    def revoke_email_register_token(cls, token: str):
        TokenManager.revoke_token(token, "email_register")

    @classmethod
    def revoke_change_email_token(cls, token: str):
        TokenManager.revoke_token(token, "change_email")

    @classmethod
    def revoke_owner_transfer_token(cls, token: str):
        TokenManager.revoke_token(token, "owner_transfer")

    @classmethod
    def get_reset_password_data(cls, token: str) -> dict[str, Any] | None:
        return TokenManager.get_token_data(token, "reset_password")

    @classmethod
    def get_email_register_data(cls, token: str) -> dict[str, Any] | None:
        return TokenManager.get_token_data(token, "email_register")

    @classmethod
    def get_change_email_data(cls, token: str) -> dict[str, Any] | None:
        return TokenManager.get_token_data(token, "change_email")

    @classmethod
    def get_owner_transfer_data(cls, token: str) -> dict[str, Any] | None:
        return TokenManager.get_token_data(token, "owner_transfer")

    @classmethod
    def send_email_code_login_email(
        cls,
        account: Account | None = None,
        email: str | None = None,
        language: str = "en-US",
    ):
        email = account.email if account else email
        if email is None:
            raise ValueError("Email must be provided.")
        if cls.email_code_login_rate_limiter.is_rate_limited(email):
            from controllers.console.auth.error import EmailCodeLoginRateLimitExceededError

            raise EmailCodeLoginRateLimitExceededError(int(cls.email_code_login_rate_limiter.time_window / 60))

        code = "".join([str(secrets.randbelow(exclusive_upper_bound=10)) for _ in range(6)])
        token = TokenManager.generate_token(
            account=account, email=email, token_type="email_code_login", additional_data={"code": code}
        )
        send_email_code_login_mail_task.delay(
            language=language,
            to=account.email if account else email,
            code=code,
        )
        cls.email_code_login_rate_limiter.increment_rate_limit(email)
        return token

    @staticmethod
    def get_account_by_email_with_case_fallback(email: str, session: Session | None = None) -> Account | None:
        """
        Retrieve an account by email and fall back to the lowercase email if the original lookup fails.

        This keeps backward compatibility for older records that stored uppercase emails while the
        rest of the system gradually normalizes new inputs.
        """
        query_session = session or db.session
        account = query_session.execute(select(Account).filter_by(email=email)).scalar_one_or_none()
        if account or email == email.lower():
            return account

        return query_session.execute(select(Account).filter_by(email=email.lower())).scalar_one_or_none()

    @classmethod
    def get_email_code_login_data(cls, token: str) -> dict[str, Any] | None:
        return TokenManager.get_token_data(token, "email_code_login")

    @classmethod
    def revoke_email_code_login_token(cls, token: str):
        TokenManager.revoke_token(token, "email_code_login")

    @classmethod
    def get_user_through_email(cls, email: str):
        if dify_config.BILLING_ENABLED and BillingService.is_email_in_freeze(email):
            raise AccountRegisterError(
                description=(
                    "This email account has been deleted within the past "
                    "30 days and is temporarily unavailable for new account registration"
                )
            )

        account = db.session.query(Account).where(Account.email == email).first()
        if not account:
            return None

        if account.status == AccountStatus.BANNED:
            raise Unauthorized("Account is banned.")

        return account

    @classmethod
    def is_account_in_freeze(cls, email: str) -> bool:
        if dify_config.BILLING_ENABLED and BillingService.is_email_in_freeze(email):
            return True
        return False

    @staticmethod
    @redis_fallback(default_return=None)
    def add_login_error_rate_limit(email: str):
        key = f"login_error_rate_limit:{email}"
        count = redis_client.get(key)
        if count is None:
            count = 0
        count = int(count) + 1
        redis_client.setex(key, dify_config.LOGIN_LOCKOUT_DURATION, count)

    @staticmethod
    @redis_fallback(default_return=False)
    def is_login_error_rate_limit(email: str) -> bool:
        key = f"login_error_rate_limit:{email}"
        count = redis_client.get(key)
        if count is None:
            return False

        count = int(count)
        if count > AccountService.LOGIN_MAX_ERROR_LIMITS:
            return True
        return False

    @staticmethod
    @redis_fallback(default_return=None)
    def reset_login_error_rate_limit(email: str):
        key = f"login_error_rate_limit:{email}"
        redis_client.delete(key)

    @staticmethod
    @redis_fallback(default_return=None)
    def add_forgot_password_error_rate_limit(email: str):
        key = f"forgot_password_error_rate_limit:{email}"
        count = redis_client.get(key)
        if count is None:
            count = 0
        count = int(count) + 1
        redis_client.setex(key, dify_config.FORGOT_PASSWORD_LOCKOUT_DURATION, count)

    @staticmethod
    @redis_fallback(default_return=None)
    def add_email_register_error_rate_limit(email: str) -> None:
        key = f"email_register_error_rate_limit:{email}"
        count = redis_client.get(key)
        if count is None:
            count = 0
        count = int(count) + 1
        redis_client.setex(key, dify_config.EMAIL_REGISTER_LOCKOUT_DURATION, count)

    @staticmethod
    @redis_fallback(default_return=False)
    def is_forgot_password_error_rate_limit(email: str) -> bool:
        key = f"forgot_password_error_rate_limit:{email}"
        count = redis_client.get(key)
        if count is None:
            return False

        count = int(count)
        if count > AccountService.FORGOT_PASSWORD_MAX_ERROR_LIMITS:
            return True
        return False

    @staticmethod
    @redis_fallback(default_return=None)
    def reset_forgot_password_error_rate_limit(email: str):
        key = f"forgot_password_error_rate_limit:{email}"
        redis_client.delete(key)

    @staticmethod
    @redis_fallback(default_return=False)
    def is_email_register_error_rate_limit(email: str) -> bool:
        key = f"email_register_error_rate_limit:{email}"
        count = redis_client.get(key)
        if count is None:
            return False
        count = int(count)
        if count > AccountService.EMAIL_REGISTER_MAX_ERROR_LIMITS:
            return True
        return False

    @staticmethod
    @redis_fallback(default_return=None)
    def reset_email_register_error_rate_limit(email: str):
        key = f"email_register_error_rate_limit:{email}"
        redis_client.delete(key)

    @staticmethod
    @redis_fallback(default_return=None)
    def add_change_email_error_rate_limit(email: str):
        key = f"change_email_error_rate_limit:{email}"
        count = redis_client.get(key)
        if count is None:
            count = 0
        count = int(count) + 1
        redis_client.setex(key, dify_config.CHANGE_EMAIL_LOCKOUT_DURATION, count)

    @staticmethod
    @redis_fallback(default_return=False)
    def is_change_email_error_rate_limit(email: str) -> bool:
        key = f"change_email_error_rate_limit:{email}"
        count = redis_client.get(key)
        if count is None:
            return False
        count = int(count)
        if count > AccountService.CHANGE_EMAIL_MAX_ERROR_LIMITS:
            return True
        return False

    @staticmethod
    @redis_fallback(default_return=None)
    def reset_change_email_error_rate_limit(email: str):
        key = f"change_email_error_rate_limit:{email}"
        redis_client.delete(key)

    @staticmethod
    @redis_fallback(default_return=None)
    def add_owner_transfer_error_rate_limit(email: str):
        key = f"owner_transfer_error_rate_limit:{email}"
        count = redis_client.get(key)
        if count is None:
            count = 0
        count = int(count) + 1
        redis_client.setex(key, dify_config.OWNER_TRANSFER_LOCKOUT_DURATION, count)

    @staticmethod
    @redis_fallback(default_return=False)
    def is_owner_transfer_error_rate_limit(email: str) -> bool:
        key = f"owner_transfer_error_rate_limit:{email}"
        count = redis_client.get(key)
        if count is None:
            return False
        count = int(count)
        if count > AccountService.OWNER_TRANSFER_MAX_ERROR_LIMITS:
            return True
        return False

    @staticmethod
    @redis_fallback(default_return=None)
    def reset_owner_transfer_error_rate_limit(email: str):
        key = f"owner_transfer_error_rate_limit:{email}"
        redis_client.delete(key)

    @staticmethod
    @redis_fallback(default_return=False)
    def is_email_send_ip_limit(ip_address: str):
        minute_key = f"email_send_ip_limit_minute:{ip_address}"
        freeze_key = f"email_send_ip_limit_freeze:{ip_address}"
        hour_limit_key = f"email_send_ip_limit_hour:{ip_address}"

        # check ip is frozen
        if redis_client.get(freeze_key):
            return True

        # check current minute count
        current_minute_count = redis_client.get(minute_key)
        if current_minute_count is None:
            current_minute_count = 0
        current_minute_count = int(current_minute_count)

        # check current hour count
        if current_minute_count > dify_config.EMAIL_SEND_IP_LIMIT_PER_MINUTE:
            hour_limit_count = redis_client.get(hour_limit_key)
            if hour_limit_count is None:
                hour_limit_count = 0
            hour_limit_count = int(hour_limit_count)

            if hour_limit_count >= 1:
                redis_client.setex(freeze_key, 60 * 60, 1)
                return True
            else:
                redis_client.setex(hour_limit_key, 60 * 10, hour_limit_count + 1)  # first time limit 10 minutes

            # add hour limit count
            redis_client.incr(hour_limit_key)
            redis_client.expire(hour_limit_key, 60 * 60)

            return True

        redis_client.setex(minute_key, 60, current_minute_count + 1)
        redis_client.expire(minute_key, 60)

        return False

    @staticmethod
    def check_email_unique(email: str) -> bool:
        return db.session.query(Account).filter_by(email=email).first() is None


class TenantService:
    @staticmethod
    def create_tenant(name: str, is_setup: bool | None = False, is_from_dashboard: bool | None = False) -> Tenant:
        """Create tenant"""
        if (
            not FeatureService.get_system_features().is_allow_create_workspace
            and not is_setup
            and not is_from_dashboard
        ):
            from controllers.console.error import NotAllowedCreateWorkspace

            raise NotAllowedCreateWorkspace()
        tenant = Tenant(name=name)

        db.session.add(tenant)
        db.session.commit()

        plugin_upgrade_strategy = TenantPluginAutoUpgradeStrategy(
            tenant_id=tenant.id,
            strategy_setting=TenantPluginAutoUpgradeStrategy.StrategySetting.FIX_ONLY,
            upgrade_time_of_day=0,
            upgrade_mode=TenantPluginAutoUpgradeStrategy.UpgradeMode.EXCLUDE,
            exclude_plugins=[],
            include_plugins=[],
        )
        db.session.add(plugin_upgrade_strategy)
        db.session.commit()

        tenant.encrypt_public_key = generate_key_pair(tenant.id)
        db.session.commit()

        from services.credit_pool_service import CreditPoolService

        CreditPoolService.create_default_pool(tenant.id)

        return tenant

    @staticmethod
    def create_owner_tenant_if_not_exist(account: Account, name: str | None = None, is_setup: bool | None = False):
        """Check if user have a workspace or not"""
        available_ta = (
            db.session.query(TenantAccountJoin)
            .filter_by(account_id=account.id)
            .order_by(TenantAccountJoin.id.asc())
            .first()
        )

        if available_ta:
            return

        """Create owner tenant if not exist"""
        if not FeatureService.get_system_features().is_allow_create_workspace and not is_setup:
            raise WorkSpaceNotAllowedCreateError()

        workspaces = FeatureService.get_system_features().license.workspaces
        if not workspaces.is_available():
            raise WorkspacesLimitExceededError()

        if name:
            tenant = TenantService.create_tenant(name=name, is_setup=is_setup)
        else:
            tenant = TenantService.create_tenant(name=f"{account.name}'s Workspace", is_setup=is_setup)
        TenantService.create_tenant_member(tenant, account, role="owner")
        account.current_tenant = tenant
        db.session.commit()
        tenant_was_created.send(tenant)

    @staticmethod
    def create_tenant_member(tenant: Tenant, account: Account, role: str = "normal") -> TenantAccountJoin:
        """Create tenant member"""
        if role == TenantAccountRole.OWNER:
            if TenantService.has_roles(tenant, [TenantAccountRole.OWNER]):
                logger.error("Tenant %s has already an owner.", tenant.id)
                raise Exception("Tenant already has an owner.")

        ta = db.session.query(TenantAccountJoin).filter_by(tenant_id=tenant.id, account_id=account.id).first()
        if ta:
            ta.role = role
        else:
            ta = TenantAccountJoin(tenant_id=tenant.id, account_id=account.id, role=role)
            db.session.add(ta)

        db.session.commit()
        if dify_config.BILLING_ENABLED:
            BillingService.clean_billing_info_cache(tenant.id)
        return ta

    @staticmethod
    def get_join_tenants(account: Account) -> list[Tenant]:
        """Get account join tenants"""
        return (
            db.session.query(Tenant)
            .join(TenantAccountJoin, Tenant.id == TenantAccountJoin.tenant_id)
            .where(TenantAccountJoin.account_id == account.id, Tenant.status == TenantStatus.NORMAL)
            .all()
        )

    @staticmethod
    def get_current_tenant_by_account(account: Account):
        """Get tenant by account and add the role"""
        tenant = account.current_tenant
        if not tenant:
            raise TenantNotFoundError("Tenant not found.")

        ta = db.session.query(TenantAccountJoin).filter_by(tenant_id=tenant.id, account_id=account.id).first()
        if ta:
            tenant.role = ta.role
        else:
            raise TenantNotFoundError("Tenant not found for the account.")
        return tenant

    @staticmethod
    def switch_tenant(account: Account, tenant_id: str | None = None):
        """Switch the current workspace for the account"""

        # Ensure tenant_id is provided
        if tenant_id is None:
            raise ValueError("Tenant ID must be provided.")

        tenant_account_join = (
            db.session.query(TenantAccountJoin)
            .join(Tenant, TenantAccountJoin.tenant_id == Tenant.id)
            .where(
                TenantAccountJoin.account_id == account.id,
                TenantAccountJoin.tenant_id == tenant_id,
                Tenant.status == TenantStatus.NORMAL,
            )
            .first()
        )

        if not tenant_account_join:
            raise AccountNotLinkTenantError("Tenant not found or account is not a member of the tenant.")
        else:
            db.session.query(TenantAccountJoin).where(
                TenantAccountJoin.account_id == account.id, TenantAccountJoin.tenant_id != tenant_id
            ).update({"current": False})
            tenant_account_join.current = True
            # Set the current tenant for the account
            account.set_tenant_id(tenant_account_join.tenant_id)
            db.session.commit()

    @staticmethod
    def get_tenant_members(tenant: Tenant) -> list[Account]:
        """Get tenant members"""
        query = (
            db.session.query(Account, TenantAccountJoin.role)
            .select_from(Account)
            .join(TenantAccountJoin, Account.id == TenantAccountJoin.account_id)
            .where(TenantAccountJoin.tenant_id == tenant.id)
        )

        # Initialize an empty list to store the updated accounts
        updated_accounts = []

        for account, role in query:
            account.role = role
            updated_accounts.append(account)

        return updated_accounts

    @staticmethod
    def get_dataset_operator_members(tenant: Tenant) -> list[Account]:
        """Get dataset admin members"""
        query = (
            db.session.query(Account, TenantAccountJoin.role)
            .select_from(Account)
            .join(TenantAccountJoin, Account.id == TenantAccountJoin.account_id)
            .where(TenantAccountJoin.tenant_id == tenant.id)
            .where(TenantAccountJoin.role == "dataset_operator")
        )

        # Initialize an empty list to store the updated accounts
        updated_accounts = []

        for account, role in query:
            account.role = role
            updated_accounts.append(account)

        return updated_accounts

    @staticmethod
    def has_roles(tenant: Tenant, roles: list[TenantAccountRole]) -> bool:
        """Check if user has any of the given roles for a tenant"""
        if not all(isinstance(role, TenantAccountRole) for role in roles):
            raise ValueError("all roles must be TenantAccountRole")

        return (
            db.session.query(TenantAccountJoin)
            .where(TenantAccountJoin.tenant_id == tenant.id, TenantAccountJoin.role.in_([role.value for role in roles]))
            .first()
            is not None
        )

    @staticmethod
    def get_user_role(account: Account, tenant: Tenant) -> TenantAccountRole | None:
        """Get the role of the current account for a given tenant"""
        join = (
            db.session.query(TenantAccountJoin)
            .where(TenantAccountJoin.tenant_id == tenant.id, TenantAccountJoin.account_id == account.id)
            .first()
        )
        return TenantAccountRole(join.role) if join else None

    @staticmethod
    def get_tenant_count() -> int:
        """Get tenant count"""
        return cast(int, db.session.query(func.count(Tenant.id)).scalar())

    @staticmethod
    def check_member_permission(tenant: Tenant, operator: Account, member: Account | None, action: str):
        """Check member permission"""
        perms = {
            "add": [TenantAccountRole.OWNER, TenantAccountRole.ADMIN],
            "remove": [TenantAccountRole.OWNER, TenantAccountRole.ADMIN],
            "update": [TenantAccountRole.OWNER, TenantAccountRole.ADMIN],
        }
        if action not in {"add", "remove", "update"}:
            raise InvalidActionError("Invalid action.")

        if member:
            if operator.id == member.id:
                raise CannotOperateSelfError("Cannot operate self.")

        ta_operator = db.session.query(TenantAccountJoin).filter_by(tenant_id=tenant.id, account_id=operator.id).first()

        if not ta_operator or ta_operator.role not in perms[action]:
            raise NoPermissionError(f"No permission to {action} member.")

        if member and action in {"remove", "update"}:
            ta_member = db.session.query(TenantAccountJoin).filter_by(tenant_id=tenant.id, account_id=member.id).first()
            if ta_member and ta_member.role == TenantAccountRole.OWNER.value and ta_operator.role != TenantAccountRole.OWNER:
                raise NoPermissionError(f"No permission to {action} owner.")

    @staticmethod
    def remove_member_from_tenant(tenant: Tenant, account: Account, operator: Account):
        """Remove member from tenant"""
        if operator.id == account.id:
            raise CannotOperateSelfError("Cannot operate self.")

        TenantService.check_member_permission(tenant, operator, account, "remove")

        ta = db.session.query(TenantAccountJoin).filter_by(tenant_id=tenant.id, account_id=account.id).first()
        if not ta:
            raise MemberNotInTenantError("Member not in tenant.")

        db.session.delete(ta)
        db.session.commit()

        if dify_config.BILLING_ENABLED:
            BillingService.clean_billing_info_cache(tenant.id)

    @staticmethod
    def update_member_role(tenant: Tenant, member: Account, new_role: str, operator: Account):
        """Update member role"""
        TenantService.check_member_permission(tenant, operator, member, "update")

        target_member_join = (
            db.session.query(TenantAccountJoin).filter_by(tenant_id=tenant.id, account_id=member.id).first()
        )

        if not target_member_join:
            raise MemberNotInTenantError("Member not in tenant.")

        if target_member_join.role == new_role:
            raise RoleAlreadyAssignedError("The provided role is already assigned to the member.")

        if new_role == "owner":
            # Find the current owner and change their role to 'admin'
            current_owner_join = (
                db.session.query(TenantAccountJoin).filter_by(tenant_id=tenant.id, role="owner").first()
            )
            if current_owner_join:
                current_owner_join.role = "admin"

        # Update the role of the target member
        target_member_join.role = new_role
        db.session.commit()

    @staticmethod
    def get_custom_config(tenant_id: str):
        tenant = db.get_or_404(Tenant, tenant_id)

        return tenant.custom_config_dict

    @staticmethod
    def is_owner(account: Account, tenant: Tenant) -> bool:
        return TenantService.get_user_role(account, tenant) == TenantAccountRole.OWNER

    @staticmethod
    def is_member(account: Account, tenant: Tenant) -> bool:
        """Check if the account is a member of the tenant"""
        return TenantService.get_user_role(account, tenant) is not None


class AccountInviteCodeService:
    INVITE_CODE_LIMIT = 5
    INVITE_CODE_ALPHABET = "23456789ABCDEFGHJKLMNPQRSTUVWXYZ"

    @classmethod
    def normalize_code(cls, code: str | None) -> str:
        return (code or "").strip().replace("-", "").upper()

    @classmethod
    def generate_code(cls) -> str:
        raw_code = "".join(secrets.choice(cls.INVITE_CODE_ALPHABET) for _ in range(12))
        return f"{raw_code[:4]}-{raw_code[4:8]}-{raw_code[8:]}"

    @classmethod
    def ensure_invite_codes(cls, account: Account) -> list[AccountInviteCode]:
        existing_codes = (
            db.session.query(AccountInviteCode)
            .where(AccountInviteCode.owner_account_id == account.id)
            .order_by(AccountInviteCode.created_at.asc())
            .all()
        )

        missing_count = cls.INVITE_CODE_LIMIT - len(existing_codes)
        for _ in range(max(missing_count, 0)):
            invite_code = AccountInviteCode(owner_account_id=account.id, code=cls._generate_unique_code())
            db.session.add(invite_code)
            existing_codes.append(invite_code)

        if missing_count > 0:
            db.session.commit()

        return existing_codes

    @classmethod
    def consume_invite_code(cls, code: str, used_by_account: Account) -> AccountInviteCode:
        normalized_code = cls.normalize_code(code)
        if not normalized_code:
            raise AccountRegisterError("Invitation code is required.")

        invite_code = (
            db.session.query(AccountInviteCode)
            .where(
                func.replace(AccountInviteCode.code, "-", "") == normalized_code,
                AccountInviteCode.status == "unused",
            )
            .with_for_update()
            .first()
        )
        if not invite_code:
            raise AccountRegisterError("Invitation code is invalid or has already been used.")

        invite_code.status = "used"
        invite_code.used_at = naive_utc_now()
        invite_code.used_by_account_id = used_by_account.id
        db.session.add(invite_code)
        AccountPointService.award_invite_used_points(invite_code, used_by_account)
        db.session.commit()
        return invite_code

    @classmethod
    def is_invite_code_available(cls, code: str | None) -> bool:
        normalized_code = cls.normalize_code(code)
        if not normalized_code:
            return False
        return (
            db.session.query(AccountInviteCode)
            .where(
                func.replace(AccountInviteCode.code, "-", "") == normalized_code,
                AccountInviteCode.status == "unused",
            )
            .first()
            is not None
        )

    @classmethod
    def _generate_unique_code(cls) -> str:
        for _ in range(20):
            code = cls.generate_code()
            exists = db.session.query(AccountInviteCode).where(AccountInviteCode.code == code).first()
            if not exists:
                return code
        raise AccountRegisterError("Failed to generate invitation code.")


class AccountPointService:
    INVITE_USED_POINTS = 100
    DAILY_CHECK_IN_POINTS = 3
    WEEKLY_CHECK_IN_BONUS_POINTS = 10
    MONTHLY_CHECK_IN_CAP = 150
    CHECK_IN_POINTS_VALID_DAYS = 90
    INVITE_POINTS_VALID_DAYS = 180
    REWARDS = [
        {
            "id": "tokens_10k",
            "name": "10,000 Tokens",
            "description": "兑换后可用于模型调用额度发放。",
            "points": 100,
            "benefit_type": "token",
            "benefit_amount": 10000,
        },
        {
            "id": "tokens_50k",
            "name": "50,000 Tokens",
            "description": "适合频繁使用对话和智能体的用户。",
            "points": 450,
            "benefit_type": "token",
            "benefit_amount": 50000,
        },
        {
            "id": "priority_support",
            "name": "优先支持权益",
            "description": "提交问题时进入优先处理队列。",
            "points": 300,
            "benefit_type": "service",
            "benefit_amount": 1,
        },
    ]

    @classmethod
    def _month_range(cls, now: datetime | None = None) -> tuple[datetime, datetime]:
        now = now or naive_utc_now()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        if month_start.month == 12:
            next_month = month_start.replace(year=month_start.year + 1, month=1)
        else:
            next_month = month_start.replace(month=month_start.month + 1)
        return month_start, next_month

    @classmethod
    def _day_range(cls, now: datetime | None = None) -> tuple[datetime, datetime]:
        now = now or naive_utc_now()
        day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        return day_start, day_start + timedelta(days=1)

    @classmethod
    def _get_reward(cls, reward_id: str) -> dict[str, Any] | None:
        return next((item for item in cls.REWARDS if item["id"] == reward_id), None)

    @classmethod
    def _add_earn_transaction(
        cls,
        *,
        account_id: str,
        points: int,
        source: str,
        description: str,
        source_id: str | None = None,
        valid_days: int,
    ) -> AccountPointTransaction:
        expires_at = naive_utc_now() + timedelta(days=valid_days)
        transaction = AccountPointTransaction(
            account_id=account_id,
            points=points,
            type="earn",
            source=source,
            source_id=source_id,
            description=description,
            remaining_points=points,
            expires_at=expires_at,
        )
        db.session.add(transaction)
        return transaction

    @classmethod
    def award_invite_used_points(cls, invite_code: AccountInviteCode, used_by_account: Account) -> None:
        if invite_code.owner_account_id == used_by_account.id:
            return

        existing = (
            db.session.query(AccountPointTransaction)
            .where(
                AccountPointTransaction.account_id == invite_code.owner_account_id,
                AccountPointTransaction.source == "invite_code",
                AccountPointTransaction.source_id == invite_code.id,
            )
            .first()
        )
        if existing:
            return

        cls._add_earn_transaction(
            account_id=invite_code.owner_account_id,
            points=cls.INVITE_USED_POINTS,
            source="invite_code",
            source_id=invite_code.id,
            description="邀请码被成功使用",
            valid_days=cls.INVITE_POINTS_VALID_DAYS,
        )

    @classmethod
    def get_balance(cls, account: Account) -> int:
        now = naive_utc_now()
        return (
            db.session.query(func.coalesce(func.sum(AccountPointTransaction.remaining_points), 0))
            .where(
                AccountPointTransaction.account_id == account.id,
                AccountPointTransaction.type == "earn",
                AccountPointTransaction.remaining_points > 0,
                AccountPointTransaction.expires_at > now,
            )
            .scalar()
            or 0
        )

    @classmethod
    def _monthly_check_in_points(cls, account: Account, now: datetime | None = None) -> int:
        month_start, next_month = cls._month_range(now)
        return (
            db.session.query(func.coalesce(func.sum(AccountPointTransaction.points), 0))
            .where(
                AccountPointTransaction.account_id == account.id,
                AccountPointTransaction.source == "daily_check_in",
                AccountPointTransaction.created_at >= month_start,
                AccountPointTransaction.created_at < next_month,
            )
            .scalar()
            or 0
        )

    @classmethod
    def _checked_today(cls, account: Account, now: datetime | None = None) -> bool:
        day_start, next_day = cls._day_range(now)
        return (
            db.session.query(AccountPointTransaction.id)
            .where(
                AccountPointTransaction.account_id == account.id,
                AccountPointTransaction.source == "daily_check_in",
                AccountPointTransaction.created_at >= day_start,
                AccountPointTransaction.created_at < next_day,
            )
            .first()
            is not None
        )

    @classmethod
    def _check_in_streak_days(cls, account: Account, now: datetime | None = None) -> int:
        now = now or naive_utc_now()
        rows = (
            db.session.query(AccountPointTransaction.created_at)
            .where(
                AccountPointTransaction.account_id == account.id,
                AccountPointTransaction.source == "daily_check_in",
            )
            .order_by(AccountPointTransaction.created_at.desc())
            .limit(60)
            .all()
        )
        checked_dates = {row.created_at.date() for row in rows if row.created_at}
        cursor = now.date()
        if cursor not in checked_dates:
            cursor = cursor - timedelta(days=1)

        streak = 0
        while cursor in checked_dates:
            streak += 1
            cursor = cursor - timedelta(days=1)
        return streak

    @classmethod
    def get_check_in_state(cls, account: Account) -> dict[str, Any]:
        now = naive_utc_now()
        monthly_points = cls._monthly_check_in_points(account, now)
        checked_today = cls._checked_today(account, now)
        streak_days = cls._check_in_streak_days(account, now)
        next_bonus_in_days = 7 - (streak_days % 7)
        if next_bonus_in_days == 7 and checked_today:
            next_bonus_in_days = 7
        today_points = 0
        if not checked_today:
            planned_points = cls.DAILY_CHECK_IN_POINTS
            if (streak_days + 1) % 7 == 0:
                planned_points += cls.WEEKLY_CHECK_IN_BONUS_POINTS
            today_points = max(0, min(planned_points, cls.MONTHLY_CHECK_IN_CAP - monthly_points))

        return {
            "checked_today": checked_today,
            "today_points": today_points,
            "daily_points": cls.DAILY_CHECK_IN_POINTS,
            "weekly_bonus_points": cls.WEEKLY_CHECK_IN_BONUS_POINTS,
            "streak_days": streak_days,
            "monthly_check_in_points": monthly_points,
            "monthly_check_in_cap": cls.MONTHLY_CHECK_IN_CAP,
            "next_bonus_in_days": next_bonus_in_days,
            "valid_days": cls.CHECK_IN_POINTS_VALID_DAYS,
        }

    @classmethod
    def get_expiration_state(cls, account: Account) -> dict[str, Any]:
        now = naive_utc_now()
        month_start, next_month = cls._month_range(now)
        expiring_this_month = (
            db.session.query(func.coalesce(func.sum(AccountPointTransaction.remaining_points), 0))
            .where(
                AccountPointTransaction.account_id == account.id,
                AccountPointTransaction.type == "earn",
                AccountPointTransaction.remaining_points > 0,
                AccountPointTransaction.expires_at >= month_start,
                AccountPointTransaction.expires_at < next_month,
            )
            .scalar()
            or 0
        )
        nearest_expiration_at = (
            db.session.query(func.min(AccountPointTransaction.expires_at))
            .where(
                AccountPointTransaction.account_id == account.id,
                AccountPointTransaction.type == "earn",
                AccountPointTransaction.remaining_points > 0,
                AccountPointTransaction.expires_at > now,
            )
            .scalar()
        )
        return {
            "expiring_points_this_month": expiring_this_month,
            "nearest_expiration_at": int(nearest_expiration_at.timestamp()) if nearest_expiration_at else None,
        }

    @classmethod
    def get_monthly_calendar(cls, account: Account) -> dict[str, Any]:
        now = naive_utc_now()
        month_start, next_month = cls._month_range(now)
        rows = (
            db.session.query(AccountPointTransaction)
            .where(
                AccountPointTransaction.account_id == account.id,
                AccountPointTransaction.created_at >= month_start,
                AccountPointTransaction.created_at < next_month,
            )
            .order_by(AccountPointTransaction.created_at.asc())
            .all()
        )

        day_count = (next_month - month_start).days
        days: dict[str, dict[str, Any]] = {}
        for offset in range(day_count):
            day = month_start + timedelta(days=offset)
            date_key = day.strftime("%Y-%m-%d")
            days[date_key] = {
                "date": date_key,
                "day": day.day,
                "is_today": date_key == now.strftime("%Y-%m-%d"),
                "is_checked_in": False,
                "earned_points": 0,
                "spent_points": 0,
                "expired_points": 0,
                "net_points": 0,
                "transactions": [],
            }

        for item in rows:
            date_key = item.created_at.strftime("%Y-%m-%d")
            day_item = days.get(date_key)
            if not day_item:
                continue

            if item.source == "daily_check_in" and item.points > 0:
                day_item["is_checked_in"] = True
            if item.points > 0:
                day_item["earned_points"] += item.points
            elif item.type == "expire":
                day_item["expired_points"] += abs(item.points)
            else:
                day_item["spent_points"] += abs(item.points)
            day_item["net_points"] += item.points
            day_item["transactions"].append(
                {
                    "id": item.id,
                    "points": item.points,
                    "type": item.type,
                    "source": item.source,
                    "description": item.description,
                    "created_at": int(item.created_at.timestamp()) if item.created_at else None,
                }
            )

        return {
            "year": month_start.year,
            "month": month_start.month,
            "month_start_weekday": month_start.weekday(),
            "today": now.strftime("%Y-%m-%d"),
            "days": list(days.values()),
        }

    @classmethod
    def check_in(cls, account: Account) -> dict[str, Any]:
        now = naive_utc_now()
        if cls._checked_today(account, now):
            raise InvalidActionError("Already checked in today.")

        state = cls.get_check_in_state(account)
        awarded_points = int(state["today_points"])
        if awarded_points <= 0:
            raise InvalidActionError("Monthly check-in point cap reached.")

        source_id = now.strftime("%Y-%m-%d")
        description = "每日签到"
        if awarded_points > cls.DAILY_CHECK_IN_POINTS:
            description = "每日签到（含连续 7 天奖励）"

        cls._add_earn_transaction(
            account_id=account.id,
            points=awarded_points,
            source="daily_check_in",
            source_id=source_id,
            description=description,
            valid_days=cls.CHECK_IN_POINTS_VALID_DAYS,
        )
        db.session.commit()
        return cls.get_summary(account)

    @classmethod
    def get_summary(cls, account: Account) -> dict[str, Any]:
        transactions = (
            db.session.query(AccountPointTransaction)
            .where(AccountPointTransaction.account_id == account.id)
            .order_by(AccountPointTransaction.created_at.desc())
            .limit(50)
            .all()
        )
        redemptions = (
            db.session.query(AccountPointRedemption)
            .where(AccountPointRedemption.account_id == account.id)
            .order_by(AccountPointRedemption.created_at.desc())
            .limit(20)
            .all()
        )
        return {
            "balance": cls.get_balance(account),
            "invite_reward_points": cls.INVITE_USED_POINTS,
            "rewards": cls.REWARDS,
            "check_in": cls.get_check_in_state(account),
            "expiration": cls.get_expiration_state(account),
            "calendar": cls.get_monthly_calendar(account),
            "transactions": [
                {
                    "id": item.id,
                    "points": item.points,
                    "remaining_points": item.remaining_points,
                    "expires_at": int(item.expires_at.timestamp()) if item.expires_at else None,
                    "type": item.type,
                    "source": item.source,
                    "description": item.description,
                    "created_at": int(item.created_at.timestamp()) if item.created_at else None,
                }
                for item in transactions
            ],
            "redemptions": [
                {
                    "id": item.id,
                    "reward_id": item.reward_id,
                    "reward_name": item.reward_name,
                    "points": item.points,
                    "status": item.status,
                    "created_at": int(item.created_at.timestamp()) if item.created_at else None,
                }
                for item in redemptions
            ],
        }

    @classmethod
    def redeem_reward(cls, account: Account, reward_id: str) -> AccountPointRedemption:
        reward = cls._get_reward(reward_id)
        if not reward:
            raise InvalidActionError("Reward is not available.")

        required_points = int(reward["points"])
        if cls.get_balance(account) < required_points:
            raise InvalidActionError("Insufficient points.")

        now = naive_utc_now()
        spendable_transactions = (
            db.session.query(AccountPointTransaction)
            .where(
                AccountPointTransaction.account_id == account.id,
                AccountPointTransaction.type == "earn",
                AccountPointTransaction.remaining_points > 0,
                AccountPointTransaction.expires_at > now,
            )
            .order_by(AccountPointTransaction.expires_at.asc(), AccountPointTransaction.created_at.asc())
            .with_for_update()
            .all()
        )
        remaining_to_spend = required_points
        for transaction in spendable_transactions:
            if remaining_to_spend <= 0:
                break
            spend = min(transaction.remaining_points, remaining_to_spend)
            transaction.remaining_points -= spend
            remaining_to_spend -= spend

        if remaining_to_spend > 0:
            raise InvalidActionError("Insufficient points.")

        redemption = AccountPointRedemption(
            account_id=account.id,
            reward_id=str(reward["id"]),
            reward_name=str(reward["name"]),
            points=required_points,
            status="pending_activation",
        )
        db.session.add(redemption)
        db.session.flush()
        db.session.add(
            AccountPointTransaction(
                account_id=account.id,
                points=-required_points,
                type="redeem",
                source="redemption",
                source_id=redemption.id,
                description=f"兑换 {reward['name']}",
                remaining_points=0,
            )
        )
        db.session.commit()
        return redemption

    @classmethod
    def settle_expired_points(cls, now: datetime | None = None) -> dict[str, int]:
        now = now or naive_utc_now()
        expired_transactions = (
            db.session.query(AccountPointTransaction)
            .where(
                AccountPointTransaction.type == "earn",
                AccountPointTransaction.remaining_points > 0,
                AccountPointTransaction.expires_at <= now,
            )
            .order_by(AccountPointTransaction.expires_at.asc(), AccountPointTransaction.created_at.asc())
            .all()
        )

        expired_points = 0
        for transaction in expired_transactions:
            points = transaction.remaining_points
            if points <= 0:
                continue
            transaction.remaining_points = 0
            expired_points += points
            db.session.add(
                AccountPointTransaction(
                    account_id=transaction.account_id,
                    points=-points,
                    type="expire",
                    source="expiration",
                    source_id=transaction.id,
                    description="积分过期清算",
                    remaining_points=0,
                )
            )

        db.session.commit()
        return {"transactions": len(expired_transactions), "points": expired_points}


class RegisterService:
    @classmethod
    def _get_invitation_token_key(cls, token: str) -> str:
        return f"member_invite:token:{token}"

    @classmethod
    def setup(cls, email: str, name: str, password: str, ip_address: str, language: str | None):
        """
        Setup dify

        :param email: email
        :param name: username
        :param password: password
        :param ip_address: ip address
        :param language: language
        """
        try:
            account = AccountService.create_account(
                email=email,
                name=name,
                interface_language=get_valid_language(language),
                password=password,
                is_setup=True,
            )

            account.last_login_ip = ip_address
            account.initialized_at = naive_utc_now()

            TenantService.create_owner_tenant_if_not_exist(account=account, is_setup=True)
            AccountInviteCodeService.ensure_invite_codes(account)

            dify_setup = DifySetup(version=dify_config.project.version)
            db.session.add(dify_setup)
            db.session.commit()
        except Exception as e:
            db.session.query(DifySetup).delete()
            db.session.query(TenantAccountJoin).delete()
            db.session.query(Account).delete()
            db.session.query(Tenant).delete()
            db.session.commit()

            logger.exception("Setup account failed, email: %s, name: %s", email, name)
            raise ValueError(f"Setup failed: {e}")

    @classmethod
    def register(
        cls,
        email,
        name,
        password: str | None = None,
        open_id: str | None = None,
        provider: str | None = None,
        language: str | None = None,
        status: AccountStatus | None = None,
        is_setup: bool | None = False,
        create_workspace_required: bool | None = True,
    ) -> Account:
        db.session.begin_nested()
        """Register account"""
        try:
            account = AccountService.create_account(
                email=email,
                name=name,
                interface_language=get_valid_language(language),
                password=password,
                is_setup=is_setup,
            )
            account.status = status or AccountStatus.PENDING
            account.initialized_at = naive_utc_now()

            if open_id is not None and provider is not None:
                AccountService.link_account_integrate(provider, open_id, account)

            if (
                FeatureService.get_system_features().is_allow_create_workspace
                and create_workspace_required
                and FeatureService.get_system_features().license.workspaces.is_available()
            ):
                tenant = TenantService.create_tenant(f"{account.name}'s Workspace")
                TenantService.create_tenant_member(tenant, account, role="owner")
                account.current_tenant = tenant
                tenant_was_created.send(tenant)

            db.session.commit()
        except WorkSpaceNotAllowedCreateError:
            db.session.rollback()
            logger.exception("Register failed")
            raise AccountRegisterError("Workspace is not allowed to create.")
        except AccountRegisterError as are:
            db.session.rollback()
            logger.exception("Register failed")
            raise are
        except Exception as e:
            db.session.rollback()
            logger.exception("Register failed")
            raise AccountRegisterError(f"Registration failed: {e}") from e

        return account

    @classmethod
    def invite_new_member(
        cls, tenant: Tenant, email: str, language: str | None, role: str = "normal", inviter: Account | None = None
    ) -> str:
        if not inviter:
            raise ValueError("Inviter is required")

        normalized_email = email.lower()

        """Invite new member"""
        # Check workspace permission for member invitations
        from libs.workspace_permission import check_workspace_member_invite_permission

        check_workspace_member_invite_permission(tenant.id)

        with Session(db.engine) as session:
            account = AccountService.get_account_by_email_with_case_fallback(email, session=session)

        if not account:
            TenantService.check_member_permission(tenant, inviter, None, "add")
            name = normalized_email.split("@")[0]

            account = cls.register(
                email=normalized_email,
                name=name,
                language=language,
                status=AccountStatus.PENDING,
                is_setup=True,
            )
            # Create new tenant member for invited tenant
            TenantService.create_tenant_member(tenant, account, role)
            TenantService.switch_tenant(account, tenant.id)
        else:
            TenantService.check_member_permission(tenant, inviter, account, "add")
            ta = db.session.query(TenantAccountJoin).filter_by(tenant_id=tenant.id, account_id=account.id).first()

            if not ta:
                TenantService.create_tenant_member(tenant, account, role)

            # Support resend invitation email when the account is pending status
            if account.status != AccountStatus.PENDING:
                raise AccountAlreadyInTenantError("Account already in tenant.")

        token = cls.generate_invite_token(tenant, account)
        language = account.interface_language or "en-US"

        # send email
        send_invite_member_mail_task.delay(
            language=language,
            to=account.email,
            token=token,
            inviter_name=inviter.name if inviter else "Dify",
            workspace_name=tenant.name,
        )

        return token

    @classmethod
    def generate_invite_token(cls, tenant: Tenant, account: Account) -> str:
        token = str(uuid.uuid4())
        invitation_data = {
            "account_id": account.id,
            "email": account.email,
            "workspace_id": tenant.id,
        }
        expiry_hours = dify_config.INVITE_EXPIRY_HOURS
        redis_client.setex(cls._get_invitation_token_key(token), expiry_hours * 60 * 60, json.dumps(invitation_data))
        return token

    @classmethod
    def is_valid_invite_token(cls, token: str) -> bool:
        data = redis_client.get(cls._get_invitation_token_key(token))
        return data is not None

    @classmethod
    def revoke_token(cls, workspace_id: str | None, email: str | None, token: str):
        if workspace_id and email:
            email_hash = sha256(email.encode()).hexdigest()
            cache_key = f"member_invite_token:{workspace_id}, {email_hash}:{token}"
            redis_client.delete(cache_key)
        else:
            redis_client.delete(cls._get_invitation_token_key(token))

    @classmethod
    def get_invitation_if_token_valid(
        cls, workspace_id: str | None, email: str | None, token: str
    ) -> dict[str, Any] | None:
        invitation_data = cls.get_invitation_by_token(token, workspace_id, email)
        if not invitation_data:
            return None

        tenant = (
            db.session.query(Tenant)
            .where(Tenant.id == invitation_data["workspace_id"], Tenant.status == "normal")
            .first()
        )

        if not tenant:
            return None

        tenant_account = (
            db.session.query(Account, TenantAccountJoin.role)
            .join(TenantAccountJoin, Account.id == TenantAccountJoin.account_id)
            .where(Account.email == invitation_data["email"], TenantAccountJoin.tenant_id == tenant.id)
            .first()
        )

        if not tenant_account:
            return None

        account = tenant_account[0]
        if not account:
            return None

        if invitation_data["account_id"] != str(account.id):
            return None

        return {
            "account": account,
            "data": invitation_data,
            "tenant": tenant,
        }

    @classmethod
    def get_invitation_by_token(
        cls, token: str, workspace_id: str | None = None, email: str | None = None
    ) -> dict[str, str] | None:
        if workspace_id is not None and email is not None:
            email_hash = sha256(email.encode()).hexdigest()
            cache_key = f"member_invite_token:{workspace_id}, {email_hash}:{token}"
            account_id = redis_client.get(cache_key)

            if not account_id:
                return None

            return {
                "account_id": account_id.decode("utf-8"),
                "email": email,
                "workspace_id": workspace_id,
            }
        else:
            data = redis_client.get(cls._get_invitation_token_key(token))
            if not data:
                return None

            invitation: dict = json.loads(data)
            return invitation

    @classmethod
    def get_invitation_with_case_fallback(
        cls, workspace_id: str | None, email: str | None, token: str
    ) -> dict[str, Any] | None:
        invitation = cls.get_invitation_if_token_valid(workspace_id, email, token)
        if invitation or not email or email == email.lower():
            return invitation
        normalized_email = email.lower()
        return cls.get_invitation_if_token_valid(workspace_id, normalized_email, token)


def _generate_refresh_token(length: int = 64):
    token = secrets.token_hex(length)
    return token
