# -*- coding: utf-8 -*-
"""Article service builders for article distribution."""

from __future__ import annotations

from sqlalchemy.orm import Session

from ..models import ArticleDistributionAccount, ArticleDistributionArticle
from ..schemas import (
    ArticleUploadItem,
    ArticleV1Update,
    ArticleV2Update,
    ArticleV2UploadItem,
)
from .helpers import (
    get_active_account_or_404,
    normalize_published_url,
    normalize_required,
    status_update_fields,
)


def build_articles(
    *,
    account: ArticleDistributionAccount,
    items: list[ArticleUploadItem],
    source: str,
    created_by_user_id: int | None,
    api_key_id: int | None,
) -> list[ArticleDistributionArticle]:
    return [
        ArticleDistributionArticle(
            user_id=account.user_id,
            account_id=account.id,
            project_id=item.project_id,
            title=normalize_required(item.title, "标题不能为空"),
            markdown_content=normalize_required(item.markdown_content, "正文不能为空"),
            article_metadata=item.metadata,
            scheduled_date=item.scheduled_date,
            publish_status="unpublished",
            source=source,
            created_by_user_id=created_by_user_id,
            api_key_id=api_key_id,
        )
        for item in items
    ]


def build_v2_articles(
    *,
    account: ArticleDistributionAccount,
    items: list[ArticleV2UploadItem],
    project_id: int,
    source: str,
    created_by_user_id: int | None,
    api_key_id: int | None,
) -> list[ArticleDistributionArticle]:
    return [
        ArticleDistributionArticle(
            user_id=account.user_id,
            account_id=account.id,
            project_id=project_id,
            title=normalize_required(item.title, "标题不能为空"),
            markdown_content=normalize_required(item.markdown_content, "正文不能为空"),
            article_metadata=item.metadata,
            scheduled_date=item.scheduled_date,
            publish_status="unpublished",
            source=source,
            created_by_user_id=created_by_user_id,
            api_key_id=api_key_id,
        )
        for item in items
    ]


def v1_update_fields(
    db: Session,
    *,
    article: ArticleDistributionArticle,
    payload: ArticleV1Update,
) -> dict[str, object]:
    raw_fields = payload.model_dump(exclude_unset=True)
    fields: dict[str, object] = {}

    account_id = raw_fields.get("account_id")
    if account_id is not None:
        account = get_active_account_or_404(db, int(account_id))
        fields["account_id"] = account.id
        fields["user_id"] = account.user_id

    title = non_empty_string(raw_fields.get("title"))
    if title is not None:
        fields["title"] = title

    markdown_content = non_empty_string(raw_fields.get("markdown_content"))
    if markdown_content is not None:
        fields["markdown_content"] = markdown_content

    if raw_fields.get("scheduled_date") is not None:
        fields["scheduled_date"] = raw_fields["scheduled_date"]

    metadata = raw_fields.get("metadata")
    if isinstance(metadata, dict) and metadata:
        fields["article_metadata"] = metadata

    if "publish_status" in raw_fields and raw_fields["publish_status"] is not None:
        publish_status = str(raw_fields["publish_status"])
        published_url = non_empty_string(raw_fields.get("published_url"))
        if publish_status == "published" and published_url is None:
            published_url = article.published_url
        fields.update(status_update_fields(publish_status, published_url))
    else:
        published_url = non_empty_string(raw_fields.get("published_url"))
        if published_url is not None and article.publish_status == "published":
            fields["published_url"] = normalize_published_url(published_url)

    return fields


def v2_update_fields(
    db: Session,
    *,
    article: ArticleDistributionArticle,
    payload: ArticleV2Update,
) -> dict[str, object]:
    raw_fields = payload.model_dump(exclude_unset=True)
    legacy_fields = {key: value for key, value in raw_fields.items() if key != "project_id"}
    fields = v1_update_fields(db, article=article, payload=ArticleV1Update(**legacy_fields))

    if raw_fields.get("project_id") is not None:
        fields["project_id"] = int(raw_fields["project_id"])
    elif raw_fields.get("account_id") is not None:
        fields["project_id"] = article.project_id

    return fields


def non_empty_string(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    normalized = value.strip()
    return normalized or None
