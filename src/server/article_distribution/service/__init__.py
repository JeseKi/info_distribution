# -*- coding: utf-8 -*-
"""Article distribution service layer."""

from .accounts import (
    create_account,
    delete_account,
    list_account_directory,
    list_accounts,
    update_account,
)
from .api_keys import (
    authenticate_api_key,
    create_api_key,
    list_api_keys,
    revoke_api_key,
)
from .articles import (
    create_articles_as_admin,
    create_articles_with_api_key,
    delete_article_as_admin,
    get_article,
    list_articles,
    list_articles_page,
    update_article_as_admin,
    update_article_status,
)
from .reports import (
    get_unpublished_report_user_detail,
    list_missing_traffic_articles,
    list_public_dashboard,
    list_unpublished_report,
)
from .traffic import (
    create_article_traffic_stat,
    delete_article_traffic_stat,
    list_article_traffic_stats,
    list_article_traffic_summaries,
)

__all__ = [
    "authenticate_api_key",
    "create_account",
    "create_api_key",
    "create_articles_as_admin",
    "create_articles_with_api_key",
    "create_article_traffic_stat",
    "delete_account",
    "delete_article_as_admin",
    "delete_article_traffic_stat",
    "get_article",
    "get_unpublished_report_user_detail",
    "list_account_directory",
    "list_accounts",
    "list_article_traffic_stats",
    "list_article_traffic_summaries",
    "list_api_keys",
    "list_missing_traffic_articles",
    "list_public_dashboard",
    "list_articles",
    "list_articles_page",
    "list_unpublished_report",
    "revoke_api_key",
    "update_account",
    "update_article_as_admin",
    "update_article_status",
]
