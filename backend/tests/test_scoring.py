import pytest
import sys
import os

# Add ml directory to sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(BASE_DIR, "ml"))

from scoring import compute_risk_score, evaluate_rules, calculate_verdict

def test_evaluate_rules_friends_and_family():
    text = "Send it as friends and family please to avoid paypal fees."
    flags = evaluate_rules(text)
    flag_ids = [f["id"] for f in flags]
    assert "friends_and_family" in flag_ids
    ff_rule = next(f for f in flags if f["id"] == "friends_and_family")
    assert ff_rule["points"] == 35

def test_evaluate_rules_advance_deposit():
    text = "You need to pay 50 deposit right now to hold it."
    flags = evaluate_rules(text)
    flag_ids = [f["id"] for f in flags]
    assert "advance_deposit" in flag_ids

def test_evaluate_rules_off_platform():
    text = "My paypal is glitching, please send via Zelle or CashApp."
    flags = evaluate_rules(text)
    flag_ids = [f["id"] for f in flags]
    assert "off_platform_payment" in flag_ids

def test_evaluate_rules_urgency():
    text = "Must sell today only, hurry up someone else is waiting."
    flags = evaluate_rules(text)
    flag_ids = [f["id"] for f in flags]
    assert "urgency_pressure" in flag_ids

def test_evaluate_rules_inspection_refusal():
    text = "I am deployed at an army military base, so cannot meet in person. Shipping only."
    flags = evaluate_rules(text)
    flag_ids = [f["id"] for f in flags]
    assert "refuses_inspection" in flag_ids

def test_verdict_thresholds():
    assert calculate_verdict(85)["level"] == "HIGH"
    assert calculate_verdict(70)["level"] == "HIGH"
    assert calculate_verdict(69)["level"] == "MEDIUM"
    assert calculate_verdict(40)["level"] == "MEDIUM"
    assert calculate_verdict(39)["level"] == "LOW"
    assert calculate_verdict(0)["level"] == "LOW"

def test_compute_risk_score_bounds():
    # Test lower bound clamping
    low_res = compute_risk_score(model_probability=0.01, chat_text="Hello, let's meet at Starbucks.", seller_reply_adjustment=-50)
    assert low_res["final_score"] >= 0

    # Test upper bound clamping
    high_res = compute_risk_score(
        model_probability=0.99,
        chat_text="Send advance deposit via Zelle and friends and family urgent today only military base.",
        seller_reply_adjustment=40
    )
    assert high_res["final_score"] == 100
    assert high_res["verdict"] == "HIGH"
