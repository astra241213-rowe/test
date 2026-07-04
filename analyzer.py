"""
分析引擎
========
三阶段流程：
1. 每位选中的大师只基于股票证据独立分析，不提前注入用户处境
2. 交叉质询把表面冲突逼成可验证的脆弱前提
3. 裁判先诊断分歧类型，再决定哪些分歧需要结合用户处境路由
"""

from masters import MASTERS, SYNTHESIS_PROMPT
from llm_client import chat
from data_provider import StockInfo
from typing import Optional


def _build_stock_context(stock: StockInfo) -> str:
    """只把股票证据拼给大师，避免在独立分析阶段提前按用户处境加权"""
    hist_str = " → ".join(str(p) for p in stock.history[-10:])
    src_label = "实时数据(yfinance)" if stock.source == "yfinance" else "离线演示数据(模拟)"
    return f"""【数据来源规则】以下股票数据来源：{src_label}。你只能引用下方提供的数字；如果你想使用任何训练记忆中的数字（历史财报、增速等），必须显式标注"⚠️ 此数字来自模型记忆，可能过时，请核实"。

【股票数据】
{stock.name}（{stock.code}）| 行业：{stock.industry}
现价 {stock.price} 元（今日 {stock.change_pct:+.2f}%）
PE {stock.pe} | PB {stock.pb} | 市值 {stock.market_cap} 亿
52周区间：{stock.low_52w} ~ {stock.high_52w}
近10日收盘：{hist_str}"""


def _build_judge_context(stock: StockInfo, user_ctx: dict, drift_note: Optional[str] = None) -> str:
    """把股票证据 + 用户情境 + 决策记忆拼给裁判"""
    drift_block = f"\n\n【决策记忆提示】\n{drift_note}" if drift_note else ""
    return _build_stock_context(stock) + f"""

【用户具体情境】
持仓状态：{user_ctx['position']}
投入本金：{user_ctx.get('holding_amount', '未填写')}
买入成本价：{user_ctx.get('cost_price', '未填写')}
可用现金：{user_ctx.get('available_cash', '未填写')}
最多愿意亏损：{user_ctx.get('max_loss_amount', '未填写')}
计划补仓金额：{user_ctx.get('add_amount', '未填写')}
系统估算仓位压力：{user_ctx.get('pressure_level', '未知')}
当前浮盈亏：{user_ctx.get('pnl_text', '未知')}
补仓后成本：{user_ctx.get('avg_cost_after_add_text', '未知')}
参考止损价：{user_ctx.get('stop_loss_price_text', '未知')}
风险偏好：{user_ctx['risk']}
投资期限：{user_ctx['horizon']}
当前困惑：{user_ctx['question'] or '无特别说明'}{drift_block}

【裁判规则】
先看四位大师和交叉质询暴露出的分歧属于事实、时间还是偏好。
事实性分歧不能用用户偏好强行加权，只能转成待验证指标。
时间/偏好分歧才允许结合用户期限、仓位、风险承受力做路由。"""


def analyze_with_master(master_key: str, stock: StockInfo, user_ctx: dict,
                        drift_note: Optional[str] = None) -> str:
    m = MASTERS[master_key]
    return chat(system_prompt=m["framework"],
                user_prompt=_build_stock_context(stock))


def synthesize(master_outputs: dict, stock: StockInfo, user_ctx: dict,
               drift_note: Optional[str] = None, extra_views: Optional[dict] = None,
               debate_text: Optional[str] = None) -> str:
    """汇总各框架观点+情绪证据+辩论实录：共识/永久分歧+框架适配+行为偏差+清单"""
    parts = [f"### {MASTERS[k]['name']}（{MASTERS[k].get('framework_name', '')}）的观点\n{v}"
             for k, v in master_outputs.items()]
    for label, text in (extra_views or {}).items():
        parts.append(f"### {label}\n{text}")
    views = "\n\n".join(parts)
    if debate_text:
        views += "\n\n【交叉质询实录】\n" + debate_text
    user_prompt = (_build_judge_context(stock, user_ctx, drift_note)
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
