from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, Response
import csv
import io
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import hashlib
import hmac
import os
import requests as http_requests
import json
import threading
from datetime import datetime, timedelta
import jwt

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///crm.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Telegram Bot Token (set this in environment variables)
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_BOT_USERNAME = os.environ.get('TELEGRAM_BOT_USERNAME', '')

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# User Model
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True)
    password_hash = db.Column(db.String(200), nullable=True)
    telegram_id = db.Column(db.String(100), unique=True, nullable=True)
    telegram_username = db.Column(db.String(100), nullable=True)
    first_name = db.Column(db.String(100), nullable=True)
    last_name = db.Column(db.String(100), nullable=True)
    photo_url = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)

# Contact Model
class Contact(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(120), nullable=True)
    phone = db.Column(db.String(50), nullable=True)
    company = db.Column(db.String(200), nullable=True)
    position = db.Column(db.String(200), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    tags = db.Column(db.String(500), nullable=True)  # Comma-separated tags
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = db.relationship('User', backref='contacts')

# Deal Model (Sales Pipeline)
class Deal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    contact_id = db.Column(db.Integer, db.ForeignKey('contact.id'), nullable=True)
    title = db.Column(db.String(200), nullable=False)
    value = db.Column(db.Float, default=0.0)
    stage = db.Column(db.String(50), default='lead')  # lead, qualified, proposal, negotiation, closed-won, closed-lost
    probability = db.Column(db.Integer, default=0)  # 0-100%
    expected_close_date = db.Column(db.Date, nullable=True)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = db.relationship('User', backref='deals')
    contact = db.relationship('Contact', backref='deals')

# Task Model (for automation and reminders)
class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    contact_id = db.Column(db.Integer, db.ForeignKey('contact.id'), nullable=True)
    deal_id = db.Column(db.Integer, db.ForeignKey('deal.id'), nullable=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    due_date = db.Column(db.DateTime, nullable=True)
    completed = db.Column(db.Boolean, default=False)
    priority = db.Column(db.String(20), default='medium')  # low, medium, high
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='tasks')
    contact = db.relationship('Contact', backref='tasks')
    deal = db.relationship('Deal', backref='tasks')

# Activity Log
class Activity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    contact_id = db.Column(db.Integer, db.ForeignKey('contact.id'), nullable=True)
    deal_id = db.Column(db.Integer, db.ForeignKey('deal.id'), nullable=True)
    activity_type = db.Column(db.String(50), nullable=False)  # email, call, meeting, note
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='activities')
    contact = db.relationship('Contact', backref='activities')
    deal = db.relationship('Deal', backref='activities')

# Notification Settings
class NotificationSettings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, unique=True)
    email_notifications = db.Column(db.Boolean, default=True)
    telegram_notifications = db.Column(db.Boolean, default=True)
    task_reminders = db.Column(db.Boolean, default=True)
    deal_updates = db.Column(db.Boolean, default=True)
    daily_summary = db.Column(db.Boolean, default=False)

    user = db.relationship('User', backref='notification_settings')

# Automation Rules
class Automation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    trigger = db.Column(db.String(100), nullable=False)  # new_contact, deal_stage_change, task_due
    action = db.Column(db.String(100), nullable=False)  # send_email, create_task, send_notification
    active = db.Column(db.Boolean, default=True)
    config = db.Column(db.Text, nullable=True)  # JSON config for the automation
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='automations')

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Verify Telegram authentication
def verify_telegram_auth(auth_data):
    print("\n🔐 Verifying Telegram Authentication...")

    if not TELEGRAM_BOT_TOKEN:
        print("❌ No TELEGRAM_BOT_TOKEN configured!")
        return False

    check_hash = auth_data.get('hash')
    if not check_hash:
        print("❌ No hash in auth_data!")
        return False

    auth_data_copy = {k: v for k, v in auth_data.items() if k != 'hash'}
    data_check_string = '\n'.join([f'{k}={v}' for k, v in sorted(auth_data_copy.items())])

    print(f"📝 Data check string:\n{data_check_string}")

    secret_key = hashlib.sha256(TELEGRAM_BOT_TOKEN.encode()).digest()
    calculated_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()

    print(f"🔑 Received hash:   {check_hash}")
    print(f"🔑 Calculated hash: {calculated_hash}")
    print(f"✅ Match: {calculated_hash == check_hash}")

    return calculated_hash == check_hash

def generate_temp_token(user_id, username, expires_in_minutes=180):
    """Generate a temporary JWT token for auto-login"""
    expiration = datetime.utcnow() + timedelta(minutes=expires_in_minutes)

    payload = {
        'user_id': user_id,
        'username': username,
        'exp': expiration,
        'iat': datetime.utcnow(),
        'type': 'temp_login'
    }

    token = jwt.encode(payload, app.config['SECRET_KEY'], algorithm='HS256')
    return token

def verify_temp_token(token):
    """Verify and decode a temporary JWT token"""
    try:
        payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])

        if payload.get('type') != 'temp_login':
            return None

        return payload
    except jwt.ExpiredSignatureError:
        print("❌ Token expired")
        return None
    except jwt.InvalidTokenError as e:
        print(f"❌ Invalid token: {e}")
        return None

# ========== TELEGRAM BOT API HELPERS ==========
def send_telegram_message(chat_id, text, parse_mode='HTML'):
    """Send a message to a Telegram user via Bot API"""
    if not TELEGRAM_BOT_TOKEN:
        print("WARNING: No TELEGRAM_BOT_TOKEN configured, cannot send message")
        return False
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            'chat_id': chat_id,
            'text': text,
            'parse_mode': parse_mode
        }
        resp = http_requests.post(url, json=payload, timeout=10)
        if resp.status_code == 200:
            print(f"Telegram message sent to {chat_id}")
            return True
        else:
            print(f"Failed to send Telegram message: {resp.status_code} {resp.text}")
            return False
    except Exception as e:
        print(f"Error sending Telegram message: {e}")
        return False


def set_telegram_webhook():
    """Set the Telegram webhook to our app's endpoint"""
    if not TELEGRAM_BOT_TOKEN:
        print("WARNING: No TELEGRAM_BOT_TOKEN, skipping webhook setup")
        return
    base_url = os.environ.get('BASE_URL', '').rstrip('/')
    if not base_url:
        print("WARNING: No BASE_URL configured, skipping webhook setup")
        return
    webhook_url = f"{base_url}/telegram/webhook"
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/setWebhook"
        resp = http_requests.post(url, json={'url': webhook_url}, timeout=10)
        data = resp.json()
        if data.get('ok'):
            print(f"Telegram webhook set to: {webhook_url}")
        else:
            print(f"Failed to set webhook: {data}")
    except Exception as e:
        print(f"Error setting webhook: {e}")


def handle_bot_command(message):
    """Process a Telegram bot command from webhook"""
    chat_id = message.get('chat', {}).get('id')
    text = message.get('text', '').strip()
    user_data = message.get('from', {})
    telegram_id = str(user_data.get('id', ''))
    first_name = user_data.get('first_name', '')
    last_name = user_data.get('last_name', '')
    username = user_data.get('username', '')

    if not chat_id or not text:
        return

    # /start command
    if text.startswith('/start'):
        send_telegram_message(chat_id,
            f"<b>Welcome to CocoCRM, {first_name}!</b>\n\n"
            f"I'm Coco, your CRM assistant bot.\n\n"
            f"<b>Commands:</b>\n"
            f"/crm - Get a login link to access CocoCRM\n"
            f"/login - Same as /crm\n"
            f"/status - Check your account status\n"
            f"/help - Show this help message\n\n"
            f"<i>Click /crm to get your personal login link!</i>"
        )
        # Auto-create user in database if not exists
        with app.app_context():
            _ensure_telegram_user(telegram_id, username, first_name, last_name)
        return

    # /help command
    if text.startswith('/help'):
        send_telegram_message(chat_id,
            "<b>CocoCRM Bot Help</b>\n\n"
            "/crm - Generate a temporary login link (3 hours)\n"
            "/login - Same as /crm\n"
            "/status - Check your account status\n"
            "/help - Show this help message\n\n"
            "Your login link gives you full access to:\n"
            "- Contact Management\n"
            "- Sales Pipeline\n"
            "- Tasks & Automation\n"
            "- Analytics Dashboard"
        )
        return

    # /crm or /login command - generate login link
    if text.startswith('/crm') or text.startswith('/login'):
        with app.app_context():
            user = _ensure_telegram_user(telegram_id, username, first_name, last_name)
            if user:
                token = generate_temp_token(user.id, user.username, expires_in_minutes=180)
                base_url = os.environ.get('BASE_URL', 'https://cococrm.onrender.com')
                login_url = f"{base_url}/?token={token}"
                send_telegram_message(chat_id,
                    f"<b>Your CocoCRM Login Link</b>\n\n"
                    f"<a href=\"{login_url}\">Click here to open CocoCRM</a>\n\n"
                    f"Valid for: 3 hours\n"
                    f"User: {user.username}\n\n"
                    f"<i>This link is personal - don't share it!</i>"
                )
            else:
                send_telegram_message(chat_id,
                    "Error creating your account. Please try again later."
                )
        return

    # /status command
    if text.startswith('/status'):
        with app.app_context():
            user = User.query.filter_by(telegram_id=telegram_id).first()
            if user:
                task_count = Task.query.filter_by(user_id=user.id, completed=False).count()
                deal_count = Deal.query.filter_by(user_id=user.id).filter(
                    Deal.stage.in_(['lead', 'qualified', 'proposal', 'negotiation'])
                ).count()
                contact_count = Contact.query.filter_by(user_id=user.id).count()
                send_telegram_message(chat_id,
                    f"<b>Your CocoCRM Status</b>\n\n"
                    f"User: {user.username}\n"
                    f"Contacts: {contact_count}\n"
                    f"Active Deals: {deal_count}\n"
                    f"Pending Tasks: {task_count}\n\n"
                    f"Use /crm to get your login link!"
                )
            else:
                send_telegram_message(chat_id,
                    "You don't have an account yet.\n"
                    "Send /crm to create one and get your login link!"
                )
        return

    # Default response for unknown commands
    if text.startswith('/'):
        send_telegram_message(chat_id,
            f"Unknown command: {text}\n\nSend /help to see available commands."
        )
    else:
        send_telegram_message(chat_id,
            f"Hi {first_name}! Send /crm to get your CocoCRM login link."
        )


def _ensure_telegram_user(telegram_id, username, first_name, last_name):
    """Find or create a user from Telegram data"""
    if not telegram_id:
        return None
    user = User.query.filter_by(telegram_id=str(telegram_id)).first()
    if not user:
        uname = username or f"user_{telegram_id}"
        # Check if username exists, add suffix if needed
        existing = User.query.filter_by(username=uname).first()
        if existing:
            uname = f"{uname}_{telegram_id}"
        user = User(
            username=uname,
            telegram_id=str(telegram_id),
            telegram_username=username,
            first_name=first_name,
            last_name=last_name
        )
        db.session.add(user)
        db.session.commit()
        print(f"Created new user from Telegram: {uname} (ID: {telegram_id})")
    return user


def run_automations(trigger, user_id, contact_id=None, deal_id=None, extra_data=None):
    """Execute active automations matching the given trigger"""
    try:
        automations = Automation.query.filter_by(user_id=user_id, trigger=trigger, active=True).all()
        for auto in automations:
            try:
                if auto.action == 'create_task':
                    task = Task(
                        user_id=user_id,
                        contact_id=contact_id,
                        deal_id=deal_id,
                        title=f'[Auto] {auto.name}',
                        description=f'Automatically created by automation: {auto.name}',
                        priority='medium'
                    )
                    db.session.add(task)
                elif auto.action == 'send_notification':
                    log_activity('note', f'[Automation] {auto.name} triggered', contact_id=contact_id, deal_id=deal_id, user_id=user_id)
                elif auto.action == 'send_email':
                    log_activity('email', f'[Automation] Email trigger: {auto.name}', contact_id=contact_id, deal_id=deal_id, user_id=user_id)
                db.session.commit()
                print(f"✅ Automation executed: {auto.name}")
            except Exception as e:
                print(f"⚠️ Automation '{auto.name}' failed: {e}")
                db.session.rollback()
    except Exception as e:
        print(f"⚠️ Error checking automations: {e}")

def log_activity(activity_type, description, contact_id=None, deal_id=None, user_id=None):
    """Helper function to log activities"""
    try:
        activity = Activity(
            activity_type=activity_type,
            description=description,
            contact_id=contact_id,
            deal_id=deal_id,
            user_id=user_id or (current_user.id if current_user.is_authenticated else None)
        )
        db.session.add(activity)
        db.session.commit()
    except Exception as e:
        print(f"⚠️ Failed to log activity: {e}")
        db.session.rollback()

@app.route('/')
def index():
    # Check for token in URL parameters
    token = request.args.get('token')

    if token and not current_user.is_authenticated:
        payload = verify_temp_token(token)
        if payload:
            user = User.query.get(payload['user_id'])
            if user:
                login_user(user)
                flash('Auto-login successful! Welcome back.', 'success')
                return redirect(url_for('index'))  # Redirect to clean URL
            else:
                flash('Invalid token: user not found', 'error')
        else:
            flash('Invalid or expired token', 'error')

    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            login_user(user)
            flash('Login successful!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password', 'error')

    return render_template('login.html', telegram_bot_token=TELEGRAM_BOT_TOKEN, telegram_bot_username=TELEGRAM_BOT_USERNAME)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return render_template('register.html')

        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'error')
            return render_template('register.html')

        if email and User.query.filter_by(email=email).first():
            flash('Email already registered', 'error')
            return render_template('register.html')

        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        login_user(user)
        flash('Registration successful!', 'success')
        return redirect(url_for('index'))

    return render_template('register.html')

@app.route('/telegram-auth', methods=['POST'])
def telegram_auth():
    try:
        auth_data = request.json

        # DEBUG: Log received data
        print("=" * 80)
        print("🔍 TELEGRAM AUTH DEBUG")
        print("=" * 80)
        print(f"📥 Received auth_data: {auth_data}")
        print(f"🔑 Bot Token configured: {bool(TELEGRAM_BOT_TOKEN)}")
        print(f"🤖 Bot Username: {TELEGRAM_BOT_USERNAME}")

        if not auth_data:
            print("❌ ERROR: No auth_data received")
            return jsonify({'success': False, 'message': 'No authentication data received'}), 400

        # Verify authentication
        if not verify_telegram_auth(auth_data):
            print("❌ ERROR: Authentication verification failed")
            print(f"   Hash received: {auth_data.get('hash', 'NO HASH')}")
            return jsonify({'success': False, 'message': 'Invalid authentication data'}), 400

        print("✅ Authentication verified successfully")

        telegram_id = str(auth_data.get('id'))
        print(f"👤 Telegram ID: {telegram_id}")

        user = User.query.filter_by(telegram_id=telegram_id).first()

        if not user:
            # Create new user from Telegram data
            username = auth_data.get('username', f"user_{telegram_id}")
            print(f"🆕 Creating new user: {username}")

            user = User(
                username=username,
                telegram_id=telegram_id,
                telegram_username=auth_data.get('username'),
                first_name=auth_data.get('first_name'),
                last_name=auth_data.get('last_name'),
                photo_url=auth_data.get('photo_url')
            )
            db.session.add(user)
            db.session.commit()
            print("✅ User created successfully")
        else:
            print(f"👤 Existing user found: {user.username}")

        login_user(user)
        print("✅ User logged in successfully")
        print("=" * 80)

        # Send welcome message via Telegram bot
        if telegram_id:
            thread = threading.Thread(target=send_telegram_message, args=(
                telegram_id,
                f"<b>Welcome to CocoCRM!</b>\n\n"
                f"You've been logged in successfully.\n\n"
                f"<b>Quick commands:</b>\n"
                f"/crm - Get a new login link anytime\n"
                f"/status - Check your CRM stats\n\n"
                f"<i>Enjoy managing your business!</i>"
            ))
            thread.daemon = True
            thread.start()

        return jsonify({'success': True, 'redirect': url_for('dashboard')})

    except Exception as e:
        print("=" * 80)
        print(f"💥 EXCEPTION in telegram_auth: {str(e)}")
        print(f"   Type: {type(e).__name__}")
        import traceback
        print(traceback.format_exc())
        print("=" * 80)
        return jsonify({'success': False, 'message': f'Server error: {str(e)}'}), 500

@app.route('/telegram/setup-webhook')
def setup_webhook_endpoint():
    """Manually trigger webhook setup - visit this URL once after deployment"""
    if not TELEGRAM_BOT_TOKEN:
        return jsonify({'error': 'TELEGRAM_BOT_TOKEN not configured'}), 400
    base_url = os.environ.get('BASE_URL', '').rstrip('/')
    if not base_url:
        return jsonify({'error': 'BASE_URL not configured'}), 400
    webhook_url = f"{base_url}/telegram/webhook"
    try:
        # Set webhook
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/setWebhook"
        resp = http_requests.post(url, json={'url': webhook_url}, timeout=10)
        result = resp.json()

        # Get webhook info
        info_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getWebhookInfo"
        info_resp = http_requests.get(info_url, timeout=10)
        info = info_resp.json()

        return jsonify({
            'webhook_set': result,
            'webhook_info': info,
            'webhook_url': webhook_url,
            'bot_username': TELEGRAM_BOT_USERNAME
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/telegram/webhook', methods=['POST'])
def telegram_webhook():
    """Receive Telegram bot updates via webhook"""
    try:
        update = request.json
        if not update:
            return jsonify({'ok': True})

        # Handle messages with commands
        message = update.get('message')
        if message:
            # Process in background thread so we don't block the webhook response
            thread = threading.Thread(target=handle_bot_command, args=(message,))
            thread.daemon = True
            thread.start()

        return jsonify({'ok': True})
    except Exception as e:
        print(f"Error in webhook: {e}")
        return jsonify({'ok': True})  # Always return 200 to Telegram


# ========== REST API FOR OPENCLAW INTEGRATION ==========
# API Key Configuration - supports OPENCLAW_API_KEY or fallback to TELEGRAM_API_KEY
OPENCLAW_API_KEY = os.environ.get('OPENCLAW_API_KEY') or os.environ.get('TELEGRAM_API_KEY', 'dev-api-key-change-me')

def require_api_key(f):
    """Decorator to require API key for REST API endpoints

    Supports multiple authentication methods:
    1. X-API-Key header (recommended)
    2. Authorization: Bearer <api_key> header
    3. api_key query parameter (less secure, use for testing only)
    """
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = None

        # Method 1: X-API-Key header (recommended)
        api_key = request.headers.get('X-API-Key')

        # Method 2: Authorization Bearer header
        if not api_key:
            auth_header = request.headers.get('Authorization', '')
            if auth_header.startswith('Bearer '):
                api_key = auth_header.replace('Bearer ', '').strip()

        # Method 3: Query parameter (least secure)
        if not api_key:
            api_key = request.args.get('api_key')

        # Verify API key
        if not api_key or api_key != OPENCLAW_API_KEY:
            return jsonify({
                'error': 'Invalid or missing API key',
                'hint': 'Use X-API-Key header, Authorization: Bearer header, or api_key query param',
                'docs': 'See OPENCLAW_API.md for authentication details'
            }), 401

        return f(*args, **kwargs)
    return decorated_function

@app.route('/api/contacts', methods=['GET'])
@require_api_key
def api_list_contacts():
    """List all contacts - for OpenClaw integration"""
    username = request.args.get('username', 'admin')
    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({'error': 'User not found'}), 404

    contacts = Contact.query.filter_by(user_id=user.id).all()
    return jsonify({
        'success': True,
        'contacts': [{
            'id': c.id,
            'name': c.name,
            'email': c.email,
            'phone': c.phone,
            'company': c.company,
            'position': c.position,
            'tags': c.tags,
            'created_at': c.created_at.isoformat() if c.created_at else None
        } for c in contacts]
    })

@app.route('/api/contacts', methods=['POST'])
@require_api_key
def api_create_contact():
    """Create a new contact - for OpenClaw integration"""
    data = request.json
    username = data.get('username', 'admin')
    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({'error': 'User not found'}), 404

    contact = Contact(
        user_id=user.id,
        name=data.get('name'),
        email=data.get('email'),
        phone=data.get('phone'),
        company=data.get('company'),
        position=data.get('position'),
        tags=data.get('tags'),
        notes=data.get('notes')
    )
    db.session.add(contact)
    db.session.commit()

    return jsonify({
        'success': True,
        'contact': {
            'id': contact.id,
            'name': contact.name,
            'email': contact.email,
            'phone': contact.phone
        }
    }), 201

@app.route('/api/deals', methods=['GET'])
@require_api_key
def api_list_deals():
    """List all deals - for OpenClaw integration"""
    username = request.args.get('username', 'admin')
    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({'error': 'User not found'}), 404

    deals = Deal.query.filter_by(user_id=user.id).all()
    return jsonify({
        'success': True,
        'deals': [{
            'id': d.id,
            'title': d.title,
            'value': d.value,
            'stage': d.stage,
            'probability': d.probability,
            'contact_id': d.contact_id,
            'created_at': d.created_at.isoformat() if d.created_at else None
        } for d in deals]
    })

@app.route('/api/deals', methods=['POST'])
@require_api_key
def api_create_deal():
    """Create a new deal - for OpenClaw integration"""
    data = request.json
    username = data.get('username', 'admin')
    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({'error': 'User not found'}), 404

    deal = Deal(
        user_id=user.id,
        contact_id=data.get('contact_id'),
        title=data.get('title'),
        value=float(data.get('value', 0)),
        stage=data.get('stage', 'lead'),
        probability=int(data.get('probability', 0)),
        description=data.get('description')
    )
    db.session.add(deal)
    db.session.commit()

    return jsonify({
        'success': True,
        'deal': {
            'id': deal.id,
            'title': deal.title,
            'value': deal.value,
            'stage': deal.stage
        }
    }), 201

@app.route('/api/tasks', methods=['GET'])
@require_api_key
def api_list_tasks():
    """List all tasks - for OpenClaw integration"""
    username = request.args.get('username', 'admin')
    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({'error': 'User not found'}), 404

    tasks = Task.query.filter_by(user_id=user.id).all()
    return jsonify({
        'success': True,
        'tasks': [{
            'id': t.id,
            'title': t.title,
            'description': t.description,
            'priority': t.priority,
            'completed': t.completed,
            'due_date': t.due_date.isoformat() if t.due_date else None,
            'created_at': t.created_at.isoformat() if t.created_at else None
        } for t in tasks]
    })

@app.route('/api/tasks', methods=['POST'])
@require_api_key
def api_create_task():
    """Create a new task - for OpenClaw integration"""
    data = request.json
    username = data.get('username', 'admin')
    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({'error': 'User not found'}), 404

    task = Task(
        user_id=user.id,
        contact_id=data.get('contact_id'),
        deal_id=data.get('deal_id'),
        title=data.get('title'),
        description=data.get('description'),
        priority=data.get('priority', 'medium')
    )

    if data.get('due_date'):
        task.due_date = datetime.fromisoformat(data['due_date'])

    db.session.add(task)
    db.session.commit()

    return jsonify({
        'success': True,
        'task': {
            'id': task.id,
            'title': task.title,
            'priority': task.priority,
            'completed': task.completed
        }
    }), 201

@app.route('/api/telegram/generate-token', methods=['POST'])
def generate_token_endpoint():
    """
    Generate a temporary login token for authorized users (like Kimi AI)

    Expected JSON payload:
    {
        "telegram_id": "123456789",  // or
        "username": "kimi_claw",
        "api_key": "secret_key"      // optional authentication
    }

    Returns:
    {
        "success": true,
        "token": "jwt_token_here",
        "url": "https://cococrm.onrender.com/?token=jwt_token_here",
        "expires_in": 180
    }
    """
    try:
        data = request.json

        if not data:
            return jsonify({'success': False, 'message': 'No data provided'}), 400

        # Get authorization method
        telegram_id = data.get('telegram_id')
        username = data.get('username')
        api_key = data.get('api_key')

        # Check for API key authentication (recommended for bot access)
        expected_api_key = os.environ.get('TELEGRAM_API_KEY', 'dev-api-key-change-me')
        if api_key and api_key == expected_api_key:
            # API key is valid, find or create user
            user = None
            if telegram_id:
                user = User.query.filter_by(telegram_id=str(telegram_id)).first()
            if not user and username:
                user = User.query.filter_by(username=username).first()
            if not user:
                # Create service user
                uname = username or f"agent_{telegram_id or 'unknown'}"
                user = User(
                    username=uname,
                    first_name=data.get('first_name', uname),
                    last_name=data.get('last_name', 'Agent'),
                    telegram_id=telegram_id if telegram_id else None,
                    telegram_username=username if username else None
                )
                db.session.add(user)
                db.session.commit()
                print(f"Created service user: {uname}")

        elif telegram_id:
            # Find user by telegram_id
            user = User.query.filter_by(telegram_id=str(telegram_id)).first()
            if not user:
                return jsonify({'success': False, 'message': 'User not found with this Telegram ID'}), 404

        elif username:
            # Find user by username
            user = User.query.filter_by(username=username).first()
            if not user:
                return jsonify({'success': False, 'message': 'User not found with this username'}), 404

        else:
            return jsonify({'success': False, 'message': 'Must provide telegram_id, username, or api_key'}), 400

        # Generate temporary token
        token = generate_temp_token(user.id, user.username, expires_in_minutes=180)

        # Get base URL (support both local and production)
        base_url = os.environ.get('BASE_URL', 'https://cococrm.onrender.com')
        login_url = f"{base_url}/?token={token}"

        print(f"✅ Generated token for user: {user.username}")
        print(f"🔗 Login URL: {login_url}")

        return jsonify({
            'success': True,
            'token': token,
            'url': login_url,
            'expires_in': 180,
            'user': {
                'id': user.id,
                'username': user.username
            }
        })

    except Exception as e:
        print(f"💥 Error generating token: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return jsonify({'success': False, 'message': f'Server error: {str(e)}'}), 500

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out', 'info')
    return redirect(url_for('login'))

@app.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')

        # Validate current password (only if user has password)
        if current_user.password_hash and not current_user.check_password(current_password):
            flash('Current password is incorrect', 'error')
            return render_template('change_password.html', user=current_user)

        # Validate new password
        if new_password != confirm_password:
            flash('New passwords do not match', 'error')
            return render_template('change_password.html', user=current_user)

        if len(new_password) < 6:
            flash('Password must be at least 6 characters', 'error')
            return render_template('change_password.html', user=current_user)

        # Update password
        current_user.set_password(new_password)
        db.session.commit()

        flash('Password changed successfully!', 'success')
        return redirect(url_for('dashboard'))

    return render_template('change_password.html', user=current_user)

@app.route('/debug/status')
def debug_status():
    """Debug endpoint to check configuration status"""
    status = {
        'telegram_bot_token_configured': bool(TELEGRAM_BOT_TOKEN),
        'telegram_bot_token_length': len(TELEGRAM_BOT_TOKEN) if TELEGRAM_BOT_TOKEN else 0,
        'telegram_bot_token_preview': TELEGRAM_BOT_TOKEN[:10] + '...' if TELEGRAM_BOT_TOKEN and len(TELEGRAM_BOT_TOKEN) > 10 else 'NOT SET',
        'telegram_bot_username': TELEGRAM_BOT_USERNAME or 'NOT SET',
        'secret_key_configured': bool(app.config['SECRET_KEY']),
        'database_uri': app.config['SQLALCHEMY_DATABASE_URI'],
        'total_users': User.query.count(),
        'environment': 'production' if not app.debug else 'development'
    }

    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>CocoCRM Debug Status</title>
        <style>
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                max-width: 800px;
                margin: 50px auto;
                padding: 20px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
            }
            .card {
                background: rgba(255, 255, 255, 0.1);
                backdrop-filter: blur(10px);
                border-radius: 15px;
                padding: 30px;
                box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
            }
            h1 {
                margin-top: 0;
                font-size: 2.5em;
            }
            .status-item {
                display: flex;
                justify-content: space-between;
                padding: 15px;
                margin: 10px 0;
                background: rgba(255, 255, 255, 0.05);
                border-radius: 10px;
                border-left: 4px solid #4CAF50;
            }
            .status-item.error {
                border-left-color: #f44336;
            }
            .label {
                font-weight: bold;
            }
            .value {
                font-family: monospace;
                background: rgba(0, 0, 0, 0.2);
                padding: 5px 10px;
                border-radius: 5px;
            }
            .status-ok {
                color: #4CAF50;
            }
            .status-error {
                color: #f44336;
            }
        </style>
    </head>
    <body>
        <div class="card">
            <h1>🔍 CocoCRM Debug Status</h1>
            <div class="status-item {{ 'error' if not status['telegram_bot_token_configured'] else '' }}">
                <span class="label">Telegram Bot Token:</span>
                <span class="value {{ 'status-ok' if status['telegram_bot_token_configured'] else 'status-error' }}">
                    {{ 'CONFIGURED ✅' if status['telegram_bot_token_configured'] else 'NOT SET ❌' }}
                </span>
            </div>
            <div class="status-item">
                <span class="label">Token Preview:</span>
                <span class="value">{{ status['telegram_bot_token_preview'] }}</span>
            </div>
            <div class="status-item">
                <span class="label">Token Length:</span>
                <span class="value">{{ status['telegram_bot_token_length'] }} chars</span>
            </div>
            <div class="status-item {{ 'error' if status['telegram_bot_username'] == 'NOT SET' else '' }}">
                <span class="label">Bot Username:</span>
                <span class="value">{{ status['telegram_bot_username'] }}</span>
            </div>
            <div class="status-item">
                <span class="label">Secret Key:</span>
                <span class="value {{ 'status-ok' if status['secret_key_configured'] else 'status-error' }}">
                    {{ 'CONFIGURED ✅' if status['secret_key_configured'] else 'NOT SET ❌' }}
                </span>
            </div>
            <div class="status-item">
                <span class="label">Database:</span>
                <span class="value">{{ status['database_uri'] }}</span>
            </div>
            <div class="status-item">
                <span class="label">Total Users:</span>
                <span class="value">{{ status['total_users'] }}</span>
            </div>
            <div class="status-item">
                <span class="label">Environment:</span>
                <span class="value">{{ status['environment'] }}</span>
            </div>
        </div>
    </body>
    </html>
    """
    from flask import render_template_string
    return render_template_string(html, status=status)

@app.route('/dashboard')
@login_required
def dashboard():
    # Get statistics for dashboard
    total_contacts = Contact.query.filter_by(user_id=current_user.id).count()
    total_deals = Deal.query.filter_by(user_id=current_user.id).count()
    active_deals = Deal.query.filter_by(user_id=current_user.id).filter(Deal.stage.in_(['lead', 'qualified', 'proposal', 'negotiation'])).count()
    total_revenue = db.session.query(db.func.sum(Deal.value)).filter_by(user_id=current_user.id, stage='closed-won').scalar() or 0
    completed_tasks = Task.query.filter_by(user_id=current_user.id, completed=True).count()

    return render_template('dashboard.html',
                         user=current_user,
                         total_contacts=total_contacts,
                         active_deals=active_deals,
                         total_revenue=total_revenue,
                         completed_tasks=completed_tasks)

# ========== CONTACTS ROUTES ==========
@app.route('/contacts')
@login_required
def contacts():
    search = request.args.get('search', '').strip()
    tag_filter = request.args.get('tag', '').strip()
    sort_by = request.args.get('sort', 'date_desc')

    query = Contact.query.filter_by(user_id=current_user.id)

    if search:
        search_pattern = f'%{search}%'
        query = query.filter(
            db.or_(
                Contact.name.ilike(search_pattern),
                Contact.email.ilike(search_pattern),
                Contact.company.ilike(search_pattern),
                Contact.phone.ilike(search_pattern)
            )
        )

    if tag_filter:
        query = query.filter(Contact.tags.ilike(f'%{tag_filter}%'))

    if sort_by == 'name_asc':
        query = query.order_by(Contact.name.asc())
    elif sort_by == 'name_desc':
        query = query.order_by(Contact.name.desc())
    elif sort_by == 'date_asc':
        query = query.order_by(Contact.created_at.asc())
    else:
        query = query.order_by(Contact.created_at.desc())

    contacts = query.all()

    all_tags = set()
    for contact in Contact.query.filter_by(user_id=current_user.id).all():
        if contact.tags:
            all_tags.update([t.strip() for t in contact.tags.split(',')])

    return render_template('contacts.html',
                         contacts=contacts,
                         user=current_user,
                         search=search,
                         tag_filter=tag_filter,
                         sort_by=sort_by,
                         all_tags=sorted(all_tags))

@app.route('/contacts/add', methods=['GET', 'POST'])
@login_required
def add_contact():
    if request.method == 'POST':
        try:
            contact = Contact(
                user_id=current_user.id,
                name=request.form.get('name'),
                email=request.form.get('email'),
                phone=request.form.get('phone'),
                company=request.form.get('company'),
                position=request.form.get('position'),
                notes=request.form.get('notes'),
                tags=request.form.get('tags')
            )
            db.session.add(contact)
            db.session.commit()

            log_activity('note', f'Contact created: {contact.name}', contact_id=contact.id)
            run_automations('new_contact', current_user.id, contact_id=contact.id)

            flash('Contact added successfully!', 'success')
            return redirect(url_for('contacts'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding contact: {str(e)}', 'error')
            print(f"Error in add_contact: {str(e)}")
            import traceback
            traceback.print_exc()

    return render_template('contact_form.html', contact=None, user=current_user)

@app.route('/contacts/edit/<int:contact_id>', methods=['GET', 'POST'])
@login_required
def edit_contact(contact_id):
    contact = Contact.query.filter_by(id=contact_id, user_id=current_user.id).first_or_404()

    if request.method == 'POST':
        try:
            contact.name = request.form.get('name')
            contact.email = request.form.get('email')
            contact.phone = request.form.get('phone')
            contact.company = request.form.get('company')
            contact.position = request.form.get('position')
            contact.notes = request.form.get('notes')
            contact.tags = request.form.get('tags')
            db.session.commit()

            log_activity('note', f'Contact updated: {contact.name}', contact_id=contact.id)

            flash('Contact updated successfully!', 'success')
            return redirect(url_for('contacts'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating contact: {str(e)}', 'error')
            print(f"Error in edit_contact: {str(e)}")

    return render_template('contact_form.html', contact=contact, user=current_user)

@app.route('/contacts/delete/<int:contact_id>', methods=['POST'])
@login_required
def delete_contact(contact_id):
    contact = Contact.query.filter_by(id=contact_id, user_id=current_user.id).first_or_404()
    try:
        # Delete related records first
        Activity.query.filter_by(contact_id=contact_id).delete()
        Task.query.filter_by(contact_id=contact_id).delete()
        Deal.query.filter_by(contact_id=contact_id).delete()
        db.session.delete(contact)
        db.session.commit()
        flash('Contact deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting contact: {str(e)}', 'error')
    return redirect(url_for('contacts'))

@app.route('/contacts/<int:contact_id>')
@login_required
def view_contact(contact_id):
    contact = Contact.query.filter_by(id=contact_id, user_id=current_user.id).first_or_404()
    activities = Activity.query.filter_by(contact_id=contact_id).order_by(Activity.created_at.desc()).all()
    deals = Deal.query.filter_by(contact_id=contact_id).all()
    tasks = Task.query.filter_by(contact_id=contact_id).order_by(Task.due_date).all()

    return render_template('contact_detail.html', contact=contact, activities=activities, deals=deals, tasks=tasks, user=current_user)

@app.route('/contacts/export')
@login_required
def export_contacts():
    contacts = Contact.query.filter_by(user_id=current_user.id).order_by(Contact.name).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Name', 'Email', 'Phone', 'Company', 'Position', 'Tags', 'Created At'])

    for contact in contacts:
        writer.writerow([
            contact.name,
            contact.email or '',
            contact.phone or '',
            contact.company or '',
            contact.position or '',
            contact.tags or '',
            contact.created_at.strftime('%Y-%m-%d %H:%M') if contact.created_at else ''
        ])

    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=contacts_export.csv'}
    )

@app.route('/deals/export')
@login_required
def export_deals():
    deals = Deal.query.filter_by(user_id=current_user.id).order_by(Deal.created_at.desc()).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Title', 'Value', 'Stage', 'Probability', 'Contact', 'Expected Close', 'Created At'])

    for deal in deals:
        contact_name = deal.contact.name if deal.contact else ''
        writer.writerow([
            deal.title,
            deal.value,
            deal.stage,
            deal.probability,
            contact_name,
            deal.expected_close_date.strftime('%Y-%m-%d') if deal.expected_close_date else '',
            deal.created_at.strftime('%Y-%m-%d %H:%M') if deal.created_at else ''
        ])

    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=deals_export.csv'}
    )

# ========== PIPELINE ROUTES ==========
@app.route('/pipeline')
@login_required
def pipeline():
    # Get deals grouped by stage
    stages = ['lead', 'qualified', 'proposal', 'negotiation', 'closed-won', 'closed-lost']
    deals_by_stage = {}

    for stage in stages:
        deals_by_stage[stage] = Deal.query.filter_by(user_id=current_user.id, stage=stage).order_by(Deal.created_at.desc()).all()

    return render_template('pipeline.html', deals_by_stage=deals_by_stage, stages=stages, user=current_user)

@app.route('/deals/add', methods=['GET', 'POST'])
@login_required
def add_deal():
    if request.method == 'POST':
        try:
            deal = Deal(
                user_id=current_user.id,
                contact_id=request.form.get('contact_id') or None,
                title=request.form.get('title'),
                value=float(request.form.get('value', 0)),
                stage=request.form.get('stage', 'lead'),
                probability=int(request.form.get('probability', 0)),
                description=request.form.get('description')
            )

            # Parse expected close date
            close_date_str = request.form.get('expected_close_date')
            if close_date_str:
                deal.expected_close_date = datetime.strptime(close_date_str, '%Y-%m-%d').date()

            db.session.add(deal)
            db.session.commit()

            log_activity('note', f'Deal created: {deal.title} (${deal.value:,.2f})', contact_id=deal.contact_id, deal_id=deal.id)

            flash('Deal added successfully!', 'success')
            return redirect(url_for('pipeline'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding deal: {str(e)}', 'error')
            print(f"Error in add_deal: {str(e)}")

    contacts = Contact.query.filter_by(user_id=current_user.id).all()
    return render_template('deal_form.html', deal=None, contacts=contacts, user=current_user)

@app.route('/deals/edit/<int:deal_id>', methods=['GET', 'POST'])
@login_required
def edit_deal(deal_id):
    deal = Deal.query.filter_by(id=deal_id, user_id=current_user.id).first_or_404()

    if request.method == 'POST':
        deal.contact_id = request.form.get('contact_id') or None
        deal.title = request.form.get('title')
        deal.value = float(request.form.get('value', 0))
        deal.stage = request.form.get('stage')
        deal.probability = int(request.form.get('probability', 0))
        deal.description = request.form.get('description')

        close_date_str = request.form.get('expected_close_date')
        if close_date_str:
            deal.expected_close_date = datetime.strptime(close_date_str, '%Y-%m-%d').date()

        db.session.commit()

        log_activity('note', f'Deal updated: {deal.title}', contact_id=deal.contact_id, deal_id=deal.id)

        flash('Deal updated successfully!', 'success')
        return redirect(url_for('pipeline'))

    contacts = Contact.query.filter_by(user_id=current_user.id).all()
    return render_template('deal_form.html', deal=deal, contacts=contacts, user=current_user)

@app.route('/deals/update-stage/<int:deal_id>', methods=['POST'])
@login_required
def update_deal_stage(deal_id):
    deal = Deal.query.filter_by(id=deal_id, user_id=current_user.id).first_or_404()
    new_stage = request.json.get('stage')

    if new_stage in ['lead', 'qualified', 'proposal', 'negotiation', 'closed-won', 'closed-lost']:
        old_stage = deal.stage
        deal.stage = new_stage
        db.session.commit()
        log_activity('note', f'Deal "{deal.title}" moved from {old_stage} to {new_stage}', contact_id=deal.contact_id, deal_id=deal.id)
        run_automations('deal_stage_change', current_user.id, contact_id=deal.contact_id, deal_id=deal.id)
        return jsonify({'success': True})

    return jsonify({'success': False}), 400

@app.route('/deals/delete/<int:deal_id>', methods=['POST'])
@login_required
def delete_deal(deal_id):
    deal = Deal.query.filter_by(id=deal_id, user_id=current_user.id).first_or_404()
    deal_title = deal.title
    Activity.query.filter_by(deal_id=deal_id).delete()
    Task.query.filter_by(deal_id=deal_id).delete()
    db.session.delete(deal)
    db.session.commit()

    flash('Deal deleted successfully!', 'success')
    return redirect(url_for('pipeline'))

# ========== ANALYTICS ROUTES ==========
@app.route('/analytics')
@login_required
def analytics():
    # Get various statistics
    total_contacts = Contact.query.filter_by(user_id=current_user.id).count()
    total_deals = Deal.query.filter_by(user_id=current_user.id).count()
    won_deals = Deal.query.filter_by(user_id=current_user.id, stage='closed-won').count()
    lost_deals = Deal.query.filter_by(user_id=current_user.id, stage='closed-lost').count()

    total_revenue = db.session.query(db.func.sum(Deal.value)).filter_by(user_id=current_user.id, stage='closed-won').scalar() or 0
    pipeline_value = db.session.query(db.func.sum(Deal.value)).filter_by(user_id=current_user.id).filter(Deal.stage.in_(['lead', 'qualified', 'proposal', 'negotiation'])).scalar() or 0

    # Deals by stage
    stages = ['lead', 'qualified', 'proposal', 'negotiation', 'closed-won', 'closed-lost']
    deals_by_stage = {}
    for stage in stages:
        deals_by_stage[stage] = Deal.query.filter_by(user_id=current_user.id, stage=stage).count()

    # Win rate
    win_rate = (won_deals / total_deals * 100) if total_deals > 0 else 0

    # Monthly trends - contacts and deals created per month (last 6 months)
    import calendar
    monthly_labels = []
    monthly_contacts = []
    monthly_deals = []
    monthly_revenue = []
    today = datetime.utcnow()

    for i in range(5, -1, -1):
        month = today.month - i
        year = today.year
        while month <= 0:
            month += 12
            year -= 1
        month_start = datetime(year, month, 1)
        if month == 12:
            month_end = datetime(year + 1, 1, 1)
        else:
            month_end = datetime(year, month + 1, 1)

        monthly_labels.append(calendar.month_abbr[month])
        monthly_contacts.append(Contact.query.filter(
            Contact.user_id == current_user.id,
            Contact.created_at >= month_start,
            Contact.created_at < month_end
        ).count())
        monthly_deals.append(Deal.query.filter(
            Deal.user_id == current_user.id,
            Deal.created_at >= month_start,
            Deal.created_at < month_end
        ).count())
        monthly_revenue.append(float(db.session.query(db.func.sum(Deal.value)).filter(
            Deal.user_id == current_user.id,
            Deal.stage == 'closed-won',
            Deal.created_at >= month_start,
            Deal.created_at < month_end
        ).scalar() or 0))

    # Recent activities
    recent_activities = Activity.query.filter_by(user_id=current_user.id).order_by(Activity.created_at.desc()).limit(10).all()

    # Tasks stats
    pending_tasks = Task.query.filter_by(user_id=current_user.id, completed=False).count()
    completed_tasks = Task.query.filter_by(user_id=current_user.id, completed=True).count()

    return render_template('analytics.html',
                         user=current_user,
                         total_contacts=total_contacts,
                         total_deals=total_deals,
                         won_deals=won_deals,
                         lost_deals=lost_deals,
                         total_revenue=total_revenue,
                         pipeline_value=pipeline_value,
                         deals_by_stage=deals_by_stage,
                         win_rate=win_rate,
                         monthly_labels=monthly_labels,
                         monthly_contacts=monthly_contacts,
                         monthly_deals=monthly_deals,
                         monthly_revenue=monthly_revenue,
                         recent_activities=recent_activities,
                         pending_tasks=pending_tasks,
                         completed_tasks=completed_tasks)

# ========== TASKS ROUTES ==========
@app.route('/tasks')
@login_required
def tasks():
    pending_tasks = Task.query.filter_by(user_id=current_user.id, completed=False).order_by(Task.due_date).all()
    completed_tasks = Task.query.filter_by(user_id=current_user.id, completed=True).order_by(Task.created_at.desc()).limit(20).all()

    return render_template('tasks.html', pending_tasks=pending_tasks, completed_tasks=completed_tasks, user=current_user)

@app.route('/tasks/add', methods=['POST'])
@login_required
def add_task():
    task = Task(
        user_id=current_user.id,
        contact_id=request.form.get('contact_id') or None,
        deal_id=request.form.get('deal_id') or None,
        title=request.form.get('title'),
        description=request.form.get('description'),
        priority=request.form.get('priority', 'medium')
    )

    due_date_str = request.form.get('due_date')
    if due_date_str:
        task.due_date = datetime.strptime(due_date_str, '%Y-%m-%d')

    db.session.add(task)
    db.session.commit()

    log_activity('note', f'Task created: {task.title}', contact_id=task.contact_id, deal_id=task.deal_id)

    flash('Task created successfully!', 'success')
    return redirect(url_for('tasks'))

@app.route('/tasks/toggle/<int:task_id>', methods=['POST'])
@login_required
def toggle_task(task_id):
    task = Task.query.filter_by(id=task_id, user_id=current_user.id).first_or_404()
    task.completed = not task.completed
    db.session.commit()

    status = 'completed' if task.completed else 'reopened'
    log_activity('note', f'Task {status}: {task.title}', contact_id=task.contact_id, deal_id=task.deal_id)

    return jsonify({'success': True, 'completed': task.completed})

@app.route('/tasks/edit/<int:task_id>', methods=['POST'])
@login_required
def edit_task(task_id):
    task = Task.query.filter_by(id=task_id, user_id=current_user.id).first_or_404()

    task.title = request.form.get('title')
    task.description = request.form.get('description')
    task.priority = request.form.get('priority', 'medium')

    due_date_str = request.form.get('due_date')
    if due_date_str:
        task.due_date = datetime.strptime(due_date_str, '%Y-%m-%d')
    else:
        task.due_date = None

    db.session.commit()
    log_activity('note', f'Task updated: {task.title}', contact_id=task.contact_id, deal_id=task.deal_id)

    flash('Task updated successfully!', 'success')
    return redirect(url_for('tasks'))

@app.route('/tasks/delete/<int:task_id>', methods=['POST'])
@login_required
def delete_task(task_id):
    task = Task.query.filter_by(id=task_id, user_id=current_user.id).first_or_404()
    task_title = task.title
    db.session.delete(task)
    db.session.commit()

    log_activity('note', f'Task deleted: {task_title}')
    flash('Task deleted successfully!', 'success')
    return redirect(url_for('tasks'))

# ========== NOTIFICATIONS ROUTES ==========
@app.route('/notifications/settings', methods=['GET', 'POST'])
@login_required
def notification_settings():
    settings = NotificationSettings.query.filter_by(user_id=current_user.id).first()

    if not settings:
        settings = NotificationSettings(user_id=current_user.id)
        db.session.add(settings)
        db.session.commit()

    if request.method == 'POST':
        settings.email_notifications = 'email_notifications' in request.form
        settings.telegram_notifications = 'telegram_notifications' in request.form
        settings.task_reminders = 'task_reminders' in request.form
        settings.deal_updates = 'deal_updates' in request.form
        settings.daily_summary = 'daily_summary' in request.form
        db.session.commit()

        flash('Notification settings updated!', 'success')
        return redirect(url_for('notification_settings'))

    return render_template('notification_settings.html', settings=settings, user=current_user)

# ========== AUTOMATION ROUTES ==========
@app.route('/automations')
@login_required
def automations():
    automations = Automation.query.filter_by(user_id=current_user.id).all()
    return render_template('automations.html', automations=automations, user=current_user)

@app.route('/automations/add', methods=['GET', 'POST'])
@login_required
def add_automation():
    if request.method == 'POST':
        automation = Automation(
            user_id=current_user.id,
            name=request.form.get('name'),
            trigger=request.form.get('trigger'),
            action=request.form.get('action'),
            active=True
        )
        db.session.add(automation)
        db.session.commit()

        flash('Automation created successfully!', 'success')
        return redirect(url_for('automations'))

    return render_template('automation_form.html', automation=None, user=current_user)

@app.route('/automations/toggle/<int:automation_id>', methods=['POST'])
@login_required
def toggle_automation(automation_id):
    automation = Automation.query.filter_by(id=automation_id, user_id=current_user.id).first_or_404()
    automation.active = not automation.active
    db.session.commit()

    return jsonify({'success': True, 'active': automation.active})

@app.route('/automations/delete/<int:automation_id>', methods=['POST'])
@login_required
def delete_automation(automation_id):
    automation = Automation.query.filter_by(id=automation_id, user_id=current_user.id).first_or_404()
    db.session.delete(automation)
    db.session.commit()

    flash('Automation deleted successfully!', 'success')
    return redirect(url_for('automations'))

# ========== ADMIN ROUTES ==========
@app.route('/admin/reset-password', methods=['GET', 'POST'])
def reset_admin_password():
    """Reset admin password - protected by secret key"""
    if request.method == 'GET':
        # Show form
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Reset Admin Password</title>
            <style>
                body {
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    min-height: 100vh;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    padding: 20px;
                }
                .card {
                    background: white;
                    border-radius: 15px;
                    padding: 40px;
                    max-width: 400px;
                    width: 100%;
                    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
                }
                h1 { color: #667eea; margin-bottom: 20px; }
                input {
                    width: 100%;
                    padding: 12px;
                    margin: 10px 0;
                    border: 1px solid #ddd;
                    border-radius: 8px;
                    font-size: 14px;
                }
                button {
                    width: 100%;
                    padding: 12px;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    border: none;
                    border-radius: 8px;
                    font-weight: 600;
                    cursor: pointer;
                    margin-top: 20px;
                }
                button:hover { opacity: 0.9; }
                .note { font-size: 12px; color: #666; margin-top: 15px; }
            </style>
        </head>
        <body>
            <div class="card">
                <h1>🔐 Reset Admin Password</h1>
                <form method="POST">
                    <input type="text" name="username" placeholder="Username (admin)" required>
                    <input type="password" name="new_password" placeholder="New Password" required>
                    <input type="password" name="confirm_password" placeholder="Confirm Password" required>
                    <input type="password" name="admin_key" placeholder="Admin Key (from SECRET_KEY)" required>
                    <button type="submit">Reset Password</button>
                </form>
                <div class="note">Admin key is the first 16 characters of your SECRET_KEY environment variable.</div>
            </div>
        </body>
        </html>
        """
        return html

    # Handle POST
    username = request.form.get('username')
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')
    admin_key = request.form.get('admin_key')

    # Verify admin key (first 16 chars of SECRET_KEY)
    expected_key = app.config['SECRET_KEY'][:16]
    if admin_key != expected_key:
        flash('Invalid admin key', 'error')
        return redirect(url_for('reset_admin_password'))

    if new_password != confirm_password:
        flash('Passwords do not match', 'error')
        return redirect(url_for('reset_admin_password'))

    if len(new_password) < 6:
        flash('Password must be at least 6 characters', 'error')
        return redirect(url_for('reset_admin_password'))

    user = User.query.filter_by(username=username).first()
    if not user:
        flash('User not found', 'error')
        return redirect(url_for('reset_admin_password'))

    user.set_password(new_password)
    db.session.commit()

    flash(f'Password reset successfully for {username}!', 'success')
    return redirect(url_for('login'))

# ========== DATABASE INITIALIZATION ROUTE ==========
@app.route('/init-db')
def init_database_route():
    """
    Initialize database and create default users
    Access this once after deployment: https://your-app.onrender.com/init-db?key=init-coco-2024
    """
    # Simple protection - require a key parameter
    init_key = request.args.get('key')
    if init_key != 'init-coco-2024':
        return jsonify({'error': 'Invalid initialization key'}), 403

    try:
        # Create all tables
        db.create_all()

        results = {
            'database_created': True,
            'users_created': [],
            'users_updated': [],
            'errors': []
        }

        # Create admin user
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(
                username='admin',
                email='admin@cococrm.com',
                first_name='Admin',
                last_name='CocoCRM'
            )
            admin.set_password('admin123')
            db.session.add(admin)
            results['users_created'].append('admin')
        else:
            results['users_updated'].append('admin (already exists)')

        # Create Coco user (openclaw)
        coco = User.query.filter_by(username='coco').first()
        if not coco:
            coco = User(
                username='coco',
                email='coco@openclaw.ai',
                first_name='Coco',
                last_name='OpenClaw'
            )
            coco.set_password('coco123')
            db.session.add(coco)
            results['users_created'].append('coco')
        else:
            results['users_updated'].append('coco (already exists)')

        # Commit changes
        db.session.commit()

        # Get all users
        all_users = User.query.all()
        results['total_users'] = len(all_users)
        results['users_list'] = [{'username': u.username, 'email': u.email} for u in all_users]

        # Return success message
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Database Initialized - CocoCRM</title>
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 50px;
                    max-width: 800px;
                    margin: 0 auto;
                }}
                .card {{
                    background: rgba(255, 255, 255, 0.1);
                    backdrop-filter: blur(10px);
                    border-radius: 15px;
                    padding: 40px;
                    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
                }}
                h1 {{ font-size: 2.5em; margin-bottom: 20px; }}
                .success {{ color: #4CAF50; font-size: 1.2em; margin: 20px 0; }}
                .info {{ background: rgba(255, 255, 255, 0.05); padding: 20px; border-radius: 10px; margin: 20px 0; }}
                .user-list {{ list-style: none; padding: 0; }}
                .user-list li {{ padding: 10px; background: rgba(255, 255, 255, 0.05); margin: 5px 0; border-radius: 5px; }}
                .btn {{
                    display: inline-block;
                    padding: 15px 30px;
                    background: white;
                    color: #667eea;
                    text-decoration: none;
                    border-radius: 10px;
                    font-weight: bold;
                    margin-top: 20px;
                }}
                .credentials {{
                    background: rgba(0, 0, 0, 0.2);
                    padding: 20px;
                    border-radius: 10px;
                    margin: 20px 0;
                    border-left: 4px solid #4CAF50;
                }}
            </style>
        </head>
        <body>
            <div class="card">
                <h1>✅ Database Initialized Successfully!</h1>

                <div class="success">
                    Database tables created and users configured
                </div>

                <div class="credentials">
                    <h3>🔑 Login Credentials:</h3>
                    <ul>
                        <li><strong>Admin:</strong> username: <code>admin</code> / password: <code>admin123</code></li>
                        <li><strong>Coco (OpenClaw):</strong> username: <code>coco</code> / password: <code>coco123</code></li>
                    </ul>
                </div>

                <div class="info">
                    <h3>📊 Summary:</h3>
                    <p><strong>Total users in database:</strong> {results['total_users']}</p>
                    <p><strong>Users created this run:</strong> {', '.join(results['users_created']) if results['users_created'] else 'None (already existed)'}</p>

                    <h4>All users:</h4>
                    <ul class="user-list">
                        {''.join([f"<li>{u['username']} ({u['email'] or 'no email'})</li>" for u in results['users_list']])}
                    </ul>
                </div>

                <a href="/login" class="btn">Go to Login →</a>
            </div>
        </body>
        </html>
        """
        return html

    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        return jsonify({
            'error': str(e),
            'trace': error_trace
        }), 500

# Initialize database
with app.app_context():
    db.create_all()

# Set up Telegram webhook on startup (in background to not block startup)
def _setup_webhook():
    """Set up Telegram webhook after a short delay to ensure app is ready"""
    import time
    time.sleep(5)  # Wait for app to be fully started
    with app.app_context():
        set_telegram_webhook()

_webhook_thread = threading.Thread(target=_setup_webhook)
_webhook_thread.daemon = True
_webhook_thread.start()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
