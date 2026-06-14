import os
import json
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)

def analyze_post(post_text):

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "system",
                "content": """
Return a JSON object with:

{
  "relevant": true,
  "company": "",
  "role": "",
  "location": "",
  "confidence": 0,
  "summary": ""
}
"""
            },
            {
                "role": "user",
                "content": f"""
Determine whether this post is actively hiring
a Full Stack Developer in Noida/NCR.

Post:

{post_text}
"""
            }
        ]
    )

    content = response.choices[0].message.content

    return json.loads(content)