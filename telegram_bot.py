import os
import requests
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def _post(method, payload):
    if not BOT_TOKEN:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is missing.")

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    if method != "sendMessage":
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/{method}"

    response = requests.post(
        url,
        json=payload,
        timeout=30,
    )
    response.raise_for_status()

    data = response.json()
    if not data.get("ok"):
        raise RuntimeError(f"Telegram API error: {data}")

    return data


def send_message(text):
    if not CHAT_ID:
        raise RuntimeError("TELEGRAM_CHAT_ID is missing.")

    return _post(
        "sendMessage",
        {
            "chat_id": CHAT_ID,
            "text": text,
        },
    )


def send_application_draft(draft):
    text = f"""
Application draft ready

To: {draft['hr_email']}
Role: {draft['role']}
Company: {draft['company']}

Subject:
{draft['subject']}

Body:
{draft['body']}
"""

    return _post(
        "sendMessage",
        {
            "chat_id": CHAT_ID,
            "text": text,
            "reply_markup": {
                "inline_keyboard": [
                    [
                        {
                            "text": "Send",
                            "callback_data": f"send:{draft['id']}",
                        },
                        {
                            "text": "Skip",
                            "callback_data": f"skip:{draft['id']}",
                        },
                    ]
                ]
            },
        },
    )


def answer_callback(callback_query_id, text):
    return _post(
        "answerCallbackQuery",
        {
            "callback_query_id": callback_query_id,
            "text": text,
        },
    )
