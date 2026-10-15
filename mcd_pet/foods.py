"""饲料库：麦当劳 MCP 真实餐品营养数据。"""

from __future__ import annotations

import json
import os
from typing import Dict, List, Optional

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "foods.json")

_CACHE: Optional[Dict[str, dict]] = None


def load() -> Dict[str, dict]:
    """加载饲料库（离线快照）。"""
    global _CACHE
    if _CACHE is None:
        with open(DATA_PATH, encoding="utf-8") as f:
            _CACHE = json.load(f)["foods"]
    return _CACHE


def reload_from(raw: Dict[str, dict]) -> None:
    """用实时数据替换饲料库（--live 模式）。"""
    global _CACHE
    _CACHE = raw


def source_label() -> str:
    with open(DATA_PATH, encoding="utf-8") as f:
        d = json.load(f)
    return f'SNAPSHOT · data/foods.json（{d.get("_count", "?")} 个真实餐品，MCP 抓取）'


def get(name: str) -> Optional[dict]:
    """精确取；找不到就做包含匹配。

    真实餐品名带规格后缀（如「麦乐鸡5块」「麦乐鸡10块」），
    所以 `feed 麦乐鸡` 这种简写必须能命中——多个命中时取名字最短的那个。
    """
    foods = load()
    if name in foods:
        return dict(foods[name], name=name)
    hits = [k for k in foods if name in k]
    if not hits:
        return None
    best = min(hits, key=len)
    return dict(foods[best], name=best)


def search(keyword: str, limit: int = 12) -> List[str]:
    foods = load()
    return [k for k in foods if keyword in k][:limit]


def by_cat(cat: str) -> List[str]:
    foods = load()
    return [k for k, v in foods.items() if v.get("cat") == cat]


def cats() -> List[str]:
    foods = load()
    seen: List[str] = []
    for v in foods.values():
        c = v.get("cat", "其他")
        if c not in seen:
            seen.append(c)
    return seen
