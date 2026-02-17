# OpenClaw Integration API - CocoCRM

Complete API documentation for integrating OpenClaw AI agent with CocoCRM.

## 🔐 Authentication

All API endpoints require an API key. There are **3 ways** to authenticate:

### Method 1: X-API-Key Header (Recommended ⭐)
```http
X-API-Key: sk-openclaw-2026-your-secret-key
```

### Method 2: Authorization Bearer Header
```http
Authorization: Bearer sk-openclaw-2026-your-secret-key
```

### Method 3: Query Parameter (Testing only ⚠️)
```
?api_key=sk-openclaw-2026-your-secret-key
```

**⚙️ Setup in Render:**

Set the environment variable `OPENCLAW_API_KEY` (or `TELEGRAM_API_KEY` as fallback):

```bash
OPENCLAW_API_KEY=sk-openclaw-2026-your-secret-key-here
```

This is a **permanent API key** that never expires, perfect for bot integration.

---

## 🚀 Getting Started for OpenClaw

### 1. Get Login Access

OpenClaw can log in via Telegram bot commands:

```bash
# Send to @Cangrekimibot in Telegram
/start    # Creates account automatically
/crm      # Generates 3-hour login link
```

### 2. Programmatic Login (for automation)

```bash
curl -X POST https://cococrm.onrender.com/api/telegram/generate-token \
  -H "Content-Type: application/json" \
  -d '{
    "api_key": "kimi-claw-secure-api-key-2026",
    "username": "openclaw",
    "first_name": "OpenClaw",
    "last_name": "AI Agent"
  }'
```

**Response:**
```json
{
  "success": true,
  "token": "eyJhbGciOiJIUzI1...",
  "url": "https://cococrm.onrender.com/?token=eyJhbGc...",
  "expires_in": 180,
  "user": {
    "id": 2,
    "username": "openclaw"
  }
}
```

---

## 📋 REST API Endpoints

All endpoints support JSON format and require API key authentication.

### Contacts API

#### **List All Contacts**
```http
GET /api/contacts?username=admin
X-API-Key: your-api-key
```

**Response:**
```json
{
  "success": true,
  "contacts": [
    {
      "id": 1,
      "name": "John Doe",
      "email": "john@example.com",
      "phone": "+1234567890",
      "company": "ACME Corp",
      "position": "CEO",
      "tags": "vip,tech",
      "created_at": "2026-02-17T10:30:00"
    }
  ]
}
```

#### **Create Contact**
```http
POST /api/contacts
X-API-Key: your-api-key
Content-Type: application/json

{
  "username": "admin",
  "name": "Jane Smith",
  "email": "jane@example.com",
  "phone": "+0987654321",
  "company": "Tech Startup",
  "position": "CTO",
  "tags": "tech,startup",
  "notes": "Met at conference 2026"
}
```

**Response:**
```json
{
  "success": true,
  "contact": {
    "id": 2,
    "name": "Jane Smith",
    "email": "jane@example.com",
    "phone": "+0987654321"
  }
}
```

---

### Deals API

#### **List All Deals**
```http
GET /api/deals?username=admin
X-API-Key: your-api-key
```

**Response:**
```json
{
  "success": true,
  "deals": [
    {
      "id": 1,
      "title": "Enterprise License Deal",
      "value": 50000.00,
      "stage": "proposal",
      "probability": 75,
      "contact_id": 1,
      "created_at": "2026-02-15T14:20:00"
    }
  ]
}
```

#### **Create Deal**
```http
POST /api/deals
X-API-Key: your-api-key
Content-Type: application/json

{
  "username": "admin",
  "contact_id": 1,
  "title": "New SaaS Subscription",
  "value": 12000,
  "stage": "lead",
  "probability": 50,
  "description": "Annual subscription for 10 users"
}
```

**Deal Stages:**
- `lead` - Initial contact
- `qualified` - Qualified opportunity
- `proposal` - Proposal sent
- `negotiation` - In negotiation
- `closed-won` - Deal won
- `closed-lost` - Deal lost

---

### Tasks API

#### **List All Tasks**
```http
GET /api/tasks?username=admin
X-API-Key: your-api-key
```

**Response:**
```json
{
  "success": true,
  "tasks": [
    {
      "id": 1,
      "title": "Follow up with John Doe",
      "description": "Send proposal document",
      "priority": "high",
      "completed": false,
      "due_date": "2026-02-20",
      "created_at": "2026-02-17T09:00:00"
    }
  ]
}
```

#### **Create Task**
```http
POST /api/tasks
X-API-Key: your-api-key
Content-Type: application/json

{
  "username": "admin",
  "title": "Prepare demo for client",
  "description": "Setup demo environment",
  "priority": "high",
  "contact_id": 1,
  "deal_id": 1,
  "due_date": "2026-02-25T15:00:00"
}
```

**Task Priorities:** `low`, `medium`, `high`

---

## 🤖 OpenClaw Usage Examples

### Example 1: Add Contact from Conversation

```python
import requests

# ⚠️ Get this from Render environment variables
API_KEY = "sk-openclaw-2026-your-secret-key"
BASE_URL = "https://cococrm.onrender.com"

def add_contact_to_crm(name, email, phone=None, company=None):
    """Add a contact to CocoCRM using permanent API key"""
    response = requests.post(
        f"{BASE_URL}/api/contacts",
        headers={"X-API-Key": API_KEY},  # Permanent key - never expires!
        json={
            "username": "admin",
            "name": name,
            "email": email,
            "phone": phone,
            "company": company
        }
    )
    return response.json()

# Usage
result = add_contact_to_crm(
    name="Alice Johnson",
    email="alice@startup.io",
    company="Future Tech"
)
print(f"Contact created: {result}")

# Alternative: Using Authorization Bearer header
def add_contact_bearer(name, email):
    """Add contact using Bearer token authentication"""
    response = requests.post(
        f"{BASE_URL}/api/contacts",
        headers={"Authorization": f"Bearer {API_KEY}"},
        json={
            "username": "admin",
            "name": name,
            "email": email
        }
    )
    return response.json()
```

### Example 2: Create Task from User Request

```python
def create_task_from_message(task_title, due_date=None):
    """Create a task in CocoCRM"""
    response = requests.post(
        f"{BASE_URL}/api/tasks",
        headers={"X-API-Key": API_KEY},
        json={
            "username": "admin",
            "title": task_title,
            "priority": "medium",
            "due_date": due_date
        }
    )
    return response.json()

# Usage
task = create_task_from_message(
    task_title="Review Q1 sales report",
    due_date="2026-03-01T10:00:00"
)
```

### Example 3: Get CRM Status

```python
def get_crm_summary():
    """Get summary of CRM data"""
    contacts = requests.get(
        f"{BASE_URL}/api/contacts?username=admin",
        headers={"X-API-Key": API_KEY}
    ).json()

    deals = requests.get(
        f"{BASE_URL}/api/deals?username=admin",
        headers={"X-API-Key": API_KEY}
    ).json()

    tasks = requests.get(
        f"{BASE_URL}/api/tasks?username=admin",
        headers={"X-API-Key": API_KEY}
    ).json()

    return {
        "total_contacts": len(contacts['contacts']),
        "total_deals": len(deals['deals']),
        "pending_tasks": sum(1 for t in tasks['tasks'] if not t['completed'])
    }

summary = get_crm_summary()
print(f"CRM Summary: {summary}")
```

---

## 🔔 Bot Commands for OpenClaw

When OpenClaw communicates via Telegram bot:

| Command | Description |
|---------|-------------|
| `/start` | Initialize and create account |
| `/crm` | Get temporary login link (3 hours) |
| `/status` | View CRM statistics (contacts, deals, tasks) |
| `/help` | Show available commands |

---

## 🛠️ Admin Operations

### Reset Admin Password

Visit: `https://cococrm.onrender.com/admin/reset-password`

- Username: `admin`
- New Password: (your choice)
- Admin Key: First 16 characters of `SECRET_KEY` env variable

---

## 📊 Data Models

### Contact
```json
{
  "id": 1,
  "name": "string (required)",
  "email": "string",
  "phone": "string",
  "company": "string",
  "position": "string",
  "tags": "comma,separated,values",
  "notes": "text",
  "created_at": "ISO8601 datetime"
}
```

### Deal
```json
{
  "id": 1,
  "title": "string (required)",
  "value": 0.00,
  "stage": "lead|qualified|proposal|negotiation|closed-won|closed-lost",
  "probability": 0-100,
  "contact_id": 1,
  "expected_close_date": "YYYY-MM-DD",
  "description": "text",
  "created_at": "ISO8601 datetime"
}
```

### Task
```json
{
  "id": 1,
  "title": "string (required)",
  "description": "text",
  "priority": "low|medium|high",
  "completed": false,
  "due_date": "ISO8601 datetime",
  "contact_id": 1,
  "deal_id": 1,
  "created_at": "ISO8601 datetime"
}
```

---

## ⚡ Quick Start Checklist

- [ ] Set `TELEGRAM_API_KEY` environment variable in Render
- [ ] Test login via `/crm` command in Telegram bot
- [ ] Test API endpoints with curl or Postman
- [ ] Integrate OpenClaw with contacts API
- [ ] Set up automated task creation
- [ ] Configure webhooks for real-time updates (coming soon)

---

## 🚨 Error Handling

All endpoints return standard JSON responses:

**Success:**
```json
{
  "success": true,
  "data": { ... }
}
```

**Error:**
```json
{
  "success": false,
  "error": "Error message description"
}
```

**HTTP Status Codes:**
- `200` - Success
- `201` - Created
- `400` - Bad Request
- `401` - Unauthorized (invalid API key)
- `404` - Not Found
- `500` - Server Error

---

## 📞 Support

For questions or issues:
- GitHub Issues: https://github.com/denverlabs/CocoCRM/issues
- Telegram: @Cangrekimibot
- Email: support@openclaw.ai

---

**Built with ❤️ for OpenClaw AI Integration**
