"""Configuration for the HSE Cunning Fox Bot."""
import os


class Config:
    """Main configuration class."""

    # Telegram
    TELEGRAM_BOT_API = os.getenv("TELEGRAM_BOT_API", "")
    TELEGRAM_WEBHOOK_URL = os.getenv("TELEGRAM_WEBHOOK_URL", "")
    TELEGRAM_WEBHOOK_SECRET = os.getenv("TELEGRAM_WEBHOOK_SECRET", "")
    PROXY_URL = os.getenv("PROXY_URL", "")

    # LLM
    LLM_APIKEY = os.getenv("LLM_APIKEY", "")
    LLM_ENDPOINT = os.getenv("LLM_ENDPOINT", "https://api.minimax.io/v1/text/chatcompletion_v2")
    LLM_MODEL = os.getenv("LLM_MODEL", "MiniMax-Text-01")

    # Qdrant
    QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
    QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))
    QDRANT_GRPC_PORT = int(os.getenv("QDRANT_GRPC_PORT", "6334"))

    # PostgreSQL
    POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
    POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", "5432"))
    POSTGRES_DB = os.getenv("POSTGRES_DB", "hse_bot")
    POSTGRES_USER = os.getenv("POSTGRES_USER", "hse_bot")
    POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "secret_password")

    @property
    def DATABASE_URL(self) -> str:
        """Get SQLAlchemy database URL."""
        return (
            f"postgresql+psycopg2://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    # Embedding
    EMBEDDING_MODEL = "BAAI/bge-m3"

    # Bot settings
    AUTH_PASSWORD = os.getenv("AUTH_PASSWORD", "secret_password")
    ADMIN_USER_IDS = os.getenv("ADMIN_USER_IDS", "").split(",")

    # Polling/Webhook
    USE_WEBHOOK = os.getenv("USE_WEBHOOK", "false").lower() == "true"
