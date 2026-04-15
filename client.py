import os
import time
import logging
import requests
from dotenv import load_dotenv

load_dotenv()

WABA_TOKEN = os.getenv("WABA_TOKEN")
PHONE_ID = os.getenv("WABA_PHONE_ID")
VERSION = os.getenv("WABA_VERSION", "v19.0")

BASE_URL = f"https://graph.facebook.com/{VERSION}/{PHONE_ID}/messages"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


def _post_with_retry(payload: dict, max_retries: int = 3) -> dict:
    """Internal: POST to Meta API with retry on HTTP errors."""
    headers = {
        "Authorization": f"Bearer {WABA_TOKEN}",
        "Content-Type": "application/json"
    }

    for attempt in range(1, max_retries + 1):
        try:
            logger.info(f"API call attempt {attempt}: to={payload.get('to')}, type={payload.get('type')}")
            response = requests.post(BASE_URL, headers=headers, json=payload, timeout=10)
            response.raise_for_status()
            result = response.json()
            logger.info(f"API success: {result}")
            return result
        except requests.exceptions.HTTPError as e:
            logger.warning(f"HTTP error on attempt {attempt}: {e} — response: {response.text}")
            if attempt == max_retries:
                logger.error("Max retries reached. Returning error dict.")
                return {"error": str(e), "response": response.text}
            time.sleep(2 ** attempt)  # Exponential backoff
        except requests.exceptions.RequestException as e:
            logger.error(f"Request exception: {e}")
            return {"error": str(e)}


def send_text(to: str, message: str) -> dict:
    """
    Send a plain text WhatsApp message.

    Args:
        to: Recipient phone number (e.g. '918121444200' — no + or spaces)
        message: Text body to send

    Returns:
        Meta API response dict
    """
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": message}
    }
    return _post_with_retry(payload)


def send_template(to: str, template_name: str, params: list[str]) -> dict:
    """
    Send an approved WhatsApp template message.

    Args:
        to: Recipient phone number (e.g. '918121444200')
        template_name: Name of approved Meta template
        params: List of parameter values to substitute in template body

    Returns:
        Meta API response dict
    """
    components = []
    if params:
        components.append({
            "type": "body",
            "parameters": [{"type": "text", "text": p} for p in params]
        })

    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "template",
        "template": {
            "name": template_name,
            "language": {"code": "en"},
            "components": components
        }
    }
    return _post_with_retry(payload)


def parse_incoming(webhook_body: dict) -> dict | None:
    """
    Extract key fields from a Meta webhook POST body.

    Args:
        webhook_body: Raw JSON dict from Meta webhook POST

    Returns:
        Dict with keys: sender_phone, message_text, message_id, timestamp
        Returns None if the body is a status update (not a message) or malformed.
    """
    try:
        entry = webhook_body["entry"][0]
        changes = entry["changes"][0]
        value = changes["value"]

        # Handle delivery status updates — skip silently
        if "statuses" in value and "messages" not in value:
            logger.info("Received status update — skipping.")
            return None

        message = value["messages"][0]

        # Only handle text messages for now
        msg_type = message.get("type")
        if msg_type != "text":
            logger.info(f"Non-text message type received: {msg_type}")
            return {
                "sender_phone": message.get("from"),
                "message_text": f"[{msg_type.upper()} MESSAGE]",
                "message_id": message.get("id"),
                "timestamp": message.get("timestamp")
            }

        return {
            "sender_phone": message["from"],
            "message_text": message["text"]["body"],
            "message_id": message["id"],
            "timestamp": message["timestamp"]
        }

    except (KeyError, IndexError, TypeError) as e:
        logger.error(f"Failed to parse incoming webhook: {e} | body={webhook_body}")
        return None


if __name__ == "__main__":
    # Quick smoke test — send to your own number
    result = send_text("918121444200", "✅ client.py is working — Axension AI")
    print(result)
