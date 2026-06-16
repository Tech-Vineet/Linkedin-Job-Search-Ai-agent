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


def _looks_like_pdf(file_bytes):
    return file_bytes.lstrip().startswith(b"%PDF-")


def _default_resume_path():
    configured_value = os.getenv("RESUME_PATH") or "assets/resume.pdf"
    configured_path = Path(configured_value)
    if configured_path.exists():
        return configured_path

    if not os.getenv("RESUME_PATH"):
        pdf_files = sorted(Path("assets").glob("*.pdf"))
        if len(pdf_files) == 1:
            return pdf_files[0]

    return configured_path


def _decode_resume_base64(resume_base64):
    value = resume_base64.strip()
    if "," in value and value.lower().startswith("data:"):
        value = value.split(",", 1)[1]

    compact_value = "".join(value.split())
    return base64.b64decode(compact_value, validate=True)


def _load_resume_base64_file():
    configured_path = os.getenv("RESUME_BASE64_FILE")
    candidate_paths = []

    if configured_path:
        candidate_paths.append(Path(configured_path))
    else:
        candidate_paths.append(Path("/etc/secrets/resume_base64.txt"))

    for path in candidate_paths:
        if path.exists():
            return path.read_text(encoding="utf-8")

    if configured_path:
        raise RuntimeError(f"Resume base64 file not found: {configured_path}")

    return None


def _load_resume():
    resume_path = _default_resume_path()
    resume_base64 = os.getenv("RESUME_BASE64")
    resume_base64_file = _load_resume_base64_file()
    resume_filename = os.getenv("RESUME_FILENAME") or resume_path.name

    if resume_base64 or resume_base64_file:
        try:
            resume_bytes = _decode_resume_base64(resume_base64 or resume_base64_file)
        except (ValueError, base64.binascii.Error) as exc:
            raise RuntimeError("Resume base64 data is not valid base64 PDF data.") from exc

        if not _looks_like_pdf(resume_bytes):
            raise RuntimeError("Resume base64 data decoded successfully, but it is not a valid PDF.")

        return resume_bytes, resume_filename

    if resume_path.exists():
        resume_bytes = resume_path.read_bytes()
        if not _looks_like_pdf(resume_bytes):
            raise RuntimeError(f"Resume file is not a valid PDF: {resume_path}")

        return resume_bytes, resume_path.name

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
