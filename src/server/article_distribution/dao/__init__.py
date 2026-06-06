# -*- coding: utf-8 -*-
"""Article distribution DAO."""

from __future__ import annotations

from .api_keys import ArticleDistributionAPIKeyDAO
from .articles import ArticleDistributionArticleDAO
from .report_missing_traffic import ArticleDistributionReportMissingTrafficDAO
from .report_overview import ArticleDistributionReportOverviewDAO
from .report_summary import ArticleDistributionReportSummaryDAO
from .traffic import ArticleDistributionTrafficDAO


class ArticleDistributionDAO(
    ArticleDistributionReportSummaryDAO,
    ArticleDistributionReportOverviewDAO,
    ArticleDistributionReportMissingTrafficDAO,
    ArticleDistributionArticleDAO,
    ArticleDistributionTrafficDAO,
    ArticleDistributionAPIKeyDAO,
):
    pass


__all__ = ["ArticleDistributionDAO"]
