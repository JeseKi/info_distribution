# -*- coding: utf-8 -*-
"""Shared router instances for article distribution endpoints."""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/api/article-distribution", tags=["文章分发"])
admin_router = APIRouter(
    prefix="/api/admin/article-distribution", tags=["文章分发管理"]
)
v1_router = APIRouter(prefix="/api/v1/article-distribution", tags=["文章分发 V1"])
v2_router = APIRouter(prefix="/api/v2/article-distribution", tags=["文章分发 V2"])
v3_router = APIRouter(prefix="/api/v3/article-distribution", tags=["文章分发 V3"])
