"""
风险雷达（Risk Radar）
=====================
不依赖 LLM 的量化风险评分：估值 / 趋势 / 波动 / 仓位 四个维度 0-100。
即时计算、即时展示——演示时的"技术含量"担当。
"""

import statistics
from data_provider import StockInfo


def compute_risk_radar(stock: StockInfo, user_ctx: dict) -> list:
    """返回 [(维度, 分数0-100, 人话解读), ...]"""
    h = stock.history or [stock.price]

    # 波动风险：近30日日均波动幅度
    rets = [(h[i + 1] - h[i]) / h[i] for i in range(len(h) - 1)] if len(h) > 1 else [0.0]
    daily_vol = statistics.pstdev(rets) * 100 if len(rets) > 1 else 0.0
    vol_score = min(100, daily_vol / 4 * 100)  # 日均波动4% = 满格

    # 估值风险：PE 相对位置（粗颗粒启发式）
    pe = stock.pe or 0
    pe_score = min(100, max(5, pe / 60 * 100)) if pe > 0 else 50

    # 趋势风险：近30日累计涨跌
    mom = (h[-1] - h[0]) / h[0] * 100 if h[0] else 0.0
    trend_score = min(100, max(5, 50 - mom * 2))  # 跌越多风险分越高

    # 仓位风险：来自真实持仓账本。weight 可能是 "36.5%"，也可能是旧版分档。
    weight_text = str(user_ctx.get("weight", ""))
    weight_map = {"<10%": 15, "10-30%": 35, "30-50%": 60, ">50%": 85, "全仓": 100}
    if weight_text.endswith("%"):
        try:
            ratio = float(weight_text[:-1])
            pos_score = min(100, max(5, ratio * 1.2))
        except Exception:
            pos_score = 50
    else:
        pos_score = weight_map.get(weight_text, 50)

    def level(s):
        return "偏高" if s >= 60 else ("中等" if s >= 35 else "偏低")

    return [
        ("估值风险", round(pe_score),
         f"PE {pe if pe else '暂无'}，估值水平{level(pe_score)}" if pe else "缺少PE数据，按中性处理"),
        ("趋势风险", round(trend_score),
         f"近30日{'累计上涨' if mom >= 0 else '累计下跌'} {abs(mom):.1f}%，趋势风险{level(trend_score)}"),
        ("波动风险", round(vol_score),
         f"日均波动约 {daily_vol:.1f}%，波动风险{level(vol_score)}"),
        ("仓位风险", round(pos_score),
         f"该股约占可见投资资金 {user_ctx.get('weight','?')}——"
         + ("集中度过高：个股的任何波动都会直接改写你的整体盈亏和心态" if pos_score >= 60 else "集中度尚可控")),
    ]
