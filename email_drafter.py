import json
import os
import re

from dotenv import load_dotenv
from openai import OpenAI

from openai_filter import TARGET_SKILLS

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

EMAIL_PATTERN = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)

EMAIL_DRAFT_SCHEMA = {
    "name": "application_email_draft",
    "strict": True,
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "subject": {"type": "string"},
            "body": {"type": "string"},
        },
        "required": ["subject", "body"],
    },
}


def extract_emails(text):
    seen = set()
    emails = []

    for email in EMAIL_PATTERN.findall(text or ""):
        normalized = email.strip().lower()
        if normalized not in seen:
            seen.add(normalized)
            emails.append(normalized)

    return emails


def generate_application_email(post_text, analysis, hr_email):
    candidate_name = os.getenv("CANDIDATE_NAME", "Vineet")
    candidate_email = os.getenv("CANDIDATE_EMAIL", "")
    candidate_phone = os.getenv("CANDIDATE_PHONE", "")
    skills = ", ".join(TARGET_SKILLS)

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        response_format={
            "type": "json_schema",
            "json_schema": EMAIL_DRAFT_SCHEMA,
        },
        messages=[
            {
                "role": "system",
                "content": """
Write a short, professional, personalized job application email.
Return only JSON.

Rules:
- Keep the body under 140 words.
- Mention the exact role/company if known.
- Mention 2-4 matching skills from the job/candidate profile.
- Mention 1 year of experience.
- Mention that the resume is attached.
- Do not invent degrees, companies, achievements, or years of experience.
- Do not use placeholders like [Your Name].
""",
            },
            {
                "role": "user",
                "content": f"""
Candidate:
- Name: {candidate_name}
- Email: {candidate_email}
- Phone: {candidate_phone}
- Experience: 1 year
- Skills: {skills}

Job analysis:
{json.dumps(analysis, ensure_ascii=False)}

HR email:
{hr_email}

Job post:
{post_text}
""",
            },
        ],
    )

    return json.loads(response.choices[0].message.content)
