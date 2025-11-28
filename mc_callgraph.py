# -*- coding: utf-8 -*-
"""
mcfunction 호출 그래프 생성 유틸.
function <ns>:<path> 호출을 파싱해 참조 관계를 만든다.
"""
from __future__ import annotations

import os
import re
from typing import Dict, List, Set, Tuple

FUNC_RE = re.compile(r"\\bfunction\\s+([a-z0-9_\\-\\.]+:[a-z0-9_\\/\\.]+)", re.IGNORECASE)


def list_functions(base: str) -> Dict[str, str]:
    """
    workspace 내 mcfunction 파일을 id -> 파일 경로 매핑으로 반환.
    id 형식: <namespace>:<path> (확장자 제외, 슬래시는 /)
    """
    mapping: Dict[str, str] = {}
    dp_root = os.path.join(base, "datapacks")
    if not os.path.isdir(dp_root):
        return mapping
    for pack in os.listdir(dp_root):
        p_path = os.path.join(dp_root, pack)
        if not os.path.isdir(p_path):
            continue
        data_dir = os.path.join(p_path, "data")
        if not os.path.isdir(data_dir):
            continue
        for ns in os.listdir(data_dir):
            fn_dir = os.path.join(data_dir, ns, "functions")
            if not os.path.isdir(fn_dir):
                continue
            for root, _, files in os.walk(fn_dir):
                for f in files:
                    if f.endswith(".mcfunction"):
                        full = os.path.join(root, f)
                        rel = os.path.relpath(full, fn_dir).replace("\\\\", "/").replace(".mcfunction", "")
                        func_id = f"{ns}:{rel}"
                        mapping[func_id] = full
    return mapping


def build_call_graph(base: str) -> Tuple[Dict[str, Set[str]], Dict[str, str]]:
    """
    returns: (graph, id_to_path)
    graph: func_id -> set(called_func_id)
    """
    id_to_path = list_functions(base)
    graph: Dict[str, Set[str]] = {fid: set() for fid in id_to_path}
    for fid, path in id_to_path.items():
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                for line in f:
                    for match in FUNC_RE.findall(line):
                        graph[fid].add(match.strip())
        except Exception:
            continue
    return graph, id_to_path


def reachable_from(graph: Dict[str, Set[str]], starts: List[str], depth: int = 5) -> Set[str]:
    seen: Set[str] = set()
    frontier: List[Tuple[str, int]] = [(s, 0) for s in starts]
    while frontier:
        node, d = frontier.pop()
        if node in seen or d > depth:
            continue
        seen.add(node)
        for nxt in graph.get(node, []):
            frontier.append((nxt, d + 1))
    return seen


__all__ = ["build_call_graph", "reachable_from", "list_functions"]
