# -*- coding: utf-8 -*-
"""Article distribution router tests."""

from __future__ import annotations

import socket

import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session

from src.server.article_distribution import router as article_distribution_router
from src.server.article_distribution.models import ArticleDistributionAPIKey
from src.server.auth.models import User
from src.server.auth.schemas import UserRole
from src.server.auth import service as auth_service


def _create_user(
    db: Session,
    *,
    username: str,
    role: UserRole = UserRole.USER,
    name: str | None = None,
) -> User:
    user = User(
        username=username,
        email=f"{username}@example.com",
        name=username if name is None else name,
        role=role,
    )
    user.set_password("Password123")
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _headers(user: User) -> dict[str, str]:
    token = auth_service.create_access_token(
        {
            "sub": user.username,
            "scope": auth_service.get_user_scopes(user),
            "tv": user.token_version,
        }
    )
    return {"Authorization": f"Bearer {token}"}


def test_image_proxy_allows_trusted_fstc_private_address(monkeypatch):
    def fake_getaddrinfo(host: str, port):
        assert host == "fstc.kispace.cc"
        assert port is None
        return [
            (
                socket.AF_INET,
                socket.SOCK_STREAM,
                6,
                "",
                ("172.29.0.33", 0),
            )
        ]

    monkeypatch.setattr(
        article_distribution_router.socket, "getaddrinfo", fake_getaddrinfo
    )

    url = "https://fstc.kispace.cc/i/8b2737602828b9d730105b75fb5f5309.jpg"
    assert article_distribution_router._validate_proxy_image_url(url) == url


def test_image_proxy_rejects_untrusted_private_address(monkeypatch):
    def fake_getaddrinfo(host: str, port):
        assert host == "private.example.com"
        assert port is None
        return [
            (
                socket.AF_INET,
                socket.SOCK_STREAM,
                6,
                "",
                ("172.29.0.33", 0),
            )
        ]

    monkeypatch.setattr(
        article_distribution_router.socket, "getaddrinfo", fake_getaddrinfo
    )

    with pytest.raises(HTTPException) as exc_info:
        article_distribution_router._validate_proxy_image_url(
            "https://private.example.com/image.jpg"
        )

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "不允许代理内网或本机图片地址"


def test_v1_account_directory_groups_accounts_by_user_with_api_key(
    test_client, test_db_session: Session
):
    owner_a = _create_user(test_db_session, username="owner_a", name="Owner A")
    owner_b = _create_user(test_db_session, username="owner_b", name="Owner B")
    owner_without_name = _create_user(
        test_db_session, username="owner_no_name", name=""
    )
    admin = _create_user(test_db_session, username="directory_admin", role=UserRole.ADMIN)

    created_accounts = []
    for user_id, publication_type in [
        (owner_a.id, "image_text"),
        (owner_a.id, "article"),
        (owner_b.id, "image_text"),
        (owner_without_name.id, "video"),
    ]:
        create_resp = test_client.post(
            "/api/article-distribution/accounts",
            headers=_headers(admin),
            json={
                "user_id": user_id,
                "account_name": "主号",
                "platform": "wechat",
                "publication_type": publication_type,
            },
        )
        assert create_resp.status_code == 201
        created_accounts.append(create_resp.json())

    key_resp = test_client.post(
        "/api/admin/article-distribution/api-keys",
        headers=_headers(admin),
        json={"name": "directory"},
    )
    assert key_resp.status_code == 201

    directory_resp = test_client.get(
        "/api/v1/article-distribution/accounts",
        headers={"X-API-Key": key_resp.json()["api_key"]},
    )

    assert directory_resp.status_code == 200
    assert directory_resp.json() == [
        {
            "id": owner_a.id,
            "name": "Owner A",
            "accounts": [
                {
                    "id": created_accounts[1]["id"],
                    "platform": "wechat",
                    "account_name": "主号",
                    "publication_type": "article",
                },
                {
                    "id": created_accounts[0]["id"],
                    "platform": "wechat",
                    "account_name": "主号",
                    "publication_type": "image_text",
                },
            ],
        },
        {
            "id": owner_b.id,
            "name": "Owner B",
            "accounts": [
                {
                    "id": created_accounts[2]["id"],
                    "platform": "wechat",
                    "account_name": "主号",
                    "publication_type": "image_text",
                },
            ],
        },
        {
            "id": owner_without_name.id,
            "name": "owner_no_name",
            "accounts": [
                {
                    "id": created_accounts[3]["id"],
                    "platform": "wechat",
                    "account_name": "主号",
                    "publication_type": "video",
                },
            ],
        },
    ]


def test_v1_account_directory_requires_api_key(
    test_client, test_db_session: Session
):
    response = test_client.get("/api/v1/article-distribution/accounts")

    assert response.status_code == 401


def test_user_can_manage_own_accounts(test_client, test_db_session: Session):
    user = _create_user(test_db_session, username="dist_user")

    create_resp = test_client.post(
        "/api/article-distribution/accounts",
        headers=_headers(user),
        json={
            "account_name": "主号",
            "platform": "知乎",
            "publication_type": "article",
        },
    )

    assert create_resp.status_code == 201
    account = create_resp.json()
    assert account["user_id"] == user.id
    assert account["account_name"] == "主号"

    list_resp = test_client.get(
        "/api/article-distribution/accounts", headers=_headers(user)
    )
    assert list_resp.status_code == 200
    assert [item["id"] for item in list_resp.json()] == [account["id"]]


def test_user_cannot_access_other_users_articles(
    test_client, test_db_session: Session
):
    owner = _create_user(test_db_session, username="owner")
    other = _create_user(test_db_session, username="other")
    admin = _create_user(test_db_session, username="article_admin", role=UserRole.ADMIN)

    account_resp = test_client.post(
        "/api/article-distribution/accounts",
        headers=_headers(owner),
        json={
            "account_name": "公众号",
            "platform": "wechat",
            "publication_type": "image_text",
        },
    )
    account_id = account_resp.json()["id"]

    upload_resp = test_client.post(
        "/api/admin/article-distribution/articles",
        headers=_headers(admin),
        json={
            "account_id": account_id,
            "articles": [
                {
                    "title": "A",
                    "markdown_content": "# A",
                    "scheduled_date": "2026-05-20",
                }
            ],
        },
    )
    assert upload_resp.status_code == 201
    article_id = upload_resp.json()[0]["id"]

    denied_resp = test_client.get(
        f"/api/article-distribution/articles/{article_id}", headers=_headers(other)
    )
    assert denied_resp.status_code == 403


def test_admin_and_api_key_can_upload_articles(
    test_client, test_db_session: Session
):
    owner = _create_user(test_db_session, username="api_owner")
    admin = _create_user(test_db_session, username="api_admin", role=UserRole.ADMIN)

    account_resp = test_client.post(
        "/api/article-distribution/accounts",
        headers=_headers(admin),
        json={
            "user_id": owner.id,
            "account_name": "知乎号",
            "platform": "zhihu",
            "publication_type": "article",
        },
    )
    assert account_resp.status_code == 201
    account_id = account_resp.json()["id"]

    key_resp = test_client.post(
        "/api/admin/article-distribution/api-keys",
        headers=_headers(admin),
        json={"name": "integration"},
    )
    assert key_resp.status_code == 201
    raw_key = key_resp.json()["api_key"]
    assert raw_key.startswith("adv1_")

    api_resp = test_client.post(
        "/api/v1/article-distribution/articles",
        headers={"X-API-Key": raw_key},
        json={
            "account_id": account_id,
            "articles": [
                {
                    "title": "API article",
                    "markdown_content": "body",
                    "scheduled_date": "2026-05-21",
                },
                {
                    "title": "API article 2",
                    "markdown_content": "body2",
                    "scheduled_date": "2026-05-21",
                },
            ],
        },
    )
    assert api_resp.status_code == 201
    data = api_resp.json()
    assert len(data) == 2
    assert data[0]["user_id"] == owner.id
    assert data[0]["source"] == "api"

    stored_key = test_db_session.query(ArticleDistributionAPIKey).first()
    assert stored_key is not None
    assert stored_key.last_used_at is not None


def test_inactive_accounts_are_hidden_from_directory_and_reject_uploads(
    test_client, test_db_session: Session
):
    owner = _create_user(test_db_session, username="inactive_owner")
    admin = _create_user(test_db_session, username="inactive_admin", role=UserRole.ADMIN)

    account_resp = test_client.post(
        "/api/article-distribution/accounts",
        headers=_headers(admin),
        json={
            "user_id": owner.id,
            "account_name": "封禁号",
            "platform": "wechat",
            "publication_type": "article",
        },
    )
    assert account_resp.status_code == 201
    account = account_resp.json()
    assert account["is_active"] is True

    inactive_resp = test_client.patch(
        f"/api/article-distribution/accounts/{account['id']}",
        headers=_headers(owner),
        json={"is_active": False},
    )
    assert inactive_resp.status_code == 200
    assert inactive_resp.json()["is_active"] is False

    key_resp = test_client.post(
        "/api/admin/article-distribution/api-keys",
        headers=_headers(admin),
        json={"name": "inactive-directory"},
    )
    assert key_resp.status_code == 201
    raw_key = key_resp.json()["api_key"]

    directory_resp = test_client.get(
        "/api/v1/article-distribution/accounts",
        headers={"X-API-Key": raw_key},
    )
    assert directory_resp.status_code == 200
    assert directory_resp.json() == []

    upload_payload = {
        "account_id": account["id"],
        "articles": [
            {
                "title": "Blocked",
                "markdown_content": "body",
                "scheduled_date": "2026-05-25",
            }
        ],
    }
    admin_upload_resp = test_client.post(
        "/api/admin/article-distribution/articles",
        headers=_headers(admin),
        json=upload_payload,
    )
    assert admin_upload_resp.status_code == 400
    assert admin_upload_resp.json()["detail"] == "账号已停用，不能新增文章"

    api_upload_resp = test_client.post(
        "/api/v1/article-distribution/articles",
        headers={"X-API-Key": raw_key},
        json=upload_payload,
    )
    assert api_upload_resp.status_code == 400
    assert api_upload_resp.json()["detail"] == "账号已停用，不能新增文章"


def test_publish_status_and_filters(test_client, test_db_session: Session):
    owner = _create_user(test_db_session, username="filter_owner")
    admin = _create_user(test_db_session, username="filter_admin", role=UserRole.ADMIN)

    account_resp = test_client.post(
        "/api/article-distribution/accounts",
        headers=_headers(owner),
        json={
            "account_name": "视频号",
            "platform": "shipinhao",
            "publication_type": "video",
        },
    )
    account_id = account_resp.json()["id"]
    upload_resp = test_client.post(
        "/api/admin/article-distribution/articles",
        headers=_headers(admin),
        json={
            "account_id": account_id,
            "articles": [
                {
                    "title": "Video",
                    "markdown_content": "content",
                    "scheduled_date": "2026-05-22",
                }
            ],
        },
    )
    article_id = upload_resp.json()[0]["id"]

    missing_url_resp = test_client.patch(
        f"/api/article-distribution/articles/{article_id}/status",
        headers=_headers(owner),
        json={"publish_status": "published"},
    )
    assert missing_url_resp.status_code == 400

    status_resp = test_client.patch(
        f"/api/article-distribution/articles/{article_id}/status",
        headers=_headers(owner),
        json={
            "publish_status": "published",
            "published_url": "https://example.com/video",
        },
    )
    assert status_resp.status_code == 200
    assert status_resp.json()["publish_status"] == "published"
    assert status_resp.json()["published_url"] == "https://example.com/video"

    filtered_resp = test_client.get(
        "/api/article-distribution/articles",
        headers=_headers(owner),
        params={
            "publish_status": "published",
            "publication_type": "video",
            "scheduled_from": "2026-05-22",
            "scheduled_to": "2026-05-22",
        },
    )
    assert filtered_resp.status_code == 200
    assert [item["id"] for item in filtered_resp.json()] == [article_id]

    invalid_resp = test_client.patch(
        f"/api/article-distribution/articles/{article_id}/status",
        headers=_headers(owner),
        json={"publish_status": "invalid"},
    )
    assert invalid_resp.status_code == 200
    assert invalid_resp.json()["publish_status"] == "invalid"
    assert invalid_resp.json()["published_url"] is None


def test_admin_can_list_update_and_delete_all_articles(
    test_client, test_db_session: Session
):
    owner = _create_user(test_db_session, username="admin_crud_owner")
    admin = _create_user(test_db_session, username="admin_crud_admin", role=UserRole.ADMIN)

    account_resp = test_client.post(
        "/api/article-distribution/accounts",
        headers=_headers(admin),
        json={
            "user_id": owner.id,
            "account_name": "公众号",
            "platform": "wechat",
            "publication_type": "article",
        },
    )
    assert account_resp.status_code == 201
    account_id = account_resp.json()["id"]

    upload_resp = test_client.post(
        "/api/admin/article-distribution/articles",
        headers=_headers(admin),
        json={
            "account_id": account_id,
            "articles": [
                {
                    "title": "Original",
                    "markdown_content": "body",
                    "scheduled_date": "2026-05-23",
                }
            ],
        },
    )
    assert upload_resp.status_code == 201
    article_id = upload_resp.json()[0]["id"]

    admin_list_resp = test_client.get(
        "/api/article-distribution/articles", headers=_headers(admin)
    )
    assert admin_list_resp.status_code == 200
    assert [item["id"] for item in admin_list_resp.json()] == [article_id]

    update_resp = test_client.patch(
        f"/api/admin/article-distribution/articles/{article_id}",
        headers=_headers(admin),
        json={
            "title": "Updated",
            "markdown_content": "updated body",
            "scheduled_date": "2026-05-24",
        },
    )
    assert update_resp.status_code == 200, update_resp.text
    assert update_resp.json()["title"] == "Updated"
    assert update_resp.json()["markdown_content"] == "updated body"
    assert update_resp.json()["scheduled_date"] == "2026-05-24"

    delete_resp = test_client.delete(
        f"/api/admin/article-distribution/articles/{article_id}",
        headers=_headers(admin),
    )
    assert delete_resp.status_code == 204

    owner_list_resp = test_client.get(
        "/api/article-distribution/articles", headers=_headers(owner)
    )
    assert owner_list_resp.status_code == 200
    assert owner_list_resp.json() == []


def test_paginated_article_list_supports_filters_counts_and_access_scope(
    test_client, test_db_session: Session
):
    owner = _create_user(test_db_session, username="page_owner")
    other = _create_user(test_db_session, username="page_other")
    admin = _create_user(test_db_session, username="page_admin", role=UserRole.ADMIN)

    owner_account_resp = test_client.post(
        "/api/article-distribution/accounts",
        headers=_headers(admin),
        json={
            "user_id": owner.id,
            "account_name": "Owner Account",
            "platform": "wechat",
            "publication_type": "article",
        },
    )
    other_account_resp = test_client.post(
        "/api/article-distribution/accounts",
        headers=_headers(admin),
        json={
            "user_id": other.id,
            "account_name": "Other Account",
            "platform": "wechat",
            "publication_type": "article",
        },
    )
    assert owner_account_resp.status_code == 201
    assert other_account_resp.status_code == 201
    owner_account_id = owner_account_resp.json()["id"]
    other_account_id = other_account_resp.json()["id"]

    upload_owner_resp = test_client.post(
        "/api/admin/article-distribution/articles",
        headers=_headers(admin),
        json={
            "account_id": owner_account_id,
            "articles": [
                {
                    "title": f"Owner Article {index}",
                    "markdown_content": "body",
                    "scheduled_date": f"2026-06-{index:02d}",
                }
                for index in range(1, 13)
            ],
        },
    )
    upload_other_resp = test_client.post(
        "/api/admin/article-distribution/articles",
        headers=_headers(admin),
        json={
            "account_id": other_account_id,
            "articles": [
                {
                    "title": "Other Article",
                    "markdown_content": "body",
                    "scheduled_date": "2026-06-20",
                }
            ],
        },
    )
    assert upload_owner_resp.status_code == 201
    assert upload_other_resp.status_code == 201
    owner_articles = upload_owner_resp.json()

    published_resp = test_client.patch(
        f"/api/article-distribution/articles/{owner_articles[0]['id']}/status",
        headers=_headers(owner),
        json={
            "publish_status": "published",
            "published_url": "https://example.com/published",
        },
    )
    invalid_resp = test_client.patch(
        f"/api/article-distribution/articles/{owner_articles[1]['id']}/status",
        headers=_headers(owner),
        json={"publish_status": "invalid"},
    )
    assert published_resp.status_code == 200
    assert invalid_resp.status_code == 200

    page_resp = test_client.get(
        "/api/article-distribution/articles/page",
        headers=_headers(owner),
        params={"page": 2, "page_size": 5, "publication_type": "article"},
    )
    assert page_resp.status_code == 200, page_resp.text
    page_data = page_resp.json()
    assert page_data["total"] == 12
    assert page_data["page"] == 2
    assert page_data["page_size"] == 5
    assert len(page_data["items"]) == 5
    assert [item["title"] for item in page_data["items"]] == [
        "Owner Article 7",
        "Owner Article 6",
        "Owner Article 5",
        "Owner Article 4",
        "Owner Article 3",
    ]
    assert page_data["status_counts"] == {
        "unpublished": 10,
        "published": 1,
        "invalid": 1,
    }

    invalid_page_resp = test_client.get(
        "/api/article-distribution/articles/page",
        headers=_headers(owner),
        params={"publish_status": "invalid", "page": 1, "page_size": 10},
    )
    assert invalid_page_resp.status_code == 200
    invalid_page = invalid_page_resp.json()
    assert invalid_page["total"] == 1
    assert invalid_page["items"][0]["publish_status"] == "invalid"
    assert invalid_page["status_counts"] == {
        "unpublished": 0,
        "published": 0,
        "invalid": 1,
    }

    other_page_resp = test_client.get(
        "/api/article-distribution/articles/page",
        headers=_headers(other),
        params={"page": 1, "page_size": 10},
    )
    assert other_page_resp.status_code == 200
    assert other_page_resp.json()["total"] == 1
    assert other_page_resp.json()["items"][0]["title"] == "Other Article"

    admin_page_resp = test_client.get(
        "/api/article-distribution/articles/page",
        headers=_headers(admin),
        params={"page": 1, "page_size": 20},
    )
    assert admin_page_resp.status_code == 200
    assert admin_page_resp.json()["total"] == 13


def test_unpublished_report_scope_can_be_assigned_to_regular_user(
    test_client, test_db_session: Session
):
    owner_a = _create_user(test_db_session, username="pending_owner_a", name="Owner A")
    owner_b = _create_user(test_db_session, username="pending_owner_b", name="Owner B")
    viewer = _create_user(test_db_session, username="pending_viewer")
    admin = _create_user(test_db_session, username="pending_admin", role=UserRole.ADMIN)

    account_ids: list[int] = []
    for owner, account_name in [(owner_a, "公众号"), (owner_b, "知乎号")]:
        account_resp = test_client.post(
            "/api/article-distribution/accounts",
            headers=_headers(admin),
            json={
                "user_id": owner.id,
                "account_name": account_name,
                "platform": "wechat" if owner.id == owner_a.id else "zhihu",
                "publication_type": "article",
            },
        )
        assert account_resp.status_code == 201
        account_ids.append(account_resp.json()["id"])

    upload_a = test_client.post(
        "/api/admin/article-distribution/articles",
        headers=_headers(admin),
        json={
            "account_id": account_ids[0],
            "articles": [
                {
                    "title": "A unpublished",
                    "markdown_content": "body",
                    "scheduled_date": "2026-05-20",
                },
                {
                    "title": "A published",
                    "markdown_content": "body",
                    "scheduled_date": "2026-05-21",
                },
            ],
        },
    )
    assert upload_a.status_code == 201
    published_article_id = upload_a.json()[1]["id"]
    mark_published = test_client.patch(
        f"/api/article-distribution/articles/{published_article_id}/status",
        headers=_headers(owner_a),
        json={
            "publish_status": "published",
            "published_url": "https://example.com/a-published",
        },
    )
    assert mark_published.status_code == 200

    upload_b = test_client.post(
        "/api/admin/article-distribution/articles",
        headers=_headers(admin),
        json={
            "account_id": account_ids[1],
            "articles": [
                {
                    "title": "B unpublished",
                    "markdown_content": "body",
                    "scheduled_date": "2026-05-22",
                }
            ],
        },
    )
    assert upload_b.status_code == 201

    denied_resp = test_client.get(
        "/api/article-distribution/reports/unpublished",
        headers=_headers(viewer),
    )
    assert denied_resp.status_code == 403

    viewer.scope_overrides = auth_service.serialize_scopes(
        [
            *auth_service.get_role_scopes(UserRole.USER),
            auth_service.SCOPE_ARTICLE_DISTRIBUTION_REPORT_READ,
        ]
    )
    test_db_session.commit()
    test_db_session.refresh(viewer)

    report_resp = test_client.get(
        "/api/article-distribution/reports/unpublished",
        headers=_headers(viewer),
    )

    assert report_resp.status_code == 200, report_resp.text
    report = report_resp.json()
    assert report["summary"] == {
        "total_users": 2,
        "unpublished_users": 2,
        "published_articles": 1,
        "unpublished_articles": 2,
        "invalid_articles": 0,
        "inactive_account_articles": 0,
    }
    data = report["users"]
    assert [item["user_id"] for item in data] == [owner_a.id, owner_b.id]
    assert [item["remaining_count"] for item in data] == [1, 1]
    assert data[0]["published_count"] == 1
    assert data[0]["platform_summaries"][0]["published_count"] == 1
    assert data[0]["platform_summaries"][0]["latest_published_url"] == "https://example.com/a-published"
    assert data[0]["articles"][0]["title"] == "A unpublished"
    assert data[0]["articles"][0]["markdown_content"] == "body"
    assert data[0]["articles"][0]["account_name"] == "公众号"
    assert data[0]["articles"][0]["platform"] == "wechat"
    assert data[0]["articles"][0]["publish_status"] == "unpublished"
    assert data[0]["articles"][1]["publish_status"] == "published"
    assert "source" not in data[0]["articles"][0]
    assert data[1]["articles"][0]["title"] == "B unpublished"


def test_unpublished_report_tracks_inactive_account_articles_separately(
    test_client, test_db_session: Session
):
    owner = _create_user(test_db_session, username="inactive_report_owner")
    admin = _create_user(
        test_db_session, username="inactive_report_admin", role=UserRole.ADMIN
    )

    active_account_resp = test_client.post(
        "/api/article-distribution/accounts",
        headers=_headers(admin),
        json={
            "user_id": owner.id,
            "account_name": "启用号",
            "platform": "wechat",
            "publication_type": "article",
        },
    )
    inactive_account_resp = test_client.post(
        "/api/article-distribution/accounts",
        headers=_headers(admin),
        json={
            "user_id": owner.id,
            "account_name": "停用号",
            "platform": "wechat",
            "publication_type": "image_text",
        },
    )
    assert active_account_resp.status_code == 201
    assert inactive_account_resp.status_code == 201
    active_account_id = active_account_resp.json()["id"]
    inactive_account_id = inactive_account_resp.json()["id"]

    active_upload_resp = test_client.post(
        "/api/admin/article-distribution/articles",
        headers=_headers(admin),
        json={
            "account_id": active_account_id,
            "articles": [
                {
                    "title": "Active unpublished",
                    "markdown_content": "body",
                    "scheduled_date": "2026-05-26",
                }
            ],
        },
    )
    inactive_upload_resp = test_client.post(
        "/api/admin/article-distribution/articles",
        headers=_headers(admin),
        json={
            "account_id": inactive_account_id,
            "articles": [
                {
                    "title": "Inactive unpublished",
                    "markdown_content": "body",
                    "scheduled_date": "2026-05-26",
                },
                {
                    "title": "Inactive published",
                    "markdown_content": "body",
                    "scheduled_date": "2026-05-27",
                },
            ],
        },
    )
    assert active_upload_resp.status_code == 201
    assert inactive_upload_resp.status_code == 201
    inactive_published_id = inactive_upload_resp.json()[1]["id"]

    published_resp = test_client.patch(
        f"/api/article-distribution/articles/{inactive_published_id}/status",
        headers=_headers(owner),
        json={
            "publish_status": "published",
            "published_url": "https://example.com/inactive-published",
        },
    )
    assert published_resp.status_code == 200

    deactivate_resp = test_client.patch(
        f"/api/article-distribution/accounts/{inactive_account_id}",
        headers=_headers(owner),
        json={"is_active": False},
    )
    assert deactivate_resp.status_code == 200

    active_report_resp = test_client.get(
        "/api/article-distribution/reports/unpublished",
        headers=_headers(admin),
    )
    assert active_report_resp.status_code == 200
    active_report = active_report_resp.json()
    assert active_report["summary"] == {
        "total_users": 1,
        "unpublished_users": 1,
        "published_articles": 0,
        "unpublished_articles": 1,
        "invalid_articles": 0,
        "inactive_account_articles": 0,
    }
    assert active_report["users"][0]["remaining_count"] == 1
    assert [article["account_is_active"] for article in active_report["users"][0]["articles"]] == [True]

    all_report_resp = test_client.get(
        "/api/article-distribution/reports/unpublished",
        headers=_headers(admin),
        params={"account_status": "all"},
    )
    assert all_report_resp.status_code == 200
    all_report = all_report_resp.json()
    assert all_report["summary"] == {
        "total_users": 1,
        "unpublished_users": 1,
        "published_articles": 1,
        "unpublished_articles": 1,
        "invalid_articles": 0,
        "inactive_account_articles": 2,
    }
    all_user = all_report["users"][0]
    assert all_user["remaining_count"] == 1
    inactive_summary = next(
        summary
        for summary in all_user["platform_summaries"]
        if summary["account_id"] == inactive_account_id
    )
    assert inactive_summary["account_is_active"] is False
    assert inactive_summary["unpublished_count"] == 0
    assert [article["account_is_active"] for article in all_user["articles"]] == [
        True,
        False,
        False,
    ]

    inactive_report_resp = test_client.get(
        "/api/article-distribution/reports/unpublished",
        headers=_headers(admin),
        params={"account_status": "inactive"},
    )
    assert inactive_report_resp.status_code == 200
    inactive_report = inactive_report_resp.json()
    assert inactive_report["summary"] == {
        "total_users": 1,
        "unpublished_users": 0,
        "published_articles": 1,
        "unpublished_articles": 0,
        "invalid_articles": 0,
        "inactive_account_articles": 2,
    }
    assert inactive_report["users"][0]["remaining_count"] == 0
