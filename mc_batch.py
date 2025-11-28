# -*- coding: utf-8 -*-
"""
mcfunction 일괄 검색/치환 유틸.
간단한 문자열 기반 치환으로, 대규모 프로젝트에서 반복 수정 시 편리하다.
"""

from __future__ import annotations

import os
from typing import Dict, List, Tuple


def iter_mcfunctions(base: str) -> List[Tuple[str, str]]:
    results = []
    dp_root = os.path.join(base, "datapacks")
    if not os.path.isdir(dp_root):
        return results
    for pack in os.listdir(dp_root):
        p_path = os.path.join(dp_root, pack)
        if not os.path.isdir(p_path):
            continue
        data_dir = os.path.join(p_path, "data")
        if not os.path.isdir(data_dir):
            continue
        for ns in os.listdir(data_dir):
            fn_dir = os.path.join(data_dir, ns, "functions")
            if not os.path.isdir(fn_dir):
                continue
            for root, _, files in os.walk(fn_dir):
                for file in files:
                    if file.endswith(".mcfunction"):
                        full = os.path.join(root, file)
                        rel = os.path.relpath(full, base)
                        results.append((rel, full))
    return results


def find_occurrences(base: str, needle: str) -> Dict[str, List[int]]:
    """needle을 포함하는 파일과 행 번호를 반환."""
    matches: Dict[str, List[int]] = {}
    for rel, full in iter_mcfunctions(base):
        with open(full, "r", encoding="utf-8", errors="replace") as f:
            for idx, line in enumerate(f, start=1):
                if needle in line:
                    matches.setdefault(rel, []).append(idx)
    return matches


def replace_in_workspace(base: str, needle: str, replacement: str) -> int:
    """모든 mcfunction에서 needle을 replacement로 치환하고 변경된 파일 수를 반환."""
    changed = 0
    for _, full in iter_mcfunctions(base):
        with open(full, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
        if needle not in content:
            continue
        new_content = content.replace(needle, replacement)
        if new_content != content:
            with open(full, "w", encoding="utf-8") as f:
                f.write(new_content)
            changed += 1
    return changed


__all__ = ["find_occurrences", "replace_in_workspace"]
