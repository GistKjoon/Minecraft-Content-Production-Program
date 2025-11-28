# -*- coding: utf-8 -*-
"""
pack.mcmeta 업데이트/생성 유틸.
배포 전에 pack_format/description을 일괄 업데이트할 때 사용한다.
"""

from __future__ import annotations

import json
import os
from typing import Tuple


def update_pack_meta(pack_path: str, pack_format: int | None = None, description: str | None = None) -> Tuple[bool, str]:
    meta_path = os.path.join(pack_path, "pack.mcmeta")
    data = {"pack": {}}
    changed = False
    if os.path.exists(meta_path):
        try:
            with open(meta_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            pass
    if "pack" not in data:
        data["pack"] = {}
    if pack_format is not None:
        if data["pack"].get("pack_format") != pack_format:
            data["pack"]["pack_format"] = pack_format
            changed = True
    if description:
        if data["pack"].get("description") != description:
            data["pack"]["description"] = description
            changed = True
    if changed or not os.path.exists(meta_path):
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True, meta_path
    return False, meta_path


def bulk_update(base: str, kind: str, pack_format: int, description: str | None = None) -> int:
    root = os.path.join(base, kind)
    if not os.path.isdir(root):
        return 0
    updated = 0
    for entry in os.listdir(root):
        pack_dir = os.path.join(root, entry)
        if not os.path.isdir(pack_dir):
            continue
        changed, _ = update_pack_meta(pack_dir, pack_format=pack_format, description=description)
        if changed:
            updated += 1
    return updated


__all__ = ["update_pack_meta", "bulk_update"]
