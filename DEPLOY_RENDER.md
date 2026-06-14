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
```

Do not upload or commit `.env`.

## After deployment

1. Open `https://your-render-service.onrender.com/health`.
2. Confirm it returns `{"status":"ok"}`.
3. Update the Apify webhook URL to:

```text
https://your-render-service.onrender.com/webhook
```

4. Run the Apify actor once and check Render logs for `POST /webhook 200 OK`.
