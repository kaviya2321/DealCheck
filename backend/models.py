import json
from datetime import datetime
from sqlalchemy import Column, String, Float, Integer, Text, DateTime, Boolean
from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(String(64), primary_key=True, index=True)
    email = Column(String(256), unique=True, index=True, nullable=False)
    hashed_password = Column(String(256), nullable=False)
    name = Column(String(128), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "email": self.email,
            "name": self.name,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

class Deal(Base):
    __tablename__ = "deals"

    id = Column(String(64), primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Participants and Status
    buyer_id = Column(String(64), nullable=True, index=True)
    seller_id = Column(String(64), nullable=True, index=True)
    status = Column(String(32), default="ACTIVE")  # 'DRAFT', 'INVITED', 'ACTIVE', 'PAYMENT_PENDING', 'COMPLETED', 'CANCELLED'
    invite_token = Column(String(64), nullable=True, index=True)
    buyer_agreed = Column(Integer, default=0)
    seller_agreed = Column(Integer, default=0)

    # Core Deal Info
    item_name = Column(String(256), nullable=False, default="Marketplace Item")
    price = Column(Float, nullable=False, default=0.0)
    currency = Column(String(8), default="USD")
    chat_text = Column(Text, nullable=False, default="")
    source_type = Column(String(32), default="in_app_room")  # 'in_app_room', 'text_paste', 'screenshot'

    # Initial Analysis Results
    initial_risk_score = Column(Integer, default=0)
    risk_score = Column(Integer, default=0)
    verdict = Column(String(16), default="LOW")  # 'LOW', 'MEDIUM', 'HIGH'
    model_probability = Column(Float, default=0.0)
    explanation = Column(Text, default="")
    rules_triggered_json = Column(Text, default="[]")
    highlighted_phrases_json = Column(Text, default="[]")

    # Protection & PayPal Sandbox Orders v2
    paypal_order_id = Column(String(128), nullable=True)
    paypal_approval_url = Column(Text, nullable=True)
    paypal_status = Column(String(32), default="NOT_STARTED")  # 'NOT_STARTED', 'CREATED', 'APPROVED', 'COMPLETED', 'FAILED'
    paypal_capture_id = Column(String(128), nullable=True)
    drafted_message = Column(Text, nullable=True)

    # Seller Reaction Test
    seller_reply_text = Column(Text, nullable=True)
    seller_classification = Column(String(64), nullable=True)
    seller_confidence = Column(Float, nullable=True)
    seller_litmus_verdict = Column(String(32), nullable=True)  # 'PASSED', 'WARNING', 'FAILED'
    seller_risk_delta = Column(Integer, default=0)

    # Chronological Audit Timeline
    timeline_json = Column(Text, default="[]")

    def to_dict(self):
        return {
            "id": self.id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "buyer_id": self.buyer_id,
            "seller_id": self.seller_id,
            "status": self.status,
            "invite_token": self.invite_token,
            "buyer_agreed": bool(self.buyer_agreed),
            "seller_agreed": bool(self.seller_agreed),
            "item_name": self.item_name,
            "price": self.price,
            "currency": self.currency,
            "chat_text": self.chat_text,
            "source_type": self.source_type,
            "initial_risk_score": self.initial_risk_score,
            "risk_score": self.risk_score,
            "verdict": self.verdict,
            "model_probability": self.model_probability,
            "explanation": self.explanation,
            "rules_triggered": json.loads(self.rules_triggered_json or "[]"),
            "highlighted_phrases": json.loads(self.highlighted_phrases_json or "[]"),
            "paypal_order_id": self.paypal_order_id,
            "paypal_approval_url": self.paypal_approval_url,
            "paypal_status": self.paypal_status,
            "paypal_capture_id": self.paypal_capture_id,
            "drafted_message": self.drafted_message,
            "seller_reply_text": self.seller_reply_text,
            "seller_classification": self.seller_classification,
            "seller_confidence": self.seller_confidence,
            "seller_litmus_verdict": self.seller_litmus_verdict,
            "seller_risk_delta": self.seller_risk_delta,
            "timeline": json.loads(self.timeline_json or "[]")
        }

    def append_timeline_event(self, event_type: str, title: str, description: str):
        events = json.loads(self.timeline_json or "[]")
        events.append({
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "type": event_type,
            "title": title,
            "description": description
        })
        self.timeline_json = json.dumps(events)

class DealInvite(Base):
    __tablename__ = "invites"

    id = Column(String(64), primary_key=True, index=True)
    deal_id = Column(String(64), nullable=False, index=True)
    token = Column(String(64), unique=True, nullable=False, index=True)
    status = Column(String(32), default="SENT")  # 'SENT', 'OPENED', 'JOINED', 'EXPIRED', 'DECLINED'
    expires_at = Column(DateTime, nullable=False)
    opened_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "deal_id": self.deal_id,
            "token": self.token,
            "status": self.status,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "opened_at": self.opened_at.isoformat() if self.opened_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

class EncryptedMessage(Base):
    __tablename__ = "encrypted_messages"

    id = Column(String(64), primary_key=True, index=True)
    deal_id = Column(String(64), nullable=False, index=True)
    sender_id = Column(String(64), nullable=False, index=True)
    encrypted_content = Column(Text, nullable=False)
    message_type = Column(String(32), default="chat")  # 'chat', 'system', 'paypal_card', 'alert', 'typing'
    is_private_to_buyer = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    def to_dict(self, decrypted_text=None, sender_name=None):
        return {
            "id": self.id,
            "deal_id": self.deal_id,
            "sender_id": self.sender_id,
            "sender_name": sender_name,
            "content": decrypted_text if decrypted_text is not None else "[Encrypted Payload]",
            "message_type": self.message_type,
            "is_private_to_buyer": bool(self.is_private_to_buyer),
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
