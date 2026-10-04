"""Tests for API module."""
import pytest
from unittest.mock import Mock, patch, MagicMock


class TestTelegramAPI:
    """Tests for Telegram API functions."""

    @patch("src.api.requests.post")
    @patch("src.api.Config")
    def test_send_telegram_message_success(self, mock_config, mock_post):
        """Test successful telegram message sending."""
        from src.api import send_telegram_message

        mock_config.TELEGRAM_BOT_API = "test_token"
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        result = send_telegram_message(chat_id=123, text="Hello")
        assert result is True

    @patch("src.api.requests.post")
    @patch("src.api.Config")
    def test_send_telegram_message_failure(self, mock_config, mock_post):
        """Test failed telegram message sending."""
        from src.api import send_telegram_message, requests

        mock_config.TELEGRAM_BOT_API = "test_token"
        mock_post.side_effect = requests.RequestException("Network error")

        result = send_telegram_message(chat_id=123, text="Hello")
        assert result is False

    @patch("src.api.Config")
    def test_send_telegram_message_no_token(self, mock_config):
        """Test telegram message without token configured."""
        from src.api import send_telegram_message

        mock_config.TELEGRAM_BOT_API = ""

        result = send_telegram_message(chat_id=123, text="Hello")
        assert result is False

    @patch("src.api.requests.post")
    @patch("src.api.Config")
    def test_set_webhook_success(self, mock_config, mock_post):
        """Test successful webhook setting."""
        from src.api import set_telegram_webhook

        mock_config.TELEGRAM_BOT_API = "test_token"
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        result = set_telegram_webhook(url="https://example.com/webhook")
        assert result is True

    @patch("src.api.requests.post")
    @patch("src.api.Config")
    def test_delete_webhook_success(self, mock_config, mock_post):
        """Test successful webhook deletion."""
        from src.api import delete_telegram_webhook

        mock_config.TELEGRAM_BOT_API = "test_token"
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        result = delete_telegram_webhook()
        assert result is True


class TestLLMAPI:
    """Tests for LLM API functions."""

    @patch("src.api.requests.post")
    @patch("src.api.Config")
    def test_call_llm_success(self, mock_config, mock_post):
        """Test successful LLM call."""
        from src.api import call_llm

        mock_config.LLM_APIKEY = "test_key"
        mock_config.LLM_ENDPOINT = "https://api.test.com/chat"
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Response text"}}]
        }
        mock_post.return_value = mock_response

        result = call_llm(system_prompt="You are helpful.", user_prompt="Hello")
        assert result == "Response text"

    @patch("src.api.requests.post")
    @patch("src.api.Config")
    def test_call_llm_failure(self, mock_config, mock_post):
        """Test failed LLM call."""
        from src.api import call_llm, requests

        mock_config.LLM_APIKEY = "test_key"
        mock_config.LLM_ENDPOINT = "https://api.test.com/chat"
        mock_post.side_effect = requests.RequestException("API error")

        result = call_llm(system_prompt="You are helpful.", user_prompt="Hello")
        assert result is None

    @patch("src.api.Config")
    def test_call_llm_no_apikey(self, mock_config):
        """Test LLM call without API key."""
        from src.api import call_llm

        mock_config.LLM_APIKEY = ""

        result = call_llm(system_prompt="You are helpful.", user_prompt="Hello")
        assert result is None


class TestQdrantAPI:
    """Tests for Qdrant API functions."""

    @patch("src.api.get_qdrant_client")
    def test_create_collection_success(self, mock_get_client):
        """Test successful collection creation."""
        from src.api import create_collection

        mock_client = Mock()
        mock_get_client.return_value = mock_client

        result = create_collection(name="test_collection")
        assert result is True
        mock_client.create_collection.assert_called_once()

    @patch("src.api.get_qdrant_client")
    def test_create_collection_failure(self, mock_get_client):
        """Test failed collection creation."""
        from src.api import create_collection

        mock_client = Mock()
        mock_client.create_collection.side_effect = Exception("Error")
        mock_get_client.return_value = mock_client

        result = create_collection(name="test_collection")
        assert result is False

    @patch("src.api.get_qdrant_client")
    def test_delete_collection_success(self, mock_get_client):
        """Test successful collection deletion."""
        from src.api import delete_collection

        mock_client = Mock()
        mock_get_client.return_value = mock_client

        result = delete_collection(name="test_collection")
        assert result is True

    @patch("src.api.get_qdrant_client")
    def test_list_collections_success(self, mock_get_client):
        """Test successful collection listing."""
        from src.api import list_collections
        from qdrant_client.models import CollectionDescription, CollectionsResponse

        mock_client = Mock()
        mock_collections = [
            CollectionDescription(name="col1"),
            CollectionDescription(name="col2"),
        ]
        mock_client.get_collections.return_value = CollectionsResponse(
            collections=mock_collections
        )
        mock_get_client.return_value = mock_client

        result = list_collections()
        assert result == ["col1", "col2"]

    @patch("src.api.get_qdrant_client")
    def test_list_collections_failure(self, mock_get_client):
        """Test failed collection listing."""
        from src.api import list_collections

        mock_client = Mock()
        mock_client.get_collections.side_effect = Exception("Error")
        mock_get_client.return_value = mock_client

        result = list_collections()
        assert result == []

    @patch("src.api.get_qdrant_client")
    @patch("src.api.get_embeddings")
    def test_add_to_collection_success(self, mock_embeddings, mock_get_client):
        """Test successful data addition to collection."""
        from src.api import add_to_collection

        mock_client = Mock()
        mock_get_client.return_value = mock_client
        mock_embeddings.return_value = [[0.1, 0.2, 0.3]]

        result = add_to_collection(
            collection_name="test",
            texts=["text1"],
            payloads=[{"text": "text1"}]
        )
        assert result is True

    @patch("src.api.get_qdrant_client")
    @patch("src.api.get_embeddings")
    def test_add_to_collection_failure(self, mock_embeddings, mock_get_client):
        """Test failed data addition to collection."""
        from src.api import add_to_collection

        mock_client = Mock()
        mock_client.upsert.side_effect = Exception("Error")
        mock_get_client.return_value = mock_client
        mock_embeddings.return_value = [[0.1, 0.2, 0.3]]

        result = add_to_collection(
            collection_name="test",
            texts=["text1"],
            payloads=[{"text": "text1"}]
        )
        assert result is False

    @patch("src.api.get_qdrant_client")
    @patch("src.api.get_embeddings")
    def test_search_collection_success(self, mock_embeddings, mock_get_client):
        """Test successful collection search."""
        from src.api import search_collection
        from qdrant_client.models import ScoredPoint

        mock_client = Mock()
        mock_get_client.return_value = mock_client
        mock_embeddings.return_value = [[0.1, 0.2]]

        mock_result = Mock()
        mock_result.id = "1"
        mock_result.score = 0.9
        mock_result.payload = {"text": "Found text"}
        mock_client.search.return_value = [mock_result]

        result = search_collection(collection_name="test", query="query")
        assert len(result) == 1
        assert result[0]["text"] == "Found text"

    @patch("src.api.get_qdrant_client")
    @patch("src.api.get_embeddings")
    def test_search_collection_failure(self, mock_embeddings, mock_get_client):
        """Test failed collection search."""
        from src.api import search_collection

        mock_client = Mock()
        mock_client.search.side_effect = Exception("Error")
        mock_get_client.return_value = mock_client
        mock_embeddings.return_value = [[0.1, 0.2]]

        result = search_collection(collection_name="test", query="query")
        assert result == []


class TestEmbeddingAPI:
    """Tests for embedding API functions."""

    def test_get_embeddings_empty_texts(self):
        """Test embedding with empty texts list."""
        from src.api import get_embeddings

        result = get_embeddings([])
        assert result == []

    def test_get_embeddings_with_text(self):
        """Test embedding with actual text returns a list."""
        from src.api import get_embeddings

        result = get_embeddings(["test text"])
        # Should return a list of embeddings
        assert isinstance(result, list)
        assert len(result) == 1


class TestQdrantPointsAPI:
    """Tests for Qdrant point operations."""

    @patch("src.api.get_qdrant_client")
    def test_list_points_success(self, mock_get_client):
        """Test successful listing of points."""
        from src.api import list_points

        mock_client = Mock()
        mock_point = Mock()
        mock_point.id = "uuid-1"
        mock_point.payload = {"filename": "file1.txt", "text": "Content 1"}

        mock_client.scroll.return_value = ([mock_point], None, None)
        mock_get_client.return_value = mock_client

        result = list_points("test_collection")
        assert len(result) == 1
        assert result[0]["id"] == "uuid-1"
        assert result[0]["filename"] == "file1.txt"

    @patch("src.api.get_qdrant_client")
    def test_list_points_failure(self, mock_get_client):
        """Test failed listing of points."""
        from src.api import list_points

        mock_client = Mock()
        mock_client.scroll.side_effect = Exception("Error")
        mock_get_client.return_value = mock_client

        result = list_points("test_collection")
        assert result == []

    @patch("src.api.get_qdrant_client")
    def test_get_point_success(self, mock_get_client):
        """Test successful getting a point."""
        from src.api import get_point

        mock_client = Mock()
        mock_point = Mock()
        mock_point.id = "uuid-1"
        mock_point.payload = {"filename": "file1.txt", "text": "Content 1"}

        mock_client.retrieve.return_value = [mock_point]
        mock_get_client.return_value = mock_client

        result = get_point("test_collection", "uuid-1")
        assert result is not None
        assert result["id"] == "uuid-1"
        assert result["filename"] == "file1.txt"

    @patch("src.api.get_qdrant_client")
    def test_get_point_not_found(self, mock_get_client):
        """Test getting non-existent point."""
        from src.api import get_point

        mock_client = Mock()
        mock_client.retrieve.return_value = []
        mock_get_client.return_value = mock_client

        result = get_point("test_collection", "nonexistent")
        assert result is None

    @patch("src.api.get_qdrant_client")
    def test_delete_point_success(self, mock_get_client):
        """Test successful point deletion."""
        from src.api import delete_point

        mock_client = Mock()
        mock_get_client.return_value = mock_client

        result = delete_point("test_collection", "uuid-1")
        assert result is True
        mock_client.delete.assert_called_once()

    @patch("src.api.get_qdrant_client")
    def test_delete_point_failure(self, mock_get_client):
        """Test failed point deletion."""
        from src.api import delete_point

        mock_client = Mock()
        mock_client.delete.side_effect = Exception("Error")
        mock_get_client.return_value = mock_client

        result = delete_point("test_collection", "uuid-1")
        assert result is False

    @patch("src.api.get_qdrant_client")
    def test_delete_all_points_success(self, mock_get_client):
        """Test successful deletion of all points."""
        from src.api import delete_all_points

        mock_client = Mock()
        mock_get_client.return_value = mock_client

        # Mock scroll to return a tuple (points, next_page_token, None)
        mock_point = Mock()
        mock_point.id = "uuid-1"
        mock_client.scroll.return_value = ([mock_point], None, None)

        result = delete_all_points("test_collection")
        assert result is True
        mock_client.delete.assert_called_once()

    @patch("src.api.get_qdrant_client")
    def test_delete_all_points_failure(self, mock_get_client):
        """Test failed deletion of all points."""
        from src.api import delete_all_points

        mock_client = Mock()
        mock_client.delete.side_effect = Exception("Error")
        mock_get_client.return_value = mock_client

        result = delete_all_points("test_collection")
        assert result is False
