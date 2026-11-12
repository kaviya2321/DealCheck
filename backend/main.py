import os
import sys
import uuid
import json
import time
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta

from fastapi import (
    FastAPI, Depends, HTTPException, UploadFile, File, Form,
    Request, Response, WebSocket, WebSocketDisconnect, Cookie, Header, status
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

# Ensure backend directory is in sys.path
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from config import settings
from database import engine, get_db, Base
from models import Deal, User, DealInvite, EncryptedMessage
from services.paypal_client import paypal_service, PayPalAPIError, PayPalConfigurationError
from services.extractor import extract_from_image_bytes, parse_text_deal_heuristics, VisionExtractionError
from services.ml_service import ml_service
from services.evidence_service import generate_evidence_html
from services.crypto_service import crypto_service
from services.socket_manager import socket_manager

# Initialize DB tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Real Buyer-Protection & Collaborative Live Deal Room for PayPal AI Hackathon"
)

# Enable CORS for React Vite Frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------------------------------------------
# In-Memory Rate Limiter
# -------------------------------------------------------------
class SimpleRateLimiter:
    def __init__(self):
        self.records: Dict[str, List[float]] = {}

    def check_rate_limit(self, key: str, max_requests: int, window_seconds: int = 60) -> bool:
        now = time.time()
        timestamps = self.records.get(key, [])
        # Filter timestamps within window
        valid_timestamps = [t for t in timestamps if now - t < window_seconds]
        if len(valid_timestamps) >= max_requests:
            self.records[key] = valid_timestamps
            return False
        valid_timestamps.append(now)
        self.records[key] = valid_timestamps
        return True

rate_limiter = SimpleRateLimiter()

# -------------------------------------------------------------
# Request & Response Schemas
# -------------------------------------------------------------

class SignUpRequest(BaseModel):
    email: str = Field(..., min_length=5, description="User email address")
    password: str = Field(..., min_length=6, description="Password must be at least 6 characters")
    name: str = Field(..., min_length=2, description="Display name")

class LoginRequest(BaseModel):
    email: str = Field(..., min_length=5, description="User email address")
    password: str

class CreateDealRequest(BaseModel):
    item_name: str = Field(..., min_length=2, description="Name of the item")
    price: float = Field(..., gt=0.0, description="Agreed or target price")
    currency: str = Field(default="USD", description="Currency code")

class AgreeTermsRequest(BaseModel):
    agreed: bool = Field(default=True)

class AskAiRequest(BaseModel):
    question: str = Field(..., min_length=3, description="Buyer question for DealCheck AI")

class ExtractTextRequest(BaseModel):
    text: str = Field(..., min_length=5, description="Pasted conversation text")
    item_name: Optional[str] = None
    price: Optional[float] = None

class AnalyzeRequest(BaseModel):
    chat_text: str = Field(..., min_length=5, description="Full buyer-seller chat transcript")
    item_name: str = Field(default="Marketplace Item", description="Name of the item")
    price: float = Field(default=0.0, ge=0.0, description="Agreed or listed price")
    currency: str = Field(default="USD", description="Currency code")
    source_type: str = Field(default="text_paste", description="'text_paste' or 'screenshot'")

class ProtectRequest(BaseModel):
    deal_id: str = Field(..., description="ID of the analyzed deal")
    item_name: Optional[str] = None
    price: Optional[float] = None
    currency: Optional[str] = "USD"

class SellerReplyRequest(BaseModel):
    deal_id: str = Field(..., description="ID of the analyzed deal")
    reply_text: str = Field(..., min_length=2, description="Seller's reaction text")

# -------------------------------------------------------------
# Authentication Dependencies
# -------------------------------------------------------------

def get_current_user_optional(
    request: Request,
    dealcheck_token: Optional[str] = Cookie(None),
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
) -> Optional[User]:
    token = None
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ")[1].strip()
    elif dealcheck_token:
        token = dealcheck_token
    elif request.query_params.get("token"):
        token = request.query_params.get("token")

    if not token:
        return None
    
    payload = crypto_service.decode_jwt_token(token)
    if not payload or "sub" not in payload:
        return None
    
    user = db.query(User).filter(User.id == payload["sub"]).first()
    return user

def get_current_user(user: Optional[User] = Depends(get_current_user_optional)) -> User:
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please log in or sign up."
        )
    return user

# -------------------------------------------------------------
# Health & Status
# -------------------------------------------------------------

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "version": settings.VERSION,
        "models_loaded": ml_service.is_ready(),
        "paypal_configured": True,
        "paypal_live": paypal_service.is_configured(),
        "paypal_mode": "live_sandbox" if paypal_service.is_configured() else "sandbox_simulator",
        "paypal_environment": settings.PAYPAL_ENV,
        "gemini_configured": True,
        "gemini_live": bool(settings.GEMINI_API_KEY.strip()),
        "gemini_mode": "gemini_vision" if bool(settings.GEMINI_API_KEY.strip()) else "transcriber_fallback",
        "security_at_rest": "Fernet AES-128-CBC + HMAC-SHA256 (key CHAT_ENC_KEY)",
        "security_in_transit": "WSS / TLS (FastAPI WebSocket)",
        "notice": "Sandbox checkout, no real money."
    }

# -------------------------------------------------------------
# Auth API Endpoints
# -------------------------------------------------------------

@app.post("/api/auth/signup")
def signup(req: SignUpRequest, response: Response, request: Request, db: Session = Depends(get_db)):
    client_ip = request.client.host if request.client else "unknown"
    if not rate_limiter.check_rate_limit(f"signup_{client_ip}", max_requests=10, window_seconds=60):
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Too many signup attempts. Please wait 1 minute.")

    normalized_email = req.email.lower().strip()
    if "@" not in normalized_email or "." not in normalized_email.split("@")[-1]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Please enter a valid email address.")
    existing = db.query(User).filter(User.email == normalized_email).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="An account with this email already exists.")

    hashed_pwd = crypto_service.hash_password(req.password)
    user_id = f"usr_{uuid.uuid4().hex[:12]}"
    user = User(
        id=user_id,
        email=normalized_email,
        hashed_password=hashed_pwd,
        name=req.name.strip()
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = crypto_service.create_jwt_token({"sub": user.id, "email": user.email, "name": user.name})
    response.set_cookie(
        key="dealcheck_token",
        value=token,
        httponly=True,
        samesite="lax",
        secure=False,  # Set to True when served over HTTPS in production
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )

    return {
        "user": user.to_dict(),
        "token": token,
        "message": "Account created successfully."
    }

@app.post("/api/auth/login")
def login(req: LoginRequest, response: Response, request: Request, db: Session = Depends(get_db)):
    client_ip = request.client.host if request.client else "unknown"
    if not rate_limiter.check_rate_limit(f"login_{client_ip}", max_requests=10, window_seconds=60):
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Too many login attempts. Please wait 1 minute.")

    normalized_email = req.email.lower().strip()
    user = db.query(User).filter(User.email == normalized_email).first()
    if not user or not crypto_service.verify_password(req.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password.")

    token = crypto_service.create_jwt_token({"sub": user.id, "email": user.email, "name": user.name})
    response.set_cookie(
        key="dealcheck_token",
        value=token,
        httponly=True,
        samesite="lax",
        secure=False,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )

    return {
        "user": user.to_dict(),
        "token": token,
        "message": "Logged in successfully."
    }

@app.post("/api/auth/logout")
def logout(response: Response):
    response.delete_cookie(key="dealcheck_token", httponly=True, samesite="lax")
    return {"message": "Logged out successfully."}

@app.get("/api/auth/me")
def get_me(user: User = Depends(get_current_user)):
    return {"user": user.to_dict()}

# -------------------------------------------------------------
# Deals and Invites API Endpoints
# -------------------------------------------------------------

@app.post("/api/deals")
def create_deal(
    req: CreateDealRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    deal_id = f"deal_{uuid.uuid4().hex[:12]}"
    invite_token = f"inv_{uuid.uuid4().hex[:16]}"
    expires_at = datetime.utcnow() + timedelta(hours=48)

    deal = Deal(
        id=deal_id,
        buyer_id=user.id,
        item_name=req.item_name.strip(),
        price=req.price,
        currency=req.currency,
        status="INVITED",
        source_type="in_app_room",
        invite_token=invite_token,
        initial_risk_score=0,
        risk_score=0,
        verdict="LOW"
    )
    deal.append_timeline_event(
        event_type="DEAL_CREATED",
        title="Deal Room Created",
        description=f"Buyer {user.name} created deal for '{req.item_name}' (${req.price:.2f})."
    )

    invite = DealInvite(
        id=f"inv_rec_{uuid.uuid4().hex[:12]}",
        deal_id=deal_id,
        token=invite_token,
        status="SENT",
        expires_at=expires_at
    )

    db.add(deal)
    db.add(invite)
    db.commit()
    db.refresh(deal)

    invite_url = f"/join/{invite_token}"
    share_message = (
        f"Hi! Let's complete the purchase of '{deal.item_name}' (${deal.price:.2f}) safely. "
        f"Join me in the secured DealCheck room here: {invite_url}\n"
        f"DealCheck automatically provides PayPal Buyer Protection and verifies checkout security."
    )

    resp = deal.to_dict()
    resp["invite_url"] = invite_url
    resp["share_message"] = share_message
    resp["expires_at"] = expires_at.isoformat() + "Z"
    return resp

@app.get("/api/deals")
def list_deals(
    user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    Returns user's deals if authenticated; otherwise returns latest public/all deals.
    """
    if user:
        deals = db.query(Deal).filter(
            (Deal.buyer_id == user.id) | (Deal.seller_id == user.id) | (Deal.buyer_id == None)
        ).order_by(Deal.created_at.desc()).all()
    else:
        deals = db.query(Deal).order_by(Deal.created_at.desc()).all()

    results = []
    for d in deals:
        d_dict = d.to_dict()
        if user:
            d_dict["user_role"] = "buyer" if d.buyer_id == user.id else ("seller" if d.seller_id == user.id else "viewer")
        results.append(d_dict)
    return results

@app.get("/api/deals/{id}")
def get_deal(id: str, user: Optional[User] = Depends(get_current_user_optional), db: Session = Depends(get_db)):
    deal = db.query(Deal).filter(Deal.id == id).first()
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found.")

    buyer = db.query(User).filter(User.id == deal.buyer_id).first() if deal.buyer_id else None
    seller = db.query(User).filter(User.id == deal.seller_id).first() if deal.seller_id else None
    invite = db.query(DealInvite).filter(DealInvite.deal_id == deal.id).first()

    data = deal.to_dict()
    data["buyer_name"] = buyer.name if buyer else "Buyer"
    data["seller_name"] = seller.name if seller else ("Pending Seller" if deal.status == "INVITED" else "Seller")
    data["invite_status"] = invite.status if invite else "UNKNOWN"
    data["invite_expires_at"] = invite.expires_at.isoformat() + "Z" if invite and invite.expires_at else None
    data["user_role"] = "buyer" if user and deal.buyer_id == user.id else ("seller" if user and deal.seller_id == user.id else "viewer")
    return data

@app.get("/api/invites/{token}")
def preview_invite(token: str, db: Session = Depends(get_db)):
    invite = db.query(DealInvite).filter(DealInvite.token == token).first()
    if not invite:
        raise HTTPException(status_code=404, detail="Invitation link not found or invalid.")

    if invite.expires_at and invite.expires_at < datetime.utcnow():
        invite.status = "EXPIRED"
        db.commit()
        raise HTTPException(status_code=410, detail="This invitation link has expired (48h validity exceeded).")

    if invite.status == "SENT":
        invite.status = "OPENED"
        invite.opened_at = datetime.utcnow()
        db.commit()

    deal = db.query(Deal).filter(Deal.id == invite.deal_id).first()
    if not deal:
        raise HTTPException(status_code=404, detail="Associated deal no longer exists.")

    buyer = db.query(User).filter(User.id == deal.buyer_id).first() if deal.buyer_id else None

    return {
        "deal_id": deal.id,
        "token": token,
        "item_name": deal.item_name,
        "price": deal.price,
        "currency": deal.currency,
        "status": invite.status,
        "buyer_name": buyer.name if buyer else "Deal Creator",
        "expires_at": invite.expires_at.isoformat() + "Z" if invite.expires_at else None
    }

@app.post("/api/deals/join/{token}")
async def join_deal(token: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    invite = db.query(DealInvite).filter(DealInvite.token == token).first()
    if not invite:
        raise HTTPException(status_code=404, detail="Invitation link not found.")

    if invite.expires_at and invite.expires_at < datetime.utcnow():
        raise HTTPException(status_code=410, detail="Invitation link has expired.")

    deal = db.query(Deal).filter(Deal.id == invite.deal_id).first()
    if not deal:
        raise HTTPException(status_code=404, detail="Associated deal not found.")

    if deal.buyer_id == user.id:
        return {"deal_id": deal.id, "message": "You created this deal (Buyer role).", "role": "buyer"}

    if deal.seller_id and deal.seller_id != user.id:
        raise HTTPException(status_code=400, detail="Another seller has already joined this deal.")

    deal.seller_id = user.id
    deal.status = "ACTIVE"
    invite.status = "JOINED"

    deal.append_timeline_event(
        event_type="SELLER_JOINED",
        title="Seller Joined Deal Room",
        description=f"Seller {user.name} ({user.email}) accepted invite and joined the live room."
    )
    db.commit()
    db.refresh(deal)

    # Notify room via WebSocket
    await socket_manager.broadcast_to_deal(deal.id, "system_message", {
        "content": f"{user.name} (Seller) joined the Deal Room.",
        "badge": "SELLER_JOINED"
    })

    return {
        "deal_id": deal.id,
        "message": "Successfully joined deal room as Seller.",
        "role": "seller"
    }

@app.post("/api/deals/{id}/agree")
async def agree_terms(
    id: str,
    req: AgreeTermsRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    deal = db.query(Deal).filter(Deal.id == id).first()
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found.")

    if user.id == deal.buyer_id:
        deal.buyer_agreed = 1 if req.agreed else 0
    elif user.id == deal.seller_id:
        deal.seller_agreed = 1 if req.agreed else 0
    else:
        raise HTTPException(status_code=403, detail="Only deal participants can confirm terms.")

    role_label = "Buyer" if user.id == deal.buyer_id else "Seller"
    deal.append_timeline_event(
        event_type="TERMS_CONFIRMED",
        title=f"{role_label} Agreed to Terms",
        description=f"{user.name} confirmed terms for {deal.item_name} at ${deal.price:.2f}."
    )

    # Broadcast agreement status
    await socket_manager.broadcast_to_deal(deal.id, "agreement_updated", {
        "buyer_agreed": bool(deal.buyer_agreed),
        "seller_agreed": bool(deal.seller_agreed)
    })

    # If both agreed and PayPal order not yet created: auto-generate PayPal checkout card!
    if deal.buyer_agreed and deal.seller_agreed and not deal.paypal_order_id:
        try:
            pp_order = await paypal_service.create_protected_order(
                item_name=deal.item_name,
                amount=deal.price,
                currency=deal.currency,
                deal_id=deal.id
            )
            deal.paypal_order_id = pp_order["order_id"]
            deal.paypal_approval_url = pp_order["approval_url"]
            deal.paypal_status = "CREATED"
            deal.status = "PAYMENT_PENDING"

            deal.append_timeline_event(
                event_type="PAYPAL_ORDER_CREATED",
                title="Protected PayPal Sandbox Order Generated",
                description=f"Both parties agreed to terms. Generated real PayPal Goods & Services Order (ID: {deal.paypal_order_id})."
            )

            # Broadcast PayPal Card to both participants
            await socket_manager.broadcast_to_deal(deal.id, "paypal_card", {
                "order_id": deal.paypal_order_id,
                "approval_url": deal.paypal_approval_url,
                "amount": deal.price,
                "currency": deal.currency,
                "item_name": deal.item_name,
                "status": "CREATED",
                "sandbox_notice": "Sandbox checkout, no real money."
            })
        except Exception as e:
            print(f"[DealCheck] Auto-create PayPal order error: {e}")

    db.commit()
    db.refresh(deal)
    return deal.to_dict()

@app.delete("/api/deals/{id}")
def delete_deal(id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    deal = db.query(Deal).filter(Deal.id == id).first()
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found.")

    if deal.buyer_id != user.id and deal.seller_id != user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this deal.")

    # Remove all messages and invites
    db.query(EncryptedMessage).filter(EncryptedMessage.deal_id == id).delete()
    db.query(DealInvite).filter(DealInvite.deal_id == id).delete()
    db.delete(deal)
    db.commit()

    return {"message": f"Deal {id} and all encrypted messages permanently deleted."}

# -------------------------------------------------------------
# Encrypted Messages & AI Q&A Endpoints
# -------------------------------------------------------------

@app.get("/api/deals/{id}/messages")
def get_deal_messages(
    id: str,
    user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    deal = db.query(Deal).filter(Deal.id == id).first()
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found.")

    raw_messages = db.query(EncryptedMessage).filter(
        EncryptedMessage.deal_id == id
    ).order_by(EncryptedMessage.created_at.asc()).all()

    # Pre-fetch users for sender names
    sender_ids = list(set(m.sender_id for m in raw_messages))
    users_by_id = {u.id: u for u in db.query(User).filter(User.id.in_(sender_ids)).all()} if sender_ids else {}

    results = []
    is_buyer = (user and user.id == deal.buyer_id) or (user is None)

    for m in raw_messages:
        # Hide buyer-private AI warnings if caller is seller
        if m.is_private_to_buyer and not is_buyer:
            continue
        decrypted = crypto_service.decrypt_message(m.encrypted_content)
        sender_obj = users_by_id.get(m.sender_id)
        sender_name = sender_obj.name if sender_obj else ("Buyer" if m.sender_id == deal.buyer_id else "Seller")
        msg_dict = m.to_dict(decrypted_text=decrypted, sender_name=sender_name)
        msg_dict["sender_role"] = "buyer" if m.sender_id == deal.buyer_id else "seller"
        results.append(msg_dict)

    return results

@app.post("/api/deals/{id}/ask-ai")
async def ask_dealcheck_ai(
    id: str,
    req: AskAiRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    deal = db.query(Deal).filter(Deal.id == id).first()
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found.")

    # Only buyer can consult the private safety advisor
    if deal.buyer_id and user.id != deal.buyer_id:
        raise HTTPException(status_code=403, detail="DealCheck Safety Advisor is private to the buyer.")

    context = {
        "item_name": deal.item_name,
        "price": deal.price,
        "risk_score": deal.risk_score,
        "verdict": deal.verdict,
        "rules_triggered": json.loads(deal.rules_triggered_json or "[]")
    }

    answer = await ml_service.ask_dealcheck_ai(req.question, context)
    return {"question": req.question, "answer": answer}

# -------------------------------------------------------------
# Real-Time WebSocket Deal Room
# -------------------------------------------------------------

@app.websocket("/ws/deals/{deal_id}")
async def deal_room_websocket(
    websocket: WebSocket,
    deal_id: str,
    token: Optional[str] = None,
    db: Session = Depends(get_db)
):
    # Authenticate via cookie or query param
    auth_token = token or websocket.cookies.get("dealcheck_token")
    if not auth_token:
        await websocket.close(code=4001, reason="Unauthorized")
        return

    payload = crypto_service.decode_jwt_token(auth_token)
    if not payload or "sub" not in payload:
        await websocket.close(code=4001, reason="Invalid token")
        return

    user_id = payload["sub"]
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        await websocket.close(code=4001, reason="User not found")
        return

    deal = db.query(Deal).filter(Deal.id == deal_id).first()
    if not deal:
        await websocket.close(code=4004, reason="Deal not found")
        return

    # Check participant permissions
    is_buyer = (deal.buyer_id == user_id)
    is_seller = (deal.seller_id == user_id)
    if not (is_buyer or is_seller):
        # If user is joining as seller
        invite = db.query(DealInvite).filter(DealInvite.deal_id == deal.id).first()
        if invite and not deal.seller_id:
            deal.seller_id = user_id
            deal.status = "ACTIVE"
            invite.status = "JOINED"
            db.commit()
            is_seller = True
        else:
            await websocket.close(code=4003, reason="Not a deal participant")
            return

    await socket_manager.connect(deal_id, user_id, websocket)

    # Send presence ack
    await websocket.send_json({
        "type": "connected",
        "deal_id": deal_id,
        "user_id": user_id,
        "user_name": user.name,
        "role": "buyer" if is_buyer else "seller",
        "deal_status": deal.status,
        "paypal_order_id": deal.paypal_order_id,
        "buyer_agreed": bool(deal.buyer_agreed),
        "seller_agreed": bool(deal.seller_agreed)
    })

    try:
        while True:
            data = await websocket.receive_json()
            event_type = data.get("type", "chat_message")

            if event_type == "chat_message":
                # Rate limit message sending: 60/min
                if not rate_limiter.check_rate_limit(f"msg_{user_id}", max_requests=60, window_seconds=60):
                    await websocket.send_json({
                        "type": "error",
                        "message": "Message rate limit exceeded. Please wait a moment."
                    })
                    continue

                content = str(data.get("content", "")).strip()
                if not content:
                    continue

                role = "buyer" if is_buyer else "seller"

                # 1. Encrypt message at rest using Fernet
                encrypted_payload = crypto_service.encrypt_message(content)
                msg_id = f"msg_{uuid.uuid4().hex[:12]}"
                db_msg = EncryptedMessage(
                    id=msg_id,
                    deal_id=deal.id,
                    sender_id=user_id,
                    encrypted_content=encrypted_payload,
                    message_type="chat"
                )
                db.add(db_msg)
                db.commit()

                # 2. Broadcast message to both participants
                msg_event = {
                    "id": msg_id,
                    "sender_id": user_id,
                    "sender_name": user.name,
                    "sender_role": role,
                    "content": content,
                    "created_at": db_msg.created_at.isoformat() + "Z"
                }
                await socket_manager.broadcast_to_deal(deal_id, "chat_message", msg_event)

                # 3. Assemble full cumulative transcript for running scoring
                all_msgs = db.query(EncryptedMessage).filter(
                    EncryptedMessage.deal_id == deal.id,
                    EncryptedMessage.message_type == "chat"
                ).order_by(EncryptedMessage.created_at.asc()).all()

                transcript_lines = []
                for m in all_msgs:
                    dec = crypto_service.decrypt_message(m.encrypted_content)
                    m_role = "Buyer" if m.sender_id == deal.buyer_id else "Seller"
                    transcript_lines.append(f"{m_role}: {dec}")
                full_transcript = "\n".join(transcript_lines)
                deal.chat_text = full_transcript

                # 4. If message is from seller: score running chat with Model A & Model B
                if role == "seller":
                    has_card = bool(deal.paypal_order_id)
                    analysis = ml_service.score_running_chat(
                        new_message=content,
                        full_transcript=full_transcript,
                        sender_role="seller",
                        item_name=deal.item_name,
                        price=deal.price,
                        has_paypal_card=has_card,
                        invite_status="JOINED"
                    )

                    deal.risk_score = analysis["risk_score"]
                    deal.verdict = analysis["verdict"]
                    deal.rules_triggered_json = json.dumps(analysis["rules_triggered"])
                    deal.highlighted_phrases_json = json.dumps(analysis["highlighted_phrases"])
                    deal.explanation = analysis["explanation"]

                    if analysis.get("seller_evaluation"):
                        deal.seller_classification = analysis["seller_evaluation"]["classification"]
                        deal.seller_confidence = analysis["seller_evaluation"]["confidence"]
                        deal.seller_litmus_verdict = analysis["seller_evaluation"]["litmus_verdict"]
                        deal.seller_risk_delta = analysis["seller_evaluation"]["risk_delta"]

                    db.commit()

                    # Send LIVE risk update PRIVATELY to BUYER ONLY
                    if deal.buyer_id:
                        await socket_manager.send_to_user(deal_id, deal.buyer_id, "ai_risk_update", {
                            "risk_score": analysis["risk_score"],
                            "verdict": analysis["verdict"],
                            "verdict_title": analysis["verdict_title"],
                            "verdict_badge": analysis["verdict_badge"],
                            "guidance": analysis["guidance"],
                            "rules_triggered": analysis["rules_triggered"],
                            "highlighted_phrases": analysis["highlighted_phrases"],
                            "explanation": analysis["explanation"],
                            "model_base_points": analysis["model_base_points"],
                            "rule_points_total": analysis["rule_points_total"],
                            "seller_evaluation": analysis.get("seller_evaluation"),
                            "refusal_warning": analysis.get("refusal_warning")
                        })

                    # If polite nudge required (seller asked for F&F or off-platform payment)
                    if analysis.get("nudge_required"):
                        await socket_manager.broadcast_to_deal(deal_id, "system_message", {
                            "content": analysis["nudge_text"],
                            "badge": "SECURITY_NOTICE"
                        })

                # 5. Check if mutual deal agreement is reached in conversation
                if not deal.paypal_order_id and ml_service.detect_deal_agreement(full_transcript):
                    try:
                        pp_order = await paypal_service.create_protected_order(
                            item_name=deal.item_name,
                            amount=deal.price,
                            currency=deal.currency,
                            deal_id=deal.id
                        )
                        deal.paypal_order_id = pp_order["order_id"]
                        deal.paypal_approval_url = pp_order["approval_url"]
                        deal.paypal_status = "CREATED"
                        deal.status = "PAYMENT_PENDING"
                        deal.append_timeline_event(
                            event_type="PAYPAL_ORDER_CREATED",
                            title="PayPal Sandbox Order Auto-Generated",
                            description=f"AI detected agreement in conversation. Created real PayPal Sandbox Order (ID: {deal.paypal_order_id})."
                        )
                        db.commit()

                        # Post protected payment card into chat
                        await socket_manager.broadcast_to_deal(deal_id, "paypal_card", {
                            "order_id": deal.paypal_order_id,
                            "approval_url": deal.paypal_approval_url,
                            "amount": deal.price,
                            "currency": deal.currency,
                            "item_name": deal.item_name,
                            "status": "CREATED",
                            "sandbox_notice": "Sandbox checkout, no real money."
                        })
                    except Exception as e:
                        print(f"[DealCheck] Auto-trigger PayPal order error: {e}")

            elif event_type == "typing":
                await socket_manager.broadcast_to_deal(deal_id, "typing", {
                    "user_id": user_id,
                    "user_name": user.name,
                    "role": "buyer" if is_buyer else "seller",
                    "is_typing": bool(data.get("is_typing", True))
                })

            elif event_type == "read_receipt":
                await socket_manager.broadcast_to_deal(deal_id, "read_receipt", {
                    "user_id": user_id,
                    "read_up_to": data.get("message_id")
                })

    except WebSocketDisconnect:
        socket_manager.disconnect(deal_id, user_id)
        logger_name = user.name if user else user_id
        await socket_manager.broadcast_to_deal(deal_id, "presence_update", {
            "user_id": user_id,
            "status": "offline"
        })
    except Exception as e:
        print(f"[WS] Error in room {deal_id}: {e}")
        socket_manager.disconnect(deal_id, user_id)

# -------------------------------------------------------------
# Legacy & Direct API Endpoints (Maintained for backward compatibility)
# -------------------------------------------------------------

@app.post("/api/extract")
async def extract_chat(
    file: Optional[UploadFile] = File(None),
    text: Optional[str] = Form(None),
    item_name: Optional[str] = Form(None),
    price: Optional[float] = Form(None),
):
    """
    Extracts text, item name, and price. Accepts screenshot or pasted text.
    """
    if file:
        content_type = file.content_type or "image/png"
        if not content_type.startswith("image/"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded file must be an image (PNG, JPEG, WebP)."
            )
        try:
            image_bytes = await file.read()
            extracted = await extract_from_image_bytes(image_bytes, content_type)
            return {
                "source_type": "screenshot",
                "chat_text": extracted["chat_text"],
                "item_name": extracted["item_name"],
                "price": extracted["price"],
                "currency": extracted["currency"]
            }
        except VisionExtractionError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )

    if text and text.strip():
        parsed = parse_text_deal_heuristics(text, item_name, price)
        return {
            "source_type": "text_paste",
            "chat_text": parsed["chat_text"],
            "item_name": parsed["item_name"],
            "price": parsed["price"],
            "currency": parsed["currency"]
        }

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Please provide either a screenshot file or paste conversation text."
    )

@app.post("/api/analyze")
async def analyze_deal(req: AnalyzeRequest, db: Session = Depends(get_db)):
    """
    Analyzes chat using DealCheck's custom trained Model A (ScamRiskModel)
    and rule engine. Persists deal in SQLite.
    """
    if not ml_service.is_ready():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="DealCheck models are not ready. Please verify 'python train.py' completed."
        )

    analysis = ml_service.analyze_chat(
        chat_text=req.chat_text,
        item_name=req.item_name,
        price=req.price
    )

    polished = await ml_service.polish_explanation_with_llm(
        chat_text=req.chat_text,
        scoring_result=analysis,
        item_name=req.item_name,
        price=req.price
    )
    if polished:
        analysis["explanation"] = polished

    deal_id = f"deal_{uuid.uuid4().hex[:12]}"
    deal = Deal(
        id=deal_id,
        item_name=req.item_name,
        price=req.price,
        currency=req.currency,
        chat_text=req.chat_text,
        source_type=req.source_type,
        initial_risk_score=analysis["risk_score"],
        risk_score=analysis["risk_score"],
        verdict=analysis["verdict"],
        model_probability=analysis["model_probability"],
        explanation=analysis["explanation"],
        rules_triggered_json=json.dumps(analysis["rules_triggered"]),
        highlighted_phrases_json=json.dumps(analysis["highlighted_phrases"]),
        drafted_message=analysis["drafted_message"]
    )
    deal.append_timeline_event(
        event_type="ANALYSIS_COMPLETED",
        title="Initial Risk Assessment",
        description=f"Model A & Rule Engine scored deal at {analysis['risk_score']}/100 ({analysis['verdict']} RISK)."
    )
    db.add(deal)
    db.commit()
    db.refresh(deal)

    resp_data = deal.to_dict()
    resp_data["model_base_points"] = analysis["model_base_points"]
    resp_data["rule_points_total"] = analysis["rule_points_total"]
    resp_data["verdict_title"] = analysis["verdict_title"]
    resp_data["verdict_badge"] = analysis["verdict_badge"]
    resp_data["guidance"] = analysis["guidance"]

    return resp_data

@app.post("/api/protect")
async def create_protection_link(req: ProtectRequest, db: Session = Depends(get_db)):
    """
    Creates an authentic PayPal Sandbox Orders v2 checkout order.
    """
    deal = db.query(Deal).filter(Deal.id == req.deal_id).first()
    if not deal:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deal not found.")

    item_name = req.item_name or deal.item_name
    price = req.price if req.price is not None else deal.price
    currency = req.currency or deal.currency

    try:
        pp_order = await paypal_service.create_protected_order(
            item_name=item_name,
            amount=price,
            currency=currency,
            deal_id=deal.id
        )

        approval_url = pp_order["approval_url"]
        order_id = pp_order["order_id"]

        drafted_msg = (
            f"Hi! I'm ready to finalize purchasing the {item_name} for ${price:.2f}. "
            f"For both of our security and to ensure full PayPal Buyer & Seller Protection, "
            f"I have created the official PayPal Goods & Services checkout here: {approval_url}\n"
            f"Once you confirm, PayPal will notify you and I will share my verified shipping address. Thanks!"
        )

        deal.paypal_order_id = order_id
        deal.paypal_approval_url = approval_url
        deal.paypal_status = "CREATED"
        deal.drafted_message = drafted_msg
        deal.append_timeline_event(
            event_type="PAYPAL_ORDER_CREATED",
            title="PayPal Sandbox Order Generated",
            description=f"Created real PayPal Goods & Services Order (ID: {order_id}) for ${price:.2f}."
        )
        db.commit()
        db.refresh(deal)

        return {
            "deal_id": deal.id,
            "order_id": order_id,
            "approval_url": approval_url,
            "status": pp_order["status"],
            "amount": price,
            "currency": currency,
            "drafted_message": drafted_msg,
            "sandbox_notice": "Sandbox checkout, no real money."
        }

    except PayPalConfigurationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": str(e), "retryable": False, "code": "PAYPAL_NOT_CONFIGURED"}
        )
    except PayPalAPIError as e:
        raise HTTPException(
            status_code=e.status_code,
            detail={"message": str(e), "retryable": True, "code": "PAYPAL_API_ERROR"}
        )

@app.post("/api/seller-reply")
async def evaluate_seller_reply(req: SellerReplyRequest, db: Session = Depends(get_db)):
    """
    Evaluates seller's reaction with Model B (SellerReplyModel).
    """
    deal = db.query(Deal).filter(Deal.id == req.deal_id).first()
    if not deal:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deal not found.")

    if not ml_service.is_ready():
        raise HTTPException(status_code=503, detail="Models not loaded.")

    reply_eval = ml_service.analyze_seller_reply(req.reply_text)
    risk_delta = reply_eval["risk_delta"]

    old_score = deal.risk_score
    new_score = max(0, min(100, old_score + risk_delta))
    new_verdict = "HIGH" if new_score >= 70 else ("MEDIUM" if new_score >= 40 else "LOW")

    deal.seller_reply_text = req.reply_text
    deal.seller_classification = reply_eval["classification"]
    deal.seller_confidence = reply_eval["confidence"]
    deal.seller_litmus_verdict = reply_eval["litmus_verdict"]
    deal.seller_risk_delta = risk_delta
    deal.risk_score = new_score
    deal.verdict = new_verdict

    deal.append_timeline_event(
        event_type="SELLER_REACTION_EVALUATED",
        title=f"Seller Litmus Test: {reply_eval['litmus_verdict']}",
        description=(
            f"Seller reply classified as '{reply_eval['classification']}' (Confidence: {reply_eval['confidence']*100:.1f}%). "
            f"Risk score adjusted by {risk_delta:+d} pts (from {old_score} to {new_score})."
        )
    )
    db.commit()
    db.refresh(deal)

    return {
        "deal_id": deal.id,
        "old_score": old_score,
        "new_score": new_score,
        "verdict": new_verdict,
        "seller_classification": reply_eval["classification"],
        "confidence": reply_eval["confidence"],
        "litmus_verdict": reply_eval["litmus_verdict"],
        "summary": reply_eval["summary"],
        "probabilities": reply_eval["probabilities"]
    }

@app.get("/api/paypal/return")
async def paypal_return(
    token: str,
    PayerID: Optional[str] = None,
    deal_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Callback endpoint triggered when buyer approves payment in PayPal Sandbox.
    Executes real capture on PayPal REST API.
    """
    order_id = token
    deal = None
    if deal_id:
        deal = db.query(Deal).filter(Deal.id == deal_id).first()
    if not deal:
        deal = db.query(Deal).filter(Deal.paypal_order_id == order_id).first()

    try:
        capture_result = await paypal_service.capture_order(order_id)
        capture_id = capture_result.get("capture_id")
        status_val = capture_result.get("status", "COMPLETED")

        if deal:
            deal.paypal_status = status_val
            deal.paypal_capture_id = capture_id
            deal.status = "COMPLETED"
            deal.append_timeline_event(
                event_type="PAYMENT_CAPTURED",
                title="PayPal Sandbox Payment Captured",
                description=f"Transaction approved by buyer and captured. Capture ID: {capture_id}."
            )
            db.commit()
            db.refresh(deal)

            # Broadcast live captured payment to the deal room!
            await socket_manager.broadcast_to_deal(deal.id, "payment_captured", {
                "order_id": order_id,
                "capture_id": capture_id,
                "status": status_val,
                "amount": deal.price,
                "currency": deal.currency
            })

        return {
            "status": status_val,
            "order_id": order_id,
            "capture_id": capture_id,
            "deal_id": deal.id if deal else None,
            "sandbox_notice": "Sandbox checkout, no real money."
        }

    except (PayPalConfigurationError, PayPalAPIError) as e:
        if deal:
            deal.paypal_status = "FAILED"
            deal.append_timeline_event(
                event_type="CAPTURE_FAILED",
                title="Capture Failed",
                description=str(e)
            )
            db.commit()
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={"message": str(e), "retryable": True}
        )

@app.get("/api/evidence/{id}")
def get_evidence(id: str, format: str = "json", db: Session = Depends(get_db)):
    deal = db.query(Deal).filter(Deal.id == id).first()
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found.")

    deal_dict = deal.to_dict()
    if format == "html":
        html_content = generate_evidence_html(deal_dict)
        return HTMLResponse(content=html_content)
    
    return deal_dict

@app.get("/api/model/metrics")
def get_model_metrics():
    metrics_path = settings.REPORTS_DIR / "metrics.json"
    if not metrics_path.exists():
        raise HTTPException(status_code=404, detail="Metrics report not found. Please run 'python train.py' first.")
    
    with open(metrics_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data

@app.delete("/api/data")
def clear_data(db: Session = Depends(get_db)):
    db.query(EncryptedMessage).delete()
    db.query(DealInvite).delete()
    db.query(Deal).delete()
    db.commit()
    return {"message": "All deal, invite, and encrypted message records have been cleared."}

# -------------------------------------------------------------
# Production SPA Static Serving
# -------------------------------------------------------------
dist_dir = Path(__file__).resolve().parent.parent / "frontend" / "dist"
if dist_dir.exists():
    from fastapi.staticfiles import StaticFiles
    from starlette.responses import FileResponse

    if (dist_dir / "assets").exists():
        app.mount("/assets", StaticFiles(directory=str(dist_dir / "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        if full_path.startswith("api/") or full_path.startswith("ws/") or full_path.startswith("health"):
            raise HTTPException(status_code=404, detail="API route not found.")
        file_path = dist_dir / full_path
        if file_path.exists() and file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(dist_dir / "index.html")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
