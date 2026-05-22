# -*- coding: utf-8 -*-
"""Article distribution routes."""

from importlib import import_module

from .shared import admin_router, router, v1_router

# Import route modules so decorators register endpoints on the shared routers.
for _route_module in ("accounts", "admin", "articles", "proxy", "reports", "v1"):
    _module = import_module(f"{__name__}.{_route_module}")
    if _route_module == "proxy":
        _proxy_module = _module
del _route_module
del _module

_validate_proxy_image_url = _proxy_module._validate_proxy_image_url
socket = _proxy_module.socket
del _proxy_module

__all__ = [
    "_validate_proxy_image_url",
    "admin_router",
    "router",
    "socket",
    "v1_router",
]
