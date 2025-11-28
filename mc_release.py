# -*- coding: utf-8 -*-
"""
배포용 README/변경 로그 템플릿을 생성하는 간단한 유틸.
"""
from __future__ import annotations

import json
import os
from typing import Dict, List, Tuple


def list_packs(base: str, kind: str) -> List[str]:
    root = os.path.join(base, kind)
    if not os.path.isdir(root):
        return []
    return sorted([d for d in os.listdir(root) if os.path.isdir(os.path.join(root, d))])


def read_pack_meta(path: str) -> Tuple[int | None, str]:
    meta = os.path.join(path, "pack.mcmeta")
    if not os.path.exists(meta):
        return None, ""
    try:
        with open(meta, "r", encoding="utf-8") as f:
            data = json.load(f)
        pf = data.get("pack", {}).get("pack_format")
        desc = data.get("pack", {}).get("description", "")
        return pf, desc
    except Exception:
        return None, ""


README_TEMPLATE = """# {name}

버전: {version}
종류: {kind}
pack_format: {pack_format}
설명: {desc}

## 설치
1. 마인크래프트 폴더 내 `{folder}`에 압축을 풀거나 폴더째 복사합니다.
2. 월드/옵션에서 데이터팩 또는 리소스팩을 활성화합니다.

## 주요 내용
- 여기에 기능 요약을 적어주세요.

## 호환
- 테스트된 버전: 1.21.x (pack_format {pack_format})
- 다른 버전은 pack_format을 맞춰야 할 수 있습니다.

## 문의
- 버그/제안: 깃허브 이슈나 DM
"""


CHANGELOG_TEMPLATE = """# 변경 로그 - {name}

## {version} - {date}
- 변경 사항을 bullet로 적어주세요.
"""


def generate_readme(base: str, kind: str, name: str, version: str) -> str:
    pack_dir = os.path.join(base, kind, name)
    pf, desc = read_pack_meta(pack_dir)
    folder = "datapacks" if kind == "datapacks" else "resourcepacks"
    return README_TEMPLATE.format(
        name=name,
        version=version,
        kind="데이터 팩" if kind == "datapacks" else "리소스 팩",
        pack_format=pf if pf is not None else "미지정",
        desc=desc or "설명 없음",
        folder=folder,
    )


def generate_changelog(name: str, version: str, date: str) -> str:
    return CHANGELOG_TEMPLATE.format(name=name, version=version, date=date)


__all__ = [
    "list_packs",
    "read_pack_meta",
    "generate_readme",
    "generate_changelog",
]
