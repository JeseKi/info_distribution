# -*- coding: utf-8 -*-
"""Article distribution models."""

from __future__ import annotations

from datetime import date, datetime, timezone

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from src.server.database import Base


class ArticleDistributionAccount(Base):
    __tablename__ = "article_distribution_accounts"
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "account_name",
            "platform",
            "publication_type",
            name="uq_article_distribution_account_identity",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    account_name: Mapped[str] = mapped_column(String(120), nullable=False)
    platform: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    publication_type: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    theme_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


class ArticleDistributionArticle(Base):
    __tablename__ = "article_distribution_articles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    account_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    project_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    keyword: Mapped[str] = mapped_column(String(200), nullable=False, default="无")
    markdown_content: Mapped[str] = mapped_column(Text, nullable=False)
    article_metadata: Mapped[dict | None] = mapped_column(
        "metadata", JSON, nullable=True
    )
    scheduled_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    publish_status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="unpublished", index=True
    )
    published_url: Mapped[str | None] = mapped_column(String(2048), default=None)
    source: Mapped[str] = mapped_column(String(40), nullable=False, default="web")
    created_by_user_id: Mapped[int | None] = mapped_column(Integer, default=None)
    api_key_id: Mapped[int | None] = mapped_column(Integer, default=None)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


class ArticleDistributionAPIKey(Base):
    __tablename__ = "article_distribution_api_keys"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    key_prefix: Mapped[str] = mapped_column(String(24), nullable=False, index=True)
    key_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    created_by_user_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    last_used_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=None
    )
    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=None
    )


class ArticleDistributionTrafficStat(Base):
    __tablename__ = "article_distribution_traffic_stats"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    account_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    article_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    read_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    like_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    favorite_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    share_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    comment_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
