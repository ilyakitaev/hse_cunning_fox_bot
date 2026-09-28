"""Tests for business logic module."""
import pytest
from unittest.mock import Mock, patch, MagicMock


class TestAuth:
    """Tests for authentication functions."""

    def test_check_auth_unauthorized_user(self):
        """Test check_auth returns False for unauthorized user."""
        from src.business_logic import check_auth, _authorized_users

        _authorized_users.clear()
        result = check_auth(user_id=123)
        assert result is False

    def test_check_auth_authorized_user(self):
        """Test check_auth returns True for authorized user."""
        from src.business_logic import check_auth, authorize_user, _authorized_users

        _authorized_users.clear()
        authorize_user(user_id=456)
        result = check_auth(user_id=456)
        assert result is True

    def test_authorize_user(self):
        """Test authorize_user adds user to authorized set."""
        from src.business_logic import authorize_user, _authorized_users

        _authorized_users.clear()
        authorize_user(user_id=789)
        assert 789 in _authorized_users

    def test_get_authorized_users(self):
        """Test get_authorized_users returns copy of authorized users."""
        from src.business_logic import authorize_user, get_authorized_users, _authorized_users

        _authorized_users.clear()
        authorize_user(user_id=111)
        authorize_user(user_id=222)
        users = get_authorized_users()
        assert 111 in users
        assert 222 in users


class TestPublicCommands:
    """Tests for public commands."""

    @patch("src.business_logic.send_telegram_message")
    def test_cmd_start(self, mock_send):
        """Test /start command sends welcome message."""
        from src.business_logic import cmd_start

        result = cmd_start(chat_id=123, user_id=456)
        assert result == "Welcome message sent"
        mock_send.assert_called_once()
        call_args = mock_send.call_args
        assert call_args[0][0] == 123
        assert "Welcome" in call_args[0][1]

    @patch("src.business_logic.send_telegram_message")
    @patch("config.Config")
    def test_cmd_auth_success(self, mock_config, mock_send):
        """Test /auth with correct password."""
        from src.business_logic import cmd_auth, _authorized_users

        _authorized_users.clear()
        mock_config.AUTH_PASSWORD = "secret"

        result = cmd_auth(chat_id=123, user_id=456, password="secret")
        assert "success" in result.lower()
        assert 456 in _authorized_users

    @patch("src.business_logic.send_telegram_message")
    @patch("config.Config")
    def test_cmd_auth_failure(self, mock_config, mock_send):
        """Test /auth with wrong password."""
        from src.business_logic import cmd_auth, _authorized_users

        _authorized_users.clear()
        mock_config.AUTH_PASSWORD = "secret"

        result = cmd_auth(chat_id=123, user_id=456, password="wrong")
        assert "failed" in result.lower() or "incorrect" in result.lower()
        assert 456 not in _authorized_users

    @patch("src.business_logic.send_telegram_message")
    def test_cmd_list_assistants_empty(self, mock_send):
        """Test /list-assistants when no assistants exist."""
        from src.business_logic import cmd_list_assistants, _assistants

        _assistants.clear()

        result = cmd_list_assistants(chat_id=123)
        assert "No assistants" in result
        mock_send.assert_called_once()

    @patch("src.business_logic.send_telegram_message")
    def test_cmd_list_assistants_with_data(self, mock_send):
        """Test /list-assistants with existing assistants."""
        from src.business_logic import cmd_list_assistants, _assistants

        _assistants.clear()
        _assistants["test123"] = {
            "name": "TestBot",
            "database_id": "db1",
            "prompt_id": "p1"
        }

        result = cmd_list_assistants(chat_id=123)
        assert "Available Assistants" in result
        assert "TestBot" in result


class TestPrivateCommands:
    """Tests for private commands."""

    @patch("src.business_logic.send_telegram_message")
    @patch("src.business_logic.list_collections")
    def test_cmd_database_list_empty(self, mock_list, mock_send):
        """Test /database-list when no databases exist."""
        from src.business_logic import cmd_database_list

        mock_list.return_value = []

        result = cmd_database_list(chat_id=123)
        assert "No databases" in result
        mock_list.assert_called_once()

    @patch("src.business_logic.send_telegram_message")
    @patch("src.business_logic.list_collections")
    def test_cmd_database_list_with_data(self, mock_list, mock_send):
        """Test /database-list with existing databases."""
        from src.business_logic import cmd_database_list

        mock_list.return_value = ["db1", "db2"]

        result = cmd_database_list(chat_id=123)
        assert "db1" in result
        assert "db2" in result

    @patch("src.business_logic.send_telegram_message")
    @patch("src.business_logic.create_collection")
    def test_cmd_database_create_success(self, mock_create, mock_send):
        """Test /database-create with success."""
        from src.business_logic import cmd_database_create, _databases

        _databases.clear()
        mock_create.return_value = True

        result = cmd_database_create(chat_id=123, name="testdb")
        assert "created" in result.lower()
        assert "testdb" in _databases

    @patch("src.business_logic.send_telegram_message")
    @patch("src.business_logic.create_collection")
    def test_cmd_database_create_failure(self, mock_create, mock_send):
        """Test /database-create with failure."""
        from src.business_logic import cmd_database_create

        mock_create.return_value = False

        result = cmd_database_create(chat_id=123, name="testdb")
        assert "failed" in result.lower()

    @patch("src.business_logic.send_telegram_message")
    def test_cmd_prompt_list_empty(self, mock_send):
        """Test /prompt-list when no prompts exist."""
        from src.business_logic import cmd_prompt_list, _prompts

        _prompts.clear()

        result = cmd_prompt_list(chat_id=123)
        assert "No prompts" in result

    @patch("src.business_logic.send_telegram_message")
    def test_cmd_prompt_list_with_data(self, mock_send):
        """Test /prompt-list with existing prompts."""
        from src.business_logic import cmd_prompt_list, _prompts

        _prompts.clear()
        _prompts["p1"] = {"name": "Test Prompt", "content": "content"}

        result = cmd_prompt_list(chat_id=123)
        assert "Test Prompt" in result

    @patch("src.business_logic.send_telegram_message")
    def test_cmd_prompt_create(self, mock_send):
        """Test /prompt-create creates new prompt."""
        from src.business_logic import cmd_prompt_create, _prompts

        _prompts.clear()

        result = cmd_prompt_create(chat_id=123, name="My Prompt", content="Prompt content")
        assert "created" in result.lower()
        assert len(_prompts) == 1

    @patch("src.business_logic.send_telegram_message")
    def test_cmd_prompt_show_exists(self, mock_send):
        """Test /prompt-show with existing prompt."""
        from src.business_logic import cmd_prompt_show, _prompts

        _prompts.clear()
        _prompts["p1"] = {"name": "Test", "content": "Content here"}

        result = cmd_prompt_show(chat_id=123, prompt_id="p1")
        assert "Content here" in result

    @patch("src.business_logic.send_telegram_message")
    def test_cmd_prompt_show_not_found(self, mock_send):
        """Test /prompt-show with non-existent prompt."""
        from src.business_logic import cmd_prompt_show, _prompts

        _prompts.clear()

        result = cmd_prompt_show(chat_id=123, prompt_id="nonexistent")
        assert "not found" in result.lower()

    @patch("src.business_logic.send_telegram_message")
    def test_cmd_prompt_update_success(self, mock_send):
        """Test /prompt-update with existing prompt."""
        from src.business_logic import cmd_prompt_update, _prompts

        _prompts.clear()
        _prompts["p1"] = {"name": "Test", "content": "Old content"}

        result = cmd_prompt_update(chat_id=123, prompt_id="p1", content="New content")
        assert "updated" in result.lower()
        assert _prompts["p1"]["content"] == "New content"

    @patch("src.business_logic.send_telegram_message")
    def test_cmd_prompt_update_not_found(self, mock_send):
        """Test /prompt-update with non-existent prompt."""
        from src.business_logic import cmd_prompt_update, _prompts

        _prompts.clear()

        result = cmd_prompt_update(chat_id=123, prompt_id="nonexistent", content="New")
        assert "not found" in result.lower()


class TestAssistantInteraction:
    """Tests for assistant query functionality."""

    @patch("src.business_logic.send_telegram_message")
    @patch("src.business_logic.call_llm")
    @patch("src.business_logic.search_collection")
    @patch("src.business_logic._prompts")
    @patch("src.business_logic._assistants")
    def test_query_assistant_success(
        self, mock_assistants, mock_prompts, mock_search, mock_llm, mock_send
    ):
        """Test query_assistant with successful response."""
        from src.business_logic import query_assistant

        mock_assistants.get.return_value = {
            "name": "TestBot",
            "database_id": "db1",
            "prompt_id": "p1"
        }
        mock_prompts.get.return_value = {"name": "Test", "content": "You are a helpful assistant."}
        mock_search.return_value = [{"text": "Relevant info"}]
        mock_llm.return_value = "Response from LLM"

        result = query_assistant(chat_id=123, user_id=456, assistant_id="a1", user_message="Hello")
        assert "Response from LLM" in result

    @patch("src.business_logic.send_telegram_message")
    @patch("src.business_logic._assistants")
    def test_query_assistant_not_found(self, mock_assistants, mock_send):
        """Test query_assistant with non-existent assistant."""
        from src.business_logic import query_assistant

        mock_assistants.get.return_value = None

        result = query_assistant(chat_id=123, user_id=456, assistant_id="nonexistent", user_message="Hello")
        assert "not found" in result.lower()

    @patch("src.business_logic.send_telegram_message")
    @patch("src.business_logic._assistants")
    @patch("src.business_logic._prompts")
    def test_query_assistant_missing_prompt(self, mock_prompts, mock_assistants, mock_send):
        """Test query_assistant with missing prompt."""
        from src.business_logic import query_assistant

        mock_assistants.get.return_value = {
            "name": "TestBot",
            "database_id": "db1",
            "prompt_id": "p1"
        }
        mock_prompts.get.return_value = None

        result = query_assistant(chat_id=123, user_id=456, assistant_id="a1", user_message="Hello")
        assert "not found" in result.lower()


class TestDataManagement:
    """Tests for data management functions."""

    @patch("src.business_logic.add_to_collection")
    def test_add_data_to_database(self, mock_add):
        """Test add_data_to_database function."""
        from src.business_logic import add_data_to_database

        mock_add.return_value = True

        result = add_data_to_database("testdb", ["text1", "text2"])
        assert result is True
        mock_add.assert_called_once()

    @patch("src.business_logic.list_collections")
    @patch("src.business_logic._prompts")
    @patch("src.business_logic._assistants")
    def test_create_assistant_success(self, mock_assistants, mock_prompts, mock_list):
        """Test create_assistant with success."""
        from src.business_logic import create_assistant

        mock_list.return_value = ["db1"]
        mock_prompts.__contains__ = lambda self, x: x == "p1"

        result = create_assistant(name="TestBot", database_id="db1", prompt_id="p1")
        assert result is not None

    @patch("src.business_logic.list_collections")
    def test_create_assistant_invalid_db(self, mock_list):
        """Test create_assistant with invalid database."""
        from src.business_logic import create_assistant

        mock_list.return_value = ["db1"]

        result = create_assistant(name="TestBot", database_id="nonexistent", prompt_id="p1")
        assert result is None
