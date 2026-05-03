import uuid

import sqlalchemy as sa
from flask_login import current_user
from sqlalchemy import func, select
from werkzeug.exceptions import NotFound

from extensions.ext_database import db
from libs.desktop_auth import has_admin_tag_override
from models.dataset import Dataset
from models.model import App, Tag, TagBinding

COMMON_VISIBILITY_TAG_NAMES = frozenset({"Common", "通用"})
DEFAULT_VISIBILITY_TAG_NAMES = ("Common", "通用")


class TagService:
    @staticmethod
    def ensure_default_visibility_bindings(
        tag_type: str,
        target_id: str,
        tenant_id: str,
        created_by: str,
    ) -> bool:
        existing_bindings = (
            db.session.query(TagBinding.id)
            .join(Tag, Tag.id == TagBinding.tag_id)
            .where(
                TagBinding.target_id == target_id,
                TagBinding.tenant_id == tenant_id,
                Tag.tenant_id == tenant_id,
                Tag.type == tag_type,
            )
            .first()
        )
        if existing_bindings:
            return False

        tags_by_name = {
            tag.name: tag
            for tag in db.session.scalars(
                select(Tag).where(
                    Tag.tenant_id == tenant_id,
                    Tag.type == tag_type,
                    Tag.name.in_(DEFAULT_VISIBILITY_TAG_NAMES),
                )
            ).all()
        }

        for tag_name in DEFAULT_VISIBILITY_TAG_NAMES:
            if tag_name in tags_by_name:
                continue
            tag = Tag(
                name=tag_name,
                type=tag_type,
                created_by=created_by,
                tenant_id=tenant_id,
            )
            tag.id = str(uuid.uuid4())
            db.session.add(tag)
            db.session.flush()
            tags_by_name[tag_name] = tag

        for tag_name in DEFAULT_VISIBILITY_TAG_NAMES:
            tag = tags_by_name[tag_name]
            db.session.add(
                TagBinding(
                    tag_id=tag.id,
                    target_id=target_id,
                    tenant_id=tenant_id,
                    created_by=created_by,
                )
            )

        return True

    @staticmethod
    def _normalize_user_tags(user_tags: list[str] | None) -> list[str]:
        normalized_tags: list[str] = []
        seen_tags: set[str] = set()
        for tag in user_tags or []:
            if not isinstance(tag, str):
                continue
            normalized_tag = tag.strip()
            if not normalized_tag or normalized_tag in seen_tags:
                continue
            normalized_tags.append(normalized_tag)
            seen_tags.add(normalized_tag)
        return normalized_tags

    @staticmethod
    def is_target_visible_by_tag_names(tag_names: list[str] | None, user_tags: list[str] | None) -> bool:
        if has_admin_tag_override(user_tags):
            return True

        normalized_tag_names = [tag.strip() for tag in (tag_names or []) if isinstance(tag, str) and tag.strip()]
        if not normalized_tag_names:
            return True

        if any(tag_name in COMMON_VISIBILITY_TAG_NAMES for tag_name in normalized_tag_names):
            return True

        normalized_user_tags = set(TagService._normalize_user_tags(user_tags))
        if not normalized_user_tags:
            return False

        return any(tag_name in normalized_user_tags for tag_name in normalized_tag_names)

    @staticmethod
    def get_tags_by_target_ids(tag_type: str, current_tenant_id: str, target_ids: list[str]) -> dict[str, list[Tag]]:
        if not target_ids:
            return {}

        rows = (
            db.session.query(TagBinding.target_id, Tag)
            .join(Tag, Tag.id == TagBinding.tag_id)
            .where(
                TagBinding.target_id.in_(target_ids),
                TagBinding.tenant_id == current_tenant_id,
                Tag.tenant_id == current_tenant_id,
                Tag.type == tag_type,
            )
            .all()
        )

        tags_by_target_id: dict[str, list[Tag]] = {}
        for target_id, tag in rows:
            if not isinstance(target_id, str):
                continue
            tags_by_target_id.setdefault(target_id, []).append(tag)

        return tags_by_target_id

    @staticmethod
    def is_target_visible(tag_type: str, current_tenant_id: str, target_id: str, user_tags: list[str] | None) -> bool:
        tag_names = [tag.name for tag in TagService.get_tags_by_target_id(tag_type, current_tenant_id, target_id)]
        return TagService.is_target_visible_by_tag_names(tag_names, user_tags)

    @staticmethod
    def build_visibility_filter(target_column: sa.ColumnElement, tag_type: str, current_tenant_id: str, user_tags: list[str] | None):
        normalized_user_tags = TagService._normalize_user_tags(user_tags)
        if has_admin_tag_override(normalized_user_tags):
            return sa.true()

        visible_tag_names = sorted(set(normalized_user_tags).union(COMMON_VISIBILITY_TAG_NAMES))

        tagged_target_ids = (
            select(TagBinding.target_id)
            .join(Tag, Tag.id == TagBinding.tag_id)
            .where(
                TagBinding.tenant_id == current_tenant_id,
                Tag.tenant_id == current_tenant_id,
                Tag.type == tag_type,
            )
            .group_by(TagBinding.target_id)
        )
        visible_target_ids = (
            select(TagBinding.target_id)
            .join(Tag, Tag.id == TagBinding.tag_id)
            .where(
                TagBinding.tenant_id == current_tenant_id,
                Tag.tenant_id == current_tenant_id,
                Tag.type == tag_type,
                Tag.name.in_(visible_tag_names),
            )
            .group_by(TagBinding.target_id)
        )

        return sa.or_(~target_column.in_(tagged_target_ids), target_column.in_(visible_target_ids))

    @staticmethod
    def get_tags(tag_type: str, current_tenant_id: str, keyword: str | None = None):
        query = (
            db.session.query(Tag.id, Tag.type, Tag.name, func.count(TagBinding.id).label("binding_count"))
            .outerjoin(TagBinding, Tag.id == TagBinding.tag_id)
            .where(Tag.type == tag_type, Tag.tenant_id == current_tenant_id)
        )
        if keyword:
            from libs.helper import escape_like_pattern

            escaped_keyword = escape_like_pattern(keyword)
            query = query.where(sa.and_(Tag.name.ilike(f"%{escaped_keyword}%", escape="\\")))
        query = query.group_by(Tag.id, Tag.type, Tag.name, Tag.created_at)
        results = query.order_by(Tag.created_at.desc()).all()
        return results

    @staticmethod
    def get_target_ids_by_tag_ids(tag_type: str, current_tenant_id: str, tag_ids: list):
        # Check if tag_ids is not empty to avoid WHERE false condition
        if not tag_ids or len(tag_ids) == 0:
            return []
        tags = db.session.scalars(
            select(Tag).where(Tag.id.in_(tag_ids), Tag.tenant_id == current_tenant_id, Tag.type == tag_type)
        ).all()
        if not tags:
            return []
        tag_ids = [tag.id for tag in tags]
        # Check if tag_ids is not empty to avoid WHERE false condition
        if not tag_ids or len(tag_ids) == 0:
            return []
        tag_bindings = db.session.scalars(
            select(TagBinding.target_id).where(
                TagBinding.tag_id.in_(tag_ids), TagBinding.tenant_id == current_tenant_id
            )
        ).all()
        return tag_bindings

    @staticmethod
    def get_tag_by_tag_name(tag_type: str, current_tenant_id: str, tag_name: str):
        if not tag_type or not tag_name:
            return []
        tags = list(
            db.session.scalars(
                select(Tag).where(Tag.name == tag_name, Tag.tenant_id == current_tenant_id, Tag.type == tag_type)
            ).all()
        )
        if not tags:
            return []
        return tags

    @staticmethod
    def get_tags_by_target_id(tag_type: str, current_tenant_id: str, target_id: str):
        tags = (
            db.session.query(Tag)
            .join(TagBinding, Tag.id == TagBinding.tag_id)
            .where(
                TagBinding.target_id == target_id,
                TagBinding.tenant_id == current_tenant_id,
                Tag.tenant_id == current_tenant_id,
                Tag.type == tag_type,
            )
            .all()
        )

        return tags or []

    @staticmethod
    def save_tags(args: dict) -> Tag:
        if TagService.get_tag_by_tag_name(args["type"], current_user.current_tenant_id, args["name"]):
            raise ValueError("Tag name already exists")
        tag = Tag(
            name=args["name"],
            type=args["type"],
            created_by=current_user.id,
            tenant_id=current_user.current_tenant_id,
        )
        tag.id = str(uuid.uuid4())
        db.session.add(tag)
        db.session.commit()
        return tag

    @staticmethod
    def update_tags(args: dict, tag_id: str) -> Tag:
        tag = TagService.get_tag(tag_id)
        if not tag:
            raise NotFound("Tag not found")
        existing_tags = TagService.get_tag_by_tag_name(args.get("type", ""), current_user.current_tenant_id, args.get("name", ""))
        if any(str(existing_tag.id) != str(tag.id) for existing_tag in existing_tags):
            raise ValueError("Tag name already exists")
        tag.name = args["name"]
        db.session.commit()
        return tag

    @staticmethod
    def get_tag_binding_count(tag_id: str) -> int:
        count = db.session.query(TagBinding).where(TagBinding.tag_id == tag_id).count()
        return count

    @staticmethod
    def delete_tag(tag_id: str):
        tag = TagService.get_tag(tag_id)
        if not tag:
            raise NotFound("Tag not found")
        db.session.delete(tag)
        # delete tag binding
        tag_bindings = db.session.scalars(select(TagBinding).where(TagBinding.tag_id == tag_id)).all()
        if tag_bindings:
            for tag_binding in tag_bindings:
                db.session.delete(tag_binding)
        db.session.commit()

    @staticmethod
    def save_tag_binding(args):
        # check if target exists
        TagService.check_target_exists(args["type"], args["target_id"])
        # save tag binding
        for tag_id in args["tag_ids"]:
            tag_binding = (
                db.session.query(TagBinding)
                .where(TagBinding.tag_id == tag_id, TagBinding.target_id == args["target_id"])
                .first()
            )
            if tag_binding:
                continue
            new_tag_binding = TagBinding(
                tag_id=tag_id,
                target_id=args["target_id"],
                tenant_id=current_user.current_tenant_id,
                created_by=current_user.id,
            )
            db.session.add(new_tag_binding)
        db.session.commit()

    @staticmethod
    def delete_tag_binding(args):
        # check if target exists
        TagService.check_target_exists(args["type"], args["target_id"])
        # delete tag binding
        tag_bindings = (
            db.session.query(TagBinding)
            .where(TagBinding.target_id == args["target_id"], TagBinding.tag_id == (args["tag_id"]))
            .first()
        )
        if tag_bindings:
            db.session.delete(tag_bindings)
            db.session.commit()

    @staticmethod
    def get_tag(tag_id: str) -> Tag | None:
        return db.session.query(Tag).where(Tag.id == tag_id).first()

    @staticmethod
    def check_target_exists(type: str, target_id: str):
        if type == "knowledge":
            dataset = (
                db.session.query(Dataset)
                .where(Dataset.tenant_id == current_user.current_tenant_id, Dataset.id == target_id)
                .first()
            )
            if not dataset:
                raise NotFound("Dataset not found")
        elif type == "app":
            app = (
                db.session.query(App)
                .where(App.tenant_id == current_user.current_tenant_id, App.id == target_id)
                .first()
            )
            if not app:
                raise NotFound("App not found")
        else:
            raise NotFound("Invalid binding type")
