import os
import logging
from collections import deque
from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from dotenv import load_dotenv

from src.whatsapp.client import send_text, parse_incoming

load_dotenv()

VERIFY_TOKEN = os.getenv("WABA_VERIFY_TOKEN", "mytoken123")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Axension AI — WhatsApp Webhook")

# In-memory store for last 50 received messages
message_log: deque = deque(maxlen=50)


# ── Request logging middleware ────────────────────────────────────────────────
class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        logger.info(f"→ {request.method} {request.url.path}")
        response = await call_next(request)
        logger.info(f"← {response.status_code} {request.url.path}")
        return response

app.add_middleware(LoggingMiddleware)


# ── Health check ──────────────────────────────────────────────────────────────
@app.get("/")
def home():
    return {"status": "running", "service": "Axension AI WhatsApp Webhook"}


# ── Meta webhook verification (GET) ──────────────────────────────────────────
@app.get("/webhook")
def verify(request: Request):
    params = request.query_params
    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        logger.info("✅ Webhook verification successful.")
        return Response(content=challenge, media_type="text/plain")

    logger.warning(f"❌ Webhook verification failed. token={token}")
    return Response(content="Forbidden", status_code=403)


# ── Receive WhatsApp messages (POST) ──────────────────────────────────────────
@app.post("/webhook")
async def receive_message(request: Request):
    data = await request.json()
    logger.info(f"Incoming webhook payload: {data}")

    # Handle status updates (delivery receipts) — skip silently
    try:
        value = data["entry"][0]["changes"][0]["value"]
        if "statuses" in value and "messages" not in value:
            status = value["statuses"][0]
            logger.info(
                f"📬 Delivery status: id={status.get('id')} "
                f"status={status.get('status')} to={status.get('recipient_id')}"
            )
            return {"status": "ok"}
    except (KeyError, IndexError):
        pass

    # Parse actual message
    parsed = parse_incoming(data)
    if parsed:
        sender = parsed["sender_phone"]
        text = parsed["message_text"]

        logger.info(f"📩 Message from {sender}: \"{text}\"")
        message_log.appendleft(parsed)

        # ✅ AUTO-REPLY — this was missing before!
        reply = generate_reply(text)
        result = send_text(sender, reply)
        logger.info(f"📤 Reply sent to {sender}: \"{reply}\" | Meta response: {result}")

    return {"status": "ok"}


# ── Reply logic — customize this ─────────────────────────────────────────────
def generate_reply(incoming_text: str) -> str:
    """
    Simple rule-based reply engine.
    Replace or extend this with AI/LLM calls as needed.
    """
    text = incoming_text.strip().lower()

    if text in ["hi", "hello", "hey", "hii", "helo"]:
        return "👋 Hello! Welcome to Axension AI. How can I help you today?"

    elif "price" in text or "cost" in text or "pricing" in text:
        return "💰 Please visit our website or contact our team for pricing details."

    elif "help" in text:
        return (
            "🤖 I'm Axension AI assistant. Here's what I can help with:\n"
            "• Product info\n"
            "• Support queries\n"
            "• General questions\n\n"
            "Just type your question!"
        )

    elif "bye" in text or "thanks" in text or "thank you" in text:
        return "😊 Thank you for reaching out! Have a great day. — Axension AI"

    else:
        return (
            f"✅ Got your message: \"{incoming_text}\"\n\n"
            "Our team will get back to you shortly. "
            "Type *help* to see what I can assist with right now."
        )


# ── Manual test send ───────────────────────────────────────────────────────────
@app.post("/send-test")
async def send_test(request: Request):
    body = await request.json()
    to = body.get("to")
    message = body.get("message")

    if not to or not message:
        return {"error": "Both 'to' and 'message' are required."}

    result = send_text(to, message)
    return {"sent": True, "meta_response": result}


# ── View received messages ─────────────────────────────────────────────────────
@app.get("/messages")
def get_messages():
    return {"messages": list(message_log)[:10]}


# ── Startup info ───────────────────────────────────────────────────────────────
@app.on_event("startup")
async def startup_info():
    logger.info("=" * 55)
    logger.info("Axension AI WhatsApp Webhook is running.")
    logger.info("Local:  http://localhost:8000")
    logger.info("Expose: ngrok http 8000")
    logger.info("Then register <ngrok-url>/webhook in Meta Dashboard")
    logger.info("=" * 55)
