"""
数据层 v3：港美股 + 新闻（Evidence Layer 的行情/新闻证据源）
=============================================================
- 优先尝试 yfinance 拉真实港美股数据（Codespace/本地联网时自动生效）
- 失败自动降级到内置模拟数据（离线演示兜底）
- 支持任意代码输入：美股字母（AAPL），港股数字+.HK（0700.HK）
"""

import random
from dataclasses import dataclass, field


@dataclass
class StockInfo:
    code: str
    name: str
    price: float
    change_pct: float
    pe: float
    pb: float
    market_cap: float      # 亿（对应币秭）
    industry: str
    high_52w: float
    low_52w: float
    currency: str          # USD / HKD
    history: list = field(default_factory=list)
    source: str = "mock"   # mock / yfinance


_MOCK = {
    "AAPL":    ("苹果 Apple", 232.5, "消费电子", 35.2, 48.0, 35600, "USD"),
    "NVDA":    ("英伟达 NVIDIA", 178.0, "半导体/AI", 52.3, 45.1, 43500, "USD"),
    "TSLA":    ("特斯拉 Tesla", 315.0, "新能源汽车", 68.5, 12.4, 10100, "USD"),
    "MSFT":    ("微软 Microsoft", 465.0, "软件/云", 38.6, 11.2, 34500, "USD"),
    "0700.HK": ("腾讯控股", 585.0, "互联网/游戏", 28.4, 4.6, 54000, "HKD"),
    "9988.HK": ("阿里巴巴", 158.0, "电商/云计算", 21.7, 2.4, 30000, "HKD"),
    "3690.HK": ("美团", 138.0, "本地生活", 32.1, 4.1, 8600, "HKD"),
    "1810.HK": ("小米集团", 52.0, "消费电子/汽车", 30.5, 5.8, 13000, "HKD"),
}

_MOCK_NEWS_TPL = [
    ("{name}公布最新季度财报，营收与利润率表现受到市场关注", "财报"),
    ("多家投行调整{name}目标价，机构观点出现分化", "评级"),
    ("{industry}赛道竞争格局生变，{name}宣布新的战略投入", "行业"),
    ("宏观数据公布后市场波动加大，{name}成交量明显放大", "宏观"),
    ("{name}管理层在业绩会上回应市场关切，谈及未来资本开支计划", "公司"),
]


def _gen_history(base_price: float, days: int = 30) -> list:
    prices, p = [], base_price * random.uniform(0.85, 1.1)
    for _ in range(days):
        p *= 1 + random.uniform(-0.03, 0.03)
        prices.append(round(p, 2))
    prices[-1] = base_price
    return prices


class DataProvider:
    """先真实数据，后模拟兜底"""

    def get_stock(self, code: str) -> StockInfo | None:
        code = code.strip().upper()
        real = self._try_yfinance(code)
        if real:
            return real
        return self._mock_stock(code)

    def get_news(self, code: str, limit: int = 5) -> list:
        """返回 [{'title':..., 'source':..., 'time':...}]"""
        code = code.strip().upper()
        real = self._try_yf_news(code, limit)
        if real:
            return real
        return self._mock_news(code, limit)

    def list_supported(self) -> dict:
        return {c: v[0] for c, v in _MOCK.items()}

    # ---------- 真实数据（yfinance） ----------
    def _try_yfinance(self, code: str) -> StockInfo | None:
        try:
            import yfinance as yf
            t = yf.Ticker(code)
            hist = t.history(period="1mo")
            if hist is None or hist.empty:
                return None
            closes = [round(float(x), 2) for x in hist["Close"].tolist()][-30:]
            info = {}
            try:
                info = t.info or {}
            except Exception:
                pass
            price = closes[-1]
            prev = closes[-2] if len(closes) > 1 else price
            name = info.get("shortName") or _MOCK.get(code, (code,))[0]
            currency = info.get("currency") or ("HKD" if code.endswith(".HK") else "USD")
            mcap = info.get("marketCap") or 0
            return StockInfo(
                code=code, name=name, price=price,
                change_pct=round((price - prev) / prev * 100, 2) if prev else 0.0,
                pe=round(info.get("trailingPE") or 0, 1),
                pb=round(info.get("priceToBook") or 0, 1),
                market_cap=round(mcap / 1e8, 0) if mcap else 0,
                industry=info.get("industry") or "-",
                high_52w=round(info.get("fiftyTwoWeekHigh") or max(closes), 2),
                low_52w=round(info.get("fiftyTwoWeekLow") or min(closes), 2),
                currency=currency, history=closes, source="yfinance",
            )
        except Exception:
            return None

    def _try_yf_news(self, code: str, limit: int) -> list | None:
        try:
            import yfinance as yf
            raw = yf.Ticker(code).news or []
            items = []
            for n in raw[:limit]:
                content = n.get("content", n)
                title = content.get("title") or n.get("title")
                if not title:
                    continue
                src = (content.get("provider") or {}).get("displayName") or n.get("publisher", "")
                items.append({"title": title, "source": src or "News", "time": ""})
            return items or None
        except Exception:
            return None

    # ---------- 模拟兜底 ----------
    def _mock_stock(self, code: str) -> StockInfo | None:
        if code not in _MOCK:
            return None
        name, price, industry, pe, pb, cap, cur = _MOCK[code]
        price = round(price * random.uniform(0.98, 1.02), 2)
        return StockInfo(
            code=code, name=name, price=price,
            change_pct=round(random.uniform(-3, 3), 2),
            pe=pe, pb=pb, market_cap=cap, industry=industry,
            high_52w=round(price * 1.35, 2), low_52w=round(price * 0.72, 2),
            currency=cur, history=_gen_history(price), source="mock",
        )

    def _mock_news(self, code: str, limit: int) -> list:
        base = _MOCK.get(code)
        name = base[0] if base else code
        industry = base[2] if base else "相关行业"
        random.shuffle(_MOCK_NEWS_TPL)
        return [{"title": t.format(name=name, industry=industry),
                 "source": f"模拟•{tag}", "time": ""}
                for t, tag in _MOCK_NEWS_TPL[:limit]]


provider = DataProvider()
