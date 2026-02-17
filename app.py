from flask import Flask, render_template, request, jsonify
import json
import os
import secrets
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CRM_FILE = "/tmp/personal_crm.json"

access_tokens = {}

def load_crm():
    if os.path.exists(CRM_FILE):
        with open(CRM_FILE, 'r') as f:
            return json.load(f)
    return {"contacts": [], "interactions": [], "last_scan": None}

def save_crm(data):
    with open(CRM_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def validate_token(token):
    return token == "demo-token-123"

@app.route('/')
def index():
    token = request.args.get('token')
    if not token or not validate_token(token):
        return "Acceso no válido", 403
    crm = load_crm()
    return render_template('index.html', contacts=crm['contacts'], token=token)

@app.route('/api/contacts')
def api_contacts():
    token = request.args.get('token')
    if not token or not validate_token(token):
        return jsonify({"error": "Acceso no válido"}), 403
    crm = load_crm()
    return jsonify(crm['contacts'])

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

2. requirements.txt

Flask==3.0.0
gunicorn==21.2.0

3. Procfile

web: gunicorn app:app --bind 0.0.0.0:$PORT

4. Carpeta templates/ y archivo index.html

Primero creá la carpeta templates, después el archivo index.html dentro:

<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>CRM - Contactos</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, sans-serif; margin: 0; display: flex; height: 100vh; }
        .sidebar { width: 300px; background: #f5f5f5; border-right: 1px solid #ddd; padding: 20px; overflow-y: auto; }
        .main { flex: 1; padding: 30px; }
        h1 { font-size: 20px; margin-bottom: 20px; }
        .contact-item { padding: 15px; background: white; margin-bottom: 10px; border-radius: 6px; cursor: pointer; }
        .contact-item:hover { background: #e3f2fd; }
        .contact-name { font-weight: 500; }
        .contact-email { font-size: 13px; color: #666; }
    </style>
</head>
<body>
    <div class="sidebar">
        <h1>📇 Contactos</h1>
        {% for contact in contacts %}
        <div class="contact-item">
            <div class="contact-name">{{ contact.name }}</div>
            <div class="contact-email">{{ contact.email }}</div>
        </div>
        {% endfor %}
    </div>
    <div class="main">
        <h2>Seleccioná un contacto</h2>
    </div>
</body>
</html>
