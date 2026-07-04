"""
大师圆桌 · Decision Intelligence（v3）
运行：streamlit run app.py
"""

import streamlit as st
from data_provider import provider
from masters import MASTERS, DISCLAIMER
from analyzer import analyze_with_master, synthesize, run_debate, analyze_sentiment
from risk_radar import compute_risk_radar
import memory

st.set_page_config(page_title="大师圆桌 · 投资决策智能", page_icon="🎓", layout="wide")
st.title("🎓 大师圆桌 · Decision Intelligence")
st.caption("同一只股票，不同的人，应该得到不同的建议 —— 我们分析的不是股票，是你的决策")

page = st.sidebar.radio("导航", ["🔍 决策分析", "📔 决策档案与复盘"])

# ================= 页面一：决策分析 =================
if page == "🔍 决策分析":
    with st.sidebar:
        st.header("① 你的情境（越真实，分析越准）")
        position = st.radio("持仓状态", ["未持有，考虑买入", "已持有，考虑加仓",
                                        "已持有，考虑卖出", "已持有，被套纠结中"])
        cost = st.text_input("持仓成本（未持有可留空）")
        weight = st.select_slider("该股占你总资金比例",
                                  ["<10%", "10-30%", "30-50%", ">50%", "全仓"])
        money_nature = st.radio("这笔钱的性质",
                                ["纯闲钱，三年不用", "一年内可能要用", "含生活费或借贷资金"])
        experience = st.radio("投资经验", ["新手（<1年）", "1-3年", "3年以上"])
        max_dd = st.select_slider("最大能承受的亏损",
                                  ["-5%", "-10%", "-20%", "-30%", "腰斩也拿得住"])
        risk = st.radio("风险偏好", ["保守：亏10%就睡不着", "稳健：能接受20%回撤", "激进：波动是朋友"])
        horizon = st.radio("投资期限", ["短线（几天~几周）", "波段（几个月）", "长期（1年以上）"])
        question = st.text_area("用你自己的话，详细描述现在的处境和纠结（强烈建议填写）",
                                height=120,
                                placeholder="例如：去年380买的，现在套了20%。这是我准备付首付的钱，"
                                            "老婆不知道我买了这么多。最近看新闻说行业有利好，"
                                            "想补仓摊成本，但又怕越补越套…")

    col1, col2 = st.columns([1, 2])
    with col1:
        st.subheader("② 选择股票（港美股）")
        supported = provider.list_supported()
        mode = st.radio("选择方式", ["常用列表", "自定义代码"], horizontal=True)
        if mode == "常用列表":
            code = st.selectbox("股票", options=list(supported.keys()),
                                format_func=lambda c: f"{c} {supported[c]}")
        else:
            code = st.text_input("输入代码：美股如 AAPL，港股如 0700.HK", value="AAPL")
    with col2:
        st.subheader("③ 组建你的分析团队")
        st.caption("大师人物是框架的载体——真正运行的是四套决策框架 + 情绪证据 Agent")
        selected = []
        cols = st.columns(len(MASTERS))
        for i, (key, m) in enumerate(MASTERS.items()):
            with cols[i]:
                if st.checkbox(f"{m['emoji']} {m['name']}", value=(i < 2), key=key):
                    selected.append(key)
                st.caption(m.get("framework_name", m["title"]))
        c1, c2 = st.columns(2)
        with c1:
            use_news = st.checkbox("📰 引入新闻情绪 Agent（Evidence Layer）", value=True)
        with c2:
            use_debate = st.checkbox("⚔️ 开启大师交叉质询（辩论模式）", value=True)

    st.divider()

    if st.button("🚀 开始圆桌分析", type="primary", use_container_width=True):
        if not selected:
            st.warning("至少选择一套框架")
            st.stop()
        with st.spinner("拉取行情数据…"):
            stock = provider.get_stock(code)
        if stock is None:
            st.error("未找到该股票。美股直接输字母代码（AAPL），港股输数字+.HK（0700.HK）")
            st.stop()

        user_ctx = dict(position=position, cost=cost, weight=weight, risk=risk,
                        horizon=horizon,
                        question=f"资金性质：{money_nature}；投资经验：{experience}；"
                                 f"最大承受亏损：{max_dd}。{question}")

        # 决策记忆：目标漂移检测
        drift_note = memory.detect_drift(code, dict(user_ctx, question=question))
        if drift_note:
            st.warning(drift_note)

        # 行情卡片（Evidence Layer：行情证据）
        src_tag = "🟢 实时数据" if stock.source == "yfinance" else "🟡 离线演示数据"
        st.subheader(f"📊 {stock.name}（{stock.code}）")
        st.caption(f"{src_tag} ｜ 币种：{stock.currency} ｜ 行业：{stock.industry}")
        a, b, c, d = st.columns(4)
        a.metric("现价", f"{stock.price} {stock.currency}", f"{stock.change_pct:+.2f}%")
        b.metric("PE / PB", f"{stock.pe or '—'} / {stock.pb or '—'}")
        c.metric("市值", f"{stock.market_cap:,.0f} 亿" if stock.market_cap else "—")
        d.metric("52周区间", f"{stock.low_52w}~{stock.high_52w}")
        st.line_chart(stock.history, height=180)

        # 新闻证据
        news_list = []
        if use_news:
            news_list = provider.get_news(code)
            with st.expander(f"📰 近期新闻证据（{len(news_list)} 条）", expanded=False):
                for n in news_list:
                    st.markdown(f"- {n['title']} ｜ *{n['source']}*")

        # 风险雷达（量化即时计算）
        st.subheader("🎯 风险雷达 Risk Radar")
        radar = compute_risk_radar(stock, user_ctx)
        rcols = st.columns(len(radar))
        for rc, (dim, score, comment) in zip(rcols, radar):
            with rc:
                st.markdown(f"**{dim}** {score}/100")
                st.progress(score / 100)
                st.caption(comment)

        # 各框架独立分析
        st.subheader("🗣️ 框架视角（独立分析）")
        outputs = {}
        tabs = st.tabs([f"{MASTERS[k]['emoji']} {MASTERS[k]['name']}" for k in selected])
        for tab, key in zip(tabs, selected):
            with tab:
                with st.spinner(f"{MASTERS[key]['name']} 思考中…"):
                    outputs[key] = analyze_with_master(key, stock, user_ctx, drift_note)
                st.markdown(outputs[key])

        # 情绪 Agent
        extra_views = {}
        if use_news and news_list:
            st.subheader("📰 情绪分析师 Sentiment Agent")
            with st.spinner("解读新闻情绪…"):
                senti = analyze_sentiment(stock, news_list, user_ctx)
            st.markdown(senti)
            extra_views["新闻情绪分析师（Sentiment Agent）"] = senti

        # 交叉质询
        debate_text = None
        if use_debate and len(selected) >= 2:
            st.subheader("⚔️ 交叉质询 · 精准打击彼此最脆弱的前提")
            with st.spinner("大师们开始互相拆台…"):
                debate_text = run_debate(outputs, stock)
            st.markdown(debate_text)

        # 决策裁判
        st.subheader("⚖️ 决策裁判 · 框架适配 + 行为偏差诊断")
        with st.spinner("汇总共识与永久分歧、适配框架、诊断行为偏差…"):
            synthesis = synthesize(outputs, stock, user_ctx, drift_note,
                                   extra_views=extra_views, debate_text=debate_text)
        st.markdown(synthesis)

        memory.record_decision(code, stock.name, dict(user_ctx, question=question), synthesis)
        st.success("📔 本次分析已存入你的决策档案（记得定期回来复盘）")
        st.info(DISCLAIMER)
    else:
        st.markdown(
            """
            **使用流程**：左侧填写真实处境 → 选股票和分析团队 → 开始分析

            **系统架构**：行情+新闻证据层 → 四套决策框架 + 情绪Agent → 交叉质询 →
            决策裁判（框架适配 + 行为偏差诊断）→ 决策记忆与复盘
            """
        )
        st.info(DISCLAIMER)

# ================= 页面二：决策档案与复盘 =================
else:
    st.subheader("📔 你的决策档案（Decision Journal）")
    st.caption("记录每一次决策处境与结论；复盘的价值在于看清自己的行为模式")
    records = memory.get_all_records()
    if not records:
        st.info("还没有决策记录。去「决策分析」页做第一次分析吧。")
    else:
        for i, r in enumerate(records):
            with st.expander(f"{r['time']} ｜ {r['name']}（{r['code']}）｜ {r['position']}"):
                st.markdown(f"**当时情境**：仓位 {r['weight']} ｜ {r['risk']} ｜ {r['horizon']}")
                if r["question"]:
                    st.markdown(f"**当时的描述**：{r['question']}")
                st.markdown(f"**裁判结论摘要**：\n\n{r['synthesis']}")
                st.divider()
                st.markdown("**🔄 复盘（一段时间后回来填）**")
                opts = ["还没到复盘时间", "执行了", "没执行", "部分执行"]
                followed = st.radio("最后你按建议做了吗？", opts, key=f"f{i}", horizontal=True,
                                    index=opts.index(r["followed"]) if r["followed"] in opts else 0)
                reflection = st.text_area("现在回头看，你当时最大的判断错误或情绪偏差是什么？",
                                          value=r["reflection"], key=f"r{i}")
                if st.button("保存复盘", key=f"b{i}"):
                    memory.update_reflection(i, followed, reflection)
                    st.success("已保存。长期坚持复盘，你会看到自己的行为模式。")
