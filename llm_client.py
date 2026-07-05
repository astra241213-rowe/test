"""
LLM 调用层（OpenAI 兼容，火山方舟可直连）
密钥读取顺序：Streamlit Secrets → 环境变量 LLM_API_KEY → 本地文件 ark_key.txt
没有密钥时自动进入 DEMO 模式（离线兜底，保证评审可演示）
"""

import os

DEFAULT_API_BASE = "https://ark.cn-beijing.volces.com/api/v3"
DEFAULT_MODEL = "doubao-seed-2-1-turbo-260628"


def _secret(name: str, default: str = "") -> str:
    try:
        import streamlit as st
        if name in st.secrets:
            return str(st.secrets[name])
    except Exception:
        pass
    return default


API_BASE = _secret("LLM_API_BASE", os.getenv("LLM_API_BASE", DEFAULT_API_BASE))
MODEL = _secret("LLM_MODEL", os.getenv("LLM_MODEL", DEFAULT_MODEL))


def _load_key() -> str:
    key = _secret("LLM_API_KEY", "")
    if key:
        return key
    key = os.getenv("LLM_API_KEY", "")
    if key:
        return key
    try:
        with open("ark_key.txt") as f:
            return f.read().strip()
    except Exception:
        return ""


API_KEY = _load_key()


def status() -> dict:
    return {
        "connected": bool(API_KEY),
        "model": MODEL,
        "api_base": API_BASE,
        "label": "已连接" if API_KEY else "DEMO 模式",
    }


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
    except Exception:
        return "（模型暂未连接，当前使用演示输出。）\n\n" + _demo_response(system_prompt)


def _demo_response(system_prompt: str) -> str:
    if "辩论主持人" in system_prompt:
        return ("**⚔️ 第一回合**\n"
                "**估值框架 → 商业质量框架**（攻击B依赖的前提\"护城河仍稳固\"）：好公司买贵了也会伤人。\n"
                "**商业质量框架回应**（隐藏前提）：我的判断依赖利润率和份额没有被新进入者破坏。\n"
                "**商业质量框架回应**（可验证条件）：如果连续两季毛利率下滑且份额被新对手抢走，我会改变判断。\n\n"
                "**⚔️ 第二回合**\n"
                "**趋势框架 → 业务理解框架**（攻击B依赖的前提\"成长故事能抵抗趋势\"）：故事再好，价格不确认就先等。\n"
                "**业务理解框架回应**（隐藏前提）：我的判断依赖用户需求真实增长，而不是短期题材。\n"
                "**业务理解框架回应**（可验证条件）：如果收入增速放缓且产品数据同步走弱，我会改变判断。\n\n"
                "**僵局点**：业务框架愿意等长期验证，趋势框架要求价格先证明。\n"
                "**用户可查信号**：毛利率/市场份额；关键价位是否重新站回。\n\n"
                "*(DEMO 模式示例输出)*")
    if "情绪分析师" in system_prompt:
        return ("**情绪温度计**：+4（偏乐观）。\n\n**最相关事件**：财报公布是你期限内最关键的变量。\n\n"
                "**噪音过滤**：投行目标价调整属于日常噪音。\n\n*(DEMO 模式示例输出)*")
    if "决策智能裁判" in system_prompt:
        return ("**🎯 最终建议：先不加仓，把事实检查点查清，再决定是否行动。**\n\n"
                "▌分歧诊断\n事实分歧：护城河和成长是否真的被削弱，需要看份额、利润率和收入增速。\n"
                "时间分歧：业务质量看长期，买点纪律看短期确认。\n"
                "偏好分歧：仓位压力高时，先听执行纪律，不要急着补仓。\n\n"
                "▌三维归类输出\n环境（裁判独立判断）：⚠️谨慎，情绪不差但波动仍高。\n"
                "标的（林奇+巴菲特整合）：⚠️，生意可能不错但成长要验证。\n"
                "执行（格雷厄姆+利弗莫尔整合）：❌，安全边际和止损纪律不足。\n\n"
                "▌分歧雷达\n业务分歧：增长是真需求还是短期故事。\n"
                "估值分歧：好公司是否已经太贵。\n"
                "时机分歧：价格有没有证明现在能行动。\n\n"
                "▌可验证检查点\n如果毛利率和份额同步下滑，商业质量框架降权。\n"
                "如果收入增速与产品数据转弱，成长框架降权。\n"
                "如果价格重新站回关键位，趋势框架的谨慎可降权。\n\n"
                "▌行为偏差诊断\n损失厌恶：不要用长期投资包装被套后的不甘心。\n\n"
                "▌行动前快速三问\n1. 环境：现在的市场，值得冒这个险吗？——谨慎。\n"
                "2. 标的：这家公司凭什么是不可替代的？——还需要验证。\n"
                "3. 执行：止损位在哪、亏多少必须走？——先设现价下方8%的硬纪律。\n\n"
                "*(DEMO 模式示例输出)*")
    if "股票到底是什么" in system_prompt:
        return ("▌这个问题在问什么\n先搞懂它卖什么、靠什么赚钱、增长是不是能用人话讲清。\n\n"
                "▌本框架结论\n谨慎通过：业务方向清楚，但增长还需要产品和收入数据验证。\n\n"
                "▌依据\n当前只看到价格、估值和行业信息，还缺收入增速与用户数据。\n\n"
                "▌可验证条件\n如果收入增速和产品数据同步转弱，成长框架降权。\n\n*(DEMO 模式示例输出)*")
    if "这家公司好不好" in system_prompt:
        return ("▌这个问题在问什么\n看这是不是一门长期能赚钱、别人不容易抢走的好生意。\n\n"
                "▌本框架结论\n谨慎：行业有吸引力，但护城河需要利润率和份额验证。\n\n"
                "▌依据\nPE/PB不低，市场已经给了较高期待。\n\n"
                "▌可验证条件\n如果毛利率和市场份额同步下滑，商业质量框架降权。\n\n*(DEMO 模式示例输出)*")
    if "现在价格贵不贵" in system_prompt:
        return ("▌这个问题在问什么\n好公司也不能乱买，关键是价格有没有安全边际。\n\n"
                "▌本框架结论\n不通过：当前估值不便宜，犯错空间偏小。\n\n"
                "▌依据\nPE/PB处在偏高位置时，补仓需要更强证据。\n\n"
                "▌可验证条件\n如果估值回落但盈利没有同步恶化，估值框架升权。\n\n*(DEMO 模式示例输出)*")
    if "现在是不是好时机" in system_prompt:
        return ("▌这个问题在问什么\n公司好不等于现在就买，价格和止损纪律要先确认。\n\n"
                "▌本框架结论\n先等：没有看到明确价格确认前，不急着补仓。\n\n"
                "▌依据\n如果已经被套，先设止损线，再谈加仓。\n\n"
                "▌可验证条件\n如果价格放量站回关键位并连续确认，趋势框架降权谨慎。\n\n*(DEMO 模式示例输出)*")
    return "*(DEMO 模式示例输出)*"
