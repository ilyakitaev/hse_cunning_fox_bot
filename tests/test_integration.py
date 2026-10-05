"""Integration tests for bot commands - run against actual services."""
import pytest
import os
import sys

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.business_logic import (
    cmd_start,
    cmd_auth,
    cmd_help,
    cmd_list_assistants,
    cmd_assist,
    cmd_database_list,
    cmd_database_create,
    cmd_prompt_list,
    cmd_prompt_create,
    cmd_prompt_show,
    cmd_prompt_update,
    cmd_assistant_create,
    query_assistant,
    get_selected_assistant,
    check_auth,
    init_database,
    is_user_authorized,
    authorize_user,
    get_all_assistants,
    get_all_collections,
    get_all_prompts,
    get_prompt_by_id,
    get_prompt_by_name,
    update_prompt,
    create_prompt,
    get_collection_by_name,
    create_db_assistant,
    create_db_collection,
    list_qdrant_collections,
    create_qdrant_collection,
    send_telegram_message,
    cmd_data_list,
    cmd_data_show,
    cmd_data_remove,
    cmd_data_remove_all,
    cmd_data_add_bulk_start,
    cmd_data_bulk_done,
    _data_bulk_state,
    _selected_assistant_state,
)
from config import Config


# Test fixtures
TEST_CHAT_ID = 123456789
TEST_USER_ID = 123456789


# ============ Mock Helpers ============


def create_mock_embeddings():
    """Create mock embeddings function that returns random vectors."""
    import numpy as np

    def mock_get_embeddings(texts):
        return [np.random.rand(1024).tolist() for _ in texts]

    return mock_get_embeddings


def create_mock_llm(response: str = "Test response"):
    """Create mock LLM function that returns fixed response."""
    def mock_call_llm(system_prompt: str, user_prompt: str) -> str:
        return response

    return mock_call_llm


class TestIntegrationSetup:
    """Test database initialization."""

    def test_init_database(self):
        """Test database tables are created."""
        # This should not raise
        init_database()
        # Tables exist if we get here


class TestPublicCommands:
    """Integration tests for public commands."""

    def test_cmd_start(self, monkeypatch):
        """Test /start command."""
        # Mock telegram sending
        calls = []
        monkeypatch.setattr("src.business_logic.send_telegram_message", lambda chat_id, text: calls.append((chat_id, text)))

        result = cmd_start(chat_id=TEST_CHAT_ID, user_id=TEST_USER_ID)
        assert "Welcome" in result or len(calls) > 0

    def test_cmd_help(self, monkeypatch):
        """Test /help command."""
        calls = []
        monkeypatch.setattr("src.business_logic.send_telegram_message", lambda chat_id, text: calls.append((chat_id, text)))

        result = cmd_help(chat_id=TEST_CHAT_ID)
        # Help should work even without help.md
        assert result is not None

    def test_cmd_auth_success(self, monkeypatch):
        """Test /auth with correct password."""
        calls = []
        monkeypatch.setattr("src.business_logic.send_telegram_message", lambda chat_id, text: calls.append((chat_id, text)))

        result = cmd_auth(chat_id=TEST_CHAT_ID, user_id=TEST_USER_ID, password=Config.AUTH_PASSWORD)
        assert "success" in result.lower() or "authorized" in result.lower()

        # Verify user is now authorized
        assert is_user_authorized(TEST_USER_ID) is True

    def test_cmd_auth_failure(self, monkeypatch):
        """Test /auth with wrong password."""
        calls = []
        monkeypatch.setattr("src.business_logic.send_telegram_message", lambda chat_id, text: calls.append((chat_id, text)))

        # Use a different user for this test
        result = cmd_auth(chat_id=TEST_CHAT_ID, user_id=999999, password="wrong_password")
        assert "failed" in result.lower() or "incorrect" in result.lower() or "wrong" in result.lower()


class TestAuthorizedCommands:
    """Integration tests for authorized commands."""

    @pytest.fixture(autouse=True)
    def setup_authorized(self):
        """Ensure user is authorized for tests."""
        # Authorize test user
        authorize_user(TEST_USER_ID)
        yield
        # Cleanup after tests if needed

    def test_cmd_collections_empty(self, monkeypatch):
        """Test /collections when empty."""
        calls = []
        monkeypatch.setattr("src.business_logic.send_telegram_message", lambda chat_id, text: calls.append((chat_id, text)))

        result = cmd_database_list(chat_id=TEST_CHAT_ID)
        # Should return some message about collections
        assert result is not None

    def test_cmd_collection_create(self, monkeypatch):
        """Test /collection_create."""
        calls = []
        monkeypatch.setattr("src.business_logic.send_telegram_message", lambda chat_id, text: calls.append((chat_id, text)))

        # Use timestamp for unique name
        import time
        test_collection_name = f"test_collection_{TEST_USER_ID}_{int(time.time())}"

        # Clean up if exists
        from src.api import delete_collection
        delete_collection(test_collection_name)

        # Let command create the Qdrant collection itself
        result = cmd_database_create(chat_id=TEST_CHAT_ID, name=test_collection_name)
        assert "created" in result.lower() or "success" in result.lower()

    def test_cmd_prompts_empty(self, monkeypatch):
        """Test /prompts when empty."""
        calls = []
        monkeypatch.setattr("src.business_logic.send_telegram_message", lambda chat_id, text: calls.append((chat_id, text)))

        result = cmd_prompt_list(chat_id=TEST_CHAT_ID)
        assert result is not None

    def test_cmd_prompt_create(self, monkeypatch):
        """Test /prompt_create."""
        calls = []
        monkeypatch.setattr("src.business_logic.send_telegram_message", lambda chat_id, text: calls.append((chat_id, text)))

        result = cmd_prompt_create(
            chat_id=TEST_CHAT_ID,
            user_id=TEST_USER_ID,
            name=f"test_prompt_{TEST_USER_ID}",
            content="This is a test prompt content"
        )
        assert "created" in result.lower() or "success" in result.lower()

    def test_cmd_prompt_show_by_id(self, monkeypatch):
        """Test /prompt_show by ID."""
        calls = []
        monkeypatch.setattr("src.business_logic.send_telegram_message", lambda chat_id, text: calls.append((chat_id, text)))

        # First create a prompt
        prompt = create_prompt(
            name=f"test_prompt_show_{TEST_USER_ID}",
            prompt_data="Test content for show",
            author_username="test_user"
        )

        result = cmd_prompt_show(chat_id=TEST_CHAT_ID, prompt_identifier=str(prompt.id))
        assert result is not None

    def test_cmd_prompt_show_by_name(self, monkeypatch):
        """Test /prompt_show by name."""
        calls = []
        monkeypatch.setattr("src.business_logic.send_telegram_message", lambda chat_id, text: calls.append((chat_id, text)))

        # First create a prompt
        prompt = create_prompt(
            name=f"test_prompt_by_name_{TEST_USER_ID}",
            prompt_data="Test content by name",
            author_username="test_user"
        )

        result = cmd_prompt_show(chat_id=TEST_CHAT_ID, prompt_identifier=prompt.name)
        assert result is not None
        assert "Test content by name" in result

    def test_cmd_prompt_update(self, monkeypatch):
        """Test /prompt_update."""
        calls = []
        monkeypatch.setattr("src.business_logic.send_telegram_message", lambda chat_id, text: calls.append((chat_id, text)))

        # First create a prompt
        prompt = create_prompt(
            name=f"test_prompt_update_{TEST_USER_ID}",
            prompt_data="Original content",
            author_username="test_user"
        )

        result = cmd_prompt_update(chat_id=TEST_CHAT_ID, prompt_id=str(prompt.id), content="Updated content")
        assert "updated" in result.lower() or "success" in result.lower()

    def test_cmd_assistants_empty(self, monkeypatch):
        """Test /assistants when empty."""
        calls = []
        monkeypatch.setattr("src.business_logic.send_telegram_message", lambda chat_id, text: calls.append((chat_id, text)))

        result = cmd_list_assistants(chat_id=TEST_CHAT_ID)
        assert result is not None

    def test_cmd_assist_select(self, monkeypatch):
        """Test /assist selects an assistant."""
        calls = []
        monkeypatch.setattr("src.business_logic.send_telegram_message", lambda chat_id, text: calls.append((chat_id, text)))

        # Clear state
        _selected_assistant_state.clear()

        # First create an assistant
        prompt = create_prompt(
            name=f"test_prompt_{TEST_USER_ID}",
            prompt_data="Test prompt",
            author_username="test"
        )

        # Create collection in DB
        collection = get_collection_by_name("test_collection")
        if not collection:
            collection = create_db_collection("test_collection")

        # Create assistant
        assistant = create_db_assistant("TestBot", collection.id, prompt.id)

        result = cmd_assist(chat_id=TEST_CHAT_ID, user_id=TEST_USER_ID, assistant_name="TestBot")
        assert result is not None
        assert TEST_USER_ID in _selected_assistant_state

    def test_cmd_assist_show_current(self, monkeypatch):
        """Test /assist shows current selection."""
        calls = []
        monkeypatch.setattr("src.business_logic.send_telegram_message", lambda chat_id, text: calls.append((chat_id, text)))

        # Set selected assistant
        _selected_assistant_state.clear()

        # First create an assistant
        prompt = create_prompt(
            name=f"test_prompt_{TEST_USER_ID}",
            prompt_data="Test prompt",
            author_username="test"
        )

        # Create collection in DB
        collection = get_collection_by_name("test_collection")
        if not collection:
            collection = create_db_collection("test_collection")

        # Create assistant
        assistant = create_db_assistant("TestBot", collection.id, prompt.id)

        # Select the assistant
        _selected_assistant_state[TEST_USER_ID] = assistant.id

        result = cmd_assist(chat_id=TEST_CHAT_ID, user_id=TEST_USER_ID, assistant_name=None)
        assert "TestBot" in result


class TestQdrantIntegration:
    """Test Qdrant integration directly."""

    def test_list_collections(self):
        """Test listing Qdrant collections."""
        collections = list_qdrant_collections()
        assert isinstance(collections, list)

    def test_create_collection(self):
        """Test creating a Qdrant collection."""
        import time
        test_name = f"integration_test_{TEST_USER_ID}_{int(time.time())}"

        result = create_qdrant_collection(test_name)
        assert result is True

        # Verify it exists
        collections = list_qdrant_collections()
        assert test_name in collections


class TestDatabaseIntegration:
    """Test database operations directly."""

    def test_get_all_collections(self):
        """Test getting all collections from database."""
        collections = get_all_collections()
        assert isinstance(collections, list)

    def test_get_all_prompts(self):
        """Test getting all prompts from database."""
        prompts = get_all_prompts()
        assert isinstance(prompts, list)

    def test_get_all_assistants(self):
        """Test getting all assistants from database."""
        assistants = get_all_assistants()
        assert isinstance(assistants, list)

    def test_check_auth(self):
        """Test authorization check."""
        # Authorized user should return True
        authorize_user(TEST_USER_ID)
        assert check_auth(TEST_USER_ID) is True


class TestErrorHandling:
    """Test error handling."""

    def test_prompt_show_not_found(self, monkeypatch):
        """Test /prompt_show with non-existent prompt."""
        calls = []
        monkeypatch.setattr("src.business_logic.send_telegram_message", lambda chat_id, text: calls.append((chat_id, text)))

        result = cmd_prompt_show(chat_id=TEST_CHAT_ID, prompt_identifier="999999")
        assert "not found" in result.lower() or "error" in result.lower()

    def test_prompt_show_not_found_by_name(self, monkeypatch):
        """Test /prompt_show with non-existent prompt name."""
        calls = []
        monkeypatch.setattr("src.business_logic.send_telegram_message", lambda chat_id, text: calls.append((chat_id, text)))

        result = cmd_prompt_show(chat_id=TEST_CHAT_ID, prompt_identifier="nonexistent_prompt_name")
        assert "not found" in result.lower() or "error" in result.lower()

    def test_prompt_update_not_found(self, monkeypatch):
        """Test /prompt_update with non-existent prompt."""
        calls = []
        monkeypatch.setattr("src.business_logic.send_telegram_message", lambda chat_id, text: calls.append((chat_id, text)))

        result = cmd_prompt_update(chat_id=TEST_CHAT_ID, prompt_id="999999", content="New content")
        assert "not found" in result.lower() or "error" in result.lower()

    def test_collection_create_duplicate(self, monkeypatch):
        """Test creating duplicate collection."""
        calls = []
        monkeypatch.setattr("src.business_logic.send_telegram_message", lambda chat_id, text: calls.append((chat_id, text)))

        # Create a collection first
        test_name = f"duplicate_test_{TEST_USER_ID}"
        cmd_database_create(chat_id=TEST_CHAT_ID, name=test_name)

        # Try to create again - should handle gracefully
        result = cmd_database_create(chat_id=TEST_CHAT_ID, name=test_name)
        # Should either succeed (idempotent) or indicate already exists
        assert result is not None


class TestDataCommandsIntegration:
    """Integration tests for data management commands."""

    @pytest.fixture(autouse=True)
    def setup_authorized(self):
        """Ensure user is authorized for tests."""
        authorize_user(TEST_USER_ID)
        # Clear bulk state before each test
        _data_bulk_state.clear()
        yield
        # Clear bulk state after each test
        _data_bulk_state.clear()

    def test_cmd_data_list_empty(self, monkeypatch):
        """Test /data_list when no records exist."""
        calls = []
        monkeypatch.setattr("src.business_logic.send_telegram_message", lambda chat_id, text: calls.append((chat_id, text)))

        # Use a unique test collection
        import time
        test_collection = f"test_data_{TEST_USER_ID}_{int(time.time())}"
        create_qdrant_collection(test_collection)

        result = cmd_data_list(chat_id=TEST_CHAT_ID, collection_name=test_collection)
        assert result is not None

    def test_cmd_data_list_with_data(self, monkeypatch):
        """Test /data_list with records."""
        calls = []
        monkeypatch.setattr("src.business_logic.send_telegram_message", lambda chat_id, text: calls.append((chat_id, text)))

        # Create a test collection with data
        import time
        test_collection = f"test_data_{TEST_USER_ID}_{int(time.time())}"
        create_qdrant_collection(test_collection)

        # Add data to the collection
        from src.api import add_to_collection
        add_to_collection(test_collection, ["Test content"], [{"filename": "test.txt"}])

        result = cmd_data_list(chat_id=TEST_CHAT_ID, collection_name=test_collection)
        assert result is not None

    def test_cmd_data_show(self, monkeypatch):
        """Test /data_show."""
        calls = []
        monkeypatch.setattr("src.business_logic.send_telegram_message", lambda chat_id, text: calls.append((chat_id, text)))

        # Create collection and add data
        import time
        test_collection = f"test_data_show_{TEST_USER_ID}_{int(time.time())}"
        create_qdrant_collection(test_collection)

        from src.api import add_to_collection
        add_to_collection(test_collection, ["Test content"], [{"filename": "show_test.txt"}])

        # List points to get ID
        from src.api import list_points
        points = list_points(test_collection)

        if points:
            result = cmd_data_show(chat_id=TEST_CHAT_ID, collection_name=test_collection, point_id=points[0]["id"])
            assert result is not None

    def test_cmd_data_remove(self, monkeypatch):
        """Test /data_remove."""
        calls = []
        monkeypatch.setattr("src.business_logic.send_telegram_message", lambda chat_id, text: calls.append((chat_id, text)))

        # Create collection and add data
        import time
        test_collection = f"test_data_remove_{TEST_USER_ID}_{int(time.time())}"
        create_qdrant_collection(test_collection)

        from src.api import add_to_collection
        add_to_collection(test_collection, ["To be removed"], [{"filename": "remove_me.txt"}])

        # List points to get ID
        from src.api import list_points
        points = list_points(test_collection)

        if points:
            result = cmd_data_remove(chat_id=TEST_CHAT_ID, collection_name=test_collection, point_id=points[0]["id"])
            assert result is not None

    def test_cmd_data_remove_all(self, monkeypatch):
        """Test /data_remove_all."""
        calls = []
        monkeypatch.setattr("src.business_logic.send_telegram_message", lambda chat_id, text: calls.append((chat_id, text)))

        # Create collection and add data
        import time
        test_collection = f"test_data_remove_all_{TEST_USER_ID}_{int(time.time())}"
        create_qdrant_collection(test_collection)

        from src.api import add_to_collection
        add_to_collection(test_collection, ["Content 1", "Content 2"], [{"filename": "f1.txt"}, {"filename": "f2.txt"}])

        result = cmd_data_remove_all(chat_id=TEST_CHAT_ID, collection_name=test_collection)
        assert result is not None

    def test_cmd_data_add_bulk_start(self, monkeypatch):
        """Test /data_add_bulk starts bulk mode."""
        calls = []
        monkeypatch.setattr("src.business_logic.send_telegram_message", lambda chat_id, text: calls.append((chat_id, text)))

        # Create collection first
        import time
        test_collection = f"test_bulk_{TEST_USER_ID}_{int(time.time())}"
        create_qdrant_collection(test_collection)

        result = cmd_data_add_bulk_start(chat_id=TEST_CHAT_ID, user_id=TEST_USER_ID, collection_name=test_collection)
        assert "bulk upload" in result.lower() or "sending" in result.lower()

    def test_cmd_data_bulk_done_empty(self, monkeypatch):
        """Test /done with no data added."""
        calls = []
        monkeypatch.setattr("src.business_logic.send_telegram_message", lambda chat_id, text: calls.append((chat_id, text)))

        # Set up state manually (no collection needed for empty)
        _data_bulk_state[TEST_USER_ID] = {"collection": "test", "files": []}

        result = cmd_data_bulk_done(user_id=TEST_USER_ID, chat_id=TEST_CHAT_ID)
        assert "no content" in result.lower() or "cancelled" in result.lower()

    def test_data_list_unauthorized(self):
        """Test /data_list requires authorization."""
        # Clear authorization - use the database module directly
        from src.database import get_session, User
        session = get_session()
        user = session.query(User).filter_by(telegram_id=TEST_USER_ID).first()
        if user:
            session.delete(user)
            session.commit()
        session.close()

        # Data commands should work via check_auth in main.py
        # This is tested via main.py handler
        assert check_auth(TEST_USER_ID) is False

    def test_cmd_data_show_not_found(self, monkeypatch):
        """Test /data_show with non-existent record."""
        calls = []
        monkeypatch.setattr("src.business_logic.send_telegram_message", lambda chat_id, text: calls.append((chat_id, text)))

        import time
        test_collection = f"test_data_notfound_{TEST_USER_ID}_{int(time.time())}"
        create_qdrant_collection(test_collection)

        result = cmd_data_show(chat_id=TEST_CHAT_ID, collection_name=test_collection, point_id="nonexistent-uuid")
        assert "not found" in result.lower()

    def test_cmd_data_remove_not_found(self, monkeypatch):
        """Test /data_remove with non-existent record."""
        calls = []
        monkeypatch.setattr("src.business_logic.send_telegram_message", lambda chat_id, text: calls.append((chat_id, text)))

        import time
        test_collection = f"test_data_remove_notfound_{TEST_USER_ID}_{int(time.time())}"
        create_qdrant_collection(test_collection)

        result = cmd_data_remove(chat_id=TEST_CHAT_ID, collection_name=test_collection, point_id="nonexistent-uuid")
        assert "not found" in result.lower()

    def test_cmd_data_bulk_with_content(self, monkeypatch):
        """Test /done with actual content added."""
        calls = []
        monkeypatch.setattr("src.business_logic.send_telegram_message", lambda chat_id, text: calls.append((chat_id, text)))

        # Create collection first
        import time
        test_collection = f"test_bulk_content_{TEST_USER_ID}_{int(time.time())}"
        create_qdrant_collection(test_collection)

        # Start bulk upload
        result_start = cmd_data_add_bulk_start(chat_id=TEST_CHAT_ID, user_id=TEST_USER_ID, collection_name=test_collection)

        # Verify bulk upload started successfully
        assert "bulk upload" in result_start.lower() or "sending" in result_start.lower()

        # Add some content directly to state
        _data_bulk_state[TEST_USER_ID]["files"] = ["Content 1", "Content 2"]

        # Finish bulk upload
        result = cmd_data_bulk_done(user_id=TEST_USER_ID, chat_id=TEST_CHAT_ID)
        assert "added" in result.lower() or "success" in result.lower()


class TestAssistantFlow:
    """Integration tests for full assistant flow."""

    def test_full_assistant_flow(self, monkeypatch):
        """Test: create assistant -> select -> query."""
        calls = []
        monkeypatch.setattr("src.business_logic.send_telegram_message", lambda chat_id, text: calls.append((chat_id, text)))

        # Mock LLM (external API), but use real embeddings
        monkeypatch.setattr("src.business_logic.call_llm", lambda system, user: "Test response")

        # Clear states
        _selected_assistant_state.clear()

        # Create prompt
        prompt = create_prompt(
            name=f"test_flow_prompt_{TEST_USER_ID}",
            prompt_data="You are a test assistant.",
            author_username="test"
        )

        # Create collection in DB
        collection = get_collection_by_name(f"test_flow_{TEST_USER_ID}")
        if not collection:
            collection = create_db_collection(f"test_flow_{TEST_USER_ID}")

        # Create assistant
        assistant = create_db_assistant("FlowTestBot", collection.id, prompt.id)

        # Select assistant
        result = cmd_assist(chat_id=TEST_CHAT_ID, user_id=TEST_USER_ID, assistant_name="FlowTestBot")
        assert "selected" in result.lower()
        assert TEST_USER_ID in _selected_assistant_state

        # Query assistant
        result = query_assistant(chat_id=TEST_CHAT_ID, user_id=TEST_USER_ID, assistant_id=str(assistant.id), user_message="Hello")
        assert "Test response" in result

        # Clear
        _selected_assistant_state.clear()


class TestAssistantQueryFlow:
    """Integration tests for full assistant query flow with real Qdrant."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup and teardown for each test."""
        # Authorize user
        authorize_user(TEST_USER_ID)
        # Clear states
        _selected_assistant_state.clear()
        yield
        # Cleanup
        _selected_assistant_state.clear()

    def test_query_with_qdrant_search(self, monkeypatch):
        """Test assistant query uses real Qdrant search."""
        import time

        calls = []
        monkeypatch.setattr(
            "src.business_logic.send_telegram_message",
            lambda chat_id, text: calls.append((chat_id, text))
        )
        monkeypatch.setattr("src.api.get_embeddings", create_mock_embeddings())
        monkeypatch.setattr("src.business_logic.call_llm", create_mock_llm("Qdrant found relevant data"))

        # Create Qdrant collection with test data
        test_collection = f"qdrant_flow_{TEST_USER_ID}_{int(time.time())}"
        create_qdrant_collection(test_collection)

        # Add data to Qdrant collection
        from src.api import add_to_collection
        test_texts = [
            "Python is a high-level programming language",
            "JavaScript is used for web development",
            "Rust is a systems programming language",
        ]
        test_payloads = [{"filename": f"file{i}.txt"} for i in range(len(test_texts))]
        add_to_collection(test_collection, test_texts, test_payloads)

        # Create prompt in database
        prompt = create_prompt(
            name=f"qdrant_prompt_{TEST_USER_ID}",
            prompt_data="You are a helpful assistant. Use the provided context to answer.",
            author_username="test"
        )

        # Create DB collection
        db_collection = get_collection_by_name(test_collection)
        if not db_collection:
            db_collection = create_db_collection(test_collection)

        # Create assistant
        assistant = create_db_assistant(f"QdrantBot_{TEST_USER_ID}", db_collection.id, prompt.id)

        # Select assistant
        cmd_assist(chat_id=TEST_CHAT_ID, user_id=TEST_USER_ID, assistant_name=f"QdrantBot_{TEST_USER_ID}")

        # Query with question that should trigger Qdrant search
        result = query_assistant(
            chat_id=TEST_CHAT_ID,
            user_id=TEST_USER_ID,
            assistant_id=str(assistant.id),
            user_message="What is Python?"
        )

        # Verify query succeeded
        assert result is not None
        assert "Qdrant found relevant data" in result

        # Cleanup Qdrant collection
        from src.api import delete_collection
        delete_collection(test_collection)
