"""
决策记忆层（Decision Memory）
=============================
产品第五层：记录用户每次分析的处境与目标，
- 再次分析同一只股票时，自动检测"目标漂移"（上次说长持，这次想止损？）
- 沉淀决策档案（Decision Journal），支持复盘
存储：本地 JSON 文件（黑客松够用；生产环境可换数据库）
"""

import json
import os
from datetime import datetime
from typing import Optional

MEMORY_FILE = "decision_journal.json"


def _load() -> list:
    if not os.path.exists(MEMORY_FILE):
        return []
    try:
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def _save(records: list):
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)


def record_decision(code: str, name: str, user_ctx: dict, synthesis_summary: str):
    """每次分析后记录一条决策档案"""
    records = _load()
    records.append({
        "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "code": code,
        "name": name,
        "position": user_ctx["position"],
        "cost": user_ctx["cost"],
        "weight": user_ctx["weight"],
        "risk": user_ctx["risk"],
        "horizon": user_ctx["horizon"],
        "question": user_ctx["question"],
        "synthesis": synthesis_summary[:500],  # 只存摘要
        "followed": None,   # 复盘时填写：是否执行了建议
        "reflection": "",   # 复盘时填写：回头看的反思
    })
    _save(records)


def get_history(code: str) -> list:
    """取该股票的历史决策记录（时间正序）"""
    return [r for r in _load() if r["code"] == code]


def detect_drift(code: str, current_ctx: dict) -> Optional[str]:
    """
    检测目标漂移：对比上一次对同一只股票的分析。
    返回一段提示文字（给 UI 展示 + 注入 LLM 上下文），无漂移返回 None。
    """
    history = get_history(code)
    if not history:
        return None
    last = history[-1]
    drifts = []
    if last["horizon"] != current_ctx["horizon"]:
        drifts.append(f"投资期限从「{last['horizon']}」变成了「{current_ctx['horizon']}」")
    if last["position"] != current_ctx["position"]:
        drifts.append(f"持仓意图从「{last['position']}」变成了「{current_ctx['position']}」")
    if last["risk"] != current_ctx["risk"]:
        drifts.append(f"风险偏好从「{last['risk']}」变成了「{current_ctx['risk']}」")
    if not drifts:
        return None
    return (f"⏳ 决策记忆：你在 {last['time']} 分析过 {last['name']}。与上次相比："
            + "；".join(drifts)
            + "。是什么新信息导致了这个变化？如果没有新信息，这可能是情绪在改写策略。")


def get_all_records() -> list:
    """复盘页用：全部决策档案（时间倒序）"""
    return list(reversed(_load()))


def update_reflection(index_from_latest: int, followed: str, reflection: str):
    """复盘页用：回填是否执行与反思"""
    records = _load()
    if not records:
        return
    real_index = len(records) - 1 - index_from_latest
    if 0 <= real_index < len(records):
        records[real_index]["followed"] = followed
        records[real_index]["reflection"] = reflection
        _save(records)
