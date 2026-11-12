import uuid
import pytest
from fastapi.testclient import TestClient
from main import app
from database import SessionLocal
from models import EncryptedMessage, Deal
from services.crypto_service import crypto_service

client = TestClient(app)

def test_websocket_chat_and_live_scoring():
    unique_suffix = uuid.uuid4().hex[:6]
    # Setup Buyer
    b_resp = client.post("/api/auth/signup", json={"email": f"ws_buyer_{unique_suffix}@example.com", "password": "password123", "name": "Buyer Alice"})
    assert b_resp.status_code == 200, b_resp.text
    b_token = b_resp.json()["token"]
    b_headers = {"Authorization": f"Bearer {b_token}"}

    # Buyer creates deal
    d_resp = client.post("/api/deals", json={"item_name": "Sony A7 IV", "price": 1400.0, "currency": "USD"}, headers=b_headers)
    assert d_resp.status_code == 200
    deal_id = d_resp.json()["id"]
    invite_token = d_resp.json()["invite_token"]

    # Setup Seller
    s_resp = client.post("/api/auth/signup", json={"email": f"ws_seller_{unique_suffix}@example.com", "password": "password123", "name": "Seller Steve"})
    assert s_resp.status_code == 200
    s_token = s_resp.json()["token"]
    s_headers = {"Authorization": f"Bearer {s_token}"}

    # Seller joins deal
    join_resp = client.post(f"/api/deals/join/{invite_token}", headers=s_headers)
    assert join_resp.status_code == 200

    # Test WebSocket for Buyer and Seller
    with client.websocket_connect(f"/ws/deals/{deal_id}?token={b_token}") as ws_buyer:
        ack_buyer = ws_buyer.receive_json()
        assert ack_buyer["type"] == "connected"
        assert ack_buyer["role"] == "buyer"

        with client.websocket_connect(f"/ws/deals/{deal_id}?token={s_token}") as ws_seller:
            ack_seller = ws_seller.receive_json()
            assert ack_seller["type"] == "connected"
            assert ack_seller["role"] == "seller"

            # 1. Buyer sends message
            ws_buyer.send_json({"type": "chat_message", "content": "Hi! Is the camera still available?"})
            
            # Both receive chat_message
            msg_b1 = ws_buyer.receive_json()
            msg_s1 = ws_seller.receive_json()
            assert msg_b1["data"]["content"] == "Hi! Is the camera still available?"
            assert msg_s1["data"]["content"] == "Hi! Is the camera still available?"

            # Verify in DB that message is stored ENCRYPTED at rest
            db = SessionLocal()
            stored = db.query(EncryptedMessage).filter(EncryptedMessage.id == msg_b1["data"]["id"]).first()
            assert stored is not None
            assert stored.encrypted_content != "Hi! Is the camera still available?"
            assert crypto_service.decrypt_message(stored.encrypted_content) == "Hi! Is the camera still available?"
            db.close()

            # 2. Seller sends normal message
            ws_seller.send_json({"type": "chat_message", "content": "Yes, it is available in mint condition."})
            ws_buyer.receive_json() # buyer gets chat_message
            ws_seller.receive_json() # seller gets chat_message

            # Buyer gets private ai_risk_update (LOW risk)
            ai_update = ws_buyer.receive_json()
            assert ai_update["type"] == "ai_risk_update"
            assert ai_update["data"]["risk_score"] < 40

            # 3. Seller sends RISKY message: "Pay me via Friends and Family"
            ws_seller.send_json({"type": "chat_message", "content": "Please send amt via friends and family to avoid fees"})
            ws_buyer.receive_json() # buyer gets chat_message
            ws_seller.receive_json() # seller gets chat_message

            # Buyer gets private ai_risk_update with high score & flagged phrase
            risky_ai_update = ws_buyer.receive_json()
            assert risky_ai_update["type"] == "ai_risk_update"
            assert risky_ai_update["data"]["risk_score"] >= 40
            assert any(r["id"] == "friends_and_family" for r in risky_ai_update["data"]["rules_triggered"])

            # Both get system nudge message
            nudge_b = ws_buyer.receive_json()
            nudge_s = ws_seller.receive_json()
            assert nudge_b["type"] == "system_message"
            assert nudge_s["type"] == "system_message"
            assert "PayPal Buyer Protection" in nudge_b["data"]["content"]

def test_ask_dealcheck_ai_endpoint():
    unique_suffix = uuid.uuid4().hex[:6]
    b_resp = client.post("/api/auth/signup", json={"email": f"ai_q_buyer_{unique_suffix}@example.com", "password": "password123", "name": "Buyer AI"})
    assert b_resp.status_code == 200
    b_token = b_resp.json()["token"]
    b_headers = {"Authorization": f"Bearer {b_token}"}

    d_resp = client.post("/api/deals", json={"item_name": "iPhone 15", "price": 600.0}, headers=b_headers)
    assert d_resp.status_code == 200
    deal_id = d_resp.json()["id"]

    ask_resp = client.post(
        f"/api/deals/{deal_id}/ask-ai",
        json={"question": "The seller is asking for Zelle. Is that safe?"},
        headers=b_headers
    )
    assert ask_resp.status_code == 200
    answer = ask_resp.json()["answer"]
    assert len(answer) > 20
    assert "PayPal" in answer or "Zelle" in answer
