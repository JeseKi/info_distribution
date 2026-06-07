# -*- coding: utf-8 -*-
"""Article distribution routes."""

from .shared import admin_router, router, v1_router, v2_router
from . import accounts as _accounts
from . import admin as _admin
from . import articles as _articles
from . import proxy as _proxy
from . import report_metadata as _report_metadata
from . import report_missing_traffic as _report_missing_traffic
from . import report_overview as _report_overview
from . import report_public as _report_public
from . import report_unpublished as _report_unpublished
from . import traffic as _traffic
from . import v1 as _v1
from . import v2 as _v2

# Keep module references so route decorators are registered and imports are explicit.
_ROUTE_MODULES = (
    _accounts,
    _admin,
    _articles,
    _proxy,
    _report_metadata,
    _report_missing_traffic,
    _report_overview,
    _report_public,
    _report_unpublished,
    _traffic,
    _v1,
    _v2,
)

_validate_proxy_image_url = _proxy._validate_proxy_image_url
socket = _proxy.socket

__all__ = [
    "_validate_proxy_image_url",
    "admin_router",
    "router",
    "socket",
    "v1_router",
    "v2_router",
]
