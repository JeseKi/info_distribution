# -*- coding: utf-8 -*-
"""API key routes for article distribution V2."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Header, status
from sqlalchemy.orm import Session

from src.server.dao.dao_base import run_in_thread
from src.server.database import get_db

from .. import service
from ..schemas import (
    ArticleBatchCreate,
    ArticleOut,
    ArticleV2Update,
    UserAccountDirectoryOut,
)
from .shared import v2_router


@v2_router.get(
    "/accounts",
    response_model=list[UserAccountDirectoryOut],
    summary="使用 API Key 获取账号目录",
)
async def list_account_directory_v2(
    x_api_key: Annotated[str | None, Header(alias="X-API-Key")] = None,
    db: Session = Depends(get_db),
):
    def _list():
        service.authenticate_api_key(db, x_api_key)
        return service.list_account_directory(db)

    return await run_in_thread(_list)


@v2_router.post(
    "/articles",
    response_model=list[ArticleOut],
    status_code=status.HTTP_201_CREATED,
    summary="使用 API Key 上传文章",
)
async def create_articles_v2(
    payload: ArticleBatchCreate,
    x_api_key: Annotated[str | None, Header(alias="X-API-Key")] = None,
    db: Session = Depends(get_db),
):
    def _create():
        api_key = service.authenticate_api_key(db, x_api_key)
        return service.create_articles_with_api_key_v2(
            db, payload=payload, api_key=api_key
        )

    return await run_in_thread(_create)


@v2_router.patch(
    "/articles/{article_id}",
    response_model=ArticleOut,
    summary="使用 API Key 更新文章",
)
async def update_article_v2(
    article_id: int,
    payload: ArticleV2Update,
    x_api_key: Annotated[str | None, Header(alias="X-API-Key")] = None,
    db: Session = Depends(get_db),
):
    def _update():
        api_key = service.authenticate_api_key(db, x_api_key)
        return service.update_article_with_api_key_v2(
            db, article_id=article_id, payload=payload, api_key=api_key
        )

    return await run_in_thread(_update)
