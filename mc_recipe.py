# -*- coding: utf-8 -*-
"""
기본 crafting recipe JSON을 생성하는 유틸.
3x3 그리드 입력을 받아 shaped/shapeless 레시피를 빌드한다.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple


def _item_entry(value: str) -> Dict[str, str]:
    value = value.strip()
    if value.startswith("#"):
        return {"tag": value[1:]}
    return {"item": value}


@dataclass
class ShapedRecipe:
    pattern: List[str]
    key: Dict[str, Dict[str, str]]
    result: Dict[str, object]

    def to_json(self) -> Dict[str, object]:
        return {
            "type": "minecraft:crafting_shaped",
            "pattern": self.pattern,
            "key": self.key,
            "result": self.result,
        }


def shaped_from_grid(grid: List[Optional[str]], result_id: str, result_count: int = 1) -> ShapedRecipe:
    """
    3x3 grid(길이 9) 문자열을 받아 공백을 잘라낸 crafting_shaped 레시피를 만든다.
    빈 칸은 None 또는 '' 로 전달.
    """
    if len(grid) != 9:
        raise ValueError("grid 길이는 9여야 합니다.")
    # 3x3 매트릭스로 reshape
    rows = [grid[i * 3 : (i + 1) * 3] for i in range(3)]
    # 문자열 정리
    rows = [[cell.strip() if cell else "" for cell in r] for r in rows]

    # 사용된 셀의 행/열 인덱스 찾기
    used_rows = [i for i, r in enumerate(rows) if any(c for c in r)]
    used_cols = [j for j in range(3) if any(rows[i][j] for i in range(3))]
    if not used_rows or not used_cols:
        raise ValueError("최소 한 칸에 아이템을 입력하세요.")

    row_min, row_max = min(used_rows), max(used_rows)
    col_min, col_max = min(used_cols), max(used_cols)

    # 패턴과 key 생성
    symbols: Dict[str, str] = {}
    next_letter = ord("A")
    pattern: List[str] = []
    for i in range(row_min, row_max + 1):
        line_chars: List[str] = []
        for j in range(col_min, col_max + 1):
            cell = rows[i][j]
            if not cell:
                line_chars.append(" ")
                continue
            if cell not in symbols:
                symbols[cell] = chr(next_letter)
                next_letter += 1
            line_chars.append(symbols[cell])
        pattern.append("".join(line_chars))

    key = {sym: _item_entry(item) for item, sym in symbols.items()}
    result = {"item": result_id, "count": max(1, int(result_count))}
    return ShapedRecipe(pattern=pattern, key=key, result=result)


def build_shapeless(ingredients: List[str], result_id: str, result_count: int = 1) -> Dict[str, object]:
    ing = [x.strip() for x in ingredients if x.strip()]
    if not ing:
        raise ValueError("최소 한 개의 재료를 입력하세요.")
    return {
        "type": "minecraft:crafting_shapeless",
        "ingredients": [_item_entry(x) for x in ing],
        "result": {"item": result_id, "count": max(1, int(result_count))},
    }


__all__ = ["shaped_from_grid", "build_shapeless", "ShapedRecipe"]
