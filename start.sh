#!/bin/bash
# Start both the Flask web server and Telegram bot

# Start the Telegram bot in the background
echo "🤖 Starting Telegram bot..."
python telegram_bot.py &
BOT_PID=$!

# Start the Flask web server in the foreground
echo "🌐 Starting Flask web server..."
gunicorn app:app --bind 0.0.0.0:$PORT

# If the web server exits, kill the bot process
kill $BOT_PID
