# -*- coding: utf-8 -*-
"""Article distribution routes."""

from __future__ import annotations

import ipaddress
import socket
from datetime import date
from typing import Annotated
from urllib.parse import urlparse

import httpx
from fastapi import APIRouter, Depends, Header, HTTPException, Query, Security, status
from fastapi.responses import Response
from sqlalchemy.orm import Session

from src.server.auth.dependencies import get_current_user
from src.server.auth.models import User
from src.server.auth.schemas import UserRole
from src.server.auth.service.scopes import (
    SCOPE_ADMIN_ARTICLE_DISTRIBUTION_WRITE,
    SCOPE_ARTICLE_DISTRIBUTION_READ,
    SCOPE_ARTICLE_DISTRIBUTION_WRITE,
)
from src.server.dao.dao_base import run_in_thread
from src.server.database import get_db

from . import service
from .schemas import (
    APIKeyCreate,
    APIKeyCreateOut,
    APIKeyOut,
    AccountCreate,
    AccountDirectoryOut,
    AccountOut,
    AccountUpdate,
    ArticleBatchCreate,
    ArticleOut,
    ArticleStatusUpdate,
    PublishStatus,
    PublicationType,
    UserAccountDirectoryOut,
)

router = APIRouter(prefix="/api/article-distribution", tags=["文章分发"])
admin_router = APIRouter(
    prefix="/api/admin/article-distribution", tags=["文章分发管理"]
)
v1_router = APIRouter(prefix="/api/v1/article-distribution", tags=["文章分发 V1"])
MAX_PROXY_IMAGE_BYTES = 10 * 1024 * 1024
ALLOWED_PROXY_SCHEMES = {"http", "https"}
TRUSTED_PRIVATE_PROXY_HOSTS = {"fstc.kispace.cc"}


@router.get("/accounts", response_model=list[AccountOut], summary="列出账号")
async def list_accounts(
    user_id: int | None = Query(default=None, ge=1),
    platform: str | None = Query(default=None),
    publication_type: PublicationType | None = Query(default=None),
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
        )

    return await run_in_thread(_list)


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


@router.get("/articles", response_model=list[ArticleOut], summary="列出文章")
async def list_articles(
    user_id: int | None = Query(default=None, ge=1),
    account_id: int | None = Query(default=None, ge=1),
    scheduled_from: date | None = Query(default=None),
    scheduled_to: date | None = Query(default=None),
    publish_status: PublishStatus | None = Query(default=None),
    platform: str | None = Query(default=None),
    publication_type: PublicationType | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Security(
        get_current_user, scopes=[SCOPE_ARTICLE_DISTRIBUTION_READ]
    ),
):
    def _list():
        return service.list_articles(
            db,
            current_user=current_user,
            user_id=user_id,
            account_id=account_id,
            scheduled_from=scheduled_from,
            scheduled_to=scheduled_to,
            publish_status=publish_status,
            platform=platform,
            publication_type=publication_type,
        )

    return await run_in_thread(_list)


@router.get("/articles/{article_id}", response_model=ArticleOut, summary="获取文章")
async def get_article(
    article_id: int,
    db: Session = Depends(get_db),
    current_user: User = Security(
        get_current_user, scopes=[SCOPE_ARTICLE_DISTRIBUTION_READ]
    ),
):
    def _get():
        return service.get_article(db, article_id=article_id, current_user=current_user)

    return await run_in_thread(_get)


@router.get("/image-proxy", summary="代理远程文章图片")
async def proxy_article_image(
    url: Annotated[str, Query(min_length=1, max_length=2048)],
    _: User = Security(get_current_user, scopes=[SCOPE_ARTICLE_DISTRIBUTION_READ]),
):
    safe_url = await run_in_thread(lambda: _validate_proxy_image_url(url))
    try:
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=False) as client:
            response = await client.get(
                safe_url,
                headers={"User-Agent": "info-distribution-image-proxy/1.0"},
            )
    except httpx.HTTPError:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="图片拉取失败",
        )

    if response.status_code >= 400:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="图片拉取失败",
        )
    if 300 <= response.status_code < 400:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="图片地址发生跳转，暂不支持代理",
        )

    content_type = response.headers.get("content-type", "").split(";", 1)[0].lower()
    if not content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="目标地址不是图片",
        )
    if len(response.content) > MAX_PROXY_IMAGE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="图片超过大小限制",
        )

    return Response(
        content=response.content,
        media_type=content_type,
        headers={"Cache-Control": "private, max-age=86400"},
    )


@router.patch(
    "/articles/{article_id}/status",
    response_model=ArticleOut,
    summary="更新文章发布状态",
)
async def update_article_status(
    article_id: int,
    payload: ArticleStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Security(
        get_current_user, scopes=[SCOPE_ARTICLE_DISTRIBUTION_WRITE]
    ),
):
    def _update():
        return service.update_article_status(
            db,
            article_id=article_id,
            publish_status=payload.publish_status,
            current_user=current_user,
        )

    return await run_in_thread(_update)


def _validate_proxy_image_url(raw_url: str) -> str:
    parsed = urlparse(raw_url.strip())
    if parsed.scheme not in ALLOWED_PROXY_SCHEMES or not parsed.hostname:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="图片地址必须是 http 或 https URL",
        )
    hostname = parsed.hostname.lower()
    allow_private_address = hostname in TRUSTED_PRIVATE_PROXY_HOSTS

    try:
        address_infos = socket.getaddrinfo(hostname, None)
    except socket.gaierror:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="图片域名无法解析",
        )

    for address_info in address_infos:
        ip_text = address_info[4][0]
        try:
            ip = ipaddress.ip_address(ip_text)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="图片地址解析失败",
            )
        if (
            ip.is_loopback
            or ip.is_link_local
            or ip.is_multicast
            or ip.is_reserved
            or ip.is_unspecified
            or (ip.is_private and not allow_private_address)
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="不允许代理内网或本机图片地址",
            )

    return raw_url.strip()


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
