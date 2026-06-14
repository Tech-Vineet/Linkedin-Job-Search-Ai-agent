import base64
import os
from email.message import EmailMessage
from pathlib import Path

from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

load_dotenv()

GMAIL_SEND_SCOPE = "https://www.googleapis.com/auth/gmail.send"


def _load_resume():
    resume_path = Path(os.getenv("RESUME_PATH", "assets/resume.pdf"))
    resume_base64 = os.getenv("RESUME_BASE64")
    resume_filename = os.getenv("RESUME_FILENAME", resume_path.name)

    if resume_base64:
        return base64.b64decode(resume_base64), resume_filename

    if resume_path.exists():
        return resume_path.read_bytes(), resume_path.name

    raise RuntimeError(f"Resume file not found: {resume_path}")


def _gmail_service():
    client_id = os.getenv("GMAIL_CLIENT_ID")
    client_secret = os.getenv("GMAIL_CLIENT_SECRET")
    refresh_token = os.getenv("GMAIL_REFRESH_TOKEN")

    missing = [
        name
        for name, value in {
            "GMAIL_CLIENT_ID": client_id,
            "GMAIL_CLIENT_SECRET": client_secret,
            "GMAIL_REFRESH_TOKEN": refresh_token,
        }.items()
        if not value
    ]

    if missing:
        raise RuntimeError(f"Missing Gmail API settings: {', '.join(missing)}")

    credentials = Credentials(
        token=None,
        refresh_token=refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=client_id,
        client_secret=client_secret,
        scopes=[GMAIL_SEND_SCOPE],
    )
    credentials.refresh(Request())

    return build("gmail", "v1", credentials=credentials)


def send_application_email(to_email, subject, body):
    mail_from = os.getenv("GMAIL_SENDER") or os.getenv("CANDIDATE_EMAIL")
    if not mail_from:
        raise RuntimeError("Missing GMAIL_SENDER or CANDIDATE_EMAIL.")

    resume_bytes, resume_filename = _load_resume()

    message = EmailMessage()
    message["From"] = mail_from
    message["To"] = to_email
    message["Subject"] = subject
    message.set_content(body)
    message.add_attachment(
        resume_bytes,
        maintype="application",
        subtype="pdf",
        filename=resume_filename,
    )

    encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
    create_message = {"raw": encoded_message}

    service = _gmail_service()
    return (
        service.users()
        .messages()
        .send(userId="me", body=create_message)
        .execute()
    )
