# -*- coding: utf-8 -*-
"""
Tag JSON 생성 유틸.
blocks/items/entity_types/functions 등에서 values 리스트와 replace 옵션을 손쉽게 만든다.
"""

from __future__ import annotations

import os
from typing import Dict, List


SUPPORTED_CATEGORIES = [
    "blocks",
    "items",
    "entity_types",
    "functions",
    "fluids",
    "game_events",
    "biomes",
]


def build_tag_json(entries: List[str], replace: bool = False) -> Dict[str, object]:
    values = [e.strip() for e in entries if e.strip()]
    if not values:
        raise ValueError("최소 한 개의 value를 입력하세요.")
    data: Dict[str, object] = {"values": values}
    if replace:
        data["replace"] = True
    return data


def save_tag(base: str, namespace: str, category: str, name: str, data: Dict[str, object]) -> str:
    if category not in SUPPORTED_CATEGORIES:
        raise ValueError(f"지원하지 않는 category: {category}")
    target_dir = os.path.join(base, "datapacks", namespace, "data", namespace, "tags", category)
    os.makedirs(target_dir, exist_ok=True)
    path = os.path.join(target_dir, f"{name}.json")
    with open(path, "w", encoding="utf-8") as f:
        import json

        json.dump(data, f, ensure_ascii=False, indent=2)
    return path


__all__ = ["SUPPORTED_CATEGORIES", "build_tag_json", "save_tag"]
