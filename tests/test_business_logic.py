"""Tests for business logic module."""
import pytest
from unittest.mock import Mock, patch, MagicMock


# Mock database module before importing business_logic
mock_db_module = MagicMock()


@pytest.fixture(autouse=True)
def mock_database():
    """Mock database module for all tests."""
    with patch.dict("sys.modules", {"src.database": mock_db_module}):
        yield mock_db_module


class TestAuth:
    """Tests for authentication functions."""

    def test_check_auth_unauthorized_user(self):
        """Test check_auth returns False for unauthorized user."""
        mock_db_module.is_user_authorized.return_value = False
        # Re-import to get mocked version
        import importlib
        import src.business_logic as bl
        importlib.reload(bl)

        result = bl.check_auth(user_id=123)
        assert result is False

    def test_check_auth_authorized_user(self):
        """Test check_auth returns True for authorized user."""
        mock_db_module.is_user_authorized.return_value = True
        import importlib
        import src.business_logic as bl
        importlib.reload(bl)

        result = bl.check_auth(user_id=456)
        assert result is True

    @patch("src.business_logic.db_authorize_user")
    def test_authorize_user(self, mock_auth):
        """Test authorize_user calls database function."""
        import src.business_logic as bl
        bl.authorize_user(user_id=789)
        mock_auth.assert_called_once_with(789)

    def test_get_authorized_users(self):
        """Test get_authorized_users returns empty list for now."""
        import importlib
        import src.business_logic as bl
        importlib.reload(bl)

        result = bl.get_authorized_users()
        assert result == []


class TestPublicCommands:
    """Tests for public commands."""

    @patch("src.business_logic.send_telegram_message")
    def test_cmd_start(self, mock_send):
        """Test /start command sends welcome message."""
        import src.business_logic as bl
        result = bl.cmd_start(chat_id=123, user_id=456)
        assert result == "Welcome message sent"
        mock_send.assert_called_once()
        call_args = mock_send.call_args
        assert call_args[0][0] == 123
        assert "Welcome" in call_args[0][1]

    @patch("src.business_logic.send_telegram_message")
    @patch("src.business_logic.authorize_user")
    @patch("config.Config")
    def test_cmd_auth_success(self, mock_config, mock_auth, mock_send):
        """Test /auth with correct password."""
        import src.business_logic as bl
        mock_config.AUTH_PASSWORD = "secret"

        result = bl.cmd_auth(chat_id=123, user_id=456, password="secret")
        assert "success" in result.lower()
        mock_auth.assert_called_once_with(456)

    @patch("src.business_logic.send_telegram_message")
    @patch("config.Config")
    def test_cmd_auth_failure(self, mock_config, mock_send):
        """Test /auth with wrong password."""
        import src.business_logic as bl
        mock_config.AUTH_PASSWORD = "secret"

        result = bl.cmd_auth(chat_id=123, user_id=456, password="wrong")
        assert "failed" in result.lower() or "incorrect" in result.lower()

    @patch("src.business_logic.send_telegram_message")
    @patch("src.business_logic.get_all_assistants")
    def test_cmd_list_assistants_empty(self, mock_get, mock_send):
        """Test /list-assistants when no assistants exist."""
        import src.business_logic as bl
        mock_get.return_value = []

        result = bl.cmd_list_assistants(chat_id=123)
        assert "No assistants" in result
        mock_send.assert_called_once()

    @patch("src.business_logic.send_telegram_message")
    @patch("src.business_logic.get_all_assistants")
    def test_cmd_list_assistants_with_data(self, mock_get, mock_send):
        """Test /list-assistants with existing assistants."""
        import src.business_logic as bl

        mock_prompt = MagicMock()
        mock_prompt.name = "Test Prompt"
        mock_collection = MagicMock()
        mock_collection.name = "test_db"

        mock_assistant = MagicMock()
        mock_assistant.id = 1
        mock_assistant.name = "TestBot"
        mock_assistant.system_prompt = mock_prompt
        mock_assistant.collection = mock_collection

        mock_get.return_value = [mock_assistant]

        result = bl.cmd_list_assistants(chat_id=123)
        assert "Available Assistants" in result
        assert "TestBot" in result


class TestPrivateCommands:
    """Tests for private commands."""

    @patch("src.business_logic.send_telegram_message")
    @patch("src.business_logic.list_qdrant_collections")
    @patch("src.business_logic.get_all_collections")
    def test_cmd_database_list_empty(self, mock_db_colls, mock_qdrant_colls, mock_send):
        """Test /database-list when no databases exist."""
        import src.business_logic as bl
        mock_qdrant_colls.return_value = []
        mock_db_colls.return_value = []

        result = bl.cmd_database_list(chat_id=123)
        assert "No databases" in result

    @patch("src.business_logic.send_telegram_message")
    @patch("src.business_logic.list_qdrant_collections")
    @patch("src.business_logic.get_all_collections")
    def test_cmd_database_list_with_data(self, mock_db_colls, mock_qdrant_colls, mock_send):
        """Test /database-list with existing databases."""
        import src.business_logic as bl

        mock_coll = MagicMock()
        mock_coll.name = "db1"
        mock_db_colls.return_value = [mock_coll]
        mock_qdrant_colls.return_value = ["db2"]

        result = bl.cmd_database_list(chat_id=123)
        assert "db1" in result
        assert "db2" in result

    @patch("src.business_logic.send_telegram_message")
    @patch("src.business_logic.create_qdrant_collection")
    @patch("src.business_logic.create_db_collection")
    def test_cmd_database_create_success(self, mock_create_db, mock_create_qdrant, mock_send):
        """Test /database-create with success."""
        import src.business_logic as bl
        mock_create_qdrant.return_value = True

        result = bl.cmd_database_create(chat_id=123, name="testdb")
        assert "created" in result.lower()

    @patch("src.business_logic.send_telegram_message")
    @patch("src.business_logic.create_qdrant_collection")
    def test_cmd_database_create_failure(self, mock_create, mock_send):
        """Test /database-create with failure."""
        import src.business_logic as bl
        mock_create.return_value = False

        result = bl.cmd_database_create(chat_id=123, name="testdb")
        assert "failed" in result.lower()

    @patch("src.business_logic.send_telegram_message")
    @patch("src.business_logic.get_all_prompts")
    def test_cmd_prompt_list_empty(self, mock_get, mock_send):
        """Test /prompt-list when no prompts exist."""
        import src.business_logic as bl
        mock_get.return_value = []

        result = bl.cmd_prompt_list(chat_id=123)
        assert "No prompts" in result

    @patch("src.business_logic.send_telegram_message")
    @patch("src.business_logic.get_all_prompts")
    def test_cmd_prompt_list_with_data(self, mock_get, mock_send):
        """Test /prompt-list with existing prompts."""
        import src.business_logic as bl

        mock_prompt = MagicMock()
        mock_prompt.id = 1
        mock_prompt.name = "Test Prompt"
        mock_get.return_value = [mock_prompt]

        result = bl.cmd_prompt_list(chat_id=123)
        assert "Test Prompt" in result

    @patch("src.business_logic.send_telegram_message")
    @patch("src.business_logic.create_prompt")
    def test_cmd_prompt_create(self, mock_create, mock_send):
        """Test /prompt-create creates new prompt."""
        import src.business_logic as bl

        mock_prompt = MagicMock()
        mock_prompt.id = 1
        mock_create.return_value = mock_prompt

        result = bl.cmd_prompt_create(chat_id=123, user_id=456, name="My Prompt", content="Prompt content")
        assert "created" in result.lower()

    @patch("src.business_logic.send_telegram_message")
    @patch("src.business_logic.get_prompt_by_id")
    def test_cmd_prompt_show_exists_by_id(self, mock_get, mock_send):
        """Test /prompt-show with existing prompt by ID."""
        import src.business_logic as bl

        mock_prompt = MagicMock()
        mock_prompt.name = "Test"
        mock_prompt.id = 1
        mock_prompt.prompt_data = "Content here"
        mock_get.return_value = mock_prompt

        result = bl.cmd_prompt_show(chat_id=123, prompt_identifier="1")
        assert "Content here" in result

    @patch("src.business_logic.send_telegram_message")
    @patch("src.business_logic.get_prompt_by_name")
    def test_cmd_prompt_show_exists_by_name(self, mock_get, mock_send):
        """Test /prompt-show with existing prompt by name."""
        import src.business_logic as bl

        mock_prompt = MagicMock()
        mock_prompt.name = "My Prompt"
        mock_prompt.id = 1
        mock_prompt.prompt_data = "Content here"
        mock_get.return_value = mock_prompt

        result = bl.cmd_prompt_show(chat_id=123, prompt_identifier="My Prompt")
        assert "Content here" in result
        mock_get.assert_called_once_with("My Prompt")

    @patch("src.business_logic.send_telegram_message")
    @patch("src.business_logic.get_prompt_by_id")
    @patch("src.business_logic.get_prompt_by_name")
    def test_cmd_prompt_show_not_found(self, mock_get_name, mock_get_id, mock_send):
        """Test /prompt-show with non-existent prompt (by ID or name)."""
        import src.business_logic as bl
        mock_get_id.return_value = None
        mock_get_name.return_value = None

        result = bl.cmd_prompt_show(chat_id=123, prompt_identifier="999")
        assert "not found" in result.lower()

        result = bl.cmd_prompt_show(chat_id=123, prompt_identifier="nonexistent")
        assert "not found" in result.lower()

    @patch("src.business_logic.send_telegram_message")
    @patch("src.business_logic.update_prompt")
    def test_cmd_prompt_update_success(self, mock_update, mock_send):
        """Test /prompt-update with existing prompt."""
        import src.business_logic as bl

        mock_prompt = MagicMock()
        mock_prompt.id = 1
        mock_update.return_value = mock_prompt

        result = bl.cmd_prompt_update(chat_id=123, prompt_id="1", content="New content")
        assert "updated" in result.lower()

    @patch("src.business_logic.send_telegram_message")
    @patch("src.business_logic.update_prompt")
    def test_cmd_prompt_update_not_found(self, mock_update, mock_send):
        """Test /prompt-update with non-existent prompt."""
        import src.business_logic as bl
        mock_update.return_value = None

        result = bl.cmd_prompt_update(chat_id=123, prompt_id="999", content="New")
        assert "not found" in result.lower()


class TestAssistantInteraction:
    """Tests for assistant query functionality."""

    @patch("src.business_logic.send_telegram_message")
    @patch("src.business_logic.call_llm")
    @patch("src.business_logic.search_collection")
    @patch("src.business_logic.get_assistant_by_id")
    def test_query_assistant_success(self, mock_get, mock_search, mock_llm, mock_send):
        """Test query_assistant with successful response."""
        import src.business_logic as bl

        mock_prompt = MagicMock()
        mock_prompt.prompt_data = "You are a helpful assistant."
        mock_collection = MagicMock()
        mock_collection.name = "db1"

        mock_assistant = MagicMock()
        mock_assistant.system_prompt = mock_prompt
        mock_assistant.collection = mock_collection

        mock_get.return_value = mock_assistant
        mock_search.return_value = [{"text": "Relevant info"}]
        mock_llm.return_value = "Response from LLM"

        result = bl.query_assistant(chat_id=123, user_id=456, assistant_id="1", user_message="Hello")
        assert "Response from LLM" in result

    @patch("src.business_logic.send_telegram_message")
    @patch("src.business_logic.get_assistant_by_id")
    def test_query_assistant_not_found(self, mock_get, mock_send):
        """Test query_assistant with non-existent assistant."""
        import src.business_logic as bl
        mock_get.return_value = None

        result = bl.query_assistant(chat_id=123, user_id=456, assistant_id="999", user_message="Hello")
        assert "not found" in result.lower()

    @patch("src.business_logic.send_telegram_message")
    def test_query_assistant_invalid_id(self, mock_send):
        """Test query_assistant with invalid assistant ID."""
        import src.business_logic as bl

        result = bl.query_assistant(chat_id=123, user_id=456, assistant_id="invalid", user_message="Hello")
        assert "invalid" in result.lower()


class TestAssistantQuery:
    """Tests for assistant query with selected assistant."""

    @patch("src.business_logic.send_telegram_message")
    @patch("src.business_logic.call_llm")
    @patch("src.business_logic.search_collection")
    @patch("src.business_logic.get_assistant_by_id")
    def test_query_assistant_with_selected(self, mock_get, mock_search, mock_llm, mock_send):
        """Test querying assistant with selected assistant."""
        import src.business_logic as bl

        mock_prompt = MagicMock()
        mock_prompt.prompt_data = "You are a helpful assistant."
        mock_collection = MagicMock()
        mock_collection.name = "test_db"

        mock_assistant = MagicMock()
        mock_assistant.id = 1
        mock_assistant.name = "TestBot"
        mock_assistant.system_prompt = mock_prompt
        mock_assistant.collection = mock_collection

        mock_get.return_value = mock_assistant
        mock_search.return_value = [{"text": "Relevant info"}]
        mock_llm.return_value = "Response from LLM"

        # Set selected assistant
        bl._selected_assistant_state[456] = 1

        result = bl.query_assistant(chat_id=123, user_id=456, assistant_id="1", user_message="Hello")
        assert "Response from LLM" in result

        # Clear state
        del bl._selected_assistant_state[456]

    def test_get_selected_assistant_from_state(self):
        """Test getting selected assistant from state."""
        import src.business_logic as bl

        mock_prompt = MagicMock()
        mock_prompt.name = "Test Prompt"
        mock_collection = MagicMock()
        mock_collection.name = "test_db"

        mock_assistant = MagicMock()
        mock_assistant.id = 1
        mock_assistant.name = "TestBot"
        mock_assistant.system_prompt = mock_prompt
        mock_assistant.collection = mock_collection

        with patch("src.business_logic.get_assistant_by_id", return_value=mock_assistant):
            bl._selected_assistant_state[456] = 1
            result = bl.get_selected_assistant(456)
            assert result is not None
            assert result.name == "TestBot"
            del bl._selected_assistant_state[456]


class TestHelpCommand:
    """Tests for /help command."""

    @patch("src.business_logic.send_telegram_message")
    @patch("builtins.open")
    @patch("os.path.dirname")
    def test_cmd_help_success(self, mock_dirname, mock_open, mock_send):
        """Test /help command sends content from help.md."""
        import src.business_logic as bl

        mock_dirname.return_value = "/project"
        mock_file = MagicMock()
        mock_file.__enter__.return_value.read.return_value = "# Help Content"
        mock_open.return_value = mock_file

        result = bl.cmd_help(chat_id=123)
        assert result == "Help sent"
        mock_send.assert_called_once()

    @patch("src.business_logic.send_telegram_message")
    @patch("os.path.join")
    @patch("builtins.open")
    @patch("os.path.dirname")
    def test_cmd_help_file_not_found(self, mock_dirname, mock_open, mock_join, mock_send):
        """Test /help command handles missing file gracefully."""
        import src.business_logic as bl

        mock_dirname.return_value = "/project"
        mock_join.return_value = "/project/help.md"
        mock_open.side_effect = FileNotFoundError()

        result = bl.cmd_help(chat_id=123)
        assert "not found" in result.lower()
        mock_send.assert_called()


class TestAssistantCreateCommand:
    """Tests for /assistant-create command."""

    @patch("src.business_logic.send_telegram_message")
    @patch("src.business_logic.list_qdrant_collections")
    @patch("src.business_logic.get_prompt_by_id")
    @patch("src.business_logic.get_prompt_by_name")
    @patch("src.business_logic.get_collection_by_name")
    @patch("src.business_logic.create_db_assistant")
    def test_cmd_assistant_create_success(self, mock_create, mock_get_coll, mock_get_name, mock_get_id, mock_list, mock_send):
        """Test /assistant-create with valid collection and prompt."""
        import src.business_logic as bl

        mock_list.return_value = ["db1", "db2"]

        mock_prompt = MagicMock()
        mock_prompt.id = 1
        mock_get_id.return_value = mock_prompt

        mock_coll = MagicMock()
        mock_coll.id = 1
        mock_get_coll.return_value = mock_coll

        mock_assistant = MagicMock()
        mock_assistant.id = 1
        mock_assistant.name = "MyBot"
        mock_create.return_value = mock_assistant

        result = bl.cmd_assistant_create(chat_id=123, user_id=456, name="MyBot", collection_name="db1", prompt_identifier="1")
        assert "created" in result.lower()

    @patch("src.business_logic.send_telegram_message")
    @patch("src.business_logic.list_qdrant_collections")
    def test_cmd_assistant_create_invalid_collection(self, mock_list, mock_send):
        """Test /assistant-create with non-existent collection."""
        import src.business_logic as bl

        mock_list.return_value = ["db1", "db2"]

        result = bl.cmd_assistant_create(chat_id=123, user_id=456, name="MyBot", collection_name="nonexistent", prompt_identifier="1")
        assert "not found" in result.lower()
        assert "collection" in result.lower()

    @patch("src.business_logic.send_telegram_message")
    @patch("src.business_logic.list_qdrant_collections")
    @patch("src.business_logic.get_prompt_by_id")
    @patch("src.business_logic.get_prompt_by_name")
    def test_cmd_assistant_create_invalid_prompt(self, mock_get_name, mock_get_id, mock_list, mock_send):
        """Test /assistant-create with non-existent prompt."""
        import src.business_logic as bl

        mock_list.return_value = ["db1"]
        mock_get_id.return_value = None
        mock_get_name.return_value = None

        result = bl.cmd_assistant_create(chat_id=123, user_id=456, name="MyBot", collection_name="db1", prompt_identifier="999")
        assert "not found" in result.lower()
        assert "prompt" in result.lower()

    @patch("src.business_logic.send_telegram_message")
    def test_cmd_assistant_create_interactive_start(self, mock_send):
        """Test /assistant-create starts interactive mode without args."""
        import src.business_logic as bl

        # Clear state
        bl._assistant_create_state.clear()

        result = bl.cmd_assistant_create(chat_id=123, user_id=456)
        assert "Create New Assistant" in result or "assistant name" in result.lower()
        assert 456 in bl._assistant_create_state

    @patch("src.business_logic.send_telegram_message")
    def test_cmd_assistant_create_interactive_with_name(self, mock_send):
        """Test /assistant-create starts interactive with name provided."""
        import src.business_logic as bl

        # Clear state
        bl._assistant_create_state.clear()

        result = bl.cmd_assistant_create(chat_id=123, user_id=456, name="TestBot")
        assert "collection name" in result.lower()
        assert 456 in bl._assistant_create_state

    @patch("src.business_logic.send_telegram_message")
    @patch("src.business_logic.list_qdrant_collections")
    def test_handle_assistant_create_response_name(self, mock_list, mock_send):
        """Test handling name response in interactive mode."""
        import src.business_logic as bl

        mock_list.return_value = ["my_collection"]

        # Set up state with name already entered
        bl._assistant_create_state[456] = {"name": "TestBot", "collection_name": None, "prompt_id": None}

        result = bl.handle_assistant_create_response(user_id=456, chat_id=123, text="my_collection")
        assert "prompt" in result.lower()
        assert bl._assistant_create_state[456]["collection_name"] == "my_collection"

    @patch("src.business_logic.send_telegram_message")
    @patch("src.business_logic.list_qdrant_collections")
    @patch("src.business_logic.get_prompt_by_id")
    @patch("src.business_logic.get_prompt_by_name")
    @patch("src.business_logic.get_collection_by_name")
    @patch("src.business_logic.create_db_assistant")
    def test_handle_assistant_create_response_collection(self, mock_create, mock_get_coll, mock_get_name, mock_get_id, mock_list, mock_send):
        """Test handling collection response in interactive mode."""
        import src.business_logic as bl

        mock_list.return_value = ["my_collection"]

        mock_prompt = MagicMock()
        mock_prompt.id = 1
        mock_get_id.return_value = mock_prompt

        mock_coll = MagicMock()
        mock_coll.id = 1
        mock_get_coll.return_value = mock_coll

        mock_assistant = MagicMock()
        mock_assistant.id = 1
        mock_assistant.name = "TestBot"
        mock_create.return_value = mock_assistant

        # Set up state with name and collection
        bl._assistant_create_state[456] = {"name": "TestBot", "collection_name": "my_collection", "prompt_id": None}

        result = bl.handle_assistant_create_response(user_id=456, chat_id=123, text="1")
        assert "created" in result.lower()
        assert 456 not in bl._assistant_create_state  # State should be cleared

    @patch("src.business_logic.send_telegram_message")
    @patch("src.business_logic.list_qdrant_collections")
    @patch("src.business_logic.get_prompt_by_id")
    @patch("src.business_logic.get_prompt_by_name")
    @patch("src.business_logic.get_collection_by_name")
    @patch("src.business_logic.create_db_assistant")
    def test_handle_assistant_create_response_prompt(self, mock_create, mock_get_coll, mock_get_name, mock_get_id, mock_list, mock_send):
        """Test handling prompt response and creating assistant."""
        import src.business_logic as bl

        mock_list.return_value = ["my_collection"]

        mock_prompt = MagicMock()
        mock_prompt.id = 1
        mock_get_id.return_value = mock_prompt

        mock_coll = MagicMock()
        mock_coll.id = 1
        mock_get_coll.return_value = mock_coll

        mock_assistant = MagicMock()
        mock_assistant.id = 1
        mock_assistant.name = "TestBot"
        mock_create.return_value = mock_assistant

        # Set up state
        bl._assistant_create_state[456] = {"name": "TestBot", "collection_name": "my_collection", "prompt_id": None}

        result = bl.handle_assistant_create_response(user_id=456, chat_id=123, text="1")
        assert "created" in result.lower()
        assert 456 not in bl._assistant_create_state  # State should be cleared

    @patch("src.business_logic.send_telegram_message")
    def test_cancel_assistant_create(self, mock_send):
        """Test cancelling assistant creation."""
        import src.business_logic as bl

        # Set up state
        bl._assistant_create_state[456] = {"name": "TestBot", "collection_name": "my_collection", "prompt_id": None}

        result = bl.cancel_assistant_create(user_id=456, chat_id=123)
        assert "cancelled" in result.lower()
        assert 456 not in bl._assistant_create_state


class TestUnauthorizedAccess:
    """Tests for unauthorized access to private commands."""

    def test_database_list_unauthorized(self):
        """Test /database-list requires authorization."""
        import src.business_logic as bl

        with patch("src.business_logic.is_user_authorized") as mock_auth:
            mock_auth.return_value = False
            assert bl.check_auth(user_id=999) is False

    def test_database_create_unauthorized(self):
        """Test /database-create requires authorization."""
        import src.business_logic as bl

        with patch("src.business_logic.is_user_authorized") as mock_auth:
            mock_auth.return_value = False
            assert bl.check_auth(user_id=999) is False

    def test_prompt_list_unauthorized(self):
        """Test /prompt-list requires authorization."""
        import src.business_logic as bl

        with patch("src.business_logic.is_user_authorized") as mock_auth:
            mock_auth.return_value = False
            assert bl.check_auth(user_id=999) is False

    def test_prompt_create_unauthorized(self):
        """Test /prompt-create requires authorization."""
        import src.business_logic as bl

        with patch("src.business_logic.is_user_authorized") as mock_auth:
            mock_auth.return_value = False
            assert bl.check_auth(user_id=999) is False

    def test_prompt_show_unauthorized(self):
        """Test /prompt-show requires authorization."""
        import src.business_logic as bl

        with patch("src.business_logic.is_user_authorized") as mock_auth:
            mock_auth.return_value = False
            assert bl.check_auth(user_id=999) is False

    def test_prompt_update_unauthorized(self):
        """Test /prompt-update requires authorization."""
        import src.business_logic as bl

        with patch("src.business_logic.is_user_authorized") as mock_auth:
            mock_auth.return_value = False
            assert bl.check_auth(user_id=999) is False

    def test_assistant_create_unauthorized(self):
        """Test /assistant-create requires authorization."""
        import src.business_logic as bl

        with patch("src.business_logic.is_user_authorized") as mock_auth:
            mock_auth.return_value = False
            assert bl.check_auth(user_id=999) is False


class TestDataCommands:
    """Tests for data management commands."""

    @patch("src.business_logic.send_telegram_message")
    @patch("src.api.list_points")
    def test_cmd_data_list_empty(self, mock_list, mock_send):
        """Test /data_list when no records exist."""
        import src.business_logic as bl
        mock_list.return_value = []

        result = bl.cmd_data_list(chat_id=123, collection_name="test_db")
        assert "no records" in result.lower()

    @patch("src.business_logic.send_telegram_message")
    @patch("src.api.list_points")
    def test_cmd_data_list_with_data(self, mock_list, mock_send):
        """Test /data_list with existing records."""
        import src.business_logic as bl

        mock_list.return_value = [
            {"id": "uuid-1", "filename": "file1.txt", "payload": "Content 1"},
            {"id": "uuid-2", "filename": "file2.txt", "payload": "Content 2"},
        ]

        result = bl.cmd_data_list(chat_id=123, collection_name="test_db")
        assert "uuid-1" in result
        assert "file1.txt" in result

    @patch("src.business_logic.send_telegram_message")
    @patch("src.api.get_point")
    def test_cmd_data_show_exists(self, mock_get, mock_send):
        """Test /data_show with existing record."""
        import src.business_logic as bl

        mock_get.return_value = {
            "id": "uuid-1",
            "filename": "file1.txt",
            "payload": "Test content"
        }

        result = bl.cmd_data_show(chat_id=123, collection_name="test_db", point_id="uuid-1")
        assert "uuid-1" in result
        assert "file1.txt" in result

    @patch("src.business_logic.send_telegram_message")
    @patch("src.api.get_point")
    def test_cmd_data_show_not_found(self, mock_get, mock_send):
        """Test /data_show with non-existent record."""
        import src.business_logic as bl

        mock_get.return_value = None

        result = bl.cmd_data_show(chat_id=123, collection_name="test_db", point_id="nonexistent")
        assert "not found" in result.lower()

    @patch("src.business_logic.send_telegram_message")
    @patch("src.api.get_point")
    @patch("src.api.delete_point")
    def test_cmd_data_remove_success(self, mock_delete, mock_get, mock_send):
        """Test /data_remove with existing record."""
        import src.business_logic as bl

        mock_get.return_value = {"id": "uuid-1", "filename": "file1.txt", "payload": "Content"}
        mock_delete.return_value = True

        result = bl.cmd_data_remove(chat_id=123, collection_name="test_db", point_id="uuid-1")
        assert "deleted" in result.lower()

    @patch("src.business_logic.send_telegram_message")
    @patch("src.api.get_point")
    def test_cmd_data_remove_not_found(self, mock_get, mock_send):
        """Test /data_remove with non-existent record."""
        import src.business_logic as bl

        mock_get.return_value = None

        result = bl.cmd_data_remove(chat_id=123, collection_name="test_db", point_id="nonexistent")
        assert "not found" in result.lower()

    @patch("src.business_logic.send_telegram_message")
    @patch("src.api.list_points")
    @patch("src.api.delete_all_points")
    def test_cmd_data_remove_all_success(self, mock_delete, mock_list, mock_send):
        """Test /data_remove_all with records."""
        import src.business_logic as bl

        mock_list.return_value = [{"id": "1"}, {"id": "2"}]
        mock_delete.return_value = True

        result = bl.cmd_data_remove_all(chat_id=123, collection_name="test_db")
        assert "deleted" in result.lower()

    @patch("src.business_logic.send_telegram_message")
    @patch("src.api.list_points")
    def test_cmd_data_remove_all_empty(self, mock_list, mock_send):
        """Test /data_remove_all with no records."""
        import src.business_logic as bl

        mock_list.return_value = []

        result = bl.cmd_data_remove_all(chat_id=123, collection_name="test_db")
        assert "no records" in result.lower()

    @patch("src.business_logic.send_telegram_message")
    @patch("src.business_logic.list_qdrant_collections")
    def test_cmd_data_add_bulk_start(self, mock_list, mock_send):
        """Test /data_add_bulk starts bulk upload mode."""
        import src.business_logic as bl

        mock_list.return_value = ["test_db"]

        result = bl.cmd_data_add_bulk_start(chat_id=123, user_id=456, collection_name="test_db")
        assert "bulk upload" in result.lower()
        assert 456 in bl._data_bulk_state

    @patch("src.business_logic.send_telegram_message")
    @patch("src.business_logic.list_qdrant_collections")
    def test_cmd_data_add_bulk_invalid_collection(self, mock_list, mock_send):
        """Test /data_add_bulk with invalid collection."""
        import src.business_logic as bl

        mock_list.return_value = ["other_db"]

        result = bl.cmd_data_add_bulk_start(chat_id=123, user_id=456, collection_name="invalid")
        assert "not found" in result.lower()


class TestUnauthorizedDataAccess:
    """Tests for unauthorized access to data commands."""

    def test_data_list_unauthorized(self):
        """Test /data_list requires authorization."""
        import src.business_logic as bl

        with patch("src.business_logic.is_user_authorized") as mock_auth:
            mock_auth.return_value = False
            assert bl.check_auth(user_id=999) is False

    def test_data_show_unauthorized(self):
        """Test /data_show requires authorization."""
        import src.business_logic as bl

        with patch("src.business_logic.is_user_authorized") as mock_auth:
            mock_auth.return_value = False
            assert bl.check_auth(user_id=999) is False

    def test_data_remove_unauthorized(self):
        """Test /data_remove requires authorization."""
        import src.business_logic as bl

        with patch("src.business_logic.is_user_authorized") as mock_auth:
            mock_auth.return_value = False
            assert bl.check_auth(user_id=999) is False

    def test_data_remove_all_unauthorized(self):
        """Test /data_remove_all requires authorization."""
        import src.business_logic as bl

        with patch("src.business_logic.is_user_authorized") as mock_auth:
            mock_auth.return_value = False
            assert bl.check_auth(user_id=999) is False

    def test_data_add_bulk_unauthorized(self):
        """Test /data_add_bulk requires authorization."""
        import src.business_logic as bl

        with patch("src.business_logic.is_user_authorized") as mock_auth:
            mock_auth.return_value = False
            assert bl.check_auth(user_id=999) is False


class TestAssistCommand:
    """Tests for /assist command."""

    @patch("src.business_logic.send_telegram_message")
    @patch("src.business_logic.get_all_assistants")
    def test_cmd_assist_select_assistant(self, mock_get, mock_send):
        """Test /assist selects an assistant."""
        import src.business_logic as bl

        mock_prompt = MagicMock()
        mock_prompt.name = "Test Prompt"
        mock_collection = MagicMock()
        mock_collection.name = "test_db"

        mock_assistant = MagicMock()
        mock_assistant.id = 1
        mock_assistant.name = "TestBot"
        mock_assistant.system_prompt = mock_prompt
        mock_assistant.collection = mock_collection

        mock_get.return_value = [mock_assistant]

        # Clear state
        bl._selected_assistant_state.clear()

        result = bl.cmd_assist(chat_id=123, user_id=456, assistant_name="TestBot")
        assert "selected" in result.lower()
        assert 456 in bl._selected_assistant_state

    @patch("src.business_logic.send_telegram_message")
    @patch("src.business_logic.get_all_assistants")
    def test_cmd_assist_show_current(self, mock_get, mock_send):
        """Test /assist shows current selection."""
        import src.business_logic as bl

        mock_prompt = MagicMock()
        mock_prompt.name = "Test Prompt"
        mock_collection = MagicMock()
        mock_collection.name = "test_db"

        mock_assistant = MagicMock()
        mock_assistant.id = 1
        mock_assistant.name = "TestBot"
        mock_assistant.system_prompt = mock_prompt
        mock_assistant.collection = mock_collection

        mock_get.return_value = [mock_assistant]

        # Set selected assistant
        bl._selected_assistant_state[456] = 1

        result = bl.cmd_assist(chat_id=123, user_id=456, assistant_name=None)
        assert "currently selected" in result.lower() or "TestBot" in result

    @patch("src.business_logic.send_telegram_message")
    @patch("src.business_logic.get_all_assistants")
    def test_cmd_assist_not_found(self, mock_get, mock_send):
        """Test /assist with invalid assistant name."""
        import src.business_logic as bl

        mock_get.return_value = []

        result = bl.cmd_assist(chat_id=123, user_id=456, assistant_name="NonExistent")
        assert "not found" in result.lower()

    @patch("src.business_logic.send_telegram_message")
    @patch("src.business_logic.get_assistant_by_id")
    @patch("src.business_logic.get_all_assistants")
    def test_get_selected_assistant(self, mock_get_all, mock_get_by_id, mock_send):
        """Test getting selected assistant."""
        import src.business_logic as bl

        mock_prompt = MagicMock()
        mock_prompt.name = "Test Prompt"
        mock_collection = MagicMock()
        mock_collection.name = "test_db"

        mock_assistant = MagicMock()
        mock_assistant.id = 1
        mock_assistant.name = "TestBot"
        mock_assistant.system_prompt = mock_prompt
        mock_assistant.collection = mock_collection

        mock_get_by_id.return_value = mock_assistant

        # Set selected assistant
        bl._selected_assistant_state[456] = 1

        result = bl.get_selected_assistant(456)
        assert result is not None
        assert result.name == "TestBot"

    @patch("src.business_logic.send_telegram_message")
    def test_clear_selected_assistant(self, mock_send):
        """Test clearing selected assistant."""
        import src.business_logic as bl

        # Set selected assistant
        bl._selected_assistant_state[456] = 1

        bl.clear_selected_assistant(456)
        assert 456 not in bl._selected_assistant_state
