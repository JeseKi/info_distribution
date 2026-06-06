# -*- coding: utf-8 -*-
"""Article distribution Pydantic schemas."""

from __future__ import annotations

from .accounts import (
    AccountCreate,
    AccountDirectoryOut,
    AccountOut,
    AccountPageOut,
    AccountUpdate,
    UserAccountDirectoryOut,
)
from .api_keys import APIKeyCreate, APIKeyCreateOut, APIKeyOut
from .articles import (
    ArticleBatchCreate,
    ArticleOut,
    ArticlePageOut,
    ArticleStatusCountsOut,
    ArticleStatusUpdate,
    ArticleUpdate,
    ArticleUploadItem,
    ArticleV1Update,
)
from .reports_metadata import (
    ArticleDistributionMetadataDashboardArticleOut,
    ArticleDistributionMetadataDashboardOut,
    ArticleDistributionMetadataDashboardSummaryOut,
    ArticleDistributionMetadataDashboardTopicOut,
)
from .reports_missing_traffic import (
    ArticleDistributionMissingTrafficArticleOut,
    ArticleDistributionMissingTrafficPageOut,
    ArticleDistributionMissingTrafficReportOut,
    ArticleDistributionMissingTrafficSummaryOut,
    ArticleDistributionMissingTrafficUserOut,
)
from .reports_overview import (
    ArticleDistributionOverviewArticleOut,
    ArticleDistributionOverviewOut,
    ArticleDistributionOverviewSummaryOut,
    ArticleDistributionOverviewTopicOut,
    ArticleDistributionOverviewUserOut,
)
from .reports_public import (
    ArticleDistributionPublicArticleOut,
    ArticleDistributionPublicDashboardOut,
)
from .reports_unpublished import (
    ArticleDistributionPendingArticleOut,
    ArticleDistributionPendingUserOut,
    ArticleDistributionPlatformSummaryOut,
    ArticleDistributionReportOut,
    ArticleDistributionReportSummaryOut,
)
from .traffic import (
    ArticleTrafficStatCreate,
    ArticleTrafficStatOut,
    ArticleTrafficSummaryOut,
    ArticleTrafficSummaryPageOut,
)
from .types import (
    AccountStatusFilter,
    ArticleDistributionOverviewView,
    PublicationType,
    PublishStatus,
)

__all__ = [
    "APIKeyCreate",
    "APIKeyCreateOut",
    "APIKeyOut",
    "AccountCreate",
    "AccountDirectoryOut",
    "AccountOut",
    "AccountPageOut",
    "AccountStatusFilter",
    "AccountUpdate",
    "ArticleBatchCreate",
    "ArticleDistributionMetadataDashboardArticleOut",
    "ArticleDistributionMetadataDashboardOut",
    "ArticleDistributionMetadataDashboardSummaryOut",
    "ArticleDistributionMetadataDashboardTopicOut",
    "ArticleDistributionMissingTrafficArticleOut",
    "ArticleDistributionMissingTrafficPageOut",
    "ArticleDistributionMissingTrafficReportOut",
    "ArticleDistributionMissingTrafficSummaryOut",
    "ArticleDistributionMissingTrafficUserOut",
    "ArticleDistributionOverviewArticleOut",
    "ArticleDistributionOverviewOut",
    "ArticleDistributionOverviewSummaryOut",
    "ArticleDistributionOverviewTopicOut",
    "ArticleDistributionOverviewUserOut",
    "ArticleDistributionOverviewView",
    "ArticleDistributionPendingArticleOut",
    "ArticleDistributionPendingUserOut",
    "ArticleDistributionPlatformSummaryOut",
    "ArticleDistributionPublicArticleOut",
    "ArticleDistributionPublicDashboardOut",
    "ArticleDistributionReportOut",
    "ArticleDistributionReportSummaryOut",
    "ArticleOut",
    "ArticlePageOut",
    "ArticleStatusCountsOut",
    "ArticleStatusUpdate",
    "ArticleTrafficStatCreate",
    "ArticleTrafficStatOut",
    "ArticleTrafficSummaryOut",
    "ArticleTrafficSummaryPageOut",
    "ArticleUpdate",
    "ArticleUploadItem",
    "ArticleV1Update",
    "PublicationType",
    "PublishStatus",
    "UserAccountDirectoryOut",
]
