# 🤖 Axension AI — WhatsApp Agent

A production-ready WhatsApp automation system powered by **FastAPI**, **Celery**, **Redis**, and the **Meta WhatsApp Business API**. It handles inbound messages with auto-replies, sends scheduled supplier follow-ups, and gives factory owners a daily morning brief.

---

## 📁 Project Structure

```
axension-ai/
│
├── src/
│   ├── whatsapp/
│   │   ├── webhook.py        # FastAPI app — receives & replies to WhatsApp messages
│   │   ├── client.py         # Meta API wrapper — send text & templates
│   │   └── templates.py      # Pre-written message templates (nudge, chase, escalate)
│   │
│   └── tasks/
│       └── celery_app.py     # Celery app — scheduled tasks (heartbeat, daily follow-up)
│
├── .env                      # Your secrets (tokens, phone IDs)
├── requirements.txt          # Python dependencies
├── docker-compose.yml        # Docker setup (Redis + Workers + Webhook)
└── README.md
```

---

## ⚙️ Prerequisites

Before you start, make sure you have:

- Python 3.10+
- [ngrok](https://ngrok.com/download) installed
- A [Meta Developer account](https://developers.facebook.com/)
- Redis (either locally or via Docker)

---

## 🔑 Step 1 — Meta Developer Setup

1. Go to [developers.facebook.com](https://developers.facebook.com/) and sign in.
2. Click **Create App** → select **Business** type.
3. Add the **WhatsApp** product to your app.
4. Under **WhatsApp → API Setup**:
   - Copy your **Temporary Access Token** → this is your `WABA_TOKEN`
   - Copy your **Phone Number ID** → this is your `WABA_PHONE_ID`
   - Add your personal number as a **test recipient** to receive messages from the business account.

---

## 🛠️ Step 2 — Configure Your `.env` File

Create a `.env` file in the project root (rename `_env` → `.env`):

```env
WABA_TOKEN=your_meta_access_token_here
WABA_PHONE_ID=your_phone_number_id_here
WABA_VERSION=v19.0
WABA_VERIFY_TOKEN=mytoken123
TEST_PHONE=91XXXXXXXXXX        # Your WhatsApp number (no + or spaces)
REDIS_URL=redis://localhost:6379/0
HEARTBEAT_NUMBER=91XXXXXXXXXX  # Number to receive heartbeat pings
```

> ⚠️ **Never commit your `.env` file to Git.** Add it to `.gitignore`.

---

## 📦 Step 3 — Install Dependencies

```bash
pip install fastapi uvicorn[standard] requests python-dotenv celery redis pydantic
```

Or using the requirements file:

```bash
pip install -r requirements.txt
```

---

## 🚀 Step 4 — Start the Webhook Server

```bash
uvicorn src.whatsapp.webhook:app --reload --port 8000
```

The server starts at: **http://localhost:8000**

You should see:
```
Axension AI WhatsApp Webhook is running.
Local:  http://localhost:8000
```

---

## 🌐 Step 5 — Expose with ngrok

Meta requires a **public HTTPS URL** to deliver webhook events. Use ngrok to create one.

1. Download & install ngrok from [ngrok.com](https://ngrok.com/download)
2. In a **new terminal**, run:

```bash
ngrok http 8000
```

3. Copy the **Forwarding URL** shown (e.g. `https://abc123.ngrok-free.app`)

---

## 🔗 Step 6 — Register Webhook on Meta

1. Go to your Meta App → **WhatsApp → Configuration**
2. Under **Webhook**, click **Edit**:
   - **Callback URL**: `https://your-ngrok-url.ngrok-free.app/webhook`
   - **Verify Token**: `mytoken123` (must match `WABA_VERIFY_TOKEN` in `.env`)
3. Click **Verify and Save**
4. Subscribe to the **`messages`** field

✅ You're live! Messages sent to your WhatsApp Business number will now hit your server.

---

## 💬 How Auto-Reply Works

When someone messages your WhatsApp number, `webhook.py` parses the message and `generate_reply()` responds automatically:

| Incoming Message | Bot Reply |
|---|---|
| `hi`, `hello`, `hey` | Welcome greeting |
| `price`, `cost`, `pricing` | Pricing info redirect |
| `help` | Lists available assistance |
| `bye`, `thanks`, `thank you` | Farewell message |
| Anything else | Acknowledgement + prompt to type *help* |

---

## 📨 Message Templates

`templates.py` contains pre-written supplier follow-up messages:

| Function | When to Use | Tone |
|---|---|---|
| `supplier_nudge()` | 1–2 days overdue | Friendly reminder |
| `supplier_chase()` | 3–5 days overdue | Firm, mentions impact |
| `supplier_escalate()` | 5+ days overdue | Urgent, requests callback |
| `owner_morning_brief()` | 7:45 AM daily | Summary for factory owner |

---

## ⏰ Step 7 — Run Celery (Scheduled Tasks) — Optional

Open **two additional terminals**:

**Terminal 2 — Celery Worker:**
```bash
celery -A src.tasks.celery_app worker --loglevel=info
```

**Terminal 3 — Celery Beat (Scheduler):**
```bash
celery -A src.tasks.celery_app beat --loglevel=info
```

### What runs automatically:

| Task | Schedule | Description |
|---|---|---|
| `send_heartbeat` | Every 5 minutes | Sends a ping to `HEARTBEAT_NUMBER` confirming the system is alive |
| `daily_supplier_followup` | 8:00 AM IST daily | Placeholder for overdue PO follow-up logic (Day 2) |

> Redis must be running for Celery to work. See Docker section below.

---

## 📤 Send a Message from Terminal (Manual Test)

You can send a WhatsApp message directly from your terminal without opening the chat:

**PowerShell (Windows):**
```powershell
Invoke-RestMethod -Method Post -Uri "http://localhost:8000/send-test" `
  -ContentType "application/json" `
  -Body '{"to": "918121444200", "message": "Hello from Axension AI!"}'
```

**curl (Mac/Linux):**
```bash
curl -X POST http://localhost:8000/send-test \
  -H "Content-Type: application/json" \
  -d '{"to": "918121444200", "message": "Hello from Axension AI!"}'
```

Replace `918121444200` with the target number (country code + number, no `+`).

---

## 🐳 Docker Setup (All-in-One)

To run everything — Redis, Celery worker, Celery beat, and the webhook server — with one command:

```bash
docker-compose up --build
```

This starts:
| Container | Role |
|---|---|
| `axension_redis` | Message broker & task backend |
| `axension_worker` | Processes Celery tasks |
| `axension_beat` | Triggers scheduled tasks |
| `axension_webhook` | FastAPI server on port 8000 |

To stop everything:
```bash
docker-compose down
```

---

## 🔍 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Health check |
| `GET` | `/webhook` | Meta webhook verification |
| `POST` | `/webhook` | Receive incoming WhatsApp messages |
| `POST` | `/send-test` | Manually send a WhatsApp message |
| `GET` | `/messages` | View last 10 received messages |

---

## 🧪 Quick Smoke Test

1. Start server → `uvicorn src.whatsapp.webhook:app --reload --port 8000`
2. Open browser → `http://localhost:8000` → should return `{"status": "running"}`
3. Open browser → `http://localhost:8000/messages` → shows received messages
4. Send a WhatsApp message to your business number → check terminal logs for the reply

---

## 🛣️ Roadmap

- [x] **Day 1** — WhatsApp webhook, auto-reply, Celery heartbeat, message templates
- [ ] **Day 2** — Fetch overdue POs from database, run template logic, auto-dispatch supplier messages
- [ ] **Day 3** — AI/LLM-powered replies via Claude or GPT integration
- [ ] **Day 4** — Owner dashboard, analytics, multi-factory support

---

## 🐛 Troubleshooting

**Webhook verification failing?**
- Make sure `WABA_VERIFY_TOKEN` in `.env` matches exactly what you entered in the Meta dashboard.
- Confirm ngrok is running and the URL is current (ngrok URLs change on restart unless you have a paid plan).

**Messages not arriving?**
- Check that you subscribed to the `messages` field in Meta webhook settings.
- Confirm your number is added as a test recipient in Meta API Setup.

**Celery tasks not running?**
- Ensure Redis is running: `redis-cli ping` should return `PONG`.
- Check that both `worker` and `beat` terminals are active.

**`ModuleNotFoundError: src`?**
- Run commands from the project root directory, not inside `src/`.
