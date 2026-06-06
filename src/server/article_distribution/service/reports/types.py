# -*- coding: utf-8 -*-
"""Shared report service types."""

from __future__ import annotations

from typing import TypeAlias

from ...schemas import (
    ArticleDistributionOverviewArticleOut,
    ArticleDistributionOverviewTopicOut,
    ArticleDistributionOverviewUserOut,
)

OverviewItemOut: TypeAlias = (
    ArticleDistributionOverviewUserOut
    | ArticleDistributionOverviewArticleOut
    | ArticleDistributionOverviewTopicOut
)
