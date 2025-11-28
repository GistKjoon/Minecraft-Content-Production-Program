# -*- coding: utf-8 -*-
"""
리소스팩 sounds.json 생성을 돕는 유틸.
이벤트 이름과 사운드 파일 경로 리스트를 받아 sounds.json을 갱신한다.
"""

from __future__ import annotations

import json
import os
from typing import Dict, List


def parse_sound_list(text: str) -> List[str]:
    """
    "custom/boop, custom/boop2" 형식의 문자열을 리스트로 변환.
    확장자는 붙이지 않는 것을 권장(ogg/wav 자동 탐색).
    """
    items = [t.strip() for t in text.split(",") if t.strip()]
    if not items:
        raise ValueError("최소 한 개의 사운드 경로를 입력하세요.")
    return items


def build_sound_event(sounds: List[str], subtitle: str | None = None, replace: bool = False) -> Dict[str, object]:
    data: Dict[str, object] = {"sounds": sounds}
    if subtitle:
        data["subtitle"] = subtitle
    if replace:
        data["replace"] = True
    return data


def update_sounds_file(base: str, namespace: str, event: str, event_data: Dict[str, object]) -> str:
    """
    workspace 내 resourcepacks/<ns>/assets/<ns>/sounds.json 을 업데이트.
    기존 파일이 있으면 병합, 없으면 새로 생성.
    """
    target_dir = os.path.join(base, "resourcepacks", namespace, "assets", namespace)
    os.makedirs(target_dir, exist_ok=True)
    path = os.path.join(target_dir, "sounds.json")
    sounds_json: Dict[str, object] = {}
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                sounds_json = json.load(f)
        except Exception:
            sounds_json = {}
    sounds_json[event] = event_data
    with open(path, "w", encoding="utf-8") as f:
        json.dump(sounds_json, f, ensure_ascii=False, indent=2)
    return path


__all__ = ["parse_sound_list", "build_sound_event", "update_sounds_file"]
