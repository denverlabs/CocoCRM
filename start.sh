#!/bin/bash
# Start CocoCRM with integrated Telegram bot (via webhook)

echo "Starting CocoCRM..."
echo "Telegram bot commands are handled via webhook at /telegram/webhook"

# Start the Flask web server (bot webhook is integrated)
gunicorn app:app --bind 0.0.0.0:$PORT --timeout 120
