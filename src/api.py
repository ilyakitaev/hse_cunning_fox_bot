"""API layer - low level functions for Telegram, LLM, Qdrant."""
import logging
import requests
from typing import Optional
from config import Config

logger = logging.getLogger(__name__)


# ============ Telegram API ============


def send_telegram_message(chat_id: int, text: str, parse_mode: str = "Markdown") -> bool:
    """Send a message to a Telegram chat."""
    if not Config.TELEGRAM_BOT_API:
        logger.error("TELEGRAM_BOT_API not configured")
        return False

    url = f"https://api.telegram.org/bot{Config.TELEGRAM_BOT_API}/sendMessage"
    data = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": parse_mode
    }

    try:
        response = requests.post(url, json=data, timeout=30)
        response.raise_for_status()
        return True
    except requests.RequestException as e:
        logger.error(f"Failed to send telegram message: {e}")
        return False


def set_telegram_webhook(url: str) -> bool:
    """Set Telegram webhook."""
    if not Config.TELEGRAM_BOT_API:
        logger.error("TELEGRAM_BOT_API not configured")
        return False

    webhook_url = f"https://api.telegram.org/bot{Config.TELEGRAM_BOT_API}/setWebhook"
    data = {"url": url}

    try:
        response = requests.post(webhook_url, json=data, timeout=30)
        response.raise_for_status()
        return True
    except requests.RequestException as e:
        logger.error(f"Failed to set webhook: {e}")
        return False


def delete_telegram_webhook() -> bool:
    """Delete Telegram webhook."""
    if not Config.TELEGRAM_BOT_API:
        return False

    url = f"https://api.telegram.org/bot{Config.TELEGRAM_BOT_API}/deleteWebhook"

    try:
        response = requests.post(url, timeout=30)
        response.raise_for_status()
        return True
    except requests.RequestException as e:
        logger.error(f"Failed to delete webhook: {e}")
        return False


# ============ LLM API ============


def call_llm(
    system_prompt: str,
    user_prompt: str,
    model: str = "abab6.5s-chat"
) -> Optional[str]:
    """Call LLM API with system and user prompts."""
    if not Config.LLM_APIKEY:
        logger.error("LLM_APIKEY not configured")
        return None

    url = Config.LLM_ENDPOINT
    headers = {
        "Authorization": f"Bearer {Config.LLM_APIKEY}",
        "Content-Type": "application/json"
    }

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]

    data = {
        "model": model,
        "messages": messages,
        "temperature": 0.7
    }

    try:
        response = requests.post(url, json=data, headers=headers, timeout=120)
        response.raise_for_status()
        result = response.json()
        return result.get("choices", [{}])[0].get("message", {}).get("content")
    except requests.RequestException as e:
        logger.error(f"Failed to call LLM: {e}")
        return None


# ============ Qdrant API ============


def get_qdrant_client():
    """Get Qdrant client."""
    try:
        from qdrant_client import QdrantClient
        return QdrantClient(host=Config.QDRANT_HOST, port=Config.QDRANT_PORT)
    except ImportError:
        logger.error("qdrant-client not installed")
        return None


def create_collection(name: str, vector_size: int = 1024) -> bool:
    """Create a Qdrant collection."""
    client = get_qdrant_client()
    if not client:
        return False

    try:
        from qdrant_client.models import Distance, VectorParams
        client.create_collection(
            collection_name=name,
            vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE)
        )
        return True
    except Exception as e:
        logger.error(f"Failed to create collection: {e}")
        return False


def delete_collection(name: str) -> bool:
    """Delete a Qdrant collection."""
    client = get_qdrant_client()
    if not client:
        return False

    try:
        client.delete_collection(collection_name=name)
        return True
    except Exception as e:
        logger.error(f"Failed to delete collection: {e}")
        return False


def list_collections() -> list:
    """List all Qdrant collections."""
    client = get_qdrant_client()
    if not client:
        return []

    try:
        collections = client.get_collections()
        return [c.name for c in collections.collections]
    except Exception as e:
        logger.error(f"Failed to list collections: {e}")
        return []


def add_to_collection(
    collection_name: str,
    texts: list,
    payloads: Optional[list] = None
) -> bool:
    """Add texts to a Qdrant collection."""
    client = get_qdrant_client()
    if not client:
        return False

    try:
        from qdrant_client.models import PointStruct
        import uuid

        embeddings = get_embeddings(texts)
        if not embeddings:
            return False

        points = []
        for i, (text, embedding) in enumerate(zip(texts, embeddings)):
            point = PointStruct(
                id=str(uuid.uuid4()),
                vector=embedding,
                payload=payloads[i] if payloads else {"text": text}
            )
            points.append(point)

        client.upsert(collection_name=collection_name, points=points)
        return True
    except Exception as e:
        logger.error(f"Failed to add to collection: {e}")
        return False


def search_collection(
    collection_name: str,
    query: str,
    limit: int = 5
) -> list:
    """Search a Qdrant collection."""
    client = get_qdrant_client()
    if not client:
        return []

    try:
        query_embedding = get_embeddings([query])
        if not query_embedding:
            return []

        results = client.search(
            collection_name=collection_name,
            query_vector=query_embedding[0],
            limit=limit
        )
        return [
            {
                "id": r.id,
                "score": r.score,
                "text": r.payload.get("text", ""),
                "metadata": r.payload
            }
            for r in results
        ]
    except Exception as e:
        logger.error(f"Failed to search collection: {e}")
        return []


# ============ Embedding API ============


def get_embeddings(texts: list) -> list:
    """Get embeddings for texts using BAAI/bge-m3."""
    try:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer("BAAI/bge-m3")
        embeddings = model.encode(texts, normalize_embeddings=True)
        return embeddings.tolist()
    except ImportError:
        logger.error("sentence-transformers not installed")
        return []
    except Exception as e:
        logger.error(f"Failed to get embeddings: {e}")
        return []
