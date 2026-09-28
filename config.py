"""Configuration for the HSE Cunning Fox Bot."""
import os


class Config:
    """Main configuration class."""

    # Telegram
    TELEGRAM_BOT_API = os.getenv("TELEGRAM_BOT_API", "")
    TELEGRAM_WEBHOOK_MODE = os.getenv("TELEGRAM_WEBHOOK_MODE", "false").lower() == "true"
    TELEGRAM_WEBHOOK_URL = os.getenv("TELEGRAM_WEBHOOK_URL", "")
    PROXY_URL = os.getenv("PROXY_URL", "")

    # LLM
    LLM_APIKEY = os.getenv("LLM_APIKEY", "")
    LLM_ENDPOINT = os.getenv("LLM_ENDPOINT", "https://api.minimax.io/v1/text/chatcompletion_v2")

    # Qdrant
    QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
    QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))
    QDRANT_GRPC_PORT = int(os.getenv("QDRANT_GRPC_PORT", "6334"))

    # Embedding
    EMBEDDING_MODEL = "BAAI/bge-m3"

    # Bot settings
    AUTH_PASSWORD = os.getenv("AUTH_PASSWORD", "secret_password")
    ADMIN_USER_IDS = os.getenv("ADMIN_USER_IDS", "").split(",")

    # Polling/Webhook
    USE_WEBHOOK = os.getenv("USE_WEBHOOK", "false").lower() == "true"
