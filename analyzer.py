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
    src_label = "实时数据(yfinance)" if stock.source == "yfinance" else "离线演示数据(模拟)"
    return f"""【数据来源规则】以下股票数据来源：{src_label}。你只能引用下方提供的数字；如果你想使用任何训练记忆中的数字（历史财报、增速等），必须显式标注"⚠️ 此数字来自模型记忆，可能过时，请核实"。

【股票数据】
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

请基于你的投资框架和输出模板，针对这只股票和这位用户的具体处境给出分析。说人话，短句，不堆术语。"""


def analyze_with_master(master_key: str, stock: StockInfo, user_ctx: dict,
                        drift_note: str | None = None) -> str:
    m = MASTERS[master_key]
    return chat(system_prompt=m["framework"],
                user_prompt=_build_context(stock, user_ctx, drift_note))


def synthesize(master_outputs: dict, stock: StockInfo, user_ctx: dict,
               drift_note: str | None = None, extra_views: dict | None = None,
               debate_text: str | None = None) -> str:
    """汇总各框架观点+情绪证据+辩论实录：共识/永久分歧+框架适配+行为偏差+清单"""
    parts = [f"### {MASTERS[k]['name']}（{MASTERS[k].get('framework_name', '')}）的观点\n{v}"
             for k, v in master_outputs.items()]
    for label, text in (extra_views or {}).items():
        parts.append(f"### {label}\n{text}")
    views = "\n\n".join(parts)
    if debate_text:
        views += "\n\n【交叉质询实录】\n" + debate_text
    user_prompt = (_build_context(stock, user_ctx, drift_note)
                   + "\n\n【各方分析】\n" + views)
    return chat(system_prompt=SYNTHESIS_PROMPT, user_prompt=user_prompt, temperature=0.5)


# ---------- v3 新增：辩论与情绪 Agent ----------
from masters import DEBATE_PROMPT, SENTIMENT_PROMPT


def run_debate(master_outputs: dict, stock: StockInfo) -> str:
    """交叉质询：各框架互相攻击对方最脆弱的前提"""
    views = "\n\n".join(
        f"### {MASTERS[k]['name']}的观点\n{v}" for k, v in master_outputs.items()
    )
    user_prompt = f"股票：{stock.name}（{stock.code}）\n\n【各方独立分析】\n{views}\n\n请开始交叉质询。"
    return chat(system_prompt=DEBATE_PROMPT, user_prompt=user_prompt, temperature=0.8)


def analyze_sentiment(stock: StockInfo, news_list: list, user_ctx: dict) -> str:
    """新闻情绪 Agent"""
    headlines = "\n".join(f"- {n['title']}（{n['source']}）" for n in news_list)
    user_prompt = (f"股票：{stock.name}（{stock.code}）\n"
                   f"用户投资期限：{user_ctx['horizon']}\n\n【近期新闻】\n{headlines}")
    return chat(system_prompt=SENTIMENT_PROMPT, user_prompt=user_prompt, temperature=0.5)
