from groq import Groq
from app.core.config import settings

# initialize once
client = Groq(api_key=settings.groq_api_key)
MODEL  = settings.groq_model

# simple prompt templates
PROMPTS = {
    "concise":  "Summarize in 30-40% of the volume of the original text:\n\n{text}\n\nSummary:",
    "standard": "Please summarize this text:\n\n{text}\n\nSummary:",
    "detailed": "Provide a detailed summary of this text:\n\n{text}\n\nDetailed Summary:",
}

def summarize_text(text: str, mode: str) -> str:
    prompt = PROMPTS.get(mode, PROMPTS["standard"]).format(text=text)
    resp = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
    )
    return resp.choices[0].message.content.strip()
