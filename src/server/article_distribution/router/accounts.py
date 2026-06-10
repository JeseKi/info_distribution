# -*- coding: utf-8 -*-
"""Account routes for article distribution."""

from __future__ import annotations

from fastapi import Depends, Query, Security, status
from sqlalchemy.orm import Session

from src.server.auth.dependencies import get_current_user
from src.server.auth.models import User
from src.server.auth.service.scopes import (
    SCOPE_ARTICLE_DISTRIBUTION_READ,
    SCOPE_ARTICLE_DISTRIBUTION_WRITE,
)
from src.server.dao.dao_base import run_in_thread
from src.server.database import get_db

from .. import service
from ..schemas import (
    AccountCreate,
    AccountOut,
    AccountPageOut,
    AccountUpdate,
    PublicationType,
)
from .shared import router


@router.get("/accounts", response_model=list[AccountOut], summary="列出账号")
async def list_accounts(
    user_id: int | None = Query(default=None, ge=1),
    platform: str | None = Query(default=None),
    publication_type: PublicationType | None = Query(default=None),
    project_id: int | None = Query(default=None, ge=1),
    theme_id: int | None = Query(default=None, ge=1),
    is_active: bool | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Security(
        get_current_user, scopes=[SCOPE_ARTICLE_DISTRIBUTION_READ]
    ),
):
    def _list():
        return service.list_accounts(
            db,
            current_user=current_user,
            user_id=user_id,
            platform=platform,
            publication_type=publication_type,
            project_id=project_id,
            theme_id=theme_id,
            is_active=is_active,
        )

    return await run_in_thread(_list)


@router.get(
    "/accounts/page",
    response_model=AccountPageOut,
    summary="分页列出账号",
)
async def list_accounts_page(
    user_id: int | None = Query(default=None, ge=1),
    platform: str | None = Query(default=None),
    publication_type: PublicationType | None = Query(default=None),
    project_id: int | None = Query(default=None, ge=1),
    theme_id: int | None = Query(default=None, ge=1),
    is_active: bool | None = Query(default=None),
    keyword: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Security(
        get_current_user, scopes=[SCOPE_ARTICLE_DISTRIBUTION_READ]
    ),
):
    def _list_page():
        return service.list_accounts_page(
            db,
            current_user=current_user,
            user_id=user_id,
            platform=platform,
            publication_type=publication_type,
            project_id=project_id,
            theme_id=theme_id,
            is_active=is_active,
            keyword=keyword,
            page=page,
            page_size=page_size,
        )

    return await run_in_thread(_list_page)


@router.post(
    "/accounts",
    response_model=AccountOut,
    status_code=status.HTTP_201_CREATED,
    summary="创建账号",
)
async def create_account(
    payload: AccountCreate,
    db: Session = Depends(get_db),
    current_user: User = Security(
        get_current_user, scopes=[SCOPE_ARTICLE_DISTRIBUTION_WRITE]
    ),
):
    def _create():
        return service.create_account(db, payload=payload, current_user=current_user)

    return await run_in_thread(_create)


@router.patch("/accounts/{account_id}", response_model=AccountOut, summary="更新账号")
async def update_account(
    account_id: int,
    payload: AccountUpdate,
    db: Session = Depends(get_db),
    current_user: User = Security(
        get_current_user, scopes=[SCOPE_ARTICLE_DISTRIBUTION_WRITE]
    ),
):
    def _update():
        return service.update_account(
            db, account_id=account_id, payload=payload, current_user=current_user
        )

    return await run_in_thread(_update)


@router.delete(
    "/accounts/{account_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="删除账号",
)
async def delete_account(
    account_id: int,
    db: Session = Depends(get_db),
    current_user: User = Security(
        get_current_user, scopes=[SCOPE_ARTICLE_DISTRIBUTION_WRITE]
    ),
):
    def _delete():
        service.delete_account(db, account_id=account_id, current_user=current_user)

    return await run_in_thread(_delete)
