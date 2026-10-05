"""API layer - low level functions for Telegram, LLM, Qdrant."""
import logging
import os
import requests
from typing import Optional
from config import Config

log_level = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, log_level, logging.INFO),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


def _get_telegram_proxy_dict() -> Optional[dict]:
    """Get proxy dict for Telegram requests."""
    if Config.PROXY_URL:
        return {"http": Config.PROXY_URL, "https": Config.PROXY_URL}
    return None


# ============ Telegram API ============


def send_telegram_message(chat_id: int, text: str, parse_mode: str = None) -> bool:
    """Send a message to a Telegram chat."""
    if not Config.TELEGRAM_BOT_API:
        logger.error("TELEGRAM_BOT_API not configured")
        return False

    url = f"https://api.telegram.org/bot{Config.TELEGRAM_BOT_API}/sendMessage"
    data = {
        "chat_id": chat_id,
        "text": text,
    }
    if parse_mode:
        data["parse_mode"] = parse_mode

    proxies = _get_telegram_proxy_dict()

    try:
        response = requests.post(url, json=data, timeout=30, proxies=proxies)
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

    proxies = _get_telegram_proxy_dict()

    try:
        response = requests.post(webhook_url, json=data, timeout=30, proxies=proxies)
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

    proxies = _get_telegram_proxy_dict()

    try:
        response = requests.post(url, timeout=30, proxies=proxies)
        response.raise_for_status()
        return True
    except requests.RequestException as e:
        logger.error(f"Failed to delete webhook: {e}")
        return False


# ============ LLM API ============


def call_llm(
    system_prompt: str,
    user_prompt: str,
    model: str = None
) -> Optional[str]:
    """Call LLM API with system and user prompts."""
    if not Config.LLM_APIKEY:
        logger.error("LLM_APIKEY not configured")
        return None

    # Use config model if not specified
    if model is None:
        model = Config.LLM_MODEL

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
        # Debug: log the full response
        logger.debug(f"LLM response: {result}")

        # Handle different response formats
        if not result:
            logger.error("Empty response from LLM")
            return None

        choices = result.get("choices")
        if not choices:
            logger.error(f"No choices in LLM response: {result}")
            return None

        first_choice = choices[0] if choices else {}
        if not first_choice:
            logger.error(f"Empty choice in LLM response: {result}")
            return None

        message = first_choice.get("message")
        if not message:
            # Try alternative format
            message = first_choice.get("text")

        if not message:
            logger.error(f"No message in LLM choice: {result}")
            return None

        return message.get("content") if isinstance(message, dict) else message
    except requests.RequestException as e:
        logger.error(f"Failed to call LLM: {e}")
        return None
    except (KeyError, IndexError, TypeError) as e:
        logger.error(f"Failed to parse LLM response: {e}")
        return None


# ============ Qdrant API ============


def get_qdrant_client():
    """Get Qdrant client."""
    try:
        from qdrant_client import QdrantClient
        return QdrantClient(
            host=Config.QDRANT_HOST,
            port=Config.QDRANT_PORT,
        )
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
    """Search a Qdrant collection using native similarity search."""
    client = get_qdrant_client()
    if not client:
        return []

    try:
        query_embedding = get_embeddings([query])
        if not query_embedding:
            return []

        # Use Qdrant's native search for server-side similarity computation
        results = client.search(
            collection_name=collection_name,
            query_vector=query_embedding[0],
            limit=limit,
            with_payload=True,
            with_vectors=False,
        )

        logger.debug(f"Retrieved {len(results)} documents from collection '{collection_name}'")

        return [
            {
                "id": str(point.id),
                "score": point.score,
                "text": point.payload.get("text", ""),
                "metadata": point.payload
            }
            for point in results
        ]

    except Exception as e:
        logger.error(f"Failed to search collection: {e}")
        return []


# ============ Embedding API ============

# Global model cache
_embedding_model = None


def _get_embedding_model():
    """Get or create cached embedding model."""
    global _embedding_model
    if _embedding_model is None:
        from sentence_transformers import SentenceTransformer
        # Use HF cache directory - set via HF_HOME env var
        # Default cache is ~/.cache/huggingface which is mounted to volume
        model_name = "BAAI/bge-m3"
        logger.info(f"Loading embedding model: {model_name}")
        _embedding_model = SentenceTransformer(model_name)
        logger.info(f"Embedding model loaded successfully")
    return _embedding_model


def get_embeddings(texts: list) -> list:
    """Get embeddings for texts using BAAI/bge-m3."""
    if not texts:
        return []

    try:
        model = _get_embedding_model()
        embeddings = model.encode(texts, normalize_embeddings=True)
        return embeddings.tolist()
    except ImportError:
        logger.error("sentence-transformers not installed")
        return []
    except Exception as e:
        logger.error(f"Failed to get embeddings: {e}")
        return []


# ============ Qdrant Point Operations ============


def list_points(collection_name: str) -> list:
    """List all points in a collection."""
    client = get_qdrant_client()
    if not client:
        return []

    try:
        # Use scroll to get all points
        scroll_result = client.scroll(
            collection_name=collection_name,
            limit=100,
            with_payload=True,
            with_vectors=False,
        )

        # Handle different return types from qdrant-client
        if isinstance(scroll_result, tuple):
            results = scroll_result[0] if scroll_result[0] is not None else []
        elif isinstance(scroll_result, list):
            results = scroll_result
        else:
            results = []

        if not results:
            return []

        return [
            {
                "id": point.id,
                "filename": point.payload.get("filename", ""),
                "payload": point.payload.get("text", ""),
            }
            for point in results
        ]
    except Exception as e:
        logger.error(f"Failed to list points: {e}")
        return []


def get_point(collection_name: str, point_id: str) -> Optional[dict]:
    """Get a single point by ID."""
    client = get_qdrant_client()
    if not client:
        return None

    try:
        results = client.retrieve(
            collection_name=collection_name,
            ids=[point_id],
            with_payload=True,
            with_vectors=False,
        )
        if not results:
            return None

        point = results[0]
        return {
            "id": point.id,
            "filename": point.payload.get("filename", ""),
            "payload": point.payload.get("text", ""),
        }
    except Exception as e:
        logger.error(f"Failed to get point: {e}")
        return None


def delete_point(collection_name: str, point_id: str) -> bool:
    """Delete a single point by ID."""
    client = get_qdrant_client()
    if not client:
        return False

    try:
        from qdrant_client.models import PointIdsList
        client.delete(
            collection_name=collection_name,
            points_selector=PointIdsList(points=[point_id]),
        )
        return True
    except Exception as e:
        logger.error(f"Failed to delete point: {e}")
        return False


def delete_all_points(collection_name: str) -> bool:
    """Delete all points from a collection."""
    client = get_qdrant_client()
    if not client:
        return False

    try:
        from qdrant_client.models import PointIdsList
        # Get all point IDs first
        scroll_result = client.scroll(
            collection_name=collection_name,
            limit=10000,
            with_payload=False,
            with_vectors=False,
        )
        all_points = scroll_result[0] if scroll_result else []
        point_ids = [point.id for point in all_points]

        if point_ids:
            client.delete(
                collection_name=collection_name,
                points_selector=PointIdsList(points=point_ids),
            )
        return True
    except Exception as e:
        logger.error(f"Failed to delete all points: {e}")
        return False
