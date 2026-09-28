"""Main logic - high-level logic for the bot."""
import json
import logging
from typing import Dict, Any, Optional
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

from config import Config
from src.business_logic import (
    cmd_start,
    cmd_auth,
    cmd_list_assistants,
    cmd_database_list,
    cmd_database_create,
    cmd_prompt_list,
    cmd_prompt_create,
    cmd_prompt_show,
    cmd_prompt_update,
    query_assistant,
    check_auth,
)

logger = logging.getLogger(__name__)


# ============ Message Handlers ============


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command."""
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    cmd_start(chat_id, user_id)


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
    """Handle /list-assistants command."""
    chat_id = update.effective_chat.id
    cmd_list_assistants(chat_id)


async def database_list_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /database-list command."""
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id

    if not check_auth(user_id):
        await context.bot.send_message(
            chat_id=chat_id,
            text="❌ This command requires authorization. Use /auth <password>"
        )
        return

    cmd_database_list(chat_id)


async def database_create_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /database-create command."""
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
            text="Usage: /database-create <name>"
        )
        return

    name = context.args[0]
    cmd_database_create(chat_id, name)


async def prompt_list_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /prompt-list command."""
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
    """Handle /prompt-create command."""
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id

    if not check_auth(user_id):
        await context.bot.send_message(
            chat_id=chat_id,
            text="❌ This command requires authorization. Use /auth <password>"
        )
        return

    # Usage: /prompt-create <name> -- <content>
    if not context.args:
        await context.bot.send_message(
            chat_id=chat_id,
            text="Usage: /prompt-create <name> -- <content>"
        )
        return

    args_text = " ".join(context.args)
    if "--" not in args_text:
        await context.bot.send_message(
            chat_id=chat_id,
            text="Usage: /prompt-create <name> -- <content>"
        )
        return

    name, content = args_text.split("--", 1)
    name = name.strip()
    content = content.strip()

    cmd_prompt_create(chat_id, name, content)


async def prompt_show_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /prompt-show command."""
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
            text="Usage: /prompt-show <id>"
        )
        return

    prompt_id = context.args[0]
    cmd_prompt_show(chat_id, prompt_id)


async def prompt_update_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /prompt-update command."""
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id

    if not check_auth(user_id):
        await context.bot.send_message(
            chat_id=chat_id,
            text="❌ This command requires authorization. Use /auth <password>"
        )
        return

    # Usage: /prompt-update <id> -- <content>
    if len(context.args) < 2:
        await context.bot.send_message(
            chat_id=chat_id,
            text="Usage: /prompt-update <id> -- <content>"
        )
        return

    args_text = " ".join(context.args)
    if "--" not in args_text:
        await context.bot.send_message(
            chat_id=chat_id,
            text="Usage: /prompt-update <id> -- <content>"
        )
        return

    prompt_id, content = args_text.split("--", 1)
    content = content.strip()

    cmd_prompt_update(chat_id, prompt_id, content)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle regular messages - query assistants."""
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    text = update.message.text

    if not text:
        return

    # TODO: Implement assistant selection by name/ID
    # For now, show available assistants
    await context.bot.send_message(
        chat_id=chat_id,
        text="Please use /list-assistants to see available assistants, then specify which one you want to query."
    )


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle errors."""
    logger.error(f"Update {update} caused error {context.error}")


# ============ Webhook Handler ============


async def webhook(request: Dict[str, Any]) -> str:
    """Handle webhook requests."""
    from telegram import Update
    from telegram.ext import ApplicationBuilder, ContextTypes

    application = ApplicationBuilder().token(Config.TELEGRAM_BOT_API).build()

    # Register handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("auth", auth_command))
    application.add_handler(CommandHandler("list-assistants", list_assistants_command))
    application.add_handler(CommandHandler("database-list", database_list_command))
    application.add_handler(CommandHandler("database-create", database_create_command))
    application.add_handler(CommandHandler("prompt-list", prompt_list_command))
    application.add_handler(CommandHandler("prompt-create", prompt_create_command))
    application.add_handler(CommandHandler("prompt-show", prompt_show_command))
    application.add_handler(CommandHandler("prompt-update", prompt_update_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Process update
    update = Update.de_json(request, application.bot)
    await application.process_update(update)

    return "OK"


# ============ Main Entry Point ============


def run_polling():
    """Run bot with polling."""
    if not Config.TELEGRAM_BOT_API:
        raise ValueError("TELEGRAM_BOT_API not configured")

    application = ApplicationBuilder().token(Config.TELEGRAM_BOT_API).build()

    # Register handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("auth", auth_command))
    application.add_handler(CommandHandler("list-assistants", list_assistants_command))
    application.add_handler(CommandHandler("database-list", database_list_command))
    application.add_handler(CommandHandler("database-create", database_create_command))
    application.add_handler(CommandHandler("prompt-list", prompt_list_command))
    application.add_handler(CommandHandler("prompt-create", prompt_create_command))
    application.add_handler(CommandHandler("prompt-show", prompt_show_command))
    application.add_handler(CommandHandler("prompt-update", prompt_update_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    application.add_error_handler(error_handler)

    logger.info("Starting bot in polling mode...")
    application.run_polling()


def run_webhook():
    """Run bot with webhook."""
    if not Config.TELEGRAM_BOT_API:
        raise ValueError("TELEGRAM_BOT_API not configured")

    from flask import Flask, request as flask_request
    from telegram import Update
    from telegram.ext import ApplicationBuilder, ContextTypes

    app = Flask(__name__)

    application = ApplicationBuilder().token(Config.TELEGRAM_BOT_API).build()

    # Register handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("auth", auth_command))
    application.add_handler(CommandHandler("list-assistants", list_assistants_command))
    application.add_handler(CommandHandler("database-list", database_list_command))
    application.add_handler(CommandHandler("database-create", database_create_command))
    application.add_handler(CommandHandler("prompt-list", prompt_list_command))
    application.add_handler(CommandHandler("prompt-create", prompt_create_command))
    application.add_handler(CommandHandler("prompt-show", prompt_show_command))
    application.add_handler(CommandHandler("prompt-update", prompt_update_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    @app.route("/webhook", methods=["POST"])
    def webhook_handler():
        update = Update.de_json(flask_request.get_json(), application.bot)
        application.run_until_complete(application.process_update(update))
        return "OK"

    logger.info("Starting bot in webhook mode...")
    app.run(host="0.0.0.0", port=5000)


def main():
    """Main entry point."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    if Config.USE_WEBHOOK:
        run_webhook()
    else:
        run_polling()


if __name__ == "__main__":
    main()
