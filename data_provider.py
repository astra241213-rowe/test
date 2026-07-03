"""
数据层（抽象接口 + 模拟数据）
============================
比赛日拿到官方 SDK 后，只需要改这个文件：
把 MockDataProvider 换成调用官方行情接口的实现，
其他文件（app.py / analyzer.py）一行都不用动。
"""

import random
from dataclasses import dataclass, field
from datetime import datetime, timedelta


@dataclass
class StockInfo:
    code: str
    name: str
    price: float          # 现价
    change_pct: float     # 今日涨跌幅 %
    pe: float             # 市盈率
    pb: float             # 市净率
    market_cap: float     # 市值（亿）
    industry: str
    high_52w: float
    low_52w: float
    history: list = field(default_factory=list)  # 近30日收盘价


# ---------- 模拟数据（今晚开发/演示用） ----------

_MOCK_STOCKS = {
    "600519": ("贵州茅台", 1450.0, "白酒", 28.5, 8.2, 18200),
    "000858": ("五粮液", 128.0, "白酒", 15.2, 3.1, 4960),
    "300750": ("宁德时代", 195.0, "新能源电池", 22.8, 4.5, 8600),
    "601318": ("中国平安", 52.0, "保险", 9.8, 1.1, 9500),
    "000001": ("平安银行", 11.5, "银行", 5.2, 0.6, 2230),
    "002594": ("比亚迪", 245.0, "新能源汽车", 24.1, 5.3, 7100),
}


def _gen_history(base_price: float, days: int = 30) -> list:
    """生成一段随机但连贯的历史价格，方便画图和让 LLM 分析趋势"""
    prices, p = [], base_price * random.uniform(0.85, 1.1)
    for _ in range(days):
        p *= 1 + random.uniform(-0.03, 0.03)
        prices.append(round(p, 2))
    # 让最后一天等于现价，看起来自然
    prices[-1] = base_price
    return prices


class MockDataProvider:
    """模拟行情。接口签名就是明天要对齐官方 SDK 的地方。"""

    def get_stock(self, code: str) -> StockInfo | None:
        code = code.strip()
        if code not in _MOCK_STOCKS:
            return None
        name, price, industry, pe, pb, cap = _MOCK_STOCKS[code]
        # 加一点随机波动，让每次演示不完全一样
        price = round(price * random.uniform(0.98, 1.02), 2)
        hist = _gen_history(price)
        return StockInfo(
            code=code, name=name, price=price,
            change_pct=round(random.uniform(-3, 3), 2),
            pe=pe, pb=pb, market_cap=cap, industry=industry,
            high_52w=round(price * 1.35, 2),
            low_52w=round(price * 0.72, 2),
            history=hist,
        )

    def list_supported(self) -> dict:
        return {c: v[0] for c, v in _MOCK_STOCKS.items()}


# ---------- 明天替换成这样（示意） ----------
# class OfficialSDKProvider:
#     def __init__(self, api_key):
#         self.client = official_sdk.Client(api_key)   # 官方SDK初始化
#     def get_stock(self, code):
#         raw = self.client.quote(code)                # 官方行情接口
#         return StockInfo(code=code, name=raw["name"], ...)  # 字段映射


# 全局单例：app.py 只 import 这个
provider = MockDataProvider()
