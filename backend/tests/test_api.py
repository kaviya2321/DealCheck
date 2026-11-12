import pytest
import os
import sys
from fastapi.testclient import TestClient

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BACKEND_DIR)

from main import app

client = TestClient(app)

def test_health_endpoint():
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert data["models_loaded"] is True
    assert "Sandbox checkout, no real money." in data["notice"]

def test_model_metrics_endpoint():
    resp = client.get("/api/model/metrics")
    assert resp.status_code == 200
    data = resp.json()
    assert "model_a_scam_classifier" in data
    assert "model_b_seller_reaction" in data
    assert data["model_a_scam_classifier"]["test_split_evaluation"]["accuracy"] > 0.90

def test_extract_endpoint_pasted_text():
    payload = {
        "text": "Buyer: Is the iPhone 15 Pro available? Seller: Yes for $650, pay via friends and family."
    }
    resp = client.post("/api/extract", data=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["source_type"] == "text_paste"
    assert "iPhone 15 Pro" in data["item_name"]
    assert data["price"] == 650.0

def test_end_to_end_deal_flow():
    # 1. Analyze Deal (Scam conversation)
    analyze_payload = {
        "chat_text": "Buyer: Can I pay with PayPal Goods and Services? Seller: No my PayPal only takes Friends and Family to avoid fees. Pay now or I sell to someone else.",
        "item_name": "PlayStation 5 Disc Edition",
        "price": 320.0,
        "currency": "USD"
    }
    analyze_resp = client.post("/api/analyze", json=analyze_payload)
    assert analyze_resp.status_code == 200
    deal_data = analyze_resp.json()
    deal_id = deal_data["id"]
    assert deal_data["risk_score"] >= 70
    assert deal_data["verdict"] == "HIGH"
    assert len(deal_data["rules_triggered"]) > 0
    assert len(deal_data["highlighted_phrases"]) > 0

    # 2. Test Seller Reaction: Seller insists on F&F
    seller_payload = {
        "deal_id": deal_id,
        "reply_text": "I said NO to Goods and Services! Send it via Friends and Family only or deal is off."
    }
    reply_resp = client.post("/api/seller-reply", json=seller_payload)
    assert reply_resp.status_code == 200
    reply_data = reply_resp.json()
    assert reply_data["seller_classification"] == "pushes_friends_and_family"
    assert reply_data["litmus_verdict"] == "FAILED"
    assert reply_data["new_score"] >= reply_data["old_score"]

    # 3. Retrieve Deal from History
    get_resp = client.get(f"/api/deals/{deal_id}")
    assert get_resp.status_code == 200
    fetched = get_resp.json()
    assert fetched["id"] == deal_id
    assert fetched["seller_litmus_verdict"] == "FAILED"

    # 4. Generate Evidence Dossier HTML
    ev_resp = client.get(f"/api/evidence/{deal_id}?format=html")
    assert ev_resp.status_code == 200
    assert "text/html" in ev_resp.headers["content-type"]
    assert "DealCheck Security Report" in ev_resp.text
    assert deal_id in ev_resp.text
