# -*- coding: utf-8 -*-
"""
워크스페이스 리포트/요약 Markdown 생성 유틸.
"""
from __future__ import annotations

import json
import os
from typing import List, Tuple

from mc_release import read_pack_meta, list_packs
from mc_stats import collect_stats, human_size


def build_pack_report(base: str) -> str:
    lines: List[str] = ["# 워크스페이스 리포트", ""]

    stats = collect_stats(base)
    lines.append("## 개요")
    lines.append(f"- 데이터팩: {stats['datapacks'].packs}개, 크기 {human_size(stats['datapacks'].size_bytes)}")
    lines.append(f"- 리소스팩: {stats['resourcepacks'].packs}개, 크기 {human_size(stats['resourcepacks'].size_bytes)}")
    lines.append("")

    for kind in ("datapacks", "resourcepacks"):
        lines.append(f"## {kind}")
        for pack in list_packs(base, kind):
            meta_path = os.path.join(base, kind, pack, "pack.mcmeta")
            pf, desc = read_pack_meta(meta_path)
            lines.append(f"- {pack}: pack_format={pf}, desc={desc or 'N/A'}")
        lines.append("")
    return "\n".join(lines)


__all__ = ["build_pack_report"]
