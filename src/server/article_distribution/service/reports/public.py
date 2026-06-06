# -*- coding: utf-8 -*-
"""Public report and export services."""

from __future__ import annotations

import csv
from datetime import date
from io import StringIO

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from src.server.auth.models import User

from ...dao import ArticleDistributionDAO
from ...schemas import (
    AccountStatusFilter,
    ArticleDistributionPublicArticleOut,
    ArticleDistributionPublicDashboardOut,
    ArticleDistributionReportSummaryOut,
    ArticleTrafficStatOut,
)
from ..helpers import assert_admin, normalize_optional, normalize_publication_type

def list_public_dashboard(
    db: Session,
    *,
    scheduled_from: date | None = None,
    scheduled_to: date | None = None,
    publication_type: str | None = None,
    page: int = 1,
    page_size: int = 10,
) -> ArticleDistributionPublicDashboardOut:
    dao = ArticleDistributionDAO(db)
    summary_rows = dao.list_report_user_summary_rows(
        scheduled_from=scheduled_from,
        scheduled_to=scheduled_to,
        publication_type=publication_type,
        account_status="active",
    )
    article_rows, total = dao.list_public_published_article_rows_page(
        scheduled_from=scheduled_from,
        scheduled_to=scheduled_to,
        publication_type=publication_type,
        page=page,
        page_size=page_size,
    )
    latest_traffic_stats = dao.latest_traffic_stats_by_article_ids(
        [article.id for article, _ in article_rows]
    )

    published_articles = [
        ArticleDistributionPublicArticleOut(
            id=article.id,
            title=article.title,
            published_at=article.scheduled_date,
            published_url=article.published_url or "",
            account_name=account.account_name,
            platform=account.platform,
            publication_type=normalize_publication_type(account.publication_type),
            latest_traffic_stat=(
                ArticleTrafficStatOut.model_validate(latest_traffic_stats[article.id])
                if article.id in latest_traffic_stats
                else None
            ),
        )
        for article, account in article_rows
    ]
    return ArticleDistributionPublicDashboardOut(
        summary=ArticleDistributionReportSummaryOut(
            total_users=len(summary_rows),
            unpublished_users=sum(1 for row in summary_rows if row[2] > 0),
            published_articles=sum(row[1] for row in summary_rows),
            unpublished_articles=sum(row[2] for row in summary_rows),
            invalid_articles=sum(row[3] for row in summary_rows),
            inactive_account_articles=sum(row[4] for row in summary_rows),
            read_count=sum(row[5] for row in summary_rows),
            like_count=sum(row[6] for row in summary_rows),
            favorite_count=sum(row[7] for row in summary_rows),
            share_count=sum(row[8] for row in summary_rows),
        ),
        articles=published_articles,
        total=total,
        page=page,
        page_size=page_size,
    )


PUBLICITY_RECORD_CSV_HEADERS = [
    "文章ID",
    "发布日期",
    "负责人ID",
    "负责人",
    "用户名",
    "邮箱",
    "平台",
    "发布账号",
    "发布类型",
    "账号状态",
    "标题",
    "链接",
    "最近阅读量",
    "最近点赞量",
    "最近收藏量",
    "最近转发量",
    "最近统计时间",
]

PUBLICATION_TYPE_LABELS = {
    "video": "视频",
    "article": "文章",
    "image_text": "图文",
}


def build_publicity_records_csv(
    db: Session,
    *,
    current_user: User,
    scheduled_from: date | None = None,
    scheduled_to: date | None = None,
    platform: str | None = None,
    publication_type: str | None = None,
    account_status: AccountStatusFilter = "all",
) -> str:
    assert_admin(current_user)
    effective_scheduled_to = scheduled_to or date.today()
    if scheduled_from is not None and scheduled_from > effective_scheduled_to:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="计划日期范围无效",
        )

    dao = ArticleDistributionDAO(db)
    rows = dao.list_publicity_record_rows(
        scheduled_from=scheduled_from,
        scheduled_to=effective_scheduled_to,
        platform=normalize_optional(platform),
        publication_type=publication_type,
        account_status=account_status,
    )
    latest_traffic_stats = dao.latest_traffic_stats_by_article_ids(
        [article.id for article, _, _ in rows]
    )

    output = StringIO(newline="")
    writer = csv.writer(output)
    writer.writerow(PUBLICITY_RECORD_CSV_HEADERS)
    for article, account, owner in rows:
        latest_stat = latest_traffic_stats.get(article.id)
        writer.writerow(
            [
                article.id,
                article.scheduled_date.isoformat(),
                owner.id,
                owner.name or owner.username,
                owner.username,
                owner.email,
                account.platform,
                account.account_name,
                PUBLICATION_TYPE_LABELS.get(
                    account.publication_type, account.publication_type
                ),
                "启用" if account.is_active else "停用",
                article.title,
                article.published_url or "",
                latest_stat.read_count if latest_stat is not None else "",
                latest_stat.like_count if latest_stat is not None else "",
                latest_stat.favorite_count if latest_stat is not None else "",
                latest_stat.share_count if latest_stat is not None else "",
                latest_stat.recorded_at.isoformat() if latest_stat is not None else "",
            ]
        )
    return "\ufeff" + output.getvalue()
