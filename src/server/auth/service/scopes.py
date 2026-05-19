# -*- coding: utf-8 -*-
"""
鉴权 scope 服务

公开接口：
- scope 常量
- `OAUTH2_SCOPES`
- `normalize_scopes`
- `serialize_scopes`
- `deserialize_scopes`
- `get_role_scopes`
- `get_user_scope_overrides`
- `validate_scope_overrides`
- `get_user_scopes`
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass

from ..models import User
from ..schemas import UserRole


@dataclass(frozen=True)
class ScopeDefinition:
    scope: str
    title: str
    description: str


SCOPE_PROFILE_READ = "profile:read"
SCOPE_PROFILE_WRITE = "profile:write"
SCOPE_PROFILE_EMAIL_WRITE = "profile:email:write"
SCOPE_PROFILE_PASSWORD_WRITE = "profile:password:write"
SCOPE_ADMIN_USERS_READ = "admin:users:read"
SCOPE_ADMIN_USERS_WRITE = "admin:users:write"
SCOPE_ARTICLE_DISTRIBUTION_READ = "article_distribution:read"
SCOPE_ARTICLE_DISTRIBUTION_WRITE = "article_distribution:write"
SCOPE_ARTICLE_DISTRIBUTION_REPORT_READ = "article_distribution:report:read"
SCOPE_ADMIN_ARTICLE_DISTRIBUTION_WRITE = "admin:article_distribution:write"

SCOPE_DEFINITIONS: tuple[ScopeDefinition, ...] = (
    ScopeDefinition(
        scope=SCOPE_PROFILE_READ,
        title="查看基础资料",
        description="读取当前用户的用户名、邮箱、显示名称和账号基础状态。",
    ),
    ScopeDefinition(
        scope=SCOPE_PROFILE_WRITE,
        title="修改基础资料",
        description="修改当前用户的用户名和显示名称等基础资料。",
    ),
    ScopeDefinition(
        scope=SCOPE_PROFILE_EMAIL_WRITE,
        title="修改邮箱",
        description="发起并确认当前用户的邮箱变更流程。",
    ),
    ScopeDefinition(
        scope=SCOPE_PROFILE_PASSWORD_WRITE,
        title="修改密码",
        description="发起当前用户的密码修改流程。",
    ),
    ScopeDefinition(
        scope=SCOPE_ADMIN_USERS_READ,
        title="查看用户",
        description="查看系统用户列表、用户角色、状态和权限范围。",
    ),
    ScopeDefinition(
        scope=SCOPE_ADMIN_USERS_WRITE,
        title="管理用户",
        description="创建、更新或删除用户，并管理用户角色、状态和权限范围。",
    ),
    ScopeDefinition(
        scope=SCOPE_ARTICLE_DISTRIBUTION_READ,
        title="查看文章分发",
        description="查看自己的分发账号、文章列表和文章内容。",
    ),
    ScopeDefinition(
        scope=SCOPE_ARTICLE_DISTRIBUTION_WRITE,
        title="管理文章分发",
        description="创建和维护自己的分发账号，并更新文章发布状态。",
    ),
    ScopeDefinition(
        scope=SCOPE_ARTICLE_DISTRIBUTION_REPORT_READ,
        title="查看分发进度后台",
        description="查看所有用户未发布文章数量、文章标题、计划日期和对应账号。",
    ),
    ScopeDefinition(
        scope=SCOPE_ADMIN_ARTICLE_DISTRIBUTION_WRITE,
        title="管理全量文章分发",
        description="为任意账号上传文章，并管理文章分发 API Key。",
    ),
)

SCOPE_DEFINITION_MAP: dict[str, ScopeDefinition] = {
    definition.scope: definition for definition in SCOPE_DEFINITIONS
}

ALL_AUTH_SCOPES: tuple[str, ...] = tuple(
    definition.scope for definition in SCOPE_DEFINITIONS
)

OAUTH2_SCOPES: dict[str, str] = {
    definition.scope: definition.title for definition in SCOPE_DEFINITIONS
}

ROLE_SCOPES: dict[UserRole, tuple[str, ...]] = {
    UserRole.USER: (
        SCOPE_PROFILE_READ,
        SCOPE_PROFILE_WRITE,
        SCOPE_PROFILE_EMAIL_WRITE,
        SCOPE_PROFILE_PASSWORD_WRITE,
        SCOPE_ARTICLE_DISTRIBUTION_READ,
        SCOPE_ARTICLE_DISTRIBUTION_WRITE,
    ),
    UserRole.ADMIN: (
        SCOPE_PROFILE_READ,
        SCOPE_PROFILE_WRITE,
        SCOPE_PROFILE_EMAIL_WRITE,
        SCOPE_PROFILE_PASSWORD_WRITE,
        SCOPE_ADMIN_USERS_READ,
        SCOPE_ADMIN_USERS_WRITE,
        SCOPE_ARTICLE_DISTRIBUTION_READ,
        SCOPE_ARTICLE_DISTRIBUTION_WRITE,
        SCOPE_ARTICLE_DISTRIBUTION_REPORT_READ,
        SCOPE_ADMIN_ARTICLE_DISTRIBUTION_WRITE,
    ),
}

ROLE_ASSIGNABLE_SCOPES: dict[UserRole, tuple[str, ...]] = {
    UserRole.USER: (
        *ROLE_SCOPES[UserRole.USER],
        SCOPE_ARTICLE_DISTRIBUTION_REPORT_READ,
    ),
    UserRole.ADMIN: ROLE_SCOPES[UserRole.ADMIN],
}


def normalize_scopes(scopes: Iterable[str] | str | None) -> tuple[str, ...]:
    if scopes is None:
        return ()

    raw_scopes = scopes.split() if isinstance(scopes, str) else scopes
    normalized_set = {
        scope.strip()
        for scope in raw_scopes
        if isinstance(scope, str) and scope.strip()
    }
    if not normalized_set:
        return ()

    known_scopes = [scope for scope in ALL_AUTH_SCOPES if scope in normalized_set]
    extra_scopes = sorted(normalized_set.difference(known_scopes))
    return tuple([*known_scopes, *extra_scopes])


def serialize_scopes(scopes: Iterable[str] | str | None) -> str:
    return " ".join(normalize_scopes(scopes))


def deserialize_scopes(scopes: Sequence[str] | str | None) -> set[str]:
    return set(normalize_scopes(scopes))


def get_scope_definition(scope: str) -> ScopeDefinition:
    return SCOPE_DEFINITION_MAP.get(
        scope,
        ScopeDefinition(
            scope=scope,
            title=scope,
            description=scope,
        ),
    )


def get_scope_title(scope: str) -> str:
    return get_scope_definition(scope).title


def get_scope_description(scope: str) -> str:
    return get_scope_definition(scope).description


def get_role_scopes(role: UserRole) -> tuple[str, ...]:
    return ROLE_SCOPES.get(role, ROLE_SCOPES[UserRole.USER])


def get_role_assignable_scopes(role: UserRole) -> tuple[str, ...]:
    return ROLE_ASSIGNABLE_SCOPES.get(role, ROLE_ASSIGNABLE_SCOPES[UserRole.USER])


def get_user_scope_overrides(user: User) -> tuple[str, ...] | None:
    raw_overrides = getattr(user, "scope_overrides", None)
    if raw_overrides is None:
        return None

    normalized = normalize_scopes(raw_overrides)
    allowed_scopes = set(get_role_assignable_scopes(user.role))
    return tuple(scope for scope in normalized if scope in allowed_scopes)


def validate_scope_overrides(
    role: UserRole, scopes: Iterable[str] | str | None
) -> tuple[str, ...]:
    normalized = normalize_scopes(scopes)
    allowed_scopes = set(get_role_assignable_scopes(role))
    invalid_scopes = [scope for scope in normalized if scope not in allowed_scopes]
    if invalid_scopes:
        invalid_display = ", ".join(invalid_scopes)
        raise ValueError(f"以下 scope 不允许分配给当前角色: {invalid_display}")
    return tuple(
        scope for scope in get_role_assignable_scopes(role) if scope in set(normalized)
    )


def get_user_scopes(user: User) -> tuple[str, ...]:
    scope_overrides = get_user_scope_overrides(user)
    if scope_overrides is not None:
        return scope_overrides
    return get_role_scopes(user.role)
