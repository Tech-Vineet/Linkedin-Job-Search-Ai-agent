from openai_filter import analyze_post

post = """
We are hiring Full Stack Developers.

Location: Noida Sector 62

Skills:
React
Node.js
MongoDB

Apply now.
"""

result = analyze_post(post)

print(result)
print(type(result))
print(result["location"])