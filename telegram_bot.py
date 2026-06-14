import os
import requests
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def _post(method, payload):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    if method != "sendMessage":
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/{method}"

    response = requests.post(
        url,
        json=payload,
        timeout=30,
    )

    return response.json()


def send_message(text):
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
