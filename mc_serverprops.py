# -*- coding: utf-8 -*-
"""
server.properties 파일을 간단히 읽고 쓰는 유틸.
민감한 값(화이트리스트, IP 등)은 노출하지 않고 주요 퍼포먼스/게임 관련 옵션만 다룹니다.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict


TARGET_KEYS = [
    "motd",
    "difficulty",
    "max-players",
    "view-distance",
    "simulation-distance",
    "allow-flight",
    "pvp",
    "enable-command-block",
    "spawn-protection",
]


@dataclass
class ServerProps:
    values: Dict[str, str] = field(default_factory=dict)

    def to_lines(self) -> str:
        return "\n".join(f"{k}={v}" for k, v in self.values.items())


def load_properties(path: str) -> ServerProps:
    values: Dict[str, str] = {}
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, val = line.split("=", 1)
            if key in TARGET_KEYS:
                values[key] = val
    return ServerProps(values=values)


def save_properties(path: str, props: ServerProps):
    # 기존 파일을 읽어 나머지 키는 유지하고 대상 키만 교체
    lines = []
    existing = {}
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                if "=" in line and not line.strip().startswith("#"):
                    k, v = line.split("=", 1)
                    existing[k] = v.rstrip("\n")
    except FileNotFoundError:
        pass

    for k, v in props.values.items():
        existing[k] = v

    # 정렬하여 기록
    for k in sorted(existing.keys()):
        lines.append(f"{k}={existing[k]}")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


__all__ = ["ServerProps", "load_properties", "save_properties", "TARGET_KEYS"]
