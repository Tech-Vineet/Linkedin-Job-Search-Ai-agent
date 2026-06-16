import json
import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

TARGET_SKILLS = [
    "TypeScript",
    "JavaScript",
    "jQuery",
    "Git",
    "MySQL",
    "Express.js",
    "Bootstrap",
    "Next.js",
    "JSON",
    "GitHub",
    "MongoDB",
    "Docker",
    "Node.js",
    "React.js",
    "AWS",
    "Redux",
    "MERN Stack",
    "MERN",
    "Fullstack Development",
    "PostgreSQL",
    "Python",
    "JWT",
]

JOB_MATCH_SCHEMA = {
    "name": "job_match",
    "strict": True,
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "relevant": {"type": "boolean"},
            "company": {"type": "string"},
            "role": {"type": "string"},
            "location": {"type": "string"},
            "experience": {"type": "string"},
            "confidence": {"type": "integer", "minimum": 0, "maximum": 100},
            "matched_skills": {
                "type": "array",
                "items": {"type": "string"},
            },
            "summary": {"type": "string"},
            "rejection_reason": {"type": "string"},
        },
        "required": [
            "relevant",
            "company",
            "role",
            "location",
            "experience",
            "confidence",
            "matched_skills",
            "summary",
            "rejection_reason",
        ],
    },
}


def analyze_post(post_text):
    skills = ", ".join(TARGET_SKILLS)

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        response_format={
            "type": "json_schema",
            "json_schema": JOB_MATCH_SCHEMA,
        },
        messages=[
            {
                "role": "system",
                "content": """
You are a strict job-alert filter for a candidate with 1 year of experience.
Return only the requested JSON.

Mark relevant=true only when all of these are true:
1. The post is actively hiring for a real job, opening, referral, walk-in, or apply-now opportunity.
2. The role is suitable for Full Stack, MERN Stack, React.js, Node.js, Next.js, JavaScript, TypeScript, or closely related web developer work.
3. The required experience is suitable for 0-1 year, fresher, entry-level, junior, associate, trainee, or explicitly says freshers can apply.
4. The post does not require more than 1 year of experience. Reject roles asking for 2+ years, 3+ years, senior, lead, architect, trainer, faculty, instructor, unpaid internship, or course/training enrollment.
5. Prefer Noida/NCR/Delhi NCR/Gurugram/Ghaziabad/Faridabad/remote-in-India roles. Reject clearly unrelated locations unless remote is allowed.
6. The post mentions at least one target skill, or the role clearly implies MERN/full-stack JavaScript work.
7. Reject low-intent engagement posts that only say to comment "Interested", "comment for details", "drop your resume", or similar, unless they also include a clear apply link, email address, company, recruiter, or concrete job details.
8. Reject QA, manual testing, automation testing, software testing, SDET, support, trainer, faculty, and non-developer internships unless the main role is clearly Full Stack/MERN/React/Node developer work.

When relevant=false, set confidence below 50 and explain the main reason in rejection_reason.
When relevant=true, summarize why it matches in one short sentence.
""",
            },
            {
                "role": "user",
                "content": f"""
Candidate profile:
- Experience: 1 year
- Target experience range: 0-1 year
- Target location: Noida/NCR or remote India
- Target skills: {skills}

Analyze this post:

{post_text}
""",
            },
        ],
    )

    content = response.choices[0].message.content
    return json.loads(content)
