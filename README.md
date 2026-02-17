# CocoCRM - Modern CRM with Telegram Integration

A powerful and beautiful CRM system with dual authentication: traditional password login and Telegram integration.

## Features

✨ **Dual Authentication System**
- Traditional username/password login
- Telegram Login Widget integration
- Secure session management with Flask-Login

🎨 **Modern UI/UX**
- Beautiful gradient designs
- Responsive layout (mobile-friendly)
- Professional dashboard
- Inspired by modern SaaS applications

📊 **CRM Capabilities**
- Contact management
- Sales pipeline tracking
- Analytics and reporting
- Telegram notifications
- Task automation

🔒 **Security**
- Password hashing with Werkzeug
- HMAC verification for Telegram auth
- CSRF protection
- Secure session management

## Quick Start

### 1. Installation

```bash
# Clone the repository
git clone <your-repo-url>
cd CocoCRM

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration

Copy the example environment file and configure it:

```bash
cp .env.example .env
```

Edit `.env` and add your configuration:

```env
SECRET_KEY=your-random-secret-key-here
TELEGRAM_BOT_TOKEN=your-telegram-bot-token
```

### 3. Set Up Telegram Bot

To enable Telegram login:

1. Open Telegram and search for [@BotFather](https://t.me/BotFather)
2. Send `/newbot` and follow the instructions
3. Copy the bot token you receive
4. Paste it in your `.env` file as `TELEGRAM_BOT_TOKEN`
5. Send `/setdomain` to BotFather
6. Enter your domain (e.g., `yourdomain.com` or `localhost:5000` for local testing)

### 4. Run the Application

```bash
python app.py
```

The application will be available at `http://localhost:5000`

## Usage

### Creating an Account

1. Go to `/register` or click "Create one" on the login page
2. Fill in your details:
   - Username (required)
   - Email (optional)
   - Password (minimum 6 characters)
3. Click "Create Account"

### Logging In

**Method 1: Username/Password**
1. Enter your username and password
2. Click "Sign In"

**Method 2: Telegram**
1. Click the "Log in with Telegram" button
2. Authorize the bot in Telegram
3. You'll be automatically logged in

### Dashboard

After logging in, you'll see:
- Welcome message with your name
- Statistics cards (contacts, deals, tasks, revenue)
- Quick access to main features
- User profile information

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `SECRET_KEY` | Flask secret key for sessions | Yes |
| `TELEGRAM_BOT_TOKEN` | Your Telegram bot token from BotFather | No (but needed for Telegram login) |
| `SQLALCHEMY_DATABASE_URI` | Database connection string | No (defaults to SQLite) |

## Database

The application uses SQLite by default. The database file `crm.db` will be created automatically on first run.

### Database Schema

**User Table:**
- `id` - Primary key
- `username` - Unique username
- `email` - Optional email
- `password_hash` - Hashed password (for password auth)
- `telegram_id` - Telegram user ID (for Telegram auth)
- `telegram_username` - Telegram username
- `first_name` - User's first name
- `last_name` - User's last name
- `photo_url` - Profile photo URL (from Telegram)
- `created_at` - Account creation timestamp

## Deployment

### Heroku

The application includes a `Procfile` for Heroku deployment:

```bash
heroku create your-app-name
heroku config:set SECRET_KEY=your-secret-key
heroku config:set TELEGRAM_BOT_TOKEN=your-bot-token
git push heroku main
```

### Docker

A `Dockerfile` is included for containerized deployment:

```bash
docker build -t cococrm .
docker run -p 5000:5000 -e SECRET_KEY=your-key -e TELEGRAM_BOT_TOKEN=your-token cococrm
```

## Development

### Project Structure

```
CocoCRM/
├── app.py                 # Main application file
├── requirements.txt       # Python dependencies
├── .env.example          # Environment variables template
├── Dockerfile            # Docker configuration
├── Procfile              # Heroku configuration
├── templates/            # HTML templates
│   ├── login.html       # Login page
│   ├── register.html    # Registration page
│   ├── dashboard.html   # Main dashboard
│   └── index.html       # Legacy template
└── crm.db               # SQLite database (auto-generated)
```

### Adding New Features

The application is built with Flask and follows standard patterns:

1. Add routes in `app.py`
2. Create templates in `templates/`
3. Add database models as needed
4. Update the dashboard with new features

## Security Notes

- Always use a strong `SECRET_KEY` in production
- Use HTTPS in production to protect credentials
- The Telegram authentication uses HMAC verification
- Passwords are hashed using Werkzeug's security functions
- Never commit `.env` files to version control

## Troubleshooting

**Telegram login not working:**
- Ensure your bot token is correct in `.env`
- Make sure you've set the domain with BotFather using `/setdomain`
- Check browser console for JavaScript errors

**Database errors:**
- Delete `crm.db` and restart the app to recreate the database
- Check file permissions in the application directory

**Import errors:**
- Run `pip install -r requirements.txt` to ensure all dependencies are installed

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is open source and available under the MIT License.

## Support

For issues and questions, please open an issue on GitHub.
