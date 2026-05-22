# -*- coding: utf-8 -*-
"""Account service functions for article distribution."""

from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.server.auth.models import User
from src.server.auth.schemas import UserRole

from ..dao import ArticleDistributionDAO
from ..models import ArticleDistributionAccount
from ..schemas import (
    AccountCreate,
    AccountDirectoryOut,
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
    is_active: bool | None = None,
) -> list[ArticleDistributionAccount]:
    target_user_id = resolve_optional_target_user_id(current_user, user_id)
    return ArticleDistributionDAO(db).list_accounts(
        user_id=target_user_id,
        platform=normalize_optional(platform),
        publication_type=publication_type,
        is_active=is_active,
    )


def list_account_directory(db: Session) -> list[UserAccountDirectoryOut]:
    grouped: dict[int, UserAccountDirectoryOut] = {}
    for account, owner in ArticleDistributionDAO(db).list_account_owner_rows(
        is_active=True
    ):
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
                platform=account.platform,
                account_name=account.account_name,
                publication_type=publication_type,
                is_active=account.is_active,
            )
        )
    return list(grouped.values())


def create_account(
    db: Session, *, payload: AccountCreate, current_user: User
) -> ArticleDistributionAccount:
    target_user_id = resolve_target_user_id(current_user, payload.user_id)
    account = ArticleDistributionAccount(
        user_id=target_user_id,
        account_name=normalize_required(payload.account_name, "账号名称不能为空"),
        platform=normalize_required(payload.platform, "平台不能为空"),
        publication_type=payload.publication_type,
        is_active=payload.is_active,
    )
    try:
        return ArticleDistributionDAO(db).create_account(account)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="同一用户下已存在相同平台、账号名称和发布类型的账号",
        )


def update_account(
    db: Session, *, account_id: int, payload: AccountUpdate, current_user: User
) -> ArticleDistributionAccount:
    dao = ArticleDistributionDAO(db)
    account = get_accessible_account(db, account_id, current_user, write=True)
    fields = payload.model_dump(exclude_unset=True)

    if "user_id" in fields:
        if current_user.role != UserRole.ADMIN:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权限")
        if fields["user_id"] is None:
            fields.pop("user_id")

    if "account_name" in fields and fields["account_name"] is not None:
        fields["account_name"] = normalize_required(
            str(fields["account_name"]), "账号名称不能为空"
        )
    if "platform" in fields and fields["platform"] is not None:
        fields["platform"] = normalize_required(str(fields["platform"]), "平台不能为空")

    try:
        return dao.update_account(account, **fields)
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
