"""
Crypto and Security Service for DealCheck.
- Password hashing and verification via bcrypt.
- Message encryption at rest using Fernet (AES-128-CBC with HMAC-SHA256).
- JWT session token generation and verification.
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import bcrypt
import jwt
from cryptography.fernet import Fernet, InvalidToken
from config import settings

class CryptoService:
    def __init__(self):
        # Initialize Fernet cipher for message encryption at rest
        raw_key = settings.CHAT_ENC_KEY.strip()
        if not raw_key:
            # Fallback to deterministic development key if not specified
            raw_key = Fernet.generate_key().decode()
        self.fernet = Fernet(raw_key.encode() if isinstance(raw_key, str) else raw_key)
        self.jwt_secret = settings.JWT_SECRET
        self.jwt_algorithm = settings.JWT_ALGORITHM
        self.expire_minutes = settings.ACCESS_TOKEN_EXPIRE_MINUTES

    # ---------------------------------------------------------
    # Password Hashing
    # ---------------------------------------------------------
    def hash_password(self, password: str) -> str:
        """Hashes password with bcrypt and salt."""
        pwd_bytes = password.encode("utf-8")
        salt = bcrypt.gensalt(rounds=12)
        hashed = bcrypt.hashpw(pwd_bytes, salt)
        return hashed.decode("utf-8")

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verifies plain password against stored bcrypt hash."""
        try:
            return bcrypt.checkpw(
                plain_password.encode("utf-8"),
                hashed_password.encode("utf-8")
            )
        except Exception:
            return False

    # ---------------------------------------------------------
    # Message Encryption at Rest (Fernet)
    # ---------------------------------------------------------
    def encrypt_message(self, plain_text: str) -> str:
        """
        Encrypts chat message for storage in database.
        Returns URL-safe base64 string.
        """
        if not plain_text:
            return ""
        encrypted_bytes = self.fernet.encrypt(plain_text.encode("utf-8"))
        return encrypted_bytes.decode("utf-8")

    def decrypt_message(self, cipher_text: str) -> str:
        """
        Decrypts message in-memory for authorized participants.
        """
        if not cipher_text:
            return ""
        try:
            decrypted_bytes = self.fernet.decrypt(cipher_text.encode("utf-8"))
            return decrypted_bytes.decode("utf-8")
        except InvalidToken:
            return "[Decryption Error: Invalid Key]"

    # ---------------------------------------------------------
    # JWT Authentication
    # ---------------------------------------------------------
    def create_jwt_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Generates signed JWT token."""
        to_encode = data.copy()
        expire = datetime.utcnow() + (expires_delta or timedelta(minutes=self.expire_minutes))
        to_encode.update({"exp": expire, "iat": datetime.utcnow()})
        return jwt.encode(to_encode, self.jwt_secret, algorithm=self.jwt_algorithm)

    def decode_jwt_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Validates and decodes JWT token. Returns payload or None if invalid/expired."""
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=[self.jwt_algorithm])
            return payload
        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
            return None

crypto_service = CryptoService()
