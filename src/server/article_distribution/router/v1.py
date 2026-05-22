# -*- coding: utf-8 -*-
"""API key routes for article distribution V1."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Header, status
from sqlalchemy.orm import Session

from src.server.dao.dao_base import run_in_thread
from src.server.database import get_db

from .. import service
from ..schemas import ArticleBatchCreate, ArticleOut, UserAccountDirectoryOut
from .shared import v1_router


@v1_router.get(
    "/accounts",
    response_model=list[UserAccountDirectoryOut],
    summary="使用 API Key 获取账号目录",
)
async def list_account_directory_v1(
    x_api_key: Annotated[str | None, Header(alias="X-API-Key")] = None,
    db: Session = Depends(get_db),
):
    def _list():
        service.authenticate_api_key(db, x_api_key)
        return service.list_account_directory(db)

    return await run_in_thread(_list)


@v1_router.post(
    "/articles",
    response_model=list[ArticleOut],
    status_code=status.HTTP_201_CREATED,
    summary="使用 API Key 上传文章",
)
async def create_articles_v1(
    payload: ArticleBatchCreate,
    x_api_key: Annotated[str | None, Header(alias="X-API-Key")] = None,
    db: Session = Depends(get_db),
):
    def _create():
        api_key = service.authenticate_api_key(db, x_api_key)
        return service.create_articles_with_api_key(
            db, payload=payload, api_key=api_key
        )

    return await run_in_thread(_create)
