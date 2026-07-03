"""
主界面（Streamlit）
运行：streamlit run app.py
"""

import streamlit as st
from data_provider import provider
from masters import MASTERS, DISCLAIMER
from analyzer import analyze_with_master, synthesize
import memory

st.set_page_config(page_title="大师圆桌 · 投资决策智能", page_icon="🎓", layout="wide")

st.title("🎓 大师圆桌 · Decision Intelligence")
st.caption("同一只股票，不同的人，应该得到不同的建议 —— 我们分析的不是股票，是你的决策")

page = st.sidebar.radio("导航", ["🔍 决策分析", "📔 决策档案与复盘"])

# ============ 页面一：决策分析 ============
if page == "🔍 决策分析":
    with st.sidebar:
        st.header("① 你的情境")
        position = st.radio("持仓状态", ["未持有，考虑买入", "已持有，考虑加仓", "已持有，考虑卖出", "已持有，被套纠结中"])
        cost = st.text_input("持仓成本（未持有可留空）")
        weight = st.select_slider("该股占你总资金比例", ["<10%", "10-30%", "30-50%", ">50%", "全仓"])
        risk = st.radio("风险偏好", ["保守：亏10%就睡不着", "稳健：能接受20%回撤", "激进：波动是朋友"])
        horizon = st.radio("投资期限", ["短线（几天~几周）", "波段（几个月）", "长期（1年以上）"])
        question = st.text_area("你现在最纠结什么？（选填）", placeholder="例如：套了15%，不知道该割还是补…")

    col1, col2 = st.columns([1, 2])
    with col1:
        st.subheader("② 选择股票")
        supported = provider.list_supported()
        code = st.selectbox("股票代码", options=list(supported.keys()),
                            format_func=lambda c: f"{c} {supported[c]}")
    with col2:
        st.subheader("③ 选择决策框架")
        st.caption("大师人物是框架的载体：真正运行的是四套决策框架")
        selected = []
        cols = st.columns(len(MASTERS))
        for i, (key, m) in enumerate(MASTERS.items()):
            with cols[i]:
                if st.checkbox(f"{m['emoji']} {m['name']}", value=(i < 2), key=key):
                    selected.append(key)
                st.caption(m.get("framework_name", m["title"]))

    st.divider()

    if st.button("🚀 开始圆桌分析", type="primary", use_container_width=True):
        if not selected:
            st.warning("至少选择一套框架")
            st.stop()

        stock = provider.get_stock(code)
        if stock is None:
            st.error("未找到该股票")
            st.stop()

        user_ctx = dict(position=position, cost=cost, weight=weight,
                        risk=risk, horizon=horizon, question=question)

        # ---- 决策记忆：目标漂移检测 ----
        drift_note = memory.detect_drift(code, user_ctx)
        if drift_note:
            st.warning(drift_note)

        # 行情卡片
        st.subheader(f"📊 {stock.name}（{stock.code}）")
        a, b, c, d = st.columns(4)
        a.metric("现价", f"{stock.price}", f"{stock.change_pct:+.2f}%")
        b.metric("PE / PB", f"{stock.pe} / {stock.pb}")
        c.metric("市值", f"{stock.market_cap} 亿")
        d.metric("52周区间", f"{stock.low_52w}~{stock.high_52w}")
        st.line_chart(stock.history, height=180)

        # 各框架分析
        st.subheader("🗣️ 框架视角")
        outputs = {}
        tabs = st.tabs([f"{MASTERS[k]['emoji']} {MASTERS[k]['name']}" for k in selected])
        for tab, key in zip(tabs, selected):
            with tab:
                with st.spinner(f"{MASTERS[key]['name']} 思考中…"):
                    outputs[key] = analyze_with_master(key, stock, user_ctx, drift_note)
                st.markdown(outputs[key])

        # 裁判合议
        st.subheader("⚖️ 决策裁判 · 框架适配与认知风险")
        with st.spinner("汇总分歧、适配框架、诊断行为偏差…"):
            synthesis = synthesize(outputs, stock, user_ctx, drift_note)
        st.markdown(synthesis)

        # ---- 决策记忆：归档本次决策 ----
        memory.record_decision(code, stock.name, user_ctx, synthesis)
        st.success("📔 本次分析已存入你的决策档案（30天后记得回来复盘）")
        st.info(DISCLAIMER)
    else:
        st.markdown(
            """
            **使用流程**：左侧填写你的真实处境 → 选股票 → 选框架 → 开始分析

            **产品理念**：市面上的工具都在回答"这只股票好不好"，
            但真正的问题是 **"这个决策适不适合此刻的你"** ——
            我们做的不是股票分析，是 Decision Intelligence。
            """
        )
        st.info(DISCLAIMER)

# ============ 页面二：决策档案与复盘 ============
else:
    st.subheader("📔 你的决策档案（Decision Journal）")
    st.caption("记录每一次决策处境与分析结论；复盘的价值在于看清自己的行为模式")
    records = memory.get_all_records()
    if not records:
        st.info("还没有决策记录。去「决策分析」页做第一次分析吧。")
    else:
        for i, r in enumerate(records):
            with st.expander(f"{r['time']} ｜ {r['name']}（{r['code']}）｜ {r['position']}"):
                st.markdown(f"**当时情境**：仓位 {r['weight']} ｜ {r['risk']} ｜ {r['horizon']}")
                if r["question"]:
                    st.markdown(f"**当时的纠结**：{r['question']}")
                st.markdown(f"**裁判结论摘要**：\n\n{r['synthesis']}")
                st.divider()
                st.markdown("**🔄 复盘（30天后回来填）**")
                followed = st.radio("最后你按建议做了吗？", ["还没到复盘时间", "执行了", "没执行", "部分执行"],
                                    key=f"f{i}", horizontal=True,
                                    index=["还没到复盘时间", "执行了", "没执行", "部分执行"].index(r["followed"]) if r["followed"] else 0)
                reflection = st.text_area("现在回头看，你当时最大的判断错误或情绪偏差是什么？",
                                          value=r["reflection"], key=f"r{i}")
                if st.button("保存复盘", key=f"b{i}"):
                    memory.update_reflection(i, followed, reflection)
                    st.success("已保存。长期坚持复盘，你会看到自己的行为模式。")
