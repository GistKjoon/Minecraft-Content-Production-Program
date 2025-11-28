# -*- coding: utf-8 -*-
"""
워크스페이스 통계/인벤토리 요약.
파일 수, 용량, mcfunction/텍스처 개수를 빠르게 집계해 개발/배포 상태를 파악합니다.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Dict, Tuple


@dataclass
class PackStats:
    packs: int = 0
    mcfunctions: int = 0
    textures: int = 0
    lang: int = 0
    size_bytes: int = 0


def human_size(num: int) -> str:
    for unit in ["B", "KB", "MB", "GB"]:
        if num < 1024:
            return f"{num:.1f}{unit}"
        num /= 1024
    return f"{num:.1f}TB"


def collect_stats(base: str) -> Dict[str, PackStats]:
    stats: Dict[str, PackStats] = {"datapacks": PackStats(), "resourcepacks": PackStats()}

    # 데이터 팩
    dp_root = os.path.join(base, "datapacks")
    if os.path.isdir(dp_root):
        for pack in os.listdir(dp_root):
            pack_path = os.path.join(dp_root, pack)
            if not os.path.isdir(pack_path):
                continue
            stats["datapacks"].packs += 1
            for root, _, files in os.walk(pack_path):
                for f in files:
                    full = os.path.join(root, f)
                    stats["datapacks"].size_bytes += os.path.getsize(full)
                    if f.endswith(".mcfunction"):
                        stats["datapacks"].mcfunctions += 1

    # 리소스 팩
    rp_root = os.path.join(base, "resourcepacks")
    if os.path.isdir(rp_root):
        for pack in os.listdir(rp_root):
            pack_path = os.path.join(rp_root, pack)
            if not os.path.isdir(pack_path):
                continue
            stats["resourcepacks"].packs += 1
            for root, _, files in os.walk(pack_path):
                for f in files:
                    full = os.path.join(root, f)
                    stats["resourcepacks"].size_bytes += os.path.getsize(full)
                    if f.endswith(".png"):
                        stats["resourcepacks"].textures += 1
                    if f.endswith(".json") and "lang" in root:
                        stats["resourcepacks"].lang += 1
    return stats


def summarize(stats: Dict[str, PackStats]) -> str:
    lines = []
    for kind, st in stats.items():
        lines.append(f"[{kind}] 팩 {st.packs}개, 크기 {human_size(st.size_bytes)}")
        if kind == "datapacks":
            lines.append(f" - mcfunction: {st.mcfunctions}개")
        else:
            lines.append(f" - 텍스처(png): {st.textures}개, lang: {st.lang}개")
    return "\n".join(lines)


__all__ = ["collect_stats", "summarize"]
