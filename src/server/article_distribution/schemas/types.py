# -*- coding: utf-8 -*-
"""Shared schema type aliases for article distribution."""

from __future__ import annotations

from typing import Literal

PublicationType = Literal["video", "article", "image_text"]
PublishStatus = Literal["unpublished", "published", "invalid"]
AccountStatusFilter = Literal["active", "inactive", "all"]
ArticleDistributionOverviewView = Literal["users", "articles", "topics"]
