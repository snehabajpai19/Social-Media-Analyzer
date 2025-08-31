import os
import json
import re
import google.generativeai as genai

MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")

def _configure():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return None
    genai.configure(api_key=api_key)
    return genai.GenerativeModel(MODEL_NAME)

def generate_insights_with_gemini(text: str) -> dict:
    model = _configure()
    if not model:
        return {}

    prompt = f"""
Return only JSON.
Analyze the text below and produce:
- caption (string)
- hashtags (array of 7-10 strings starting with #, lowercase)
- suggestions (exactly 10 short actionable strings)
- tone (positive|neutral|negative)
- confidence (0-1 number)

Text:
{text[:4000]}
"""

    try:
        rsp = model.generate_content(
            prompt,
            generation_config={
                "temperature": 0.6,
                "max_output_tokens": 512,
            },
        )
        raw = rsp.text.strip()
        if raw.startswith("```"):
            raw = re.sub(r"^```(?:json)?", "", raw)
            raw = raw.strip("` \n")
        return json.loads(raw)
    except Exception:
        return {}
