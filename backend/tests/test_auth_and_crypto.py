import pytest
from fastapi.testclient import TestClient
from main import app
from services.crypto_service import crypto_service
from database import get_db, Base, engine
from models import User

client = TestClient(app)

def test_crypto_service_hashing_and_encryption():
    password = "SuperSecretPassword123!"
    hashed = crypto_service.hash_password(password)
    assert hashed != password
    assert crypto_service.verify_password(password, hashed) is True
    assert crypto_service.verify_password("WrongPassword", hashed) is False

    plain_text = "Seller says: Pay me via Friends & Family to hold the camera."
    cipher = crypto_service.encrypt_message(plain_text)
    assert cipher != plain_text
    decrypted = crypto_service.decrypt_message(cipher)
    assert decrypted == plain_text

def test_jwt_token_round_trip():
    payload = {"sub": "usr_test123", "email": "test@dealcheck.app", "name": "Test User"}
    token = crypto_service.create_jwt_token(payload)
    decoded = crypto_service.decode_jwt_token(token)
    assert decoded is not None
    assert decoded["sub"] == "usr_test123"
    assert decoded["email"] == "test@dealcheck.app"

def test_auth_signup_login_me_logout():
    email = f"user_{id(client)}@example.com"
    pwd = "securepassword123"
    name = "Alice Buyer"

    # 1. Signup
    signup_resp = client.post("/api/auth/signup", json={"email": email, "password": pwd, "name": name})
    assert signup_resp.status_code == 200
    signup_data = signup_resp.json()
    assert signup_data["user"]["email"] == email
    token = signup_data["token"]
    assert "dealcheck_token" in signup_resp.cookies

    # 2. Get Me (using cookie)
    me_resp = client.get("/api/auth/me", cookies={"dealcheck_token": token})
    assert me_resp.status_code == 200
    assert me_resp.json()["user"]["name"] == name

    # 3. Login
    login_resp = client.post("/api/auth/login", json={"email": email, "password": pwd})
    assert login_resp.status_code == 200
    assert login_resp.json()["user"]["email"] == email

    # 4. Logout
    logout_resp = client.post("/api/auth/logout")
    assert logout_resp.status_code == 200
