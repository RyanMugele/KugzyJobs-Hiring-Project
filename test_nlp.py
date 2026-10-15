
from app.nlp.job_parser import parse_job_description

description = """
I am a gaming content creator looking for a video editor
experienced in Adobe Premiere Pro and After Effects.
I need cinematic videos with motion graphics.
"""

result = parse_job_description(description)

print("Extracted NLP information:")
print("Skills:", result["skills"])
print("Styles:", result["styles"])
print("Niches:", result["niches"])
