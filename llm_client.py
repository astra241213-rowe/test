"""
LLM 调用层（OpenAI 兼容，火山方舟可直连）
密钥读取顺序：环境变量 LLM_API_KEY → 本地文件 ark_key.txt（重启不丢）
没有密钥时自动进入 DEMO 模式（离线兜底，保证评审可演示）
"""

import os

API_BASE = os.getenv("LLM_API_BASE", "https://ark.cn-beijing.volces.com/api/v3")
MODEL = os.getenv("LLM_MODEL", "doubao-seed-2-1-turbo-260628")


def _load_key() -> str:
    key = os.getenv("LLM_API_KEY", "")
    if key:
        return key
    try:  # Streamlit Cloud 部署时从 Secrets 读取
        import streamlit as st
        if "LLM_API_KEY" in st.secrets:
            return st.secrets["LLM_API_KEY"]
    except Exception:
        pass
    try:
        with open("ark_key.txt") as f:
            return f.read().strip()
    except Exception:
        return ""


API_KEY = _load_key()


def chat(system_prompt: str, user_prompt: str, temperature: float = 0.7) -> str:
    if not API_KEY:
        return _demo_response(system_prompt)
    try:
        from openai import OpenAI
        client = OpenAI(base_url=API_BASE, api_key=API_KEY)
        resp = client.chat.completions.create(
            model=MODEL,
            temperature=temperature,
            max_tokens=700,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        return resp.choices[0].message.content
    except Exception as e:
        return f"（API 调用失败，已降级为离线模式：{e}）\n\n" + _demo_response(system_prompt)


def _demo_response(system_prompt: str) -> str:
    if "辩论主持人" in system_prompt:
        return ("**格雷厄姆**：巴菲特先生，你的判断依赖护城河还在变宽——这个前提有数据支撑吗？\n\n"
                "**巴菲特**：量化上我让你一步，估值确实不便宜。但市场只给平庸公司便宜价——你的框架永远买不到伟大的公司。\n\n"
                "**利弗莫尔**：你们说的都对。但讨论这些的时候，股价已经跌破关键位了。这位用户拿的还是重仓。\n\n"
                "*(DEMO 模式示例输出)*")
    if "情绪分析师" in system_prompt:
        return ("**情绪温度计**：+4（偏乐观）。\n\n**最相关事件**：财报公布是你期限内最关键的变量。\n\n"
                "**噪音过滤**：投行目标价调整属于日常噪音。\n\n*(DEMO 模式示例输出)*")
    if "巴菲特" in system_prompt:
        return ("▌生意本质\n这是一门能一句话说清的生意。\n▌巴菲特的判断\n等更便宜——如果十年不能看它一眼，你还敢持有吗？\n*(DEMO 模式示例输出)*")
    if "格雷厄姆" in system_prompt:
        return ("▌投资还是投机？\n你的动机里有不甘心，这是投机信号。\n▌格雷厄姆的判断\n等更大折让。\n*(DEMO 模式示例输出)*")
    if "林奇" in system_prompt:
        return ("▌两分钟故事测试\n讲不清它为什么会赚更多钱，先别买。\n▌林奇的判断\n继续观察。\n*(DEMO 模式示例输出)*")
    if "利弗莫尔" in system_prompt:
        return ("等。\n▌止损纪律\n建议止损位：现价下方8%。\n▌利弗莫尔的判断\n等待。\n*(DEMO 模式示例输出)*")
    return ("【裁判 · 情境化决策】\n▌永久分歧区\n价值派看三五年，交易派看三五周——不调和。\n"
            "▌行为偏差诊断\n损失厌恶：你在用长期投资安慰被套的自己。\n▌最大盲区提示\n最大风险不是股票，是你的仓位结构。\n*(DEMO 模式示例输出)*")
