# -*- coding: utf-8 -*-
"""
구조 블록(.nbt) 관리 유틸: 간단한 메타 읽기 및 좌표/회전/미러 옵션 안내.
"""
from __future__ import annotations

import os
import json
import gzip
from typing import Dict, Any


def read_nbt(path: str) -> Dict[str, Any]:
    """
    NBT를 JSON 스타일로 읽습니다. (단순 디버그용: gzip+nbtlite 없이 최소 구현)
    구조 블록 저장 파일(.nbt)은 gzip으로 압축됨.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(path)
    with gzip.open(path, "rb") as f:
        raw = f.read()
    try:
        import nbtlib
        data = nbtlib.File.parse(raw)
        return json.loads(data.json())
    except Exception:
        # nbtlib 없을 때 최소한의 정보만 반환
        return {"raw_bytes": len(raw)}


__all__ = ["read_nbt"]
