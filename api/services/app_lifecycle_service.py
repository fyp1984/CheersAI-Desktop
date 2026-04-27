import json
from datetime import datetime

from werkzeug.exceptions import Conflict

from extensions.ext_database import db
from libs.login import current_user
from models.model import App, AppLifecycleEvent
from services.audit_service import log_operation

class AppLifecycleValidationException(Exception):
    def __init__(self, message, details=None):
        self.message = message
        self.details = details or []

class AppLifecycleService:
    @staticmethod
    def _is_configuration_ready(app: App):
        if app.mode in {"workflow", "advanced-chat"}:
            return bool(app.workflow)
        return bool(app.app_model_config)

    @staticmethod
    def get_lifecycle_status(app: App, user):
        display_status = "unpublished"
        display_status_description = "当前已配置，但尚未对外发布"
        val_passed, errors = AppLifecycleService._validate_publish(app)

        if app.lifecycle_status == "unpublished":
            display_status = "unpublished"
        elif app.lifecycle_status == "published":
            if not val_passed:
                display_status = "unpublished"
            else:
                display_status = "published"
            if display_status == "published" and AppLifecycleService._has_draft_difference(app):
                display_status = "pending"
        elif app.lifecycle_status == "recalled":
            display_status = "recalled"

        if app.lifecycle_status == "recalled":
            display_status_description = "当前已被回收，暂不可用"
        elif not val_passed:
            display_status_description = "当前配置不完整，应用暂不可用"
        elif display_status == "pending":
            display_status_description = "当前存在未发布改动"
        elif display_status == "published":
            display_status_description = "当前版本已可对外使用"

        can_publish = False
        can_recall = False
        can_stash = True

        can_publish = True
        can_recall = True

        if app.lifecycle_status == "unpublished" and not val_passed:
            can_publish = False

        if app.lifecycle_status != "published":
            can_recall = False

        return {
            "app_id": app.id,
            "lifecycle_status": app.lifecycle_status,
            "display_status": display_status,
            "display_status_description": display_status_description,
            "is_configuration_ready": val_passed,
            "validation_errors": errors,
            "can_publish": can_publish,
            "can_recall": can_recall,
            "can_stash": can_stash,
            "last_published_at": int(app.last_published_at.timestamp() * 1000) if app.last_published_at else None,
            "last_recalled_at": int(app.last_recalled_at.timestamp() * 1000) if app.last_recalled_at else None,
            "row_version": app.row_version
        }

    @staticmethod
    def _has_draft_difference(app: App):
        from models.workflow import Workflow
        from sqlalchemy import desc

        if app.last_published_at and app.updated_at and app.updated_at > app.last_published_at:
            return True

        if app.mode in {"workflow", "advanced-chat"}:
            draft_workflow = db.session.query(Workflow).filter(
                Workflow.version == Workflow.VERSION_DRAFT,
                Workflow.app_id == app.id
            ).first()
            if not draft_workflow:
                return False

            latest_published_workflow = (
                db.session.query(Workflow)
                .filter(
                    Workflow.app_id == app.id,
                    Workflow.version != Workflow.VERSION_DRAFT,
                )
                .order_by(desc(Workflow.created_at))
                .first()
            )
            if latest_published_workflow:
                try:
                    return draft_workflow.unique_hash != latest_published_workflow.unique_hash
                except Exception:
                    return True
        return False

    @staticmethod
    def _validate_publish(app: App):
        errors = []
        passed = AppLifecycleService._is_configuration_ready(app)
        if not passed:
            if app.mode in {"workflow", "advanced-chat"}:
                errors.append("缺少可用工作流配置")
            else:
                errors.append("缺少可用模型配置")
        return passed, errors

    @staticmethod
    def publish_app(app: App, expected_row_version: int, reason: str = None):
        passed, errors = AppLifecycleService._validate_publish(app)
        
        content = {
            "app_id": app.id,
            "app_name": app.name,
            "from_status": app.lifecycle_status,
            "to_status": "published",
            "reason": reason,
            "validation_result": {"passed": passed, "errors": errors},
            "draft_version": None,
            "published_version": None
        }
        
        if not passed:
            log_operation(action="publish_app_failed", content=content, operation_type="workflow", error_message="当前配置不完整，无法发布")
            raise AppLifecycleValidationException("当前配置不完整，无法发布", errors)
            
        if app.row_version != expected_row_version:
            log_operation(action="publish_app_failed", content=content, operation_type="workflow", error_message="当前配置已被其他用户更新")
            raise Conflict("当前配置已被其他用户更新，请刷新后重试")
            
        from_status = app.lifecycle_status
        app.lifecycle_status = 'published'
        app.lifecycle_status_changed_at = datetime.utcnow()
        app.lifecycle_status_changed_by = current_user.id
        app.lifecycle_status_reason = reason
        app.last_published_at = datetime.utcnow()
        app.last_published_by = current_user.id
        app.row_version += 1
        app.enable_site = True
        app.enable_api = True
        
        # log event
        event = AppLifecycleEvent(
            tenant_id=app.tenant_id,
            app_id=app.id,
            from_status=from_status,
            to_status='published',
            action='publish' if from_status == 'unpublished' else 'republish',
            reason=reason,
            validation_result=json.dumps({"passed": passed, "errors": errors}),
            operator_id=current_user.id,
            operator_name=current_user.name
        )
        db.session.add(event)
        db.session.commit()
        
        log_operation(action="publish_app" if from_status == "unpublished" else "republish_app", content=content, operation_type="workflow")
        
        return AppLifecycleService.get_lifecycle_status(app, current_user)

    @staticmethod
    def recall_app(app: App, expected_row_version: int, reason: str):
        content = {
            "app_id": app.id,
            "app_name": app.name,
            "from_status": app.lifecycle_status,
            "to_status": "recalled",
            "reason": reason,
            "validation_result": {"passed": True, "errors": []},
            "draft_version": None,
            "published_version": None
        }
        
        if not reason:
            log_operation(action="recall_app_failed", content=content, operation_type="workflow", error_message="必须填写回收原因")
            raise ValueError("必须填写回收原因")
            
        if app.lifecycle_status != 'published':
            log_operation(action="recall_app_failed", content=content, operation_type="workflow", error_message="当前状态不是已发布，无法回收")
            raise ValueError("当前状态不是已发布，无法回收")
            
        if app.row_version != expected_row_version:
            log_operation(action="recall_app_failed", content=content, operation_type="workflow", error_message="当前配置已被其他用户更新")
            raise Conflict("当前配置已被其他用户更新，请刷新后重试")
            
        from_status = app.lifecycle_status
        app.lifecycle_status = 'recalled'
        app.lifecycle_status_changed_at = datetime.utcnow()
        app.lifecycle_status_changed_by = current_user.id
        app.lifecycle_status_reason = reason
        app.last_recalled_at = datetime.utcnow()
        app.last_recalled_by = current_user.id
        app.enable_site = False
        app.enable_api = False
        app.row_version += 1
        
        # log event
        event = AppLifecycleEvent(
            tenant_id=app.tenant_id,
            app_id=app.id,
            from_status=from_status,
            to_status='recalled',
            action='recall',
            reason=reason,
            validation_result=json.dumps({"passed": True, "errors": []}),
            operator_id=current_user.id,
            operator_name=current_user.name
        )
        db.session.add(event)
        db.session.commit()
        
        log_operation(action="recall_app", content=content, operation_type="workflow")
        
        return AppLifecycleService.get_lifecycle_status(app, current_user)

    @staticmethod
    def stash_app(app: App, expected_row_version: int):
        content = {
            "app_id": app.id,
            "app_name": app.name,
            "from_status": app.lifecycle_status,
            "to_status": app.lifecycle_status,
            "action": "stash",
            "reason": None,
            "validation_result": {"passed": True, "errors": []},
            "draft_version": None,
            "published_version": None
        }
        if app.row_version != expected_row_version:
            log_operation(action="stash_app_draft_failed", content=content, operation_type="workflow", error_message="当前配置已被其他用户更新")
            raise Conflict("当前配置已被其他用户更新，请刷新后重试")
            
        app.row_version += 1
        
        # log event
        event = AppLifecycleEvent(
            tenant_id=app.tenant_id,
            app_id=app.id,
            from_status=app.lifecycle_status,
            to_status=app.lifecycle_status,
            action='stash',
            reason=None,
            validation_result=json.dumps({"passed": True, "errors": []}),
            operator_id=current_user.id,
            operator_name=current_user.name
        )
        db.session.add(event)
        db.session.commit()
        
        log_operation(action="stash_app_draft", content=content, operation_type="workflow")
        
        return AppLifecycleService.get_lifecycle_status(app, current_user)
