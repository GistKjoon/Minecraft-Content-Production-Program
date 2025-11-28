# -*- coding: utf-8 -*-
"""
채팅/타이틀용 텍스트 유틸.
주요 기능: 그라디언트 tellraw/title JSON 생성.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple


def _hex_to_rgb(hex_code: str) -> Tuple[int, int, int]:
    code = hex_code.strip().lstrip("#")
    if len(code) not in (6, 3):
        raise ValueError("색상은 #RRGGBB 또는 #RGB 형식이어야 합니다.")
    if len(code) == 3:
        code = "".join(ch * 2 for ch in code)
    try:
        r = int(code[0:2], 16)
        g = int(code[2:4], 16)
        b = int(code[4:6], 16)
        return r, g, b
    except Exception as exc:
        raise ValueError(f"색상 변환 실패: {hex_code}") from exc


def _lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


@dataclass
class StyledChar:
    text: str
    color: str
    bold: bool = False
    italic: bool = False

    def to_json(self) -> Dict[str, object]:
        data: Dict[str, object] = {"text": self.text, "color": self.color}
        if self.bold:
            data["bold"] = True
        if self.italic:
            data["italic"] = True
        return data


def gradient_text_payload(text: str, start_color: str, end_color: str, bold: bool = False, italic: bool = False) -> List[Dict[str, object]]:
    chars = list(text)
    if not chars:
        raise ValueError("텍스트를 입력하세요.")
    r1, g1, b1 = _hex_to_rgb(start_color)
    r2, g2, b2 = _hex_to_rgb(end_color)
    payload: List[Dict[str, object]] = []
    length = max(1, len(chars) - 1)
    for idx, ch in enumerate(chars):
        t = idx / length
        r = int(_lerp(r1, r2, t))
        g = int(_lerp(g1, g2, t))
        b = int(_lerp(b1, b2, t))
        color = "#{:02x}{:02x}{:02x}".format(r, g, b)
        payload.append(StyledChar(text=ch, color=color, bold=bold, italic=italic).to_json())
    return payload


__all__ = ["gradient_text_payload"]
