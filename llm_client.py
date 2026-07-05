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
                "**本杰明·格雷厄姆 → 沃伦·巴菲特**（攻击B依赖的前提\"护城河足够抵消高估值\"）：好公司买贵了，也会拖累长期收益。\n"
                "**沃伦·巴菲特回应**（隐藏前提）：我的判断依赖利润率、ROE和份额没有被竞争者破坏。\n"
                "**沃伦·巴菲特回应**（可验证条件）：如果连续两季毛利率下滑且份额被新对手抢走，我会改变判断。\n\n"
                "**⚔️ 第二回合**\n"
                "**杰西·利弗莫尔 → 彼得·林奇**（攻击B依赖的前提\"成长故事能抵抗趋势\"）：故事再好，价格不确认就先等。\n"
                "**彼得·林奇回应**（隐藏前提）：我的判断依赖用户需求真实增长，而不是短期题材。\n"
                "**彼得·林奇回应**（可验证条件）：如果收入增速放缓且产品数据同步走弱，我会改变判断。\n\n"
                "**⚔️ 第三回合**\n"
                "**彼得·林奇 → 本杰明·格雷厄姆**（攻击B依赖的前提\"估值便宜才值得行动\"）：错过高质量成长，有时也是成本。\n"
                "**本杰明·格雷厄姆回应**（隐藏前提）：我的判断依赖当前价格没有给足安全边际。\n"
                "**本杰明·格雷厄姆回应**（可验证条件）：如果盈利继续上修且估值回落到合理区间，我会改变判断。\n\n"
                "**僵局点**：林奇愿意为真实成长多给时间，格雷厄姆和利弗莫尔要求价格先给证据。\n"
                "**用户可查信号**：毛利率/市场份额；收入增速/产品数据；关键价位是否重新站回。")
    if "情绪分析师" in system_prompt:
        return ("**情绪温度计**：+4（偏乐观）。\n\n**最相关事件**：财报公布是你期限内最关键的变量。\n\n"
                "**噪音过滤**：投行目标价调整属于日常噪音。")
    if "决策智能裁判" in system_prompt:
        return ("**🎯 最终建议：先别急着加动作，先确认最关键的财务和趋势信号。**\n\n"
                "▌事实层面\n收入增速、ROE和利润率里还有关键项没验证完，现在不能把长期优势当成已确认事实。\n\n"
                "▌时间层面\n长期看法和短期操作还有冲突：公司值得继续看，但短线价格和量能还没完全确认。\n\n"
                "▌偏好层面\n如果这笔钱一年内可能要用，或者你对回撤敏感，现在更适合观察而不是追着操作。\n\n"
                "▌可能的行为偏差\n损失厌恶：别因为不甘心亏损，就急着替自己找继续扛或补的理由。\n\n"
                "▌行动前快速三问\n1. 环境：现在的市场，值得冒这个险吗？——暂时一般。\n"
                "2. 标的：这家公司凭什么值得继续看？——业务强，但增长和护城河还要继续核实。\n"
                "3. 执行：如果判断错了，下一步怎么做？——跌破止损位先减仓，别拖。")
    if "股票到底是什么" in system_prompt:
        return ("▌大师视角\n彼得·林奇会先问：这家公司卖什么、怎么赚钱、增长故事能不能两分钟讲清。\n\n"
                "▌量化检查\n先看收入增速、产品/用户数据；如果有利润数据，再看PEG是否合理。\n\n"
                "▌本轮结论\n谨慎通过：业务方向清楚，但增长还需要产品和收入数据验证。")
    if "这家公司好不好" in system_prompt:
        return ("▌大师视角\n巴菲特会看护城河、利润质量、ROE和管理层是否靠谱。\n\n"
                "▌量化检查\n重点看毛利率/净利率、ROE、市场份额是否稳定。\n\n"
                "▌本轮结论\n谨慎：行业有吸引力，但护城河需要利润率和份额验证。")
    if "现在价格贵不贵" in system_prompt:
        return ("▌大师视角\n格雷厄姆会先问：内在价值在哪里，安全边际够不够。\n\n"
                "▌量化检查\n重点看PE、PB、盈利是否被下修，以及估值比历史位置贵不贵。\n\n"
                "▌本轮结论\n不通过：当前估值不便宜，犯错空间偏小。")
    if "现在是不是好时机" in system_prompt:
        return ("▌大师视角\n利弗莫尔会看趋势、关键价位、成交量和止损纪律。\n\n"
                "▌量化检查\n重点看是否站回关键位、成交量是否确认、止损价是否已经写清楚。\n\n"
                "▌本轮结论\n先等：没有看到明确价格确认前，不急着补仓。")
    return "暂时没有生成有效分析，请检查模型配置后重试。"
