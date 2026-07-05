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
                "▌可验证检查点\n如果毛利率和份额同步下滑，巴菲特视角降权。\n"
                "如果收入增速与产品数据转弱，林奇视角降权。\n"
                "如果价格重新站回关键位，利弗莫尔的谨慎可降权。\n\n"
                "▌行为偏差诊断\n损失厌恶：不要用长期投资包装被套后的不甘心。\n\n"
                "▌行动前快速三问\n1. 环境：现在的市场，值得冒这个险吗？——谨慎。\n"
                "2. 标的：这家公司凭什么是不可替代的？——还需要验证。\n"
                "3. 执行：止损位在哪、亏多少必须走？——先设现价下方8%的硬纪律。")
    if "股票到底是什么" in system_prompt:
        return ("▌小白先懂\n股票不是一串价格，而是你买了一小部分公司。\n\n"
                "▌大师视角\n彼得·林奇会先问：这家公司卖什么、怎么赚钱、增长故事能不能两分钟讲清。\n\n"
                "▌量化检查\n先看收入增速、产品/用户数据；如果有利润数据，再看PEG是否合理。\n\n"
                "▌本轮结论\n谨慎通过：业务方向清楚，但增长还需要产品和收入数据验证。\n\n"
                "▌可验证条件\n如果收入增速和产品数据同步转弱，林奇视角降权。")
    if "这家公司好不好" in system_prompt:
        return ("▌小白先懂\n好公司不是名字响，而是长期赚钱能力强、竞争者不容易抢走。\n\n"
                "▌大师视角\n巴菲特会看护城河、利润质量、ROE和管理层是否靠谱。\n\n"
                "▌量化检查\n重点看毛利率/净利率、ROE、市场份额是否稳定。\n\n"
                "▌本轮结论\n谨慎：行业有吸引力，但护城河需要利润率和份额验证。\n\n"
                "▌可验证条件\n如果毛利率和市场份额同步下滑，巴菲特视角降权。")
    if "现在价格贵不贵" in system_prompt:
        return ("▌小白先懂\n好公司买贵了也会受伤，价格决定你有没有犯错空间。\n\n"
                "▌大师视角\n格雷厄姆会先问：内在价值在哪里，安全边际够不够。\n\n"
                "▌量化检查\n重点看PE、PB、盈利是否被下修，以及估值比历史位置贵不贵。\n\n"
                "▌本轮结论\n不通过：当前估值不便宜，犯错空间偏小。\n\n"
                "▌可验证条件\n如果估值回落但盈利没有同步恶化，格雷厄姆视角升权。")
    if "现在是不是好时机" in system_prompt:
        return ("▌小白先懂\n公司好不等于现在就该买，买点和止损决定账户会不会受伤。\n\n"
                "▌大师视角\n利弗莫尔会看趋势、关键价位、成交量和止损纪律。\n\n"
                "▌量化检查\n重点看是否站回关键位、成交量是否确认、止损价是否已经写清楚。\n\n"
                "▌本轮结论\n先等：没有看到明确价格确认前，不急着补仓。\n\n"
                "▌可验证条件\n如果价格放量站回关键位并连续确认，利弗莫尔的谨慎降权。")
    return "暂时没有生成有效分析，请检查模型配置后重试。"
