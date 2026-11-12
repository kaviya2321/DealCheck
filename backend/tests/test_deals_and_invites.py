import pytest
from fastapi.testclient import TestClient
from main import app
from services.crypto_service import crypto_service

client = TestClient(app)

def test_deal_creation_invite_and_join():
    # 1. Buyer signs up
    buyer_email = f"buyer_invite_{id(client)}@example.com"
    buyer_resp = client.post("/api/auth/signup", json={"email": buyer_email, "password": "password123", "name": "Buyer Bob"})
    buyer_token = buyer_resp.json()["token"]
    buyer_headers = {"Authorization": f"Bearer {buyer_token}"}

    # 2. Buyer creates a deal
    create_resp = client.post(
        "/api/deals",
        json={"item_name": "MacBook Pro M3", "price": 1200.0, "currency": "USD"},
        headers=buyer_headers
    )
    assert create_resp.status_code == 200
    deal_data = create_resp.json()
    assert deal_data["item_name"] == "MacBook Pro M3"
    assert deal_data["status"] == "INVITED"
    invite_token = deal_data["invite_token"]
    deal_id = deal_data["id"]

    # 3. Seller previews invite without logging in
    preview_resp = client.get(f"/api/invites/{invite_token}")
    assert preview_resp.status_code == 200
    preview_data = preview_resp.json()
    assert preview_data["item_name"] == "MacBook Pro M3"
    assert preview_data["price"] == 1200.0

    # 4. Seller signs up and joins
    seller_email = f"seller_invite_{id(client)}@example.com"
    seller_resp = client.post("/api/auth/signup", json={"email": seller_email, "password": "password123", "name": "Seller Sam"})
    seller_token = seller_resp.json()["token"]
    seller_headers = {"Authorization": f"Bearer {seller_token}"}

    join_resp = client.post(
        f"/api/deals/join/{invite_token}",
        headers=seller_headers
    )
    assert join_resp.status_code == 200
    assert join_resp.json()["role"] == "seller"

    # 5. Check deal status is now ACTIVE
    deal_check_resp = client.get(f"/api/deals/{deal_id}", headers=buyer_headers)
    assert deal_check_resp.status_code == 200
    assert deal_check_resp.json()["status"] == "ACTIVE"

    # 6. Both agree to terms -> PayPal Sandbox order auto-generated
    agree_buyer = client.post(f"/api/deals/{deal_id}/agree", json={"agreed": True}, headers=buyer_headers)
    assert agree_buyer.status_code == 200

    agree_seller = client.post(f"/api/deals/{deal_id}/agree", json={"agreed": True}, headers=seller_headers)
    assert agree_seller.status_code == 200
    updated_deal = agree_seller.json()
    assert updated_deal["buyer_agreed"] is True
    assert updated_deal["seller_agreed"] is True
    # PayPal order created!
    assert updated_deal["paypal_order_id"] is not None
    assert "sandbox.paypal.com" in (updated_deal["paypal_approval_url"] or "")

    # 7. Delete deal
    del_resp = client.delete(f"/api/deals/{deal_id}", headers=buyer_headers)
    assert del_resp.status_code == 200
