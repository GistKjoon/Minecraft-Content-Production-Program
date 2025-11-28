# -*- coding: utf-8 -*-
"""
파티클/이펙트 명령어 생성 유틸.
라인/원형 궤적에 따라 execute+particle 명령을 만들어 mcfunction으로 저장하기 좋게 한다.
"""

from __future__ import annotations

import math
from typing import List, Tuple


def _parse_num(val: str) -> float:
    try:
        return float(val)
    except Exception as exc:
        raise ValueError(f"숫자를 입력하세요: {val}") from exc


def generate_line_commands(
    particle: str,
    start: Tuple[str, str, str],
    end: Tuple[str, str, str],
    steps: int,
    count: int,
    speed: float,
) -> List[str]:
    if steps < 2:
        raise ValueError("steps는 2 이상이어야 합니다.")
    sx, sy, sz = map(_parse_num, start)
    ex, ey, ez = map(_parse_num, end)
    dx = (ex - sx) / (steps - 1)
    dy = (ey - sy) / (steps - 1)
    dz = (ez - sz) / (steps - 1)
    cmds = []
    for i in range(steps):
        x = sx + dx * i
        y = sy + dy * i
        z = sz + dz * i
        cmds.append(f"execute positioned {x:.3f} {y:.3f} {z:.3f} run particle {particle} ~ ~ ~ 0 0 0 {speed} {count}")
    return cmds


def generate_circle_commands(
    particle: str,
    center: Tuple[str, str, str],
    radius: float,
    points: int,
    count: int,
    speed: float,
) -> List[str]:
    if radius <= 0:
        raise ValueError("반지름은 0보다 커야 합니다.")
    if points < 3:
        raise ValueError("points는 3 이상이어야 합니다.")
    cx, cy, cz = map(_parse_num, center)
    cmds = []
    for i in range(points):
        angle = 2 * math.pi * i / points
        x = cx + radius * math.cos(angle)
        z = cz + radius * math.sin(angle)
        cmds.append(f"execute positioned {x:.3f} {cy:.3f} {z:.3f} run particle {particle} ~ ~ ~ 0 0 0 {speed} {count}")
    return cmds


__all__ = ["generate_line_commands", "generate_circle_commands"]
