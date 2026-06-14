# Render Deploy Checklist

## Build settings

Build command:

```sh
pip install -r requirements.txt
```

Start command:

```sh
uvicorn app:app --host 0.0.0.0 --port $PORT
```

Health check path:

```text
/health
```

## Environment variables

Add these in Render, using the same values from your local `.env`:

```text
DATABASE_URL
OPENAI_API_KEY
APIFY_TOKEN
TELEGRAM_BOT_TOKEN
TELEGRAM_CHAT_ID
RESUME_PATH
RESUME_BASE64
RESUME_FILENAME
GMAIL_CLIENT_ID
GMAIL_CLIENT_SECRET
GMAIL_REFRESH_TOKEN
GMAIL_SENDER
CANDIDATE_NAME
CANDIDATE_EMAIL
CANDIDATE_PHONE
```

Use either `RESUME_PATH` when the PDF exists on the server, or `RESUME_BASE64`
when storing the PDF as an environment variable. For Render, `RESUME_BASE64`
is usually safer than committing a personal resume.

## Gmail API setup

1. Create a Google Cloud project.
2. Enable the Gmail API.
3. Create an OAuth client for a desktop app.
4. Download the OAuth client JSON as `gmail_client_secret.json`.
5. Run:

```sh
python scripts/get_gmail_refresh_token.py
```

6. Add the printed values to Render as environment variables.

Do not upload or commit `.env`.

## After deployment

1. Open `https://your-render-service.onrender.com/health`.
2. Confirm it returns `{"status":"ok"}`.
3. Update the Apify webhook URL to:

```text
https://your-render-service.onrender.com/webhook
```

4. Run the Apify actor once and check Render logs for `POST /webhook 200 OK`.

## Telegram approval buttons

Set your Telegram bot webhook to:

```text
https://your-render-service.onrender.com/telegram-webhook
```

For local testing with Cloudflare Tunnel, use:

```text
https://your-tunnel.trycloudflare.com/telegram-webhook
```
