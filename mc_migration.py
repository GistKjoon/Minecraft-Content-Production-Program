# -*- coding: utf-8 -*-
"""
팩 버전 마이그레이션 가이드/체커.
pack_format 변경 시 체크해야 할 항목을 안내하고 간단한 자동 변환(리네임) 규칙을 적용한다.
"""
from __future__ import annotations

import os
import shutil
from typing import List, Tuple

MIGRATION_RULES = {
    # 예시: 1.20→1.21 데이터팩에서 변경되는 리소스 키가 있다면 여기에 매핑
    # "minecraft:old_id": "minecraft:new_id",
}

GUIDE_LINES = [
    "pack.mcmeta의 pack_format을 새 버전에 맞게 업데이트하세요.",
    "리소스팩의 lang 파일이 최신 키를 사용하는지 확인하세요.",
    "데이터팩의 load/tick 태그 위치: data/minecraft/tags/functions/load.json, tick.json 유지.",
    "실험적 기능이 필요한 경우, 해당 버전에서 지원하는지 릴리즈 노트를 확인하세요.",
    "커맨드/태그/NBT가 버전에서 제거/변경되었는지 점검하세요.",
]


def apply_migration(base: str, kind: str, dry_run: bool = True) -> List[str]:
    """
    매우 제한적인 자동 변환: MIGRATION_RULES에 따라 문자열 치환.
    dry_run=True이면 변경 없이 보고만 한다.
    """
    results: List[str] = []
    root = os.path.join(base, kind)
    if not os.path.isdir(root):
        return [f"{kind} 폴더가 없습니다."]
    for pack in os.listdir(root):
        pack_dir = os.path.join(root, pack)
        if not os.path.isdir(pack_dir):
            continue
        for sub, _, files in os.walk(pack_dir):
            for f in files:
                if not f.endswith((".json", ".mcfunction")):
                    continue
                path = os.path.join(sub, f)
                try:
                    with open(path, "r", encoding="utf-8", errors="replace") as rf:
                        content = rf.read()
                    new_content = content
                    for old, new in MIGRATION_RULES.items():
                        if old in new_content:
                            new_content = new_content.replace(old, new)
                    if new_content != content:
                        results.append(f"{pack}/{os.path.relpath(path, pack_dir)}: 변경 발생")
                        if not dry_run:
                            with open(path, "w", encoding="utf-8") as wf:
                                wf.write(new_content)
                except Exception as exc:
                    results.append(f"{pack}/{os.path.relpath(path, pack_dir)}: 처리 실패 {exc}")
    if not results:
        results.append("변경 또는 치환 대상이 없습니다.")
    return results


def backup_before_migrate(base: str, kind: str) -> str:
    root = os.path.join(base, kind)
    if not os.path.isdir(root):
        raise FileNotFoundError(f"{kind} 폴더가 없습니다: {root}")
    dst = f"{root}_backup_migrate"
    shutil.copytree(root, dst, dirs_exist_ok=True)
    return dst


__all__ = ["apply_migration", "backup_before_migrate", "GUIDE_LINES"]
