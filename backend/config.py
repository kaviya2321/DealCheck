import os
from pathlib import Path
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load .env file from project root or backend dir
ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(ROOT_DIR / ".env")

class Settings(BaseSettings):
    PROJECT_NAME: str = "DealCheck API"
    VERSION: str = "1.0.0"

    # PayPal Settings
    PAYPAL_CLIENT_ID: str = os.getenv("PAYPAL_CLIENT_ID", "")
    PAYPAL_CLIENT_SECRET: str = os.getenv("PAYPAL_CLIENT_SECRET", "")
    PAYPAL_ENV: str = os.getenv("PAYPAL_ENV", "sandbox")
    PAYPAL_API_BASE: str = os.getenv(
        "PAYPAL_API_BASE",
        "https://api-m.sandbox.paypal.com" if os.getenv("PAYPAL_ENV", "sandbox") == "sandbox" else "https://api-m.paypal.com"
    )

    # Gemini Settings
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

    # Application URLs
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:5173")
    BACKEND_URL: str = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")

    # Database
    DB_PATH: str = os.getenv("DB_PATH", str(ROOT_DIR / "dealcheck.db"))

    # Security & Auth
    JWT_SECRET: str = os.getenv("JWT_SECRET", "4b7306809114e44c97c36f6cda181f6012e638fdde4d4f851f1d602f7be46374")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "4320"))

    # Chat Message Encryption at Rest
    CHAT_ENC_KEY: str = os.getenv("CHAT_ENC_KEY", "7Z4IFMJx26yVNKtfeaPLbO20X3ejjgyMaHuqgBtiM7c=")

    # File Paths
    BASE_DIR: Path = ROOT_DIR
    ML_DIR: Path = ROOT_DIR / "ml"
    MODELS_DIR: Path = ROOT_DIR / "ml" / "models"
    REPORTS_DIR: Path = ROOT_DIR / "ml" / "reports"

    class Config:
        case_sensitive = True

settings = Settings()
