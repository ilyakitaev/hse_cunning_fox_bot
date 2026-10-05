"""Business logic - bot commands implemented as python functions."""
import logging
import os
from typing import Optional

log_level = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, log_level, logging.INFO),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
from src.api import (
    send_telegram_message,
    create_collection as create_qdrant_collection,
    delete_collection,
    list_collections as list_qdrant_collections,
    add_to_collection,
    search_collection,
    call_llm,
    list_points,
    get_point,
    delete_point,
    delete_all_points,
)
from src.database import (
    is_user_authorized,
    authorize_user as db_authorize_user,
    get_all_prompts,
    get_prompt_by_id,
    get_prompt_by_name,
    create_prompt,
    update_prompt,
    get_all_collections,
    get_collection_by_name,
    create_collection as create_db_collection,
    get_all_assistants,
    get_assistant_by_id,
    create_assistant as create_db_assistant,
    init_db,
    Assistant,
)
from src.migrations import run_migrations

logger = logging.getLogger(__name__)


def check_auth(user_id: int) -> bool:
    """Check if user is authorized."""
    return is_user_authorized(user_id)


def authorize_user(user_id: int) -> None:
    """Authorize a user."""
    db_authorize_user(user_id)


def get_authorized_users() -> list:
    """Get all authorized users (not implemented for now)."""
    return []


def init_database() -> None:
    """Initialize the database."""
    init_db()
    run_migrations()


# ============ Public Commands ============


def cmd_start(chat_id: int, user_id: int) -> str:
    """Handle /start command."""
    welcome = """👋 *Welcome to HSE Cunning Fox Bot!*

I'm a RAG-powered assistant. Here's how to use me:

*Public Commands:*
/start - Show this welcome message
/help - Show help information
/auth <password> - Authorize yourself
/assistants - See available assistants

*Private Commands (authorized users only):*
/collections - List all collections
/collection-create <name> - Create a new collection
/prompts - List all prompts
/prompt-create <name> -- <content> - Create a new prompt
/prompt-show <id or name> - Show prompt content
/prompt-update <id> -- <content> - Update prompt
/assistant-create <name> <collection> <prompt_id> - Create new assistant

*Using an Assistant:*
Just send a message to any assistant listed in /assistants!
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
    assistants = get_all_assistants()
    if not assistants:
        msg = "No assistants configured yet."
    else:
        msg = "*Available Assistants:*\n\n"
        for assistant in assistants:
            msg += f"• `{assistant.id}`: {assistant.name} (Collection: {assistant.collection.name}, Prompt: {assistant.system_prompt.name})\n"

    send_telegram_message(chat_id, msg)
    return msg


# ============ Private Commands ============


def cmd_database_list(chat_id: int) -> str:
    """Handle /database-list command."""
    # Get from both Qdrant and system DB
    qdrant_collections = list_qdrant_collections()
    db_collections = get_all_collections()

    all_collections = list(set(qdrant_collections + [c.name for c in db_collections]))

    if not all_collections:
        msg = "No databases exist yet."
    else:
        msg = "*Existing Databases:*\n\n"
        for db in all_collections:
            msg += f"• {db}\n"

    send_telegram_message(chat_id, msg)
    return msg


def cmd_database_create(chat_id: int, name: str) -> str:
    """Handle /database-create command."""
    # Create in Qdrant
    if create_qdrant_collection(name):
        # Also save to system DB
        create_db_collection(name)
        msg = f"✅ Database `{name}` created successfully!"
    else:
        msg = f"❌ Failed to create database `{name}`"

    send_telegram_message(chat_id, msg)
    return msg


def cmd_prompt_list(chat_id: int) -> str:
    """Handle /prompts command."""
    prompts = get_all_prompts()
    if not prompts:
        msg = "No prompts exist yet."
    else:
        msg = "*Existing Prompts:*\n\n"
        for prompt in prompts:
            created = prompt.created_at.strftime("%Y-%m-%d %H:%M") if prompt.created_at else "N/A"
            updated = prompt.updated_at.strftime("%Y-%m-%d %H:%M") if prompt.updated_at else "N/A"
            author = prompt.author_telegram_username or "Unknown"
            msg += f"• `{prompt.id}`: {prompt.name}\n"
            msg += f"  Created: {created}, Updated: {updated}, Author: @{author}\n"

    send_telegram_message(chat_id, msg)
    return msg


# Prompt creation state: user_id -> {"name": str, "author_username": str}
_prompt_create_state: dict = {}


def cmd_prompt_create(chat_id: int, user_id: int, name: str = None, content: str = None, author_username: str = None) -> str:
    """Handle /prompt_create command - interactive or with args."""
    # If both name and content provided, create prompt directly
    if name and content:
        prompt = create_prompt(name, content, author_username)
        msg = f"✅ Prompt created!\n*ID:* `{prompt.id}`\n*Name:* {name}"
        send_telegram_message(chat_id, msg)
        return msg

    # Start interactive mode - ask for name
    if user_id not in _prompt_create_state:
        _prompt_create_state[user_id] = {"name": None, "author_username": author_username}
        msg = "📝 *Create New Prompt*\n\nPlease enter the prompt name:"
        send_telegram_message(chat_id, msg)
        return msg

    # Already in process - should not happen via command
    msg = "Prompt creation in progress. Please enter the name or /cancel to abort."
    send_telegram_message(chat_id, msg)
    return msg


def handle_prompt_create_response(user_id: int, chat_id: int, text: str, author_username: str = None) -> str:
    """Handle response during interactive prompt creation."""
    if user_id not in _prompt_create_state:
        return None

    state = _prompt_create_state[user_id]

    if state.get("name") is None:
        # Waiting for name
        state["name"] = text.strip()
        state["author_username"] = author_username
        msg = f"✅ Name saved: *{text.strip()}*\n\nNow enter the prompt content:"
        send_telegram_message(chat_id, msg)
        return msg
    else:
        # Waiting for content - create prompt
        prompt = create_prompt(state["name"], text, state.get("author_username"))
        msg = f"✅ Prompt created!\n*ID:* `{prompt.id}`\n*Name:* {state['name']}"
        send_telegram_message(chat_id, msg)
        del _prompt_create_state[user_id]
        return msg


def cancel_prompt_create(user_id: int, chat_id: int) -> str:
    """Cancel interactive prompt creation."""
    if user_id in _prompt_create_state:
        del _prompt_create_state[user_id]
        msg = "❌ Prompt creation cancelled."
        send_telegram_message(chat_id, msg)
        return msg
    return None


# Assistant creation state: user_id -> {"name": str, "collection_name": str, "prompt_id": str}
_assistant_create_state: dict = {}


def cmd_assistant_create(chat_id: int, user_id: int, name: str = None, collection_name: str = None, prompt_identifier: str = None) -> str:
    """Handle /assistant_create command - interactive or with args."""
    # If all args provided, create assistant directly
    if name and collection_name and prompt_identifier:
        return _create_assistant_direct(chat_id, name, collection_name, prompt_identifier)

    # Start interactive mode
    if user_id not in _assistant_create_state:
        # If name provided but not others, start from beginning
        if name:
            _assistant_create_state[user_id] = {"name": name, "collection_name": None, "prompt_id": None}
            msg = f"✅ Name saved: *{name}*\n\nNow enter the collection name:"
        else:
            _assistant_create_state[user_id] = {"name": None, "collection_name": None, "prompt_id": None}
            msg = "🤖 *Create New Assistant*\n\nPlease enter the assistant name:"
        send_telegram_message(chat_id, msg)
        return msg

    # Already in process
    msg = "Assistant creation in progress. Enter the next value or /cancel to abort."
    send_telegram_message(chat_id, msg)
    return msg


def _create_assistant_direct(chat_id: int, name: str, collection_name: str, prompt_identifier: str) -> str:
    """Create assistant with direct arguments."""
    # Validate collection exists in Qdrant
    qdrant_collections = list_qdrant_collections()
    if collection_name not in qdrant_collections:
        msg = f"❌ Collection `{collection_name}` not found in Qdrant. Use /collections to see available."
        send_telegram_message(chat_id, msg)
        return msg

    # Validate prompt exists (try ID first, then name)
    prompt = None
    try:
        pid = int(prompt_identifier)
        prompt = get_prompt_by_id(pid)
    except ValueError:
        prompt = get_prompt_by_name(prompt_identifier)

    if not prompt:
        msg = f"❌ Prompt `{prompt_identifier}` not found. Use /prompts to see available."
        send_telegram_message(chat_id, msg)
        return msg

    # Get or create collection in system DB
    db_collection = get_collection_by_name(collection_name)
    if not db_collection:
        db_collection = create_db_collection(collection_name)

    # Create assistant
    assistant = create_db_assistant(name, db_collection.id, prompt.id)
    msg = f"✅ Assistant created!\n*ID:* `{assistant.id}`\n*Name:* {name}"
    send_telegram_message(chat_id, msg)
    return msg


def handle_assistant_create_response(user_id: int, chat_id: int, text: str) -> str:
    """Handle response during interactive assistant creation."""
    if user_id not in _assistant_create_state:
        return None

    state = _assistant_create_state[user_id]

    if state.get("name") is None:
        # Waiting for name
        state["name"] = text.strip()
        msg = f"✅ Name saved: *{text.strip()}*\n\nNow enter the collection name:"
        send_telegram_message(chat_id, msg)
        return msg
    elif state.get("collection_name") is None:
        # Waiting for collection name
        state["collection_name"] = text.strip()
        # Validate collection exists
        qdrant_collections = list_qdrant_collections()
        if text.strip() not in qdrant_collections:
            msg = f"❌ Collection `{text.strip()}` not found. Use /collections to see available."
            send_telegram_message(chat_id, msg)
            del _assistant_create_state[user_id]
            return msg
        msg = f"✅ Collection saved: *{text.strip()}*\n\nNow enter the prompt ID or name:"
        send_telegram_message(chat_id, msg)
        return msg
    else:
        # Waiting for prompt - create assistant
        prompt_identifier = text.strip()
        name = state["name"]
        collection_name = state["collection_name"]

        # Validate prompt exists
        prompt = None
        try:
            pid = int(prompt_identifier)
            prompt = get_prompt_by_id(pid)
        except ValueError:
            prompt = get_prompt_by_name(prompt_identifier)

        if not prompt:
            msg = f"❌ Prompt `{prompt_identifier}` not found. Use /prompts to see available."
            send_telegram_message(chat_id, msg)
            del _assistant_create_state[user_id]
            return msg

        # Get or create collection in system DB
        db_collection = get_collection_by_name(collection_name)
        if not db_collection:
            db_collection = create_db_collection(collection_name)

        # Create assistant
        assistant = create_db_assistant(name, db_collection.id, prompt.id)
        msg = f"✅ Assistant created!\n*ID:* `{assistant.id}`\n*Name:* {name}"
        send_telegram_message(chat_id, msg)
        del _assistant_create_state[user_id]
        return msg


def cancel_assistant_create(user_id: int, chat_id: int) -> str:
    """Cancel interactive assistant creation."""
    if user_id in _assistant_create_state:
        del _assistant_create_state[user_id]
        msg = "❌ Assistant creation cancelled."
        send_telegram_message(chat_id, msg)
        return msg
    return None


def cmd_prompt_show(chat_id: int, prompt_identifier: str) -> str:
    """Handle /prompt_show command - accepts ID or name."""
    # Try as ID first
    try:
        pid = int(prompt_identifier)
        prompt = get_prompt_by_id(pid)
    except ValueError:
        # Try as name
        prompt = get_prompt_by_name(prompt_identifier)

    if not prompt:
        msg = f"❌ Prompt `{prompt_identifier}` not found"
    else:
        msg = f"*Prompt: {prompt.name}* (ID: `{prompt.id}`)\n\n{prompt.prompt_data}"

    send_telegram_message(chat_id, msg)
    return msg


def cmd_prompt_update(chat_id: int, prompt_id: str, content: str) -> str:
    """Handle /prompt-update command."""
    try:
        pid = int(prompt_id)
    except ValueError:
        msg = f"❌ Invalid prompt ID: {prompt_id}"
        send_telegram_message(chat_id, msg)
        return msg

    prompt = update_prompt(pid, content)
    if not prompt:
        msg = f"❌ Prompt `{prompt_id}` not found"
    else:
        msg = f"✅ Prompt `{prompt_id}` updated!"

    send_telegram_message(chat_id, msg)
    return msg


def cmd_help(chat_id: int) -> str:
    """Handle /help command."""
    help_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "help.txt")
    try:
        with open(help_file, "r", encoding="utf-8") as f:
            content = f.read()
        send_telegram_message(chat_id, content)
        return "Help sent"
    except FileNotFoundError:
        msg = "Help file not found."
        send_telegram_message(chat_id, msg)
        return msg


# ============ Assistant Interaction ============


def query_assistant(chat_id: int, user_id: int, assistant_id: str, user_message: str) -> str:
    """Query an assistant with a user message."""
    try:
        aid = int(assistant_id)
    except ValueError:
        msg = f"❌ Invalid assistant ID: {assistant_id}"
        send_telegram_message(chat_id, msg)
        return msg

    assistant = get_assistant_by_id(aid)
    if not assistant:
        msg = f"❌ Assistant `{assistant_id}` not found"
        send_telegram_message(chat_id, msg)
        return msg

    # Get prompt content - check for None relationships
    if not assistant.system_prompt:
        logger.error(f"Assistant {assistant_id} has no system_prompt")
        msg = "❌ Assistant configuration error: missing prompt"
        send_telegram_message(chat_id, msg)
        return msg

    try:
        system_prompt = assistant.system_prompt.prompt_data
    except AttributeError as e:
        logger.error(f"Failed to get system prompt: {e}")
        msg = "❌ Assistant configuration error: missing prompt"
        send_telegram_message(chat_id, msg)
        return msg

    if not assistant.collection:
        logger.error(f"Assistant {assistant_id} has no collection")
        msg = "❌ Assistant configuration error: missing collection"
        send_telegram_message(chat_id, msg)
        return msg

    # Search relevant data from database (Qdrant)
    try:
        collection_name = assistant.collection.name
    except AttributeError as e:
        logger.error(f"Failed to get collection: {e}")
        msg = "❌ Assistant configuration error: missing collection"
        send_telegram_message(chat_id, msg)
        return msg

    try:
        score_threshold = assistant.score_threshold or 0.0
        retrieved_data = search_collection(
            collection_name, user_message, limit=5, score_threshold=score_threshold
        )
    except Exception as e:
        logger.error(f"Search collection failed: {e}")
        retrieved_data = []

    if not retrieved_data:
        context = ""
    else:
        # Filter out None entries and get text
        context = "\n\n".join([r.get("text", "") for r in retrieved_data if r])

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


# User selected assistant state: user_id -> assistant_id
_selected_assistant_state: dict = {}


def cmd_assist(chat_id: int, user_id: int, assistant_name: str = None) -> str:
    """Handle /assist command - select an assistant for RAG queries."""
    if not assistant_name:
        # Show current selection or help
        if user_id in _selected_assistant_state:
            assistant_id = _selected_assistant_state[user_id]
            assistant = get_assistant_by_id(assistant_id)
            if assistant:
                msg = f"Currently selected assistant: *{assistant.name}* (ID: `{assistant.id}`)\n\nSend a message to query this assistant."
            else:
                msg = "No assistant selected. Use /assist <name> to select an assistant."
                del _selected_assistant_state[user_id]
        else:
            msg = "No assistant selected. Use /assist <name> to select an assistant."
        send_telegram_message(chat_id, msg)
        return msg

    # Find assistant by name
    assistants = get_all_assistants()
    assistant = None
    for a in assistants:
        if a.name.lower() == assistant_name.lower():
            assistant = a
            break

    if not assistant:
        msg = f"❌ Assistant `{assistant_name}` not found. Use /assistants to see available."
        send_telegram_message(chat_id, msg)
        return msg

    # Select the assistant
    _selected_assistant_state[user_id] = assistant.id
    msg = f"✅ Assistant *{assistant.name}* selected!\n\nSend a message to query this assistant."
    send_telegram_message(chat_id, msg)
    return msg


def get_selected_assistant(user_id: int) -> Optional[Assistant]:
    """Get the currently selected assistant for a user."""
    if user_id not in _selected_assistant_state:
        return None
    return get_assistant_by_id(_selected_assistant_state[user_id])


def clear_selected_assistant(user_id: int) -> None:
    """Clear the selected assistant for a user."""
    if user_id in _selected_assistant_state:
        del _selected_assistant_state[user_id]


# ============ Data Management ============


def add_data_to_database(database_name: str, texts: list, metadata: list = None) -> bool:
    """Add data to a database."""
    payloads = None
    if metadata:
        payloads = [{"text": text, **meta} for text, meta in zip(texts, metadata)]
    else:
        payloads = [{"text": text} for text in texts]

    return add_to_collection(database_name, texts, payloads)


# ============ Data Management Commands ============


# User state for bulk upload - dict: user_id -> {"collection": str, "files": list}
_data_bulk_state: dict = {}


def cmd_data_list(chat_id: int, collection_name: str) -> str:
    """Handle /data_list command."""
    from src.api import list_points as api_list_points

    points = api_list_points(collection_name)
    if not points:
        msg = f"No records found in collection `{collection_name}`."
    else:
        msg = f"*Records in {collection_name}:*\n\n"
        msg += "*ID | Filename*\n"
        msg += "---|---\n"
        for point in points:
            filename = point.get("filename", "") or "N/A"
            msg += f"`{point['id']}` | {filename}\n"

    send_telegram_message(chat_id, msg)
    return msg


def cmd_data_show(chat_id: int, collection_name: str, point_id: str) -> str:
    """Handle /data_show command."""
    from src.api import get_point as api_get_point

    point = api_get_point(collection_name, point_id)
    if not point:
        msg = f"❌ Record `{point_id}` not found in collection `{collection_name}`."
    else:
        filename = point.get("filename", "") or "N/A"
        payload = point.get("payload", "") or "N/A"
        msg = f"*Record Details:*\n\n"
        msg += f"*ID:* `{point['id']}`\n"
        msg += f"*Filename:* {filename}\n"
        msg += f"*Content:*\n{payload}"

    send_telegram_message(chat_id, msg)
    return msg


def cmd_data_remove(chat_id: int, collection_name: str, point_id: str) -> str:
    """Handle /data_remove command."""
    from src.api import delete_point as api_delete_point

    # First check if point exists
    from src.api import get_point as api_get_point
    point = api_get_point(collection_name, point_id)

    if not point:
        msg = f"❌ Record `{point_id}` not found in collection `{collection_name}`."
    else:
        filename = point.get("filename", "") or "N/A"
        if api_delete_point(collection_name, point_id):
            msg = f"✅ Record `{point_id}` ({filename}) deleted from `{collection_name}`."
        else:
            msg = f"❌ Failed to delete record `{point_id}`."

    send_telegram_message(chat_id, msg)
    return msg


def cmd_data_remove_all(chat_id: int, collection_name: str) -> str:
    """Handle /data_remove_all command."""
    from src.api import delete_all_points as api_delete_all_points

    # Check if there are any records
    from src.api import list_points as api_list_points
    points = api_list_points(collection_name)

    if not points:
        msg = f"No records to delete in collection `{collection_name}`."
    else:
        count = len(points)
        if api_delete_all_points(collection_name):
            msg = f"✅ All {count} records deleted from `{collection_name}`."
        else:
            msg = f"❌ Failed to delete records from `{collection_name}`."

    send_telegram_message(chat_id, msg)
    return msg


def cmd_data_add_bulk_start(chat_id: int, user_id: int, collection_name: str) -> str:
    """Handle /data_add_bulk command - starts interactive bulk upload."""
    # Verify collection exists
    qdrant_collections = list_qdrant_collections()
    if collection_name not in qdrant_collections:
        msg = f"❌ Collection `{collection_name}` not found. Use /collections to see available."
        send_telegram_message(chat_id, msg)
        return msg

    # Set user state for bulk upload
    _data_bulk_state[user_id] = {"collection": collection_name, "files": []}

    msg = f"📎 *Bulk Upload Mode Started*\n\n"
    msg += f"Collection: `{collection_name}`\n\n"
    msg += "Send me the text files or messages you want to add.\n"
    msg += "When done, send /done to finish."

    send_telegram_message(chat_id, msg)
    return msg


def handle_data_bulk_upload(user_id: int, chat_id: int, text: str, filename: str = None) -> str:
    """Handle incoming text or document during bulk upload mode."""
    if user_id not in _data_bulk_state:
        return None

    state = _data_bulk_state[user_id]
    collection_name = state["collection"]

    # Add text to files list with optional filename
    if filename:
        state["files"].append({"text": text, "filename": filename})
    else:
        state["files"].append(text)

    count = len(state["files"])
    if filename:
        msg = f"✅ Added {filename} ({count} items so far). Send more or /done to finish."
    else:
        msg = f"✅ Added text ({count} items so far). Send more or /done to finish."

    send_telegram_message(chat_id, msg)
    return msg


def cmd_data_bulk_done(user_id: int, chat_id: int) -> str:
    """Handle /done command - finish bulk upload."""
    if user_id not in _data_bulk_state:
        msg = "No active bulk upload session. Use /data_add_bulk <collection> to start."
        send_telegram_message(chat_id, msg)
        return msg

    state = _data_bulk_state[user_id]
    collection_name = state["collection"]
    files = state["files"]

    if not files:
        msg = "No content added. Bulk upload cancelled."
        send_telegram_message(chat_id, msg)
        del _data_bulk_state[user_id]
        return msg

    # Separate texts and metadata from dict format
    texts = []
    metadata = []
    for item in files:
        if isinstance(item, dict):
            texts.append(item.get("text", ""))
            filename = item.get("filename", "")
            metadata.append({"filename": filename} if filename else {})
        else:
            texts.append(item)
            metadata.append({})

    # Add all texts to collection
    success = add_data_to_database(collection_name, texts, metadata)

    if success:
        msg = f"✅ Added {len(files)} records to `{collection_name}`!"
    else:
        msg = f"❌ Failed to add records to `{collection_name}`."

    send_telegram_message(chat_id, msg)

    # Clear state
    del _data_bulk_state[user_id]
    return msg
