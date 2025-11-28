# -*- coding: utf-8 -*-
"""
/schedule, /function 예약 실행 스니펫 생성 유틸.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List


@dataclass
class ScheduledCommand:
    ticks: int
    command: str


def build_schedule(namespace: str, name: str, entries: List[ScheduledCommand]) -> str:
    """
    예약 실행용 mcfunction 문자열을 반환한다.
    결과는 data/<ns>/functions/<name>.mcfunction 에 저장하면 된다.
    """
    lines = []
    for entry in entries:
        lines.append(f"schedule function {namespace}:{entry.command} {entry.ticks}t replace")
    return "\n".join(lines)


__all__ = ["ScheduledCommand", "build_schedule"]
