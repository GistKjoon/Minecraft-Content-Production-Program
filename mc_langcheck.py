# -*- coding: utf-8 -*-
"""
리소스팩 lang 파일(en_us vs ko_kr) 누락 키를 점검하는 유틸.
"""
from __future__ import annotations

import json
import os
from typing import Dict, List, Tuple


def load_lang(path: str) -> Dict[str, str]:
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def check_lang_pack(base: str, pack: str) -> Tuple[List[str], List[str]]:
    rp_dir = os.path.join(base, "resourcepacks", pack)
    assets = os.path.join(rp_dir, "assets")
    if not os.path.isdir(assets):
        raise FileNotFoundError(f"assets 폴더 없음: {assets}")
    # 네임스페이스 추정: 첫 번째 assets 하위 폴더 사용
    namespaces = [d for d in os.listdir(assets) if os.path.isdir(os.path.join(assets, d))]
    if not namespaces:
        raise FileNotFoundError("assets 하위 네임스페이스가 없습니다.")
    ns = namespaces[0]
    lang_dir = os.path.join(assets, ns, "lang")
    if not os.path.isdir(lang_dir):
        raise FileNotFoundError(f"lang 폴더 없음: {lang_dir}")
    en = load_lang(os.path.join(lang_dir, "en_us.json"))
    ko = load_lang(os.path.join(lang_dir, "ko_kr.json"))
    missing = [k for k in en.keys() if k not in ko]
    extra = [k for k in ko.keys() if k not in en]
    return missing, extra


__all__ = ["check_lang_pack"]
