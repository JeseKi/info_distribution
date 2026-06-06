# -*- coding: utf-8 -*-
"""Base DAO class for article distribution."""

from __future__ import annotations

from sqlalchemy.orm import Session

from src.server.dao.dao_base import BaseDAO


class ArticleDistributionBaseDAO(BaseDAO):
    def __init__(self, db_session: Session):
        super().__init__(db_session)
