# -*- coding: utf-8 -*-
"""Image proxy route for article distribution."""

from __future__ import annotations

import ipaddress
import socket
from typing import Annotated
from urllib.parse import urlparse

import httpx
from fastapi import HTTPException, Query, Security, status
from fastapi.responses import Response

from src.server.auth.dependencies import get_current_user
from src.server.auth.models import User
from src.server.auth.service.scopes import SCOPE_ARTICLE_DISTRIBUTION_READ
from src.server.dao.dao_base import run_in_thread

from .shared import router

MAX_PROXY_IMAGE_BYTES = 10 * 1024 * 1024
ALLOWED_PROXY_SCHEMES = {"http", "https"}
TRUSTED_PRIVATE_PROXY_HOSTS = {"fstc.kispace.cc"}


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
