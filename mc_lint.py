# -*- coding: utf-8 -*-
"""
mcfunction 간단 린터: 흔히 실수하는 포맷 문제를 빠르게 알려준다.
완벽한 문법 검사는 아니며, 배포 전 기본 품질 확인용이다.
"""

from __future__ import annotations

import os
from typing import List, Tuple


def iter_mcfunctions(base: str) -> List[Tuple[str, str]]:
    """datapacks/*/data/*/functions 내 mcfunction 경로를 리스트로 반환."""
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


def lint_function(path: str) -> List[str]:
    issues: List[str] = []
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        lines = f.readlines()
    if not lines:
        issues.append("빈 파일")
        return issues
    for idx, line in enumerate(lines, start=1):
        if line.rstrip("\n").endswith(" "):
            issues.append(f"{idx}행: 끝 공백 존재")
        if "\t" in line:
            issues.append(f"{idx}행: 탭 문자가 있습니다 (스페이스 권장)")
        if line.strip() == "":
            continue
        if line.startswith(" " * 4):
            issues.append(f"{idx}행: 들여쓰기 4스페이스 (불필요할 수 있음)")
    return issues


def lint_workspace(base: str) -> List[str]:
    results: List[str] = []
    mcfs = iter_mcfunctions(base)
    if not mcfs:
        return ["검사할 mcfunction 파일이 없습니다."]
    for rel, full in mcfs:
        issues = lint_function(full)
        if issues:
            for msg in issues:
                results.append(f"{rel}: {msg}")
    if not results:
        results.append("모든 mcfunction 기본 포맷 OK")
    return results


__all__ = ["lint_workspace"]
