from typing import Any
import os

from fastapi import Body, FastAPI, HTTPException

from apify_integration import extract_posts
from database import (
    claim,
    create_application_draft,
    get_pending_application_draft,
    init_db,
    mark_application_sent,
    mark_application_skipped,
)
from email_drafter import extract_post_emails, generate_application_email
from email_sender import send_application_email
from openai_filter import analyze_post
from telegram_bot import answer_callback, send_application_draft, send_message

app = FastAPI()

SEND_SCAN_SUMMARY = os.getenv("SEND_SCAN_SUMMARY", "true").lower() == "true"


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
    drafts = 0
    duplicates = 0
    skipped = 0
    irrelevant = 0
    claimed = 0
    rejection_reasons = []

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
            print("Skipped empty post content.", flush=True)
            continue

        if not claim(linkedin_url):
            duplicates += 1
            print(f"Skipped duplicate post: {linkedin_url}", flush=True)
            continue

        claimed += 1
        result = analyze_post(content)
        print(
            "Analyzed post: "
            f"relevant={result.get('relevant')} "
            f"role={result.get('role')} "
            f"confidence={result.get('confidence')} "
            f"url={linkedin_url}",
            flush=True,
        )

        if result.get("relevant"):
            author_name = post.get("author", {}).get("name", "")
            emails = extract_post_emails(post)
            print(
                f"Relevant post email count={len(emails)} url={linkedin_url}",
                flush=True,
            )

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

            if emails:
                draft_content = generate_application_email(content, result, emails[0])
                draft = create_application_draft(
                    post_url=linkedin_url,
                    hr_email=emails[0],
                    company=result.get("company"),
                    role=result.get("role"),
                    subject=draft_content["subject"],
                    body=draft_content["body"],
                )
                send_application_draft(draft)
                drafts += 1
            else:
                print(f"No email found; sending alert only: {linkedin_url}", flush=True)
                send_message(msg)
                alerts += 1
        else:
            irrelevant += 1
            reason = result.get("rejection_reason") or "No reason returned."
            if len(rejection_reasons) < 5:
                rejection_reasons.append(reason)
            print(f"Rejected post: {reason}", flush=True)

    if SEND_SCAN_SUMMARY and not alerts and not drafts:
        reason_text = "\n".join(f"- {reason}" for reason in rejection_reasons)
        if not reason_text:
            reason_text = "- No new relevant posts found."

        send_message(
            f"""
Job scan complete

Posts received: {len(posts)}
New posts analyzed: {claimed}
Relevant alerts: {alerts}
Application drafts: {drafts}
Duplicates skipped: {duplicates}
Empty posts skipped: {skipped}
Irrelevant posts: {irrelevant}

Sample rejection reasons:
{reason_text}
"""
        )

    return {
        "posts_received": len(posts),
        "new_posts_analyzed": claimed,
        "alerts_sent": alerts,
        "drafts_sent": drafts,
        "duplicates_skipped": duplicates,
        "empty_posts_skipped": skipped,
        "irrelevant_posts": irrelevant,
    }


@app.post("/telegram-webhook")
async def telegram_webhook(payload: Any = Body(...)):
    callback_query = payload.get("callback_query")

    if not callback_query:
        return {"ok": True, "ignored": True}

    callback_query_id = callback_query.get("id")
    data = callback_query.get("data", "")

    try:
        action, draft_id = data.split(":", 1)
    except ValueError:
        if callback_query_id:
            answer_callback(callback_query_id, "Unknown action.")
        return {"ok": False, "error": "unknown_callback_data"}

    draft = get_pending_application_draft(draft_id)
    if not draft:
        if callback_query_id:
            answer_callback(callback_query_id, "Draft is no longer pending.")
        return {"ok": True, "status": "not_pending"}

    if action == "skip":
        mark_application_skipped(draft_id)
        if callback_query_id:
            answer_callback(callback_query_id, "Skipped.")
        send_message(f"Skipped application draft for {draft['role']} at {draft['company']}.")
        return {"ok": True, "status": "skipped"}

    if action == "send":
        send_application_email(
            to_email=draft["hr_email"],
            subject=draft["subject"],
            body=draft["body"],
        )
        mark_application_sent(draft_id)
        if callback_query_id:
            answer_callback(callback_query_id, "Application sent.")
        send_message(f"Application sent to {draft['hr_email']} for {draft['role']}.")
        return {"ok": True, "status": "sent"}

    if callback_query_id:
        answer_callback(callback_query_id, "Unknown action.")
    return {"ok": False, "error": "unknown_action"}
