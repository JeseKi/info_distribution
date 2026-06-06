# -*- coding: utf-8 -*-
"""Metadata helpers for report services."""

from __future__ import annotations

def _metadata_output_id(metadata: dict | None) -> str | None:
    return _metadata_string(metadata, "output_id")


def _metadata_topic(metadata: dict | None) -> str | None:
    return _metadata_string(metadata, "topic")


def _metadata_string(metadata: dict | None, key: str) -> str | None:
    if not metadata:
        return None
    value = metadata.get(key)
    if not isinstance(value, str):
        return None
    normalized = value.strip()
    return normalized or None


def _metadata_article_string(metadata: dict | None, key: str) -> str | None:
    if not metadata:
        return None
    article = metadata.get("article")
    if not isinstance(article, dict):
        return None
    value = article.get(key)
    if not isinstance(value, str):
        return None
    normalized = value.strip()
    return normalized or None


def _metadata_material_titles(metadata: dict | None) -> list[str]:
    if not metadata:
        return []
    article = metadata.get("article")
    if not isinstance(article, dict):
        return []
    materials = article.get("materials_used")
    if not isinstance(materials, list):
        return []

    titles: list[str] = []
    for material in materials:
        if not isinstance(material, dict):
            continue
        title = material.get("title")
        if not isinstance(title, str):
            continue
        normalized = title.strip()
        if normalized:
            titles.append(normalized)
    return _merge_unique([], titles)


def _merge_unique(current: list[str], additions: list[str]) -> list[str]:
    seen = set(current)
    merged = list(current)
    for item in additions:
        if item in seen:
            continue
        seen.add(item)
        merged.append(item)
    return merged
