# -*- coding: utf-8 -*-
"""
팩/디렉터리 비교 및 동기화 유틸.
두 경로를 비교해 추가/삭제/수정된 파일을 리스트업하고,
필요하면 src→dst로 복사/동기화를 수행한다.
"""

from __future__ import annotations

import hashlib
import os
import shutil
from dataclasses import dataclass
from typing import Dict, List, Tuple


def file_hash(path: str) -> str:
    h = hashlib.sha1()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


@dataclass
class DiffResult:
    added: List[str]
    removed: List[str]
    modified: List[str]

    def summary_lines(self) -> List[str]:
        lines: List[str] = []
        lines.append(f"추가 {len(self.added)}개, 삭제 {len(self.removed)}개, 수정 {len(self.modified)}개")
        if self.added:
            lines.append("추가:")
            lines.extend(f" + {p}" for p in self.added)
        if self.removed:
            lines.append("삭제:")
            lines.extend(f" - {p}" for p in self.removed)
        if self.modified:
            lines.append("수정:")
            lines.extend(f" * {p}" for p in self.modified)
        return lines


def compare_dirs(src: str, dst: str) -> DiffResult:
    src_files: Dict[str, str] = {}
    dst_files: Dict[str, str] = {}

    for root, _, files in os.walk(src):
        for f in files:
            path = os.path.join(root, f)
            rel = os.path.relpath(path, src)
            src_files[rel] = file_hash(path)

    for root, _, files in os.walk(dst):
        for f in files:
            path = os.path.join(root, f)
            rel = os.path.relpath(path, dst)
            dst_files[rel] = file_hash(path)

    added = [p for p in src_files.keys() if p not in dst_files]
    removed = [p for p in dst_files.keys() if p not in src_files]
    modified = [p for p in src_files.keys() if p in dst_files and src_files[p] != dst_files[p]]

    return DiffResult(added=sorted(added), removed=sorted(removed), modified=sorted(modified))


def sync_dirs(src: str, dst: str, diff: DiffResult) -> int:
    """
    src→dst로 추가/수정 파일을 복사. 삭제 항목은 건드리지 않는다.
    반환: 복사된 파일 개수.
    """
    copied = 0
    for rel in diff.added + diff.modified:
        src_path = os.path.join(src, rel)
        dst_path = os.path.join(dst, rel)
        os.makedirs(os.path.dirname(dst_path), exist_ok=True)
        shutil.copy2(src_path, dst_path)
        copied += 1
    return copied


__all__ = ["DiffResult", "compare_dirs", "sync_dirs"]
