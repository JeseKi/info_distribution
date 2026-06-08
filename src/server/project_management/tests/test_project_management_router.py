# -*- coding: utf-8 -*-
from __future__ import annotations

from sqlalchemy.orm import Session

from src.server.auth import service as auth_service
from src.server.auth.models import User
from src.server.auth.schemas import UserRole
from src.server.project_management.dao import ProjectManagementDAO
from src.server.project_management.service import set_user_projects


def _create_user(db: Session, username: str, role: UserRole = UserRole.USER) -> User:
    user = User(
        username=username,
        email=f"{username}@example.com",
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


def test_project_code_registration_attaches_project(test_client):
    email = "project-register@example.com"
    send_resp = test_client.post(
        "/api/auth/send-verification-code",
        json={"email": email},
    )
    assert send_resp.status_code == 200, send_resp.text
    code = auth_service.verification_codes[email]["code"]

    register_resp = test_client.post(
        "/api/auth/register-with-code",
        json={
            "username": "project_registered_user",
            "email": email,
            "password": "Password123",
            "code": code,
            "project_code": "AIFCAIFC",
        },
    )
    assert register_resp.status_code == 201, register_resp.text
    data = register_resp.json()
    assert [project["name"] for project in data["projects"]] == ["AIFC"]


def test_admin_can_manage_projects_themes_and_user_projects(
    test_client,
    test_db_session: Session,
):
    admin = _create_user(test_db_session, "project_admin", UserRole.ADMIN)
    member = _create_user(test_db_session, "project_member")
    headers = _headers(admin)

    theme_resp = test_client.post(
        "/api/admin/themes",
        headers=headers,
        json={"name": "ML", "is_active": True},
    )
    assert theme_resp.status_code == 201, theme_resp.text
    theme_id = theme_resp.json()["id"]

    project_resp = test_client.post(
        "/api/admin/projects",
        headers=headers,
        json={
            "name": "Research",
            "code": "RESEARCH",
            "is_active": True,
            "theme_ids": [theme_id],
        },
    )
    assert project_resp.status_code == 201, project_resp.text
    project = project_resp.json()
    assert project["code"] == "RESEARCH"
    assert project["themes"][0]["name"] == "ML"

    user_projects_resp = test_client.put(
        f"/api/admin/users/{member.id}/projects",
        headers=headers,
        json={"project_ids": [project["id"]]},
    )
    assert user_projects_resp.status_code == 200, user_projects_resp.text
    assert user_projects_resp.json()[0]["name"] == "Research"

    users_resp = test_client.get("/api/admin/users", headers=headers)
    assert users_resp.status_code == 200, users_resp.text
    member_row = next(item for item in users_resp.json() if item["id"] == member.id)
    assert [project["name"] for project in member_row["projects"]] == ["Research"]


def test_account_theme_must_be_accessible_to_owner(
    test_client,
    test_db_session: Session,
):
    admin = _create_user(test_db_session, "account_theme_admin", UserRole.ADMIN)
    owner = _create_user(test_db_session, "account_theme_owner")
    dao = ProjectManagementDAO(test_db_session)
    default_project = dao.get_project_by_code("AIFCAIFC")
    assert default_project is not None
    set_user_projects(test_db_session, owner.id, [default_project.id])

    inaccessible_theme_resp = test_client.post(
        "/api/admin/themes",
        headers=_headers(admin),
        json={"name": "Hidden Theme", "is_active": True},
    )
    assert inaccessible_theme_resp.status_code == 201, inaccessible_theme_resp.text

    denied_resp = test_client.post(
        "/api/article-distribution/accounts",
        headers=_headers(owner),
        json={
            "account_name": "主号",
            "platform": "公众号",
            "publication_type": "article",
            "theme_id": inaccessible_theme_resp.json()["id"],
        },
    )
    assert denied_resp.status_code == 400
    assert denied_resp.json()["detail"] == "账号主题必须来自该用户所在项目关联的主题"

    allowed_theme_id = dao.list_project_theme_ids(default_project.id)[0]
    allowed_resp = test_client.post(
        "/api/article-distribution/accounts",
        headers=_headers(owner),
        json={
            "account_name": "主号",
            "platform": "公众号",
            "publication_type": "article",
            "theme_id": allowed_theme_id,
        },
    )
    assert allowed_resp.status_code == 201, allowed_resp.text
    assert allowed_resp.json()["project_ids"] == [default_project.id]
    assert allowed_resp.json()["theme_id"] == allowed_theme_id
