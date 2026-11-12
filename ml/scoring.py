"""
Transparent Risk Scoring Engine for DealCheck
Combines calibrated Model A probability (0-1) with deterministic rule flags
and dynamic Model B seller litmus test adjustments.

Scoring Formula:
  Score = min(100, max(0, round(ModelA_Prob * 55 + Rule_Points + Seller_Adjustment)))
"""

import re
from typing import Dict, Any, List

RULE_DEFINITIONS = [
    {
        "id": "friends_and_family",
        "name": "PayPal Friends & Family Coercion",
        "points": 35,
        "pattern": r"(friends\s*(and|or|&|\/)\s*fam(ily)?|f&f|f\s*(and|or|&)\s*f|personal payment|sending to a friend|friends option)",
        "explanation": "Seller demands or suggests PayPal Friends & Family payment, explicitly waiving PayPal Purchase Protection."
    },
    {
        "id": "advance_deposit",
        "name": "Advance Deposit / Token Demand",
        "points": 20,
        "pattern": r"(deposit|token|advance|booking amount|pay half upfront|before viewing|to hold)",
        "explanation": "Demanding advance payment or deposit before in-person inspection or official shipment."
    },
    {
        "id": "off_platform_payment",
        "name": "Off-Platform Payment Redirection",
        "points": 15,
        "pattern": r"(zelle|cashapp|cash app|venmo|crypto|usdt|bitcoin|gift card|telegram|western union)",
        "explanation": "Redirecting payment to non-commercial, irreversible rails with zero buyer dispute mechanisms."
    },
    {
        "id": "urgency_pressure",
        "name": "Manufactured Urgency / Pressure",
        "points": 10,
        "pattern": r"(urgent|today only|someone else is waiting|multiple buyers|within 30 mins|hurry|first come|moving tomorrow)",
        "explanation": "Artificial urgency designed to induce hasty transfers and circumvent normal verification."
    },
    {
        "id": "refuses_inspection",
        "name": "Refusal of In-Person Inspection",
        "points": 10,
        "pattern": r"(can'?t meet|cannot meet|military base|out of town|deployed|shipping only|no in person|courier will collect)",
        "explanation": "Excuses preventing physical inspection of high-value goods before purchase."
    }
]

def evaluate_rules(text: str, price: float = None, item_name: str = None) -> List[Dict[str, Any]]:
    """Evaluates deterministic rule flags against chat transcript."""
    text_lower = text.lower() if text else ""
    triggered = []

    for rule in RULE_DEFINITIONS:
        if re.search(rule["pattern"], text_lower):
            triggered.append({
                "id": rule["id"],
                "name": rule["name"],
                "points": rule["points"],
                "explanation": rule["explanation"]
            })

    # Optional price sanity flag: suspiciously low for flagship devices
    if price and price > 0 and item_name:
        item_lower = item_name.lower()
        if ("iphone 15" in item_lower or "rtx 40" in item_lower or "macbook" in item_lower) and price < 350:
            triggered.append({
                "id": "suspiciously_low_price",
                "name": "Too-Good-To-Be-True Price",
                "points": 10,
                "explanation": f"Price of ${price:,.2f} is substantially below market floor for {item_name} (classic bait pricing)."
            })

    return triggered

def calculate_verdict(score: int) -> Dict[str, str]:
    if score >= 70:
        return {
            "level": "HIGH",
            "title": "High Risk — Likely Scam",
            "badge_color": "red",
            "guidance": "Do NOT send unprotected funds. Insist on PayPal Goods & Services or terminate negotiations immediately."
        }
    elif score >= 40:
        return {
            "level": "MEDIUM",
            "title": "Medium Risk — Proceed With Caution",
            "badge_color": "amber",
            "guidance": "Caution advised. Generate an official PayPal Goods & Services payment link to test seller legitimacy."
        }
    else:
        return {
            "level": "LOW",
            "title": "Low Risk — Normal Negotiation",
            "badge_color": "emerald",
            "guidance": "Deal appears standard. Continue using PayPal Goods & Services to ensure full buyer protection."
        }

def compute_risk_score(
    model_probability: float,
    chat_text: str,
    price: float = None,
    item_name: str = None,
    seller_reply_adjustment: int = 0
) -> Dict[str, Any]:
    """
    Computes transparent risk breakdown (0-100).
    """
    model_points = round(model_probability * 55)
    rules_triggered = evaluate_rules(chat_text, price, item_name)
    rule_points_total = sum(r["points"] for r in rules_triggered)

    raw_score = model_points + rule_points_total + seller_reply_adjustment
    final_score = max(0, min(100, raw_score))
    verdict = calculate_verdict(final_score)

    breakdown = {
        "model_probability": round(model_probability, 4),
        "model_base_points": model_points,
        "max_model_points": 55,
        "rules_triggered": rules_triggered,
        "rule_points_total": rule_points_total,
        "seller_reply_adjustment": seller_reply_adjustment,
        "raw_score": raw_score,
        "final_score": final_score,
        "verdict": verdict["level"],
        "verdict_title": verdict["title"],
        "verdict_badge": verdict["badge_color"],
        "guidance": verdict["guidance"]
    }
    return breakdown
