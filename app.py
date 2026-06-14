from typing import Any

from fastapi import Body, FastAPI, HTTPException

from apify_integration import extract_posts
from database import exists, init_db, save
from openai_filter import analyze_post
from telegram_bot import send_message

app = FastAPI()


@app.on_event("startup")
async def startup():
    init_db()


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/webhook")
async def webhook_info():
    return {"status": "ok", "message": "Webhook is ready. Apify must call this URL with POST."}


@app.post("/webhook")
async def webhook(payload: Any = Body(...)):
    try:
        posts = extract_posts(payload)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    alerts = 0

    for post in posts:
        content = post.get("content", "")
        linkedin_url = (
            post.get("linkedinUrl")
            or post.get("shareLinkedinUrl")
            or post.get("url")
            or post.get("id", "")
        )

        if not content:
            continue

        if exists(linkedin_url):
            continue

        result = analyze_post(content)

        if result.get("relevant"):
            author_name = post.get("author", {}).get("name", "")

            msg = f"""
🚨 Full Stack Hiring Alert

👤 Recruiter: {author_name}
💼 Role: {result.get('role')}
📍 Location: {result.get('location')}
🏢 Company: {result.get('company')}

📝 Summary:
{result.get('summary')}

🔗 {linkedin_url}
"""

            send_message(msg)
            save(linkedin_url)
            alerts += 1

    return {"posts_received": len(posts), "alerts_sent": alerts}
