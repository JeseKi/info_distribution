# -*- coding: utf-8 -*-
"""API key schemas for article distribution."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

class APIKeyCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)


class APIKeyOut(BaseModel):
    id: int
    name: str
    key_prefix: str
    created_by_user_id: int
    is_active: bool
    created_at: datetime
    last_used_at: datetime | None
    revoked_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


class APIKeyCreateOut(APIKeyOut):
    api_key: str
