"""
分析引擎
========
两阶段流程：
1. 每位选中的大师独立分析（并行视角）
2. 综合裁判汇总分歧 + 结合用户具体情境给可执行建议
"""

from masters import MASTERS, SYNTHESIS_PROMPT
from llm_client import chat
from data_provider import StockInfo


def _build_context(stock: StockInfo, user_ctx: dict, drift_note: str | None = None) -> str:
    """把行情数据 + 用户情境 + 决策记忆拼成给 LLM 的输入"""
    hist_str = " → ".join(str(p) for p in stock.history[-10:])
    drift_block = f"\n\n【决策记忆提示】\n{drift_note}" if drift_note else ""
    return f"""【股票数据】
{stock.name}（{stock.code}）| 行业：{stock.industry}
现价 {stock.price} 元（今日 {stock.change_pct:+.2f}%）
PE {stock.pe} | PB {stock.pb} | 市值 {stock.market_cap} 亿
52周区间：{stock.low_52w} ~ {stock.high_52w}
近10日收盘：{hist_str}

【用户具体情境】
持仓状态：{user_ctx['position']}
持仓成本：{user_ctx['cost'] or '未持有/未填写'}
该股占总仓位比例：{user_ctx['weight']}
风险偏好：{user_ctx['risk']}
投资期限：{user_ctx['horizon']}
当前困惑：{user_ctx['question'] or '无特别说明'}{drift_block}

请基于你的投资框架，针对这只股票和这位用户的具体处境给出分析。控制在 300 字以内，用 Markdown 分点。"""


def analyze_with_master(master_key: str, stock: StockInfo, user_ctx: dict,
                        drift_note: str | None = None) -> str:
    m = MASTERS[master_key]
    return chat(system_prompt=m["framework"],
                user_prompt=_build_context(stock, user_ctx, drift_note))


def synthesize(master_outputs: dict, stock: StockInfo, user_ctx: dict,
               drift_note: str | None = None) -> str:
    """汇总各框架观点：共识/永久分歧 + 框架适配 + 认知风险 + 可执行清单"""
    views = "\n\n".join(
        f"### {MASTERS[k]['name']}（{MASTERS[k].get('framework_name', '')}）的观点\n{v}"
        for k, v in master_outputs.items()
    )
    user_prompt = (_build_context(stock, user_ctx, drift_note)
                   + "\n\n【各框架的分析】\n" + views)
    return chat(system_prompt=SYNTHESIS_PROMPT, user_prompt=user_prompt, temperature=0.5)
