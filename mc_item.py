# -*- coding: utf-8 -*-
"""
아이템 NBT 빌더: /give 명령어용 커스텀 이름, 색상, 로어, 인챈트를 손쉽게 생성.
"""
from __future__ import annotations

import json
from typing import List, Tuple


def parse_enchants(text: str) -> List[Tuple[str, int]]:
    """
    "sharpness:5, unbreaking:3" 형식 문자열을 파싱.
    """
    enchants = []
    for part in text.split(","):
        part = part.strip()
        if not part:
            continue
        if ":" not in part:
            raise ValueError("인챈트는 id:레벨 형식이어야 합니다.")
        eid, level = part.split(":", 1)
        try:
            lvl = int(level)
        except ValueError:
            raise ValueError(f"인챈트 레벨이 숫자가 아닙니다: {part}")
        enchants.append((eid.strip(), lvl))
    return enchants


def build_item_nbt(name: str, color: str, italic: bool, lore: List[str], enchants: List[Tuple[str, int]]) -> str:
    """
    간단한 SNBT 문자열을 생성한다.
    display.Name/Lore는 JSON 텍스트 형식을 유지한다.
    """
    nbt_parts = []
    # display
    display_parts = []
    if name:
        name_json = json.dumps({"text": name, "color": color or "white", "italic": italic}, ensure_ascii=False)
        display_parts.append(f"Name:'{name_json}'")
    if lore:
        lore_json = [json.dumps({"text": line}, ensure_ascii=False) for line in lore]
        lore_array = ",".join(f"'{x}'" for x in lore_json)
        display_parts.append(f"Lore:[{lore_array}]")
    if display_parts:
        nbt_parts.append(f"display:{{{','.join(display_parts)}}}")

    # Enchantments
    if enchants:
        ench = ",".join(f'{{id:"{eid}",lvl:{lvl}s}}' for eid, lvl in enchants)
        nbt_parts.append(f"Enchantments:[{ench}]")

    if not nbt_parts:
        return ""
    return "{" + ",".join(nbt_parts) + "}"


def build_give_command(
    target: str,
    item_id: str,
    count: int,
    name: str = "",
    color: str = "",
    italic: bool = False,
    lore: List[str] | None = None,
    enchants: List[Tuple[str, int]] | None = None,
) -> str:
    nbt = build_item_nbt(name, color, italic, lore or [], enchants or [])
    item_full = item_id
    if nbt:
        item_full += nbt
    return f"give {target} {item_full} {max(1, count)}"


__all__ = ["parse_enchants", "build_item_nbt", "build_give_command"]
