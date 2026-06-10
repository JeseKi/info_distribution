# -*- coding: utf-8 -*-
"""Account service functions for article distribution."""

from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.server.auth.models import User
from src.server.auth.schemas import UserRole
from src.server.project_management.dao import ProjectManagementDAO
from src.server.project_management.schemas import ProjectSummary, ThemeSummary
from src.server.project_management.service import (
    list_user_theme_summaries,
    validate_user_theme_id,
)

from ..dao import ArticleDistributionDAO
from ..models import ArticleDistributionAccount
from ..schemas import (
    AccountCreate,
    AccountDirectoryOut,
    AccountOut,
    AccountPageOut,
    AccountUpdate,
    UserAccountDirectoryOut,
)
from .helpers import (
    get_accessible_account,
    normalize_optional,
    normalize_publication_type,
    normalize_required,
    resolve_optional_target_user_id,
    resolve_target_user_id,
)


def list_accounts(
    db: Session,
    *,
    current_user: User,
    user_id: int | None = None,
    platform: str | None = None,
    publication_type: str | None = None,
    project_id: int | None = None,
    theme_id: int | None = None,
    is_active: bool | None = None,
) -> list[AccountOut]:
    target_user_id = resolve_optional_target_user_id(current_user, user_id)
    accounts = ArticleDistributionDAO(db).list_accounts(
        user_id=target_user_id,
        platform=normalize_optional(platform),
        publication_type=publication_type,
        project_id=project_id,
        theme_id=theme_id,
        is_active=is_active,
    )
    return [account_to_out(db, account) for account in accounts]


def list_accounts_page(
    db: Session,
    *,
    current_user: User,
    user_id: int | None = None,
    platform: str | None = None,
    publication_type: str | None = None,
    project_id: int | None = None,
    theme_id: int | None = None,
    is_active: bool | None = None,
    keyword: str | None = None,
    page: int = 1,
    page_size: int = 10,
) -> AccountPageOut:
    target_user_id = resolve_optional_target_user_id(current_user, user_id)
    items, total = ArticleDistributionDAO(db).list_accounts_page(
        user_id=target_user_id,
        platform=normalize_optional(platform),
        publication_type=publication_type,
        project_id=project_id,
        theme_id=theme_id,
        is_active=is_active,
        keyword=normalize_optional(keyword),
        page=page,
        page_size=page_size,
    )
    return AccountPageOut(
        items=[account_to_out(db, item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
    )


def list_account_directory(db: Session) -> list[UserAccountDirectoryOut]:
    project_dao = ProjectManagementDAO(db)
    grouped: dict[int, UserAccountDirectoryOut] = {}
    for account, owner in ArticleDistributionDAO(db).list_account_owner_rows(
        is_active=True
    ):
        theme = project_dao.get_theme(account.theme_id)
        projects = _account_project_summaries(db, account.user_id, account.theme_id)
        publication_type = normalize_publication_type(account.publication_type)
        if owner.id not in grouped:
            grouped[owner.id] = UserAccountDirectoryOut(
                id=owner.id,
                name=owner.name or owner.username,
                accounts=[],
            )
        grouped[owner.id].accounts.append(
            AccountDirectoryOut(
                id=account.id,
                project_ids=[project.id for project in projects],
                projects=projects,
                theme_id=account.theme_id,
                theme=ThemeSummary.model_validate(theme) if theme else None,
                platform=account.platform,
                account_name=account.account_name,
                publication_type=publication_type,
                is_active=account.is_active,
            )
        )
    return list(grouped.values())


def create_account(
    db: Session, *, payload: AccountCreate, current_user: User
) -> AccountOut:
    target_user_id = resolve_target_user_id(current_user, payload.user_id)
    theme_id = payload.theme_id
    if theme_id is None:
        available_themes = list_user_theme_summaries(db, target_user_id)
        if len(available_themes) != 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="请选择账号主题",
            )
        theme_id = available_themes[0].id
    theme_id = validate_user_theme_id(db, target_user_id, theme_id)
    account = ArticleDistributionAccount(
        user_id=target_user_id,
        account_name=normalize_required(payload.account_name, "账号名称不能为空"),
        platform=normalize_required(payload.platform, "平台不能为空"),
        publication_type=payload.publication_type,
        theme_id=theme_id,
        is_active=payload.is_active,
    )
    try:
        account = ArticleDistributionDAO(db).create_account(account)
        return account_to_out(db, account)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="同一用户下已存在相同平台、账号名称和发布类型的账号",
        )


def update_account(
    db: Session, *, account_id: int, payload: AccountUpdate, current_user: User
) -> AccountOut:
    dao = ArticleDistributionDAO(db)
    account = get_accessible_account(db, account_id, current_user, write=True)
    fields = payload.model_dump(exclude_unset=True)

    if "user_id" in fields:
        if current_user.role != UserRole.ADMIN:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权限")
        if fields["user_id"] is None:
            fields.pop("user_id")
    target_user_id = int(fields.get("user_id") or account.user_id)
    next_theme_id = int(fields.get("theme_id") or account.theme_id)
    fields["theme_id"] = validate_user_theme_id(db, target_user_id, next_theme_id)

    if "account_name" in fields and fields["account_name"] is not None:
        fields["account_name"] = normalize_required(
            str(fields["account_name"]), "账号名称不能为空"
        )
    if "platform" in fields and fields["platform"] is not None:
        fields["platform"] = normalize_required(str(fields["platform"]), "平台不能为空")

    try:
        account = dao.update_account(account, **fields)
        return account_to_out(db, account)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="同一用户下已存在相同平台、账号名称和发布类型的账号",
        )


def delete_account(db: Session, *, account_id: int, current_user: User) -> None:
    dao = ArticleDistributionDAO(db)
    account = get_accessible_account(db, account_id, current_user, write=True)
    article_count = dao.list_articles(account_id=account.id)
    if article_count:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="账号下已有文章，不能删除",
        )
    dao.delete_account(account)


def account_to_out(db: Session, account: ArticleDistributionAccount) -> AccountOut:
    projects = _account_project_summaries(db, account.user_id, account.theme_id)
    return AccountOut.model_validate(
        {
            **account.__dict__,
            "project_ids": [project.id for project in projects],
            "projects": projects,
            "theme": _theme_summary(db, account.theme_id),
        }
    )


def _theme_summary(db: Session, theme_id: int) -> ThemeSummary | None:
    theme = ProjectManagementDAO(db).get_theme(theme_id)
    if theme is None:
        return None
    return ThemeSummary.model_validate(theme)


def _account_project_summaries(
    db: Session, user_id: int, theme_id: int
) -> list[ProjectSummary]:
    dao = ProjectManagementDAO(db)
    return [
        ProjectSummary.model_validate(project)
        for project in dao.list_user_projects(user_id)
        if theme_id in set(dao.list_project_theme_ids(project.id))
    ]
