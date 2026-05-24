# -*- coding: utf-8 -*-
"""Article distribution routes."""

from .shared import admin_router, router, v1_router
from . import accounts as _accounts
from . import admin as _admin
from . import articles as _articles
from . import proxy as _proxy
from . import reports as _reports
from . import traffic as _traffic
from . import v1 as _v1

# Keep module references so route decorators are registered and imports are explicit.
_ROUTE_MODULES = (_accounts, _admin, _articles, _proxy, _reports, _traffic, _v1)

_validate_proxy_image_url = _proxy._validate_proxy_image_url
socket = _proxy.socket

__all__ = [
    "_validate_proxy_image_url",
    "admin_router",
    "router",
    "socket",
    "v1_router",
]
