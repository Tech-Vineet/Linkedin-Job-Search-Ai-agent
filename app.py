from typing import Any

from fastapi import Body, FastAPI, HTTPException

from apify_integration import extract_posts
from database import claim, init_db
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
    duplicates = 0
    skipped = 0

    for post in posts:
        content = post.get("content", "")
        linkedin_url = (
            post.get("linkedinUrl")
            or post.get("shareLinkedinUrl")
            or post.get("url")
            or post.get("id", "")
        )

        if not content:
            skipped += 1
            continue

        if not claim(linkedin_url):
            duplicates += 1
            continue

        result = analyze_post(content)

        if result.get("relevant"):
            author_name = post.get("author", {}).get("name", "")

            msg = f"""
Full Stack Hiring Alert

Recruiter: {author_name}
Role: {result.get('role')}
Location: {result.get('location')}
Company: {result.get('company')}
Experience: {result.get('experience')}
Matched skills: {', '.join(result.get('matched_skills', []))}
Confidence: {result.get('confidence')}%

Summary:
{result.get('summary')}

Link: {linkedin_url}
"""

            send_message(msg)
            alerts += 1

    return {
        "posts_received": len(posts),
        "alerts_sent": alerts,
        "duplicates_skipped": duplicates,
        "empty_posts_skipped": skipped,
    }
