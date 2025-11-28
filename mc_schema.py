# -*- coding: utf-8 -*-
"""
데이터팩/리소스팩 JSON의 기본 스키마를 가볍게 검사하는 유틸.
정교한 검증은 아니며, 필수 키 누락/타입 오류 등을 빠르게 확인하는 용도.
"""
from __future__ import annotations

import json
import os
from typing import Dict, List


def load_json(path: str) -> Dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def validate_recipe(data: Dict) -> List[str]:
    issues = []
    if data.get("type") not in ("minecraft:crafting_shaped", "minecraft:crafting_shapeless"):
        issues.append("type이 crafting_shaped/shapeless가 아님")
    if "result" not in data:
        issues.append("result 누락")
    return issues


def validate_loot(data: Dict) -> List[str]:
    issues = []
    if "pools" not in data:
        issues.append("pools 누락")
    return issues


def validate_advancement(data: Dict) -> List[str]:
    issues = []
    if "criteria" not in data:
        issues.append("criteria 누락")
    if "display" not in data:
        issues.append("display 누락")
    return issues


def validate_predicate(data: Dict) -> List[str]:
    issues = []
    if "condition" not in data:
        issues.append("condition 누락")
    return issues


def validate_tag(data: Dict) -> List[str]:
    issues = []
    if "values" not in data:
        issues.append("values 누락")
    return issues


VALIDATORS = {
    "recipes": validate_recipe,
    "loot_tables": validate_loot,
    "advancements": validate_advancement,
    "predicates": validate_predicate,
    "tags": validate_tag,
}


def guess_validator(path: str):
    for key, validator in VALIDATORS.items():
        if os.sep + key + os.sep in path:
            return validator, key
    return None, None


def validate_file(path: str) -> List[str]:
    data = load_json(path)
    validator, kind = guess_validator(path)
    if not validator:
        return ["알 수 없는 JSON 유형 (경로로 추정 실패)"]
    issues = validator(data)
    if not issues:
        return [f"{kind}: OK"]
    return issues


def scan_workspace_json(base: str) -> List[str]:
    results: List[str] = []
    for root, _, files in os.walk(base):
        for f in files:
            if not f.endswith(".json"):
                continue
            full = os.path.join(root, f)
            validator, kind = guess_validator(full)
            if not validator:
                continue
            try:
                data = load_json(full)
                issues = validator(data)
                if issues:
                    for msg in issues:
                        results.append(f"{os.path.relpath(full, base)}: {msg}")
            except Exception as exc:
                results.append(f"{os.path.relpath(full, base)}: 파싱 실패 {exc}")
    if not results:
        results.append("검사 대상 JSON에서 오류를 찾지 못했습니다.")
    return results


__all__ = ["validate_file", "scan_workspace_json"]
