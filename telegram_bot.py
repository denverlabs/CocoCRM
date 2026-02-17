#!/usr/bin/env python3
"""
Telegram Bot for CocoCRM
Handles /login command to generate temporary access tokens for AI agents
"""

import os
import asyncio
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Configuration
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
TELEGRAM_API_KEY = os.environ.get('TELEGRAM_API_KEY')
BASE_URL = os.environ.get('BASE_URL', 'https://cococrm.onrender.com')

# Authorized users (can be Telegram IDs or usernames)
AUTHORIZED_USERS = os.environ.get('AUTHORIZED_TELEGRAM_USERS', '').split(',')


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    await update.message.reply_html(
        f"👋 Hello {user.mention_html()}!\n\n"
        f"I'm the CocoCRM bot. I can help you access the CRM system.\n\n"
        f"Available commands:\n"
        f"/login - Get a temporary login link (180 minutes)\n"
        f"/help - Show this help message"
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    await update.message.reply_text(
        "🤖 CocoCRM Bot Help\n\n"
        "Commands:\n"
        "/login - Generate a temporary login link to access the CRM\n"
        "/help - Show this help message\n\n"
        "The login link is valid for 180 minutes (3 hours)."
    )


async def login_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /login command to generate a temporary access token."""
    user = update.effective_user
    telegram_id = str(user.id)
    username = user.username

    logger.info(f"Login request from user: {username} (ID: {telegram_id})")

    # Send "generating..." message
    status_message = await update.message.reply_text("🔐 Generating your login link...")

    try:
        # Call the backend API to generate token
        api_url = f"{BASE_URL}/api/telegram/generate-token"

        payload = {
            'api_key': TELEGRAM_API_KEY,
            'telegram_id': telegram_id,
            'username': username
        }

        logger.info(f"Calling API: {api_url}")

        response = requests.post(api_url, json=payload, timeout=10)

        if response.status_code == 200:
            data = response.json()

            if data.get('success'):
                token = data.get('token')
                login_url = data.get('url')
                expires_in = data.get('expires_in', 180)

                # Send success message with login link
                await status_message.edit_text(
                    f"✅ Login link generated successfully!\n\n"
                    f"🔗 Click here to access CocoCRM:\n"
                    f"{login_url}\n\n"
                    f"⏱ Valid for: {expires_in} minutes\n\n"
                    f"🔒 This link is personal and temporary. Don't share it!"
                )

                logger.info(f"✅ Token generated successfully for {username}")
            else:
                error_msg = data.get('message', 'Unknown error')
                await status_message.edit_text(
                    f"❌ Error: {error_msg}\n\n"
                    f"Please contact the administrator."
                )
                logger.error(f"API returned error: {error_msg}")
        else:
            await status_message.edit_text(
                f"❌ Server error (HTTP {response.status_code})\n\n"
                f"Please try again later or contact the administrator."
            )
            logger.error(f"HTTP error: {response.status_code} - {response.text}")

    except requests.exceptions.Timeout:
        await status_message.edit_text(
            "⏰ Request timeout. The server might be starting up.\n"
            "Please try again in a few moments."
        )
        logger.error("Request timeout")

    except requests.exceptions.RequestException as e:
        await status_message.edit_text(
            f"❌ Connection error: {str(e)}\n\n"
            f"Please try again later."
        )
        logger.error(f"Request exception: {e}")

    except Exception as e:
        await status_message.edit_text(
            f"❌ Unexpected error: {str(e)}\n\n"
            f"Please contact the administrator."
        )
        logger.error(f"Unexpected error: {e}")


def main() -> None:
    """Start the bot."""
    if not TELEGRAM_BOT_TOKEN:
        logger.error("❌ TELEGRAM_BOT_TOKEN not set!")
        return

    if not TELEGRAM_API_KEY:
        logger.warning("⚠️ TELEGRAM_API_KEY not set - using default (not secure!)")

    logger.info("🤖 Starting CocoCRM Telegram Bot...")
    logger.info(f"📍 Base URL: {BASE_URL}")

    # Create the Application
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Register command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("login", login_command))

    # Start the Bot
    logger.info("✅ Bot is running! Press Ctrl+C to stop.")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
