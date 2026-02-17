from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import hashlib
import hmac
import os
from datetime import datetime

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

@app.route('/')
def index():
    if current_user.is_authenticated:
        return render_template('dashboard.html', user=current_user)
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

        return jsonify({'success': True, 'redirect': url_for('index')})

    except Exception as e:
        print("=" * 80)
        print(f"💥 EXCEPTION in telegram_auth: {str(e)}")
        print(f"   Type: {type(e).__name__}")
        import traceback
        print(traceback.format_exc())
        print("=" * 80)
        return jsonify({'success': False, 'message': f'Server error: {str(e)}'}), 500

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out', 'info')
    return redirect(url_for('login'))

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
    return render_template('dashboard.html', user=current_user)

# Initialize database
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
