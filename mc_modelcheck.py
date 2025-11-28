# -*- coding: utf-8 -*-
"""
모델 JSON에서 참조하는 텍스처가 존재하는지 빠르게 검사.
"""
from __future__ import annotations

import json
import os
from typing import Dict, List, Tuple


def load_json(path: str) -> Dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def check_models(base: str, pack: str) -> List[str]:
    rp_dir = os.path.join(base, "resourcepacks", pack)
    assets = os.path.join(rp_dir, "assets")
    if not os.path.isdir(assets):
        return [f"assets 폴더 없음: {assets}"]
    namespaces = [d for d in os.listdir(assets) if os.path.isdir(os.path.join(assets, d))]
    if not namespaces:
        return ["assets 하위 네임스페이스 없음"]
    ns = namespaces[0]
    model_dir = os.path.join(assets, ns, "models")
    tex_dir = os.path.join(assets, ns, "textures")
    if not os.path.isdir(model_dir):
        return [f"models 폴더 없음: {model_dir}"]

    issues: List[str] = []
    for root, _, files in os.walk(model_dir):
        for f in files:
            if not f.endswith(".json"):
                continue
            full = os.path.join(root, f)
            rel = os.path.relpath(full, rp_dir)
            try:
                data = load_json(full)
                textures = data.get("textures", {})
                for key, tex in textures.items():
                    # 텍스처 경로는 namespace 생략 가능; 파일 존재 여부 확인
                    tex_path = os.path.join(tex_dir, tex + ".png")
                    if not os.path.exists(tex_path):
                        issues.append(f"{rel}: 텍스처 없음 -> {tex_path}")
            except Exception as exc:
                issues.append(f"{rel}: 파싱 실패 {exc}")
    if not issues:
        issues.append("모델 텍스처 누락 없음")
    return issues


__all__ = ["check_models"]
