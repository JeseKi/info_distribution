# -*- coding: utf-8 -*-
"""Article distribution service layer."""

from __future__ import annotations

import hashlib
import hmac
import secrets
from datetime import date, datetime, timezone
from urllib.parse import urlparse

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.server.auth.models import User
from src.server.auth.schemas import UserRole

from .dao import ArticleDistributionDAO
from .models import (
    ArticleDistributionAPIKey,
    ArticleDistributionAccount,
    ArticleDistributionArticle,
)
from .schemas import (
    AccountCreate,
    AccountStatusFilter,
    AccountUpdate,
    AccountDirectoryOut,
    ArticleBatchCreate,
    ArticleDistributionPlatformSummaryOut,
    ArticleDistributionPendingArticleOut,
    ArticlePageOut,
    ArticleDistributionReportOut,
    ArticleDistributionReportSummaryOut,
    ArticleDistributionPendingUserOut,
    ArticleOut,
    ArticleStatusCountsOut,
    ArticleUpdate,
    ArticleUploadItem,
    PublishStatus,
    PublicationType,
    UserAccountDirectoryOut,
)

API_KEY_PREFIX = "adv1"
API_KEY_PREFIX_LENGTH = 16


def list_accounts(
    db: Session,
    *,
    current_user: User,
    user_id: int | None = None,
    platform: str | None = None,
    publication_type: str | None = None,
    is_active: bool | None = None,
) -> list[ArticleDistributionAccount]:
    target_user_id = _resolve_optional_target_user_id(current_user, user_id)
    return ArticleDistributionDAO(db).list_accounts(
        user_id=target_user_id,
        platform=_normalize_optional(platform),
        publication_type=publication_type,
        is_active=is_active,
    )


def list_account_directory(db: Session) -> list[UserAccountDirectoryOut]:
    grouped: dict[int, UserAccountDirectoryOut] = {}
    for account, owner in ArticleDistributionDAO(db).list_account_owner_rows(
        is_active=True
    ):
        publication_type = _normalize_publication_type(account.publication_type)
        if owner.id not in grouped:
            grouped[owner.id] = UserAccountDirectoryOut(
                id=owner.id,
                name=owner.name or owner.username,
                accounts=[],
            )
        grouped[owner.id].accounts.append(
            AccountDirectoryOut(
                id=account.id,
                platform=account.platform,
                account_name=account.account_name,
                publication_type=publication_type,
            )
        )
    return list(grouped.values())


def create_account(
    db: Session, *, payload: AccountCreate, current_user: User
) -> ArticleDistributionAccount:
    target_user_id = _resolve_target_user_id(current_user, payload.user_id)
    account = ArticleDistributionAccount(
        user_id=target_user_id,
        account_name=_normalize_required(payload.account_name, "账号名称不能为空"),
        platform=_normalize_required(payload.platform, "平台不能为空"),
        publication_type=payload.publication_type,
        is_active=payload.is_active,
    )
    try:
        return ArticleDistributionDAO(db).create_account(account)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="同一用户下已存在相同平台、账号名称和发布类型的账号",
        )


def update_account(
    db: Session, *, account_id: int, payload: AccountUpdate, current_user: User
) -> ArticleDistributionAccount:
    dao = ArticleDistributionDAO(db)
    account = _get_accessible_account(db, account_id, current_user, write=True)
    fields = payload.model_dump(exclude_unset=True)

    if "user_id" in fields:
        if current_user.role != UserRole.ADMIN:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权限")
        if fields["user_id"] is None:
            fields.pop("user_id")

    if "account_name" in fields and fields["account_name"] is not None:
        fields["account_name"] = _normalize_required(
            str(fields["account_name"]), "账号名称不能为空"
        )
    if "platform" in fields and fields["platform"] is not None:
        fields["platform"] = _normalize_required(str(fields["platform"]), "平台不能为空")

    try:
        return dao.update_account(account, **fields)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="同一用户下已存在相同平台、账号名称和发布类型的账号",
        )


def delete_account(db: Session, *, account_id: int, current_user: User) -> None:
    dao = ArticleDistributionDAO(db)
    account = _get_accessible_account(db, account_id, current_user, write=True)
    article_count = dao.list_articles(account_id=account.id)
    if article_count:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="账号下已有文章，不能删除",
        )
    dao.delete_account(account)


def list_articles(
    db: Session,
    *,
    current_user: User,
    user_id: int | None = None,
    account_id: int | None = None,
    scheduled_from: date | None = None,
    scheduled_to: date | None = None,
    publish_status: str | None = None,
    platform: str | None = None,
    publication_type: str | None = None,
) -> list[ArticleOut]:
    target_user_id = _resolve_optional_target_user_id(current_user, user_id)
    if account_id is not None:
        account = _get_accessible_account(db, account_id, current_user, write=False)
        if target_user_id is not None and account.user_id != target_user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权限")

    dao = ArticleDistributionDAO(db)
    articles = dao.list_articles(
        user_id=target_user_id,
        account_id=account_id,
        scheduled_from=scheduled_from,
        scheduled_to=scheduled_to,
        publish_status=publish_status,
        platform=_normalize_optional(platform),
        publication_type=publication_type,
    )
    return _articles_to_out(db, articles)


def list_articles_page(
    db: Session,
    *,
    current_user: User,
    user_id: int | None = None,
    account_id: int | None = None,
    scheduled_from: date | None = None,
    scheduled_to: date | None = None,
    publish_status: str | None = None,
    platform: str | None = None,
    publication_type: str | None = None,
    page: int = 1,
    page_size: int = 10,
) -> ArticlePageOut:
    target_user_id = _resolve_optional_target_user_id(current_user, user_id)
    if account_id is not None:
        account = _get_accessible_account(db, account_id, current_user, write=False)
        if target_user_id is not None and account.user_id != target_user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权限")

    dao = ArticleDistributionDAO(db)
    normalized_platform = _normalize_optional(platform)
    articles, total = dao.list_articles_page(
        user_id=target_user_id,
        account_id=account_id,
        scheduled_from=scheduled_from,
        scheduled_to=scheduled_to,
        publish_status=publish_status,
        platform=normalized_platform,
        publication_type=publication_type,
        page=page,
        page_size=page_size,
    )
    status_counts = dao.count_articles_by_status(
        user_id=target_user_id,
        account_id=account_id,
        scheduled_from=scheduled_from,
        scheduled_to=scheduled_to,
        publish_status=publish_status,
        platform=normalized_platform,
        publication_type=publication_type,
    )
    return ArticlePageOut(
        items=_articles_to_out(db, articles),
        total=total,
        page=page,
        page_size=page_size,
        status_counts=ArticleStatusCountsOut(
            unpublished=status_counts.get("unpublished", 0),
            published=status_counts.get("published", 0),
            invalid=status_counts.get("invalid", 0),
        ),
    )


def list_unpublished_report(
    db: Session,
    *,
    scheduled_from: date | None = None,
    scheduled_to: date | None = None,
    platform: str | None = None,
    publication_type: str | None = None,
    account_status: AccountStatusFilter = "active",
) -> ArticleDistributionReportOut:
    grouped: dict[int, ArticleDistributionPendingUserOut] = {}
    platform_summaries: dict[tuple[int, int], ArticleDistributionPlatformSummaryOut] = {}
    rows = ArticleDistributionDAO(db).list_report_article_owner_rows(
        scheduled_from=scheduled_from,
        scheduled_to=scheduled_to,
        platform=_normalize_optional(platform),
        publication_type=publication_type,
        account_status=account_status,
    )
    inactive_account_articles = 0
    for article, account, owner in rows:
        account_is_active = account.is_active
        if not account_is_active:
            inactive_account_articles += 1
        if owner.id not in grouped:
            grouped[owner.id] = ArticleDistributionPendingUserOut(
                user_id=owner.id,
                username=owner.username,
                name=owner.name,
                email=owner.email,
                remaining_count=0,
                published_count=0,
                invalid_count=0,
                platform_summaries=[],
                articles=[],
            )
        user_report = grouped[owner.id]
        summary_key = (owner.id, account.id)
        if summary_key not in platform_summaries:
            platform_summary = ArticleDistributionPlatformSummaryOut(
                account_id=account.id,
                account_name=account.account_name,
                platform=account.platform,
                publication_type=_normalize_publication_type(account.publication_type),
                account_is_active=account_is_active,
                published_count=0,
                unpublished_count=0,
                invalid_count=0,
                latest_published_url=None,
            )
            platform_summaries[summary_key] = platform_summary
            user_report.platform_summaries.append(platform_summary)
        platform_summary = platform_summaries[summary_key]
        if article.publish_status == "published":
            user_report.published_count += 1
            platform_summary.published_count += 1
            if article.published_url:
                platform_summary.latest_published_url = article.published_url
        elif article.publish_status == "invalid":
            user_report.invalid_count += 1
            platform_summary.invalid_count += 1
        else:
            if account_is_active:
                user_report.remaining_count += 1
                platform_summary.unpublished_count += 1
        user_report.articles.append(
            ArticleDistributionPendingArticleOut(
                id=article.id,
                title=article.title,
                markdown_content=article.markdown_content,
                scheduled_date=article.scheduled_date,
                account_id=account.id,
                account_name=account.account_name,
                platform=account.platform,
                publication_type=_normalize_publication_type(account.publication_type),
                account_is_active=account_is_active,
                publish_status=_normalize_publish_status(article.publish_status),
                published_url=article.published_url,
                created_at=article.created_at,
            )
        )
    users = list(grouped.values())
    return ArticleDistributionReportOut(
        summary=ArticleDistributionReportSummaryOut(
            total_users=len(users),
            unpublished_users=sum(1 for user in users if user.remaining_count > 0),
            published_articles=sum(user.published_count for user in users),
            unpublished_articles=sum(user.remaining_count for user in users),
            invalid_articles=sum(user.invalid_count for user in users),
            inactive_account_articles=inactive_account_articles,
        ),
        users=users,
    )


def get_article(db: Session, *, article_id: int, current_user: User) -> ArticleOut:
    article = _get_accessible_article(db, article_id, current_user)
    return _article_to_out(db, article)


def update_article_status(
    db: Session,
    *,
    article_id: int,
    publish_status: str,
    published_url: str | None,
    current_user: User,
) -> ArticleOut:
    article = _get_accessible_article(db, article_id, current_user)
    fields = _status_update_fields(publish_status, published_url)
    updated = ArticleDistributionDAO(db).update_article(
        article,
        **fields,
    )
    return _article_to_out(db, updated)


def update_article_as_admin(
    db: Session, *, article_id: int, payload: ArticleUpdate, current_user: User
) -> ArticleOut:
    _assert_admin(current_user)
    dao = ArticleDistributionDAO(db)
    article = dao.get_article(article_id)
    if article is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="文章不存在")

    fields = payload.model_dump(exclude_unset=True)
    if "account_id" in fields and fields["account_id"] is not None:
        account = _get_active_account_or_404(db, int(fields["account_id"]))
        fields["account_id"] = account.id
        fields["user_id"] = account.user_id
    if "title" in fields and fields["title"] is not None:
        fields["title"] = _normalize_required(str(fields["title"]), "标题不能为空")
    if "markdown_content" in fields and fields["markdown_content"] is not None:
        fields["markdown_content"] = _normalize_required(
            str(fields["markdown_content"]), "正文不能为空"
        )
    if "publish_status" in fields:
        status_value = fields.pop("publish_status")
        published_url = fields.pop("published_url", None)
        if status_value is not None:
            fields.update(_status_update_fields(str(status_value), published_url))
    elif "published_url" in fields:
        published_url = fields.pop("published_url")
        if article.publish_status == "published":
            fields["published_url"] = _normalize_published_url(published_url)

    updated = dao.update_article(article, **fields)
    return _article_to_out(db, updated)


def delete_article_as_admin(db: Session, *, article_id: int, current_user: User) -> None:
    _assert_admin(current_user)
    dao = ArticleDistributionDAO(db)
    article = dao.get_article(article_id)
    if article is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="文章不存在")
    dao.delete_article(article)


def create_articles_as_admin(
    db: Session, *, payload: ArticleBatchCreate, current_user: User
) -> list[ArticleOut]:
    _assert_admin(current_user)
    account = _get_active_account_or_404(db, payload.account_id)
    articles = _build_articles(
        account=account,
        items=payload.articles,
        source="admin",
        created_by_user_id=current_user.id,
        api_key_id=None,
    )
    created = ArticleDistributionDAO(db).create_articles(articles)
    return _articles_to_out(db, created)


def create_articles_with_api_key(
    db: Session,
    *,
    payload: ArticleBatchCreate,
    api_key: ArticleDistributionAPIKey,
) -> list[ArticleOut]:
    account = _get_active_account_or_404(db, payload.account_id)
    articles = _build_articles(
        account=account,
        items=payload.articles,
        source="api",
        created_by_user_id=api_key.created_by_user_id,
        api_key_id=api_key.id,
    )
    created = ArticleDistributionDAO(db).create_articles(articles)
    return _articles_to_out(db, created)


def list_api_keys(db: Session, *, current_user: User) -> list[ArticleDistributionAPIKey]:
    _assert_admin(current_user)
    return ArticleDistributionDAO(db).list_api_keys()


def create_api_key(
    db: Session, *, name: str, current_user: User
) -> tuple[ArticleDistributionAPIKey, str]:
    _assert_admin(current_user)
    normalized_name = _normalize_required(name, "API Key 名称不能为空")
    raw_key = _generate_api_key()
    api_key = ArticleDistributionAPIKey(
        name=normalized_name,
        key_prefix=raw_key[:API_KEY_PREFIX_LENGTH],
        key_hash=_hash_api_key(raw_key),
        created_by_user_id=current_user.id,
        is_active=True,
    )
    created = ArticleDistributionDAO(db).create_api_key(api_key)
    return created, raw_key


def revoke_api_key(
    db: Session, *, api_key_id: int, current_user: User
) -> ArticleDistributionAPIKey:
    _assert_admin(current_user)
    dao = ArticleDistributionDAO(db)
    api_key = dao.get_api_key(api_key_id)
    if api_key is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API Key 不存在")
    if not api_key.is_active:
        return api_key
    return dao.revoke_api_key(api_key, datetime.now(timezone.utc))


def authenticate_api_key(db: Session, raw_key: str | None) -> ArticleDistributionAPIKey:
    normalized = raw_key.strip() if isinstance(raw_key, str) else ""
    if not normalized:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="缺少 API Key")
    if not normalized.startswith(f"{API_KEY_PREFIX}_"):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="API Key 无效")

    key_hash = _hash_api_key(normalized)
    key_prefix = normalized[:API_KEY_PREFIX_LENGTH]
    dao = ArticleDistributionDAO(db)
    api_key = dao.find_active_api_key(key_hash=key_hash, key_prefix=key_prefix)
    if api_key is None or not hmac.compare_digest(api_key.key_hash, key_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="API Key 无效")
    return dao.mark_api_key_used(api_key, datetime.now(timezone.utc))


def _build_articles(
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
            title=_normalize_required(item.title, "标题不能为空"),
            markdown_content=_normalize_required(item.markdown_content, "正文不能为空"),
            scheduled_date=item.scheduled_date,
            publish_status="unpublished",
            source=source,
            created_by_user_id=created_by_user_id,
            api_key_id=api_key_id,
        )
        for item in items
    ]


def _get_accessible_account(
    db: Session, account_id: int, current_user: User, *, write: bool
) -> ArticleDistributionAccount:
    account = _get_account_or_404(db, account_id)
    if current_user.role == UserRole.ADMIN:
        return account
    if account.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权限")
    return account


def _get_account_or_404(db: Session, account_id: int) -> ArticleDistributionAccount:
    account = ArticleDistributionDAO(db).get_account(account_id)
    if account is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="账号不存在")
    return account


def _get_active_account_or_404(
    db: Session, account_id: int
) -> ArticleDistributionAccount:
    account = _get_account_or_404(db, account_id)
    if not account.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="账号已停用，不能新增文章",
        )
    return account


def _get_accessible_article(
    db: Session, article_id: int, current_user: User
) -> ArticleDistributionArticle:
    article = ArticleDistributionDAO(db).get_article(article_id)
    if article is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="文章不存在")
    if current_user.role == UserRole.ADMIN or article.user_id == current_user.id:
        return article
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权限")


def _resolve_target_user_id(current_user: User, requested_user_id: int | None) -> int:
    if requested_user_id is None:
        return current_user.id
    if current_user.role == UserRole.ADMIN:
        return requested_user_id
    if requested_user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权限")
    return current_user.id


def _resolve_optional_target_user_id(
    current_user: User, requested_user_id: int | None
) -> int | None:
    if requested_user_id is None and current_user.role == UserRole.ADMIN:
        return None
    return _resolve_target_user_id(current_user, requested_user_id)


def _assert_admin(user: User) -> None:
    if user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="需要管理员权限")


def _articles_to_out(
    db: Session, articles: list[ArticleDistributionArticle]
) -> list[ArticleOut]:
    return [_article_to_out(db, article) for article in articles]


def _article_to_out(db: Session, article: ArticleDistributionArticle) -> ArticleOut:
    account = ArticleDistributionDAO(db).get_account(article.account_id)
    return ArticleOut.model_validate({**article.__dict__, "account": account})


def _normalize_required(value: str, error_message: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_message)
    return normalized


def _normalize_optional(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip()
    return normalized or None


def _normalize_publication_type(value: str) -> PublicationType:
    if value == "video":
        return "video"
    if value == "article":
        return "article"
    if value == "image_text":
        return "image_text"
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="账号发布类型无效",
    )


def _normalize_publish_status(value: str) -> PublishStatus:
    if value == "unpublished":
        return "unpublished"
    if value == "published":
        return "published"
    if value == "invalid":
        return "invalid"
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="文章发布状态无效",
    )


def _status_update_fields(
    publish_status: str, published_url: str | None
) -> dict[str, str | None]:
    normalized_status = _normalize_publish_status(publish_status)
    if normalized_status == "published":
        return {
            "publish_status": normalized_status,
            "published_url": _normalize_published_url(published_url),
        }
    return {"publish_status": normalized_status, "published_url": None}


def _normalize_published_url(value: str | None) -> str:
    normalized = _normalize_optional(value)
    if not normalized:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="标记已发布时必须填写发布地址",
        )
    parsed = urlparse(normalized)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="发布地址必须是 http 或 https URL",
        )
    return normalized


def _generate_api_key() -> str:
    return f"{API_KEY_PREFIX}_{secrets.token_urlsafe(32)}"


def _hash_api_key(raw_key: str) -> str:
    return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()
