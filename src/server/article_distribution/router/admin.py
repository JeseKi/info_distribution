# -*- coding: utf-8 -*-
"""Admin routes for article distribution."""

from __future__ import annotations

from fastapi import Depends, HTTPException, Security, status
from sqlalchemy.orm import Session

from src.server.auth.dependencies import get_current_user
from src.server.auth.models import User
from src.server.auth.schemas import UserRole
from src.server.auth.service.scopes import SCOPE_ADMIN_ARTICLE_DISTRIBUTION_WRITE
from src.server.dao.dao_base import run_in_thread
from src.server.database import get_db

from .. import service
from ..schemas import (
    APIKeyCreate,
    APIKeyCreateOut,
    APIKeyOut,
    ArticleBatchCreate,
    ArticleOut,
)
from .shared import admin_router


@admin_router.post(
    "/articles",
    response_model=list[ArticleOut],
    status_code=status.HTTP_201_CREATED,
    summary="管理员上传文章",
)
async def create_articles_as_admin(
    payload: ArticleBatchCreate,
    db: Session = Depends(get_db),
    current_user: User = Security(
        get_current_user, scopes=[SCOPE_ADMIN_ARTICLE_DISTRIBUTION_WRITE]
    ),
):
    def _create():
        if current_user.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="需要管理员权限"
            )
        return service.create_articles_as_admin(
            db, payload=payload, current_user=current_user
        )

    return await run_in_thread(_create)


@admin_router.get("/api-keys", response_model=list[APIKeyOut], summary="列出 API Key")
async def list_api_keys(
    db: Session = Depends(get_db),
    current_user: User = Security(
        get_current_user, scopes=[SCOPE_ADMIN_ARTICLE_DISTRIBUTION_WRITE]
    ),
):
    def _list():
        return service.list_api_keys(db, current_user=current_user)

    return await run_in_thread(_list)


@admin_router.post(
    "/api-keys",
    response_model=APIKeyCreateOut,
    status_code=status.HTTP_201_CREATED,
    summary="创建 API Key",
)
async def create_api_key(
    payload: APIKeyCreate,
    db: Session = Depends(get_db),
    current_user: User = Security(
        get_current_user, scopes=[SCOPE_ADMIN_ARTICLE_DISTRIBUTION_WRITE]
    ),
):
    def _create():
        api_key, raw_key = service.create_api_key(
            db, name=payload.name, current_user=current_user
        )
        return APIKeyCreateOut.model_validate({**api_key.__dict__, "api_key": raw_key})

    return await run_in_thread(_create)


@admin_router.post(
    "/api-keys/{api_key_id}/revoke",
    response_model=APIKeyOut,
    summary="吊销 API Key",
)
async def revoke_api_key(
    api_key_id: int,
    db: Session = Depends(get_db),
    current_user: User = Security(
        get_current_user, scopes=[SCOPE_ADMIN_ARTICLE_DISTRIBUTION_WRITE]
    ),
):
    def _revoke():
        return service.revoke_api_key(
            db, api_key_id=api_key_id, current_user=current_user
        )

    return await run_in_thread(_revoke)
