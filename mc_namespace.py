# -*- coding: utf-8 -*-
"""
네임스페이스 리네임/치환 유틸.
datapacks/<old>/data/<old>/... 구조와 파일 내용 내 old:new 문자열을 new로 바꾼다.
"""
from __future__ import annotations

import os
import shutil
from typing import List, Tuple


def rename_namespace(base: str, old: str, new: str) -> List[str]:
    """
    데이터팩 폴더 이름 및 내부 참조를 old->new로 바꾼다.
    returns: 변경된 항목 로그 리스트
    """
    logs: List[str] = []
    dp_root = os.path.join(base, "datapacks")
    if not os.path.isdir(dp_root):
        raise FileNotFoundError(f"datapacks 폴더가 없습니다: {dp_root}")
    old_pack = os.path.join(dp_root, old)
    if not os.path.isdir(old_pack):
        raise FileNotFoundError(f"대상 데이터팩 없음: {old_pack}")

    new_pack = os.path.join(dp_root, new)
    if not os.path.exists(new_pack):
        shutil.move(old_pack, new_pack)
        logs.append(f"폴더 이동: {old_pack} -> {new_pack}")

    # 내부 파일 치환
    for root, _, files in os.walk(new_pack):
        for f in files:
            if not f.endswith((".mcfunction", ".json")):
                continue
            path = os.path.join(root, f)
            with open(path, "r", encoding="utf-8", errors="replace") as rf:
                content = rf.read()
            new_content = content.replace(f"{old}:", f"{new}:")
            if new_content != content:
                with open(path, "w", encoding="utf-8") as wf:
                    wf.write(new_content)
                logs.append(f"치환: {os.path.relpath(path, base)}")
    if not logs:
        logs.append("변경 사항 없음")
    return logs


__all__ = ["rename_namespace"]
