"""Main logic - high-level logic for the bot."""
import json
import logging
import asyncio
from typing import Dict, Any, Optional
from telegram import Update
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

from config import Config
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
    handle_prompt_create_response,
    handle_assistant_create_response,
    cmd_data_list,
    cmd_data_show,
    cmd_data_remove,
    cmd_data_remove_all,
    cmd_data_add_bulk_start,
    handle_data_bulk_upload,
    cmd_data_bulk_done,
    _data_bulk_state,
    _assistant_create_state,
)

logger = logging.getLogger(__name__)


# ============ Message Handlers ============


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command."""
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    cmd_start(chat_id, user_id)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /help command."""
    chat_id = update.effective_chat.id
    cmd_help(chat_id)


async def auth_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /auth command."""
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id

    if not context.args:
        await context.bot.send_message(
            chat_id=chat_id,
            text="Usage: /auth <password>"
        )
        return

    password = context.args[0]
    cmd_auth(chat_id, user_id, password)


async def list_assistants_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /assistants command."""
    chat_id = update.effective_chat.id
    cmd_list_assistants(chat_id)


async def assist_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /assist command - select an assistant for RAG queries."""
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id

    if not check_auth(user_id):
        await context.bot.send_message(
            chat_id=chat_id,
            text="❌ This command requires authorization. Use /auth <password>"
        )
        return

    assistant_name = context.args[0] if context.args else None
    cmd_assist(chat_id, user_id, assistant_name)


async def collections_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /collections command."""
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id

    if not check_auth(user_id):
        await context.bot.send_message(
            chat_id=chat_id,
            text="❌ This command requires authorization. Use /auth <password>"
        )
        return

    cmd_database_list(chat_id)


async def collection_create_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /collection_create command."""
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id

    if not check_auth(user_id):
        await context.bot.send_message(
            chat_id=chat_id,
            text="❌ This command requires authorization. Use /auth <password>"
        )
        return

    if not context.args:
        await context.bot.send_message(
            chat_id=chat_id,
            text="Usage: /collection_create <name>"
        )
        return

    name = context.args[0]
    cmd_database_create(chat_id, name)


async def prompts_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /prompts command."""
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id

    if not check_auth(user_id):
        await context.bot.send_message(
            chat_id=chat_id,
            text="❌ This command requires authorization. Use /auth <password>"
        )
        return

    cmd_prompt_list(chat_id)


async def prompt_create_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /prompt_create command."""
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id

    if not check_auth(user_id):
        await context.bot.send_message(
            chat_id=chat_id,
            text="❌ This command requires authorization. Use /auth <password>"
        )
        return

    # If no args, start interactive mode
    if not context.args:
        username = update.effective_user.username
        cmd_prompt_create(chat_id, user_id, author_username=username)
        return

    # If args provided, check for -- separator
    args_text = " ".join(context.args)
    if "--" not in args_text:
        # Start interactive mode instead of showing error
        username = update.effective_user.username
        cmd_prompt_create(chat_id, user_id, author_username=username)
        return

    name, content = args_text.split("--", 1)
    name = name.strip()
    content = content.strip()

    username = update.effective_user.username
    cmd_prompt_create(chat_id, user_id, name, content, username)


async def prompt_show_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /prompt_show command."""
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id

    if not check_auth(user_id):
        await context.bot.send_message(
            chat_id=chat_id,
            text="❌ This command requires authorization. Use /auth <password>"
        )
        return

    if not context.args:
        await context.bot.send_message(
            chat_id=chat_id,
            text="Usage: /prompt_show <id or name>"
        )
        return

    prompt_identifier = context.args[0]
    cmd_prompt_show(chat_id, prompt_identifier)


async def prompt_update_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /prompt_update command."""
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id

    if not check_auth(user_id):
        await context.bot.send_message(
            chat_id=chat_id,
            text="❌ This command requires authorization. Use /auth <password>"
        )
        return

    # Usage: /prompt_update <id> -- <content>
    if len(context.args) < 2:
        await context.bot.send_message(
            chat_id=chat_id,
            text="Usage: /prompt_update <id> -- <content>"
        )
        return

    args_text = " ".join(context.args)
    if "--" not in args_text:
        await context.bot.send_message(
            chat_id=chat_id,
            text="Usage: /prompt_update <id> -- <content>"
        )
        return

    prompt_id, content = args_text.split("--", 1)
    content = content.strip()

    cmd_prompt_update(chat_id, prompt_id, content)


async def assistant_create_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /assistant_create command - interactive or with args."""
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id

    if not check_auth(user_id):
        await context.bot.send_message(
            chat_id=chat_id,
            text="❌ This command requires authorization. Use /auth <password>"
        )
        return

    # If all args provided, create directly
    if len(context.args) >= 3:
        name = context.args[0]
        collection_name = context.args[1]
        prompt_identifier = context.args[2]
        cmd_assistant_create(chat_id, user_id, name, collection_name, prompt_identifier)
        return

    # Otherwise start interactive mode
    name = context.args[0] if context.args else None
    cmd_assistant_create(chat_id, user_id, name=name)


async def data_list_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /data_list command."""
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id

    if not check_auth(user_id):
        await context.bot.send_message(
            chat_id=chat_id,
            text="❌ This command requires authorization. Use /auth <password>"
        )
        return

    if not context.args:
        await context.bot.send_message(
            chat_id=chat_id,
            text="Usage: /data_list <collection_name>"
        )
        return

    collection_name = context.args[0]
    cmd_data_list(chat_id, collection_name)


async def data_show_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /data_show command."""
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id

    if not check_auth(user_id):
        await context.bot.send_message(
            chat_id=chat_id,
            text="❌ This command requires authorization. Use /auth <password>"
        )
        return

    if len(context.args) < 2:
        await context.bot.send_message(
            chat_id=chat_id,
            text="Usage: /data_show <collection_name> <point_id>"
        )
        return

    collection_name = context.args[0]
    point_id = context.args[1]
    cmd_data_show(chat_id, collection_name, point_id)


async def data_remove_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /data_remove command."""
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id

    if not check_auth(user_id):
        await context.bot.send_message(
            chat_id=chat_id,
            text="❌ This command requires authorization. Use /auth <password>"
        )
        return

    if len(context.args) < 2:
        await context.bot.send_message(
            chat_id=chat_id,
            text="Usage: /data_remove <collection_name> <point_id>"
        )
        return

    collection_name = context.args[0]
    point_id = context.args[1]
    cmd_data_remove(chat_id, collection_name, point_id)


async def data_remove_all_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /data_remove_all command."""
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id

    if not check_auth(user_id):
        await context.bot.send_message(
            chat_id=chat_id,
            text="❌ This command requires authorization. Use /auth <password>"
        )
        return

    if not context.args:
        await context.bot.send_message(
            chat_id=chat_id,
            text="Usage: /data_remove_all <collection_name>"
        )
        return

    collection_name = context.args[0]
    cmd_data_remove_all(chat_id, collection_name)


async def data_add_bulk_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /data_add_bulk command."""
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id

    if not check_auth(user_id):
        await context.bot.send_message(
            chat_id=chat_id,
            text="❌ This command requires authorization. Use /auth <password>"
        )
        return

    if not context.args:
        await context.bot.send_message(
            chat_id=chat_id,
            text="Usage: /data_add_bulk <collection_name>"
        )
        return

    collection_name = context.args[0]
    cmd_data_add_bulk_start(chat_id, user_id, collection_name)


async def done_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /done command - finish bulk upload."""
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id

    cmd_data_bulk_done(user_id, chat_id)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle regular messages - query assistants or bulk upload."""
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    text = update.message.text

    if not text:
        return

    # Check for /cancel command
    if text.strip().lower() == "/cancel":
        from src.business_logic import cancel_prompt_create, cancel_assistant_create
        result = cancel_prompt_create(user_id, chat_id) or cancel_assistant_create(user_id, chat_id)
        if result:
            return

    # Check if user is in bulk upload mode
    from src.business_logic import _data_bulk_state
    if user_id in _data_bulk_state:
        handle_data_bulk_upload(user_id, chat_id, text)
        return

    # Check if user is in prompt creation mode
    from src.business_logic import _prompt_create_state
    if user_id in _prompt_create_state:
        username = update.effective_user.username
        handle_prompt_create_response(user_id, chat_id, text, username)
        return

    # Check if user is in assistant creation mode
    from src.business_logic import _assistant_create_state
    if user_id in _assistant_create_state:
        handle_assistant_create_response(user_id, chat_id, text)
        return

    # Check if user has selected an assistant - route to RAG query
    selected_assistant = get_selected_assistant(user_id)
    if selected_assistant:
        query_assistant(chat_id, user_id, str(selected_assistant.id), text)
        return

    await context.bot.send_message(
        chat_id=chat_id,
        text="Please use /assistants to see available assistants, then use /assist <name> to select one."
    )


async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle document uploads - for bulk upload mode."""
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id

    # Check if user is in bulk upload mode
    from src.business_logic import _data_bulk_state
    if user_id in _data_bulk_state:
        # Download and read the document
        document = update.message.document
        file = await context.bot.get_file(document.file_id)

        # Get file content
        import io
        file_content = io.BytesIO()
        await file.download_to_memory(file_content)
        text = file_content.getvalue().decode("utf-8", errors="ignore")

        # Get filename
        filename = document.file_name or "unknown.txt"

        from src.business_logic import handle_data_bulk_upload
        handle_data_bulk_upload(user_id, chat_id, text, filename)
        return

    # Not in bulk mode - inform user
    await context.bot.send_message(
        chat_id=chat_id,
        text="Send /data_add_bulk <collection> first to start bulk upload, then send documents."
    )


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle errors."""
    logger.error(f"Update {update} caused error {context.error}")


# ============ Command Registration ============


async def register_commands(application: Application) -> None:
    """Register bot commands with Telegram using setMyCommands."""
    from telegram import BotCommand

    commands = [
        BotCommand("start", "Start the bot"),
        BotCommand("help", "Show help information"),
        BotCommand("auth", "Authorize with password"),
        BotCommand("assistants", "List available assistants"),
        BotCommand("assist", "Select an assistant for queries"),
        BotCommand("collections", "List collections"),
        BotCommand("collection_create", "Create a new collection"),
        BotCommand("prompts", "List prompts"),
        BotCommand("prompt_create", "Create a new prompt"),
        BotCommand("prompt_show", "Show prompt content"),
        BotCommand("prompt_update", "Update a prompt"),
        BotCommand("assistant_create", "Create a new assistant"),
        BotCommand("data_list", "List data in collection"),
        BotCommand("data_show", "Show data record"),
        BotCommand("data_remove", "Remove data record"),
        BotCommand("data_remove_all", "Remove all data"),
        BotCommand("data_add_bulk", "Bulk add data"),
        BotCommand("done", "Finish bulk upload"),
    ]

    try:
        await application.bot.set_my_commands(commands)
        logger.info("Commands registered with Telegram")
    except Exception as e:
        logger.error(f"Failed to register commands: {e}")


# ============ Main Entry Point ============


def main():
    """Main entry point."""
    import os
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    logging.basicConfig(
        level=getattr(logging, log_level, logging.INFO),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Initialize database
    init_database()

    if Config.USE_WEBHOOK:
        run_webhook()
    else:
        # Simple polling - proxy should be handled by environment
        application = ApplicationBuilder().token(Config.TELEGRAM_BOT_API).build()

        application.add_handler(CommandHandler("start", start_command))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("auth", auth_command))
        application.add_handler(CommandHandler("assistants", list_assistants_command))
        application.add_handler(CommandHandler("assist", assist_command))
        application.add_handler(CommandHandler("collections", collections_command))
        application.add_handler(CommandHandler("collection_create", collection_create_command))
        application.add_handler(CommandHandler("prompts", prompts_command))
        application.add_handler(CommandHandler("prompt_create", prompt_create_command))
        application.add_handler(CommandHandler("prompt_show", prompt_show_command))
        application.add_handler(CommandHandler("prompt_update", prompt_update_command))
        application.add_handler(CommandHandler("assistant_create", assistant_create_command))
        application.add_handler(CommandHandler("data_list", data_list_command))
        application.add_handler(CommandHandler("data_show", data_show_command))
        application.add_handler(CommandHandler("data_remove", data_remove_command))
        application.add_handler(CommandHandler("data_remove_all", data_remove_all_command))
        application.add_handler(CommandHandler("data_add_bulk", data_add_bulk_command))
        application.add_handler(CommandHandler("done", done_command))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        application.add_handler(MessageHandler(filters.Document.ALL, handle_document))
        application.add_error_handler(error_handler)

        logger.info("Starting bot in polling mode...")
        application.run_polling()


def run_polling_with_health():
    """Run bot with polling and health endpoint."""
    import subprocess
    import time

    # Start health check server as subprocess
    health_proc = subprocess.Popen(
        ["python", "-c", """
from flask import Flask
app = Flask(__name__)
@app.route('/health')
def health():
    return 'OK', 200
app.run(host='0.0.0.0', port=5000, threaded=True)
"""],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    # Give health server time to start
    time.sleep(2)

    # Run polling
    application = ApplicationBuilder().token(Config.TELEGRAM_BOT_API).build()

    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("auth", auth_command))
    application.add_handler(CommandHandler("assistants", list_assistants_command))
    application.add_handler(CommandHandler("collections", collections_command))
    application.add_handler(CommandHandler("collection_create", collection_create_command))
    application.add_handler(CommandHandler("prompts", prompts_command))
    application.add_handler(CommandHandler("prompt_create", prompt_create_command))
    application.add_handler(CommandHandler("prompt_show", prompt_show_command))
    application.add_handler(CommandHandler("prompt_update", prompt_update_command))
    application.add_handler(CommandHandler("assistant_create", assistant_create_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_error_handler(error_handler)

    async def run_async():
        await register_commands(application)
        await application.run_polling()

    try:
        asyncio.run(run_async())
    finally:
        health_proc.terminate()


def run_webhook():
    """Run bot with webhook (also serves health endpoint)."""
    from flask import Flask, request as flask_request
    from telegram import Update
    from telegram.ext import ApplicationBuilder

    app = Flask(__name__)

    application = ApplicationBuilder().token(Config.TELEGRAM_BOT_API).build()

    # Register handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("auth", auth_command))
    application.add_handler(CommandHandler("assistants", list_assistants_command))
    application.add_handler(CommandHandler("collections", collections_command))
    application.add_handler(CommandHandler("collection_create", collection_create_command))
    application.add_handler(CommandHandler("prompts", prompts_command))
    application.add_handler(CommandHandler("prompt_create", prompt_create_command))
    application.add_handler(CommandHandler("prompt_show", prompt_show_command))
    application.add_handler(CommandHandler("prompt_update", prompt_update_command))
    application.add_handler(CommandHandler("assistant_create", assistant_create_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Health check endpoint
    @app.route("/health", methods=["GET"])
    def health():
        return "OK", 200

    @app.route("/webhook", methods=["POST"])
    def webhook_handler():
        update = Update.de_json(flask_request.get_json(), application.bot)
        application.run_until_complete(application.process_update(update))
        return "OK"

    logger.info("Starting bot in webhook mode...")
    app.run(host="0.0.0.0", port=5000)


if __name__ == "__main__":
    main()
