# -*- coding: utf-8 -*-
"""
서버/클라이언트 latest.log에서 오류/경고를 빠르게 추출하는 유틸.
"""
from __future__ import annotations

import os
from typing import List


ERROR_KEYWORDS = ["[ERROR]", "Exception", "Caused by", "Couldn't", "Failed", "java.lang"]


def parse_log(log_path: str, tail: int = 400) -> List[str]:
    if not os.path.exists(log_path):
        raise FileNotFoundError(f"log 파일을 찾을 수 없습니다: {log_path}")
    with open(log_path, "r", encoding="utf-8", errors="replace") as f:
        lines = f.readlines()
    lines = lines[-tail:]
    hits = []
    for line in lines:
        if any(key in line for key in ERROR_KEYWORDS):
            hits.append(line.rstrip("\n"))
    if not hits:
        hits.append("오류/경고 패턴이 발견되지 않았습니다.")
    return hits


__all__ = ["parse_log", "ERROR_KEYWORDS"]
