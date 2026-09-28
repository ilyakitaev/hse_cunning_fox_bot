"""Business logic - bot commands implemented as python functions."""
import logging
from typing import Optional
from src.api import (
    send_telegram_message,
    create_collection,
    delete_collection,
    list_collections,
    add_to_collection,
    search_collection,
    call_llm,
)

logger = logging.getLogger(__name__)


# In-memory storage for prompts, assistants, and authorized users
_prompts = {}  # prompt_id -> {"name": str, "content": str}
_assistants = {}  # assistant_id -> {"name": str, "database_id": str, "prompt_id": str}
_databases = {}  # database_id -> {"name": str}
_authorized_users = set()  # set of user_ids


def check_auth(user_id: int) -> bool:
    """Check if user is authorized."""
    return user_id in _authorized_users


def authorize_user(user_id: int) -> None:
    """Authorize a user."""
    _authorized_users.add(user_id)


def get_authorized_users() -> set:
    """Get all authorized users."""
    return _authorized_users.copy()


# ============ Public Commands ============


def cmd_start(chat_id: int, user_id: int) -> str:
    """Handle /start command."""
    welcome = """👋 *Welcome to HSE Cunning Fox Bot!*

I'm a RAG-powered assistant. Here's how to use me:

*Public Commands:*
/start - Show this welcome message
/auth <password> - Authorize yourself
/list-assistants - See available assistants

*Private Commands (authorized users only):*
/database-list - List all databases
/database-create <name> - Create a new database
/prompt-list - List all prompts
/prompt-create <name> - Create a new prompt
/prompt-show <id> - Show prompt content
/prompt-update <id> <content> - Update prompt

*Using an Assistant:*
Just send a message to any assistant listed in /list-assistants!
"""
    send_telegram_message(chat_id, welcome)
    return "Welcome message sent"


def cmd_auth(chat_id: int, user_id: int, password: str) -> str:
    """Handle /auth command."""
    from config import Config

    if password == Config.AUTH_PASSWORD:
        authorize_user(user_id)
        msg = "✅ *Authorization successful!* You now have access to private commands."
    else:
        msg = "❌ *Authorization failed!* Incorrect password."

    send_telegram_message(chat_id, msg)
    return msg


def cmd_list_assistants(chat_id: int) -> str:
    """Handle /list-assistants command."""
    if not _assistants:
        msg = "No assistants configured yet."
    else:
        msg = "*Available Assistants:*\n\n"
        for aid, data in _assistants.items():
            msg += f"• `{aid}`: {data['name']} (DB: {data['database_id']}, Prompt: {data['prompt_id']})\n"

    send_telegram_message(chat_id, msg)
    return msg


# ============ Private Commands ============


def cmd_database_list(chat_id: int) -> str:
    """Handle /database-list command."""
    databases = list_collections()
    if not databases:
        msg = "No databases exist yet."
    else:
        msg = "*Existing Databases:*\n\n"
        for db in databases:
            msg += f"• {db}\n"

    send_telegram_message(chat_id, msg)
    return msg


def cmd_database_create(chat_id: int, name: str) -> str:
    """Handle /database-create command."""
    if create_collection(name):
        _databases[name] = {"name": name}
        msg = f"✅ Database `{name}` created successfully!"
    else:
        msg = f"❌ Failed to create database `{name}`"

    send_telegram_message(chat_id, msg)
    return msg


def cmd_prompt_list(chat_id: int) -> str:
    """Handle /prompt-list command."""
    if not _prompts:
        msg = "No prompts exist yet."
    else:
        msg = "*Existing Prompts:*\n\n"
        for pid, data in _prompts.items():
            msg += f"• `{pid}`: {data['name']}\n"

    send_telegram_message(chat_id, msg)
    return msg


def cmd_prompt_create(chat_id: int, name: str, content: str) -> str:
    """Handle /prompt-create command."""
    import uuid
    pid = str(uuid.uuid4())[:8]
    _prompts[pid] = {"name": name, "content": content}
    msg = f"✅ Prompt created!\n*ID:* `{pid}`\n*Name:* {name}"
    send_telegram_message(chat_id, msg)
    return msg


def cmd_prompt_show(chat_id: int, prompt_id: str) -> str:
    """Handle /prompt-show command."""
    prompt = _prompts.get(prompt_id)
    if not prompt:
        msg = f"❌ Prompt `{prompt_id}` not found"
    else:
        msg = f"*Prompt: {prompt['name']}* (ID: `{prompt_id}`)\n\n{prompt['content']}"

    send_telegram_message(chat_id, msg)
    return msg


def cmd_prompt_update(chat_id: int, prompt_id: str, content: str) -> str:
    """Handle /prompt-update command."""
    if prompt_id not in _prompts:
        msg = f"❌ Prompt `{prompt_id}` not found"
    else:
        _prompts[prompt_id]["content"] = content
        msg = f"✅ Prompt `{prompt_id}` updated!"

    send_telegram_message(chat_id, msg)
    return msg


# ============ Assistant Interaction ============


def query_assistant(chat_id: int, user_id: int, assistant_id: str, user_message: str) -> str:
    """Query an assistant with a user message."""
    assistant = _assistants.get(assistant_id)
    if not assistant:
        msg = f"❌ Assistant `{assistant_id}` not found"
        send_telegram_message(chat_id, msg)
        return msg

    database_id = assistant["database_id"]
    prompt_id = assistant["prompt_id"]

    # Get prompt content
    prompt_data = _prompts.get(prompt_id)
    if not prompt_data:
        msg = f"❌ Prompt `{prompt_id}` not found for this assistant"
        send_telegram_message(chat_id, msg)
        return msg

    system_prompt = prompt_data["content"]

    # Search relevant data from database
    retrieved_data = search_collection(database_id, user_message, limit=5)
    context = "\n\n".join([r["text"] for r in retrieved_data])

    # Build the full prompt with context
    full_prompt = f"Context from knowledge base:\n{context}\n\nUser question: {user_message}"

    # Call LLM
    send_telegram_message(chat_id, "🤔 Thinking...")

    response = call_llm(system_prompt, full_prompt)
    if response:
        send_telegram_message(chat_id, response)
        return response
    else:
        msg = "❌ Failed to get response from LLM"
        send_telegram_message(chat_id, msg)
        return msg


# ============ Data Management ============


def add_data_to_database(database_name: str, texts: list, metadata: list = None) -> bool:
    """Add data to a database."""
    payloads = None
    if metadata:
        payloads = [{"text": text, **meta} for text, meta in zip(texts, metadata)]
    else:
        payloads = [{"text": text} for text in texts]

    return add_to_collection(database_name, texts, payloads)


def create_assistant(name: str, database_id: str, prompt_id: str) -> Optional[str]:
    """Create a new assistant."""
    import uuid

    if database_id not in list_collections():
        return None
    if prompt_id not in _prompts:
        return None

    aid = str(uuid.uuid4())[:8]
    _assistants[aid] = {
        "name": name,
        "database_id": database_id,
        "prompt_id": prompt_id
    }
    return aid
