"""
LLM 调用层
==========
用 OpenAI 兼容协议（国内绝大多数算力 API 都兼容，明天官方给的大概率也是）。
- 有 API key：真实调用
- 没有 key：进入 DEMO 模式，返回预置文案，保证界面今晚就能跑通、
  评审当天 API 万一挂了也有兜底演示方案（评审规则明确要求可替代演示方案）。
"""

import os

# ====== 明天拿到官方算力 API 后，只改这三行 ======
API_BASE = os.getenv("LLM_API_BASE", "https://api.openai.com/v1")
API_KEY = os.getenv("LLM_API_KEY", "")          # 留空 = DEMO 模式
MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")
# ================================================


def chat(system_prompt: str, user_prompt: str, temperature: float = 0.7) -> str:
    """统一入口。失败或无 key 时自动降级到 DEMO 模式。"""
    if not API_KEY:
        return _demo_response(system_prompt)
    try:
        from openai import OpenAI
        client = OpenAI(base_url=API_BASE, api_key=API_KEY)
        resp = client.chat.completions.create(
            model=MODEL,
            temperature=temperature,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        return resp.choices[0].message.content
    except Exception as e:
        return f"（API 调用失败，已降级为离线模式：{e}）\n\n" + _demo_response(system_prompt)


def _demo_response(system_prompt: str) -> str:
    """离线兜底文案：按人格返回一段像样的示例分析，保证演示不空白。"""
    if "巴菲特" in system_prompt:
        return ("**生意本质**：这是一门能一句话说清的生意，这是好的开始。\n\n"
                "**护城河**：品牌与渠道构成的护城河仍在，但需要观察它是在变宽还是被新对手侵蚀。\n\n"
                "**价格与价值**：以当前估值看，安全边际并不算厚。记住：以合理价格买伟大的公司，"
                "胜过以便宜价格买平庸的公司。\n\n**十年测试**：如果你不打算持有十年，就不要持有十分钟。\n\n"
                "*(DEMO 模式示例输出，接入 API 后为实时生成)*")
    if "格雷厄姆" in system_prompt:
        return ("**定量筛查**：以当前 PE 与 PB 计算，PE×PB 超出防御型投资者的经典阈值。\n\n"
                "**安全边际**：折让不足，本金保护有限。\n\n**市场先生**：他现在情绪偏乐观，"
                "你不必陪他狂热。\n\n**结论**：这更接近投机而非投资，请诚实面对这一点。\n\n"
                "*(DEMO 模式示例输出)*")
    if "林奇" in system_prompt:
        return ("**分类**：更接近稳定增长股而非快速增长股，预期收益要相应调整。\n\n"
                "**PEG**：增速与估值的匹配度一般。\n\n**两分钟故事**：如果你没法向家人讲清楚"
                "为什么买它，先别买。\n\n*(DEMO 模式示例输出)*")
    if "利弗莫尔" in system_prompt:
        return ("**趋势**：近 30 日价格结构显示最小阻力线方向不明，处于盘整区。\n\n"
                "**止损**：先回答'亏到哪必须走'，再谈要不要进。没有止损计划的交易是赌博。\n\n"
                "**情绪审视**：'不甘心'不是持仓理由。我用破产的教训告诉你：纪律高于判断。\n\n"
                "*(DEMO 模式示例输出)*")
    return ("**综合视角**：各位大师的分歧主要来自时间尺度——价值派看三到五年，交易派看三到五周。\n\n"
            "**情境适配**：以你的仓位占比和风险偏好，格雷厄姆的防御框架更适合当前处境。\n\n"
            "**可执行清单**：1) 先设定明确止损/止盈位；2) 单一持仓不超过总仓位的 20%；"
            "3) 写下买入理由，理由消失即卖出。\n\n**最大盲区**：你在用'长期投资'安慰短期被套的自己。\n\n"
            "*(DEMO 模式示例输出，接入 API 后为实时生成)*")
