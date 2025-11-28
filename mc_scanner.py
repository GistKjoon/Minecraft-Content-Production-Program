# -*- coding: utf-8 -*-
"""
데이터 팩/리소스 팩의 기본 구조를 빠르게 점검하는 간단한 스캐너.
정적 분석이므로 Minecraft 내부 로딩 수준의 완벽한 검증은 아니지만,
배포 전 흔히 놓치는 부분을 잡아주는 용도로 사용합니다.
"""

from __future__ import annotations

import json
import os
import re
from typing import List

VALID_NS = re.compile(r"^[a-z0-9_\-\.]+$")


def scan_datapack(path: str) -> List[str]:
    issues: List[str] = []
    pack_meta = os.path.join(path, "pack.mcmeta")
    if not os.path.exists(pack_meta):
        issues.append("pack.mcmeta 없음")
    else:
        try:
            with open(pack_meta, "r", encoding="utf-8") as f:
                meta = json.load(f)
            pf = meta.get("pack", {}).get("pack_format")
            if not pf:
                issues.append("pack.mcmeta pack_format 누락")
        except Exception as exc:
            issues.append(f"pack.mcmeta 파싱 실패: {exc}")

    data_dir = os.path.join(path, "data")
    if not os.path.isdir(data_dir):
        issues.append("data 디렉터리 없음")
        return issues

    namespaces = [d for d in os.listdir(data_dir) if os.path.isdir(os.path.join(data_dir, d))]
    if not namespaces:
        issues.append("네임스페이스가 없습니다 (data/* 비어있음)")
    for ns in namespaces:
        if not VALID_NS.match(ns):
            issues.append(f"네임스페이스 이름 규칙 위반: {ns}")

    # functions 유무, load/tick 태그 확인
    for ns in namespaces:
        fn_dir = os.path.join(data_dir, ns, "functions")
        if not os.path.isdir(fn_dir):
            issues.append(f"{ns}: functions 폴더 없음")
        else:
            mcfunctions = [f for f in os.listdir(fn_dir) if f.endswith(".mcfunction")]
            if not mcfunctions:
                issues.append(f"{ns}: mcfunction 파일이 없습니다")
        # tags check
        tag_dir = os.path.join(data_dir, "minecraft", "tags", "functions")
        load_tag = os.path.join(tag_dir, "load.json")
        tick_tag = os.path.join(tag_dir, "tick.json")
        if not os.path.exists(load_tag):
            issues.append(f"{ns}: load 태그 없음 (data/minecraft/tags/functions/load.json)")
        if not os.path.exists(tick_tag):
            issues.append(f"{ns}: tick 태그 없음 (data/minecraft/tags/functions/tick.json)")
        break  # 공통 태그이므로 한 번만 확인

    return issues


def scan_resourcepack(path: str) -> List[str]:
    issues: List[str] = []
    pack_meta = os.path.join(path, "pack.mcmeta")
    if not os.path.exists(pack_meta):
        issues.append("pack.mcmeta 없음")
    else:
        try:
            with open(pack_meta, "r", encoding="utf-8") as f:
                meta = json.load(f)
            pf = meta.get("pack", {}).get("pack_format")
            if not pf:
                issues.append("pack.mcmeta pack_format 누락")
        except Exception as exc:
            issues.append(f"pack.mcmeta 파싱 실패: {exc}")

    assets_dir = os.path.join(path, "assets")
    if not os.path.isdir(assets_dir):
        issues.append("assets 디렉터리 없음")
        return issues

    namespaces = [d for d in os.listdir(assets_dir) if os.path.isdir(os.path.join(assets_dir, d))]
    if not namespaces:
        issues.append("네임스페이스가 없습니다 (assets/* 비어있음)")
    for ns in namespaces:
        if not VALID_NS.match(ns):
            issues.append(f"네임스페이스 이름 규칙 위반: {ns}")
        lang_dir = os.path.join(assets_dir, ns, "lang")
        if not os.path.isdir(lang_dir):
            issues.append(f"{ns}: lang 폴더 없음")
        tex_dir = os.path.join(assets_dir, ns, "textures")
        if not os.path.isdir(tex_dir):
            issues.append(f"{ns}: textures 폴더 없음")
    return issues


def scan_workspace(base: str) -> List[str]:
    issues: List[str] = []
    for kind, scan_func in (("datapacks", scan_datapack), ("resourcepacks", scan_resourcepack)):
        root = os.path.join(base, kind)
        if not os.path.isdir(root):
            issues.append(f"[{kind}] 폴더 없음: {root}")
            continue
        for entry in sorted(os.listdir(root)):
            pack_path = os.path.join(root, entry)
            if not os.path.isdir(pack_path):
                continue
            sub = scan_func(pack_path)
            if sub:
                for msg in sub:
                    issues.append(f"[{kind}] {entry}: {msg}")
            else:
                issues.append(f"[{kind}] {entry}: OK")
    if not issues:
        issues.append("검사할 팩이 없습니다.")
    return issues


__all__ = ["scan_workspace", "scan_datapack", "scan_resourcepack"]
