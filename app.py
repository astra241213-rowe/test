"""
大师圆桌 · Decision Intelligence
运行：streamlit run app.py
"""

from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta

import pandas as pd
import streamlit as st

import memory
import llm_client
from analyzer import analyze_sentiment, analyze_with_master, run_debate, synthesize
from data_provider import provider
from masters import DISCLAIMER, MASTERS
from portfolio import calculate_portfolio
from risk_radar import compute_risk_radar


st.set_page_config(page_title="大师圆桌 · 投资决策智能", page_icon="🎓", layout="wide")

# ---------- 纯黑主题：去掉红色和多余工具栏 ----------
st.markdown("""<style>
.stApp { background:#050505; }
[data-testid="stSidebar"] { background:#080808; border-right:1px solid #222; }
[data-testid="stToolbar"], [data-testid="stDecoration"], #MainMenu, footer, header { visibility:hidden; height:0; }
h1, h2, h3 { color:#F4D27A !important; letter-spacing:0; }
h1 { font-weight:700; border-bottom:1px solid #222; padding-bottom:.35em; }
.stApp, .stMarkdown, p, label, span { color:#F2F2F2; }
.stCaption, [data-testid="stCaptionContainer"] { color:#9B9B9B !important; }
.stButton>button[kind="primary"] { background:#F4D27A; color:#050505; font-weight:800; border:none; border-radius:8px; }
.stButton>button[kind="primary"]:hover { background:#FFE39A; color:#050505; border:none; }
[data-testid="stMetric"] { background:#0D0D0D; border:1px solid #242424; border-radius:8px; padding:10px 14px; }
[data-testid="stMetricValue"] { color:#F4D27A; }
.stProgress > div > div > div > div { background:#F4D27A; }
[data-testid="stExpander"] { background:#0D0D0D; border:1px solid #242424; border-radius:8px; }
.stTabs [data-baseweb="tab-list"] { border-bottom:1px solid #222; }
.stTabs [aria-selected="true"] { color:#F4D27A !important; border-bottom-color:#F4D27A !important; }
div[data-testid="stAlert"] { border-radius:8px; }
hr { border-color:#222; }
.stRadio [role="radiogroup"] label > div:first-child,
.stCheckbox label > div:first-child { border-color:#555 !important; background:#1A1A1A !important; }
.stRadio [role="radiogroup"] label[data-checked="true"] > div:first-child,
.stCheckbox label[data-checked="true"] > div:first-child { border-color:#F4D27A !important; background:#F4D27A !important; }
input[type="radio"], input[type="checkbox"] { accent-color:#F4D27A !important; }
.step-strip { display:flex; gap:8px; flex-wrap:wrap; margin:.5rem 0 1rem 0; }
.step-chip { border:1px solid #333; background:#0D0D0D; border-radius:999px; padding:8px 12px; color:#F2F2F2; font-size:14px; }
.step-chip b { color:#F4D27A; }
.timeline-item { border-left:3px solid #F4D27A; padding:2px 0 12px 12px; margin-left:6px; }
.timeline-date { color:#F4D27A; font-weight:700; }
.soft-box { border:1px solid #333; background:#0D0D0D; border-radius:8px; padding:14px; }
</style>""", unsafe_allow_html=True)

st.title("大师圆桌 · 个人投资决策智能")
st.caption("先算账，再让四位大师用不同框架审一遍：林奇看业务，巴菲特看生意，格雷厄姆看估值，利弗莫尔看时机。")


def money(value, currency=""):
    try:
        return f"{value:,.2f} {currency}".strip()
    except Exception:
        return "—"


def pct(value):
    try:
        return f"{value:+.2f}%"
    except Exception:
        return "—"


def maybe_pct(value):
    return f"{value:.1f}%" if value is not None else "—"


def maybe_money_yi(value, currency=""):
    return f"{value:,.1f} 亿 {currency}".strip() if value is not None else "—"


def build_timeline(stock, portfolio, news_list):
    today = date.today()
    events = [
        {
            "date": today - timedelta(days=29),
            "title": "30日前价格",
            "detail": f"价格约 {stock.history[0]} {stock.currency}，作为短期走势起点。",
        },
        {
            "date": today - timedelta(days=14),
            "title": "区间中点观察",
            "detail": f"近30日中段价格约 {stock.history[len(stock.history)//2]} {stock.currency}。",
        },
        {
            "date": today - timedelta(days=7),
            "title": "用户成本线",
            "detail": f"你的买入成本约 {portfolio['cost_price'] or 0:.2f} {stock.currency}，用来判断被套/盈利压力。",
        },
        {
            "date": today,
            "title": "当前价格",
            "detail": f"当前价格 {stock.price} {stock.currency}，相对你的成本浮盈亏 {pct(portfolio['pnl_pct'])}。",
        },
    ]
    for idx, item in enumerate(news_list[:2]):
        events.insert(2 + idx, {
            "date": today - timedelta(days=10 - idx * 3),
            "title": item["source"],
            "detail": item["title"],
        })
    return sorted(events, key=lambda x: x["date"])


def render_framework_cards():
    st.subheader("四位大师怎么帮你看")
    st.markdown(
        """
        <div class="step-strip">
          <span class="step-chip"><b>彼得·林奇</b> 股票是什么</span>
          <span class="step-chip"><b>沃伦·巴菲特</b> 公司好不好</span>
          <span class="step-chip"><b>格雷厄姆</b> 价格贵不贵</span>
          <span class="step-chip"><b>利弗莫尔</b> 时机对不对</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


page = st.sidebar.selectbox("导航", ["决策分析", "决策档案与复盘"])
model_status = llm_client.status()
st.sidebar.caption(f"模型：{model_status['label']} · {model_status['model']}")
st.sidebar.caption(f"数据：{provider.status_label()}，失败自动切换演示数据")

if page == "决策分析":
    st.subheader("1. 先填写你的持仓账本")
    st.caption("这一步是核心：系统会先算清你的成本、浮盈亏、参考止损位和资金压力。")
    with st.container():
        a1, a2, a3, a4 = st.columns(4)
        with a1:
            position = st.selectbox("现在状态", ["未持有，考虑买入", "已持有，考虑加仓", "已持有，考虑卖出", "已持有，被套纠结中"])
            holding_amount = st.number_input("已经投入多少钱", min_value=0.0, value=10000.0, step=1000.0)
        with a2:
            cost_price = st.number_input("你的买入成本价", min_value=0.0, value=250.0, step=1.0)
            available_cash = st.number_input("还能用于投资的现金", min_value=0.0, value=10000.0, step=1000.0)
        with a3:
            st.markdown("<div class='soft-box'>系统会根据你当前成本、浮盈亏和现金状况，自动估算资金压力。</div>", unsafe_allow_html=True)
        with a4:
            money_nature = st.selectbox("这笔钱的性质", ["纯闲钱，三年不用", "一年内可能要用", "含生活费或借贷资金"])
            experience = st.selectbox("投资经验", ["新手（<1年）", "1-3年", "3年以上"])
        b1, b2, b3 = st.columns([1, 1, 2])
        with b1:
            risk = st.selectbox("风险偏好", ["保守：亏10%就睡不着", "稳健：能接受20%回撤", "激进：波动是朋友"])
        with b2:
            horizon = st.selectbox("投资期限", ["短线（几天~几周）", "波段（几个月）", "长期（1年以上）"])
        with b3:
            question = st.text_area(
                "现在最纠结什么",
                height=80,
                placeholder="例如：已经亏了不少，想补仓摊成本，但又怕越补越套。",
            )

    st.subheader("2. 选择股票")
    col1, col2 = st.columns([1, 1.3])
    with col1:
        supported = provider.list_supported()
        mode = st.selectbox("选择方式", ["常用列表", "自定义代码"])
        if mode == "常用列表":
            code = st.selectbox("股票", options=list(supported.keys()), format_func=lambda c: f"{c} {supported[c]}")
        else:
            code = st.text_input("输入代码：美股如 AAPL，港股如 0700.HK", value="AAPL")
    with col2:
        render_framework_cards()

    st.divider()

    if st.button("开始分析我的决策", type="primary", use_container_width=True):
        with st.spinner("整理股票证据和持仓账本…"):
            stock = provider.get_stock(code)
        if stock is None:
            st.error("未找到该股票。美股直接输字母代码（AAPL），港股输数字+.HK（0700.HK）")
            st.stop()

        portfolio = calculate_portfolio(
            stock,
            holding_amount=holding_amount,
            cost_price=cost_price,
            available_cash=available_cash,
            max_loss_amount=0,
            add_amount=0,
        )

        user_ctx = dict(
            position=position,
            holding_amount=money(portfolio["holding_amount"], stock.currency),
            cost_price=money(portfolio["cost_price"], stock.currency),
            available_cash=money(portfolio["available_cash"], stock.currency),
            pressure_level=portfolio["pressure_level"],
            pnl_text=f"{money(portfolio['pnl'], stock.currency)}（{pct(portfolio['pnl_pct'])}）",
            stop_loss_price_text=money(portfolio["stop_loss_price"], stock.currency),
            cost=money(portfolio["cost_price"], stock.currency),
            weight=f"{portfolio['position_ratio']:.1f}%",
            risk=risk,
            horizon=horizon,
            question=f"资金性质：{money_nature}；投资经验：{experience}；{question}",
        )

        drift_note = memory.detect_drift(code, dict(user_ctx, question=question))
        if drift_note:
            st.warning(drift_note)

        src_tag = "实时数据" if stock.source == "yfinance" else "离线演示数据"
        st.subheader(f"{stock.name}（{stock.code}）")
        st.caption(f"{src_tag} ｜ 币种：{stock.currency} ｜ 行业：{stock.industry}")

        a, b, c, d = st.columns(4)
        a.metric("当前价格", f"{stock.price} {stock.currency}", pct(stock.change_pct))
        b.metric("PE / PB", f"{stock.pe or '—'} / {stock.pb or '—'}")
        c.metric("52周区间", f"{stock.low_52w} ~ {stock.high_52w}")
        d.metric("市值", f"{stock.market_cap:,.0f} 亿" if stock.market_cap else "—")

        st.subheader("自动拉取到的财务信号")
        f1, f2, f3, f4 = st.columns(4)
        f1.metric("收入增速", maybe_pct(stock.revenue_growth))
        f2.metric("ROE", maybe_pct(stock.roe))
        f3.metric("毛利率 / 净利率", f"{maybe_pct(stock.gross_margin)} / {maybe_pct(stock.profit_margin)}")
        f4.metric("经营现金流", maybe_money_yi(stock.operating_cashflow, stock.currency))
        st.caption("这些信号已自动尝试拉取；市场份额、产品/用户数据、年报原文等更深层信息，仍需要额外数据源。")

        st.subheader("系统计算结果：先把账算清楚")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("当前浮盈亏", money(portfolio["pnl"], stock.currency), pct(portfolio["pnl_pct"]))
        c2.metric("持仓股数", f"{portfolio['shares']:.2f}")
        c3.metric("参考止损价", money(portfolio["stop_loss_price"], stock.currency), f"-{portfolio['stop_loss_pct']}%")
        c4.metric("资金压力", portfolio["pressure_level"], f"仓位约 {portfolio['position_ratio']:.1f}%")
        st.info(portfolio["pressure_note"])

        st.subheader("价格 + 事件 + 你的成本线")
        chart_df = pd.DataFrame({
            "价格": stock.history,
            "你的成本线": [portfolio["cost_price"] if portfolio["cost_price"] else None] * len(stock.history),
            "参考止损线": [portfolio["stop_loss_price"] if portfolio["stop_loss_price"] else None] * len(stock.history),
        })
        st.line_chart(chart_df, height=220)

        news_list = provider.get_news(code)
        with st.expander("证据时间线", expanded=True):
            for event in build_timeline(stock, portfolio, news_list):
                st.markdown(
                    f"""<div class="timeline-item">
                    <span class="timeline-date">{event['date'].strftime('%m-%d')}</span> · <b>{event['title']}</b><br>
                    {event['detail']}
                    </div>""",
                    unsafe_allow_html=True,
                )

        st.subheader("量化风险雷达")
        radar = compute_risk_radar(stock, user_ctx)
        rcols = st.columns(len(radar))
        for rc, (dim, score, comment) in zip(rcols, radar):
            with rc:
                st.markdown(f"**{dim}** {score}/100")
                st.progress(score / 100)
                st.caption(comment)

        st.subheader("四位大师独立判断")
        selected = ["lynch", "buffett", "graham", "livermore"]
        with st.spinner("四套框架正在独立检查股票…"):
            with ThreadPoolExecutor(max_workers=4) as pool:
                futures = {k: pool.submit(analyze_with_master, k, stock, user_ctx, drift_note) for k in selected}
                outputs = {k: f.result() for k, f in futures.items()}

        for key in selected:
            title = f"{MASTERS[key]['name']}视角｜第{MASTERS[key]['emoji']}问：{MASTERS[key]['framework_name']}"
            with st.expander(title, expanded=(key == "lynch")):
                st.caption("量化检查：" + " / ".join(MASTERS[key]["checks"]))
                st.markdown(outputs[key])

        extra_views = {}
        if news_list:
            with st.spinner("提取新闻情绪证据…"):
                senti = analyze_sentiment(stock, news_list, user_ctx)
            extra_views["新闻情绪证据"] = senti

        with st.spinner("后台圆桌正在交叉质询，整理最终建议…"):
            debate_text = run_debate(outputs, stock)

        st.subheader("裁判结论：适不适合现在的你")
        with st.spinner("裁判正在把框架分歧映射到你的持仓账本…"):
            synthesis = synthesize(outputs, stock, user_ctx, drift_note, extra_views=extra_views, debate_text=debate_text)
        st.markdown(synthesis)

        memory.record_decision(code, stock.name, dict(user_ctx, question=question), synthesis)
        st.success("本次分析已存入决策档案。")
        st.info(DISCLAIMER)
    else:
        st.caption("填写持仓账本，选择股票后开始分析。")
        st.info(DISCLAIMER)
else:
    st.subheader("你的决策档案")
    st.caption("记录每次分析的处境与结论；复盘价值在于看清自己的行为模式。")
    records = memory.get_all_records()
    if not records:
        st.info("还没有决策记录。去「决策分析」页做第一次分析吧。")
    else:
        for i, r in enumerate(records):
            with st.expander(f"{r['time']} ｜ {r['name']}（{r['code']}）｜ {r['position']}"):
                st.markdown(f"**当时情境**：仓位 {r.get('weight', '—')} ｜ {r['risk']} ｜ {r['horizon']}")
                if r["question"]:
                    st.markdown(f"**当时的描述**：{r['question']}")
                st.markdown(f"**裁判结论摘要**：\n\n{r['synthesis']}")
                st.divider()
                opts = ["还没到复盘时间", "执行了", "没执行", "部分执行"]
                followed = st.selectbox("最后你按建议做了吗？", opts, key=f"f{i}",
                                        index=opts.index(r["followed"]) if r["followed"] in opts else 0)
                reflection = st.text_area("现在回头看，当时最大的判断错误或情绪偏差是什么？",
                                          value=r["reflection"], key=f"r{i}")
                if st.button("保存复盘", key=f"b{i}"):
                    memory.update_reflection(i, followed, reflection)
                    st.success("已保存。")
