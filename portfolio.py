"""
持仓账本计算层
==============
不用 LLM，直接根据用户输入计算浮盈亏、持仓股数、止损价和资金压力。
这是产品从“聊天”变成“决策工具”的关键一层。
"""


def _to_float(value, default=0.0):
    try:
        if value is None:
            return default
        text = str(value).replace(",", "").strip()
        if not text:
            return default
        return float(text)
    except Exception:
        return default


def calculate_portfolio(stock, holding_amount, cost_price, available_cash,
                        max_loss_amount, add_amount=0):
    current_price = _to_float(stock.price)
    holding_amount = _to_float(holding_amount)
    cost_price = _to_float(cost_price)
    available_cash = _to_float(available_cash)
    max_loss_amount = _to_float(max_loss_amount)
    add_amount = _to_float(add_amount)

    has_position = holding_amount > 0 and cost_price > 0 and current_price > 0
    shares = holding_amount / cost_price if has_position else 0
    market_value = shares * current_price
    pnl = market_value - holding_amount if has_position else 0
    pnl_pct = pnl / holding_amount * 100 if holding_amount else 0

    add_shares = add_amount / current_price if current_price and add_amount else 0
    total_cost = holding_amount + add_amount
    total_shares = shares + add_shares
    avg_cost_after_add = total_cost / total_shares if total_shares else 0

    stop_loss_pct = 8 if pnl_pct > -15 else 5
    stop_loss_price = current_price * (1 - stop_loss_pct / 100) if current_price else 0
    loss_at_stop = max(0, (current_price - stop_loss_price) * shares)

    total_visible_money = holding_amount + available_cash
    position_ratio = holding_amount / total_visible_money * 100 if total_visible_money else 0
    loss_capacity_used = abs(min(pnl, 0)) / max_loss_amount * 100 if max_loss_amount else 0

    if position_ratio >= 60 or loss_capacity_used >= 100:
        pressure_level = "高"
        pressure_note = "仓位或亏损已经明显影响决策，优先控制风险。"
    elif position_ratio >= 30 or loss_capacity_used >= 60:
        pressure_level = "中"
        pressure_note = "有压力但还可管理，补仓前必须先设止损。"
    else:
        pressure_level = "低"
        pressure_note = "资金压力相对可控，重点验证股票本身。"

    return {
        "holding_amount": holding_amount,
        "cost_price": cost_price,
        "available_cash": available_cash,
        "max_loss_amount": max_loss_amount,
        "add_amount": add_amount,
        "shares": shares,
        "market_value": market_value,
        "pnl": pnl,
        "pnl_pct": pnl_pct,
        "avg_cost_after_add": avg_cost_after_add,
        "stop_loss_price": stop_loss_price,
        "stop_loss_pct": stop_loss_pct,
        "loss_at_stop": loss_at_stop,
        "position_ratio": position_ratio,
        "loss_capacity_used": loss_capacity_used,
        "pressure_level": pressure_level,
        "pressure_note": pressure_note,
        "has_position": has_position,
    }


def pressure_to_score(level):
    return {"低": 25, "中": 60, "高": 90}.get(level, 50)
