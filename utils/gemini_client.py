import os, json, re
import google.generativeai as genai

GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")

def _configure():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("[Gemini] No API key found in environment")
        return None
    genai.configure(api_key=api_key)
    return genai.GenerativeModel(GEMINI_MODEL)

def generate_insights_with_gemini(text: str) -> dict:
    """
    Use Gemini to generate caption, hashtags, exactly 10 engagement suggestions,
    tone, and confidence. Returns a dict or {} on failure.
    """
    model = _configure()
    if not model:
        return {}

    prompt = f"""
You are a social media content strategist. Analyze the following text and return STRICT JSON only.

Text:
\"\"\"{text[:4000]}\"\"\"

Return JSON with exactly these keys:
{{
  "caption": "...",
  "hashtags": ["#...", "#..."],
  "suggestions": [
    "...",
    "...",
    "...",
    "...",
    "...",
    "...",
    "...",
    "...",
    "...",
    "..."
  ],
  "tone": "positive",
  "confidence": 0.87
}}

Rules:
- caption: catchy ≤140 chars, emoji allowed, no hashtags or links.
- hashtags: 7–10 items, lowercase, start with '#', no stopwords (#with, #using, #the).
- suggestions: exactly 10 items, each a clear actionable bullet point (no numbering).
  Cover these angles:
   • Hook (how to open strongly)
   • Tagging (companies, people)
   • Call-to-action (invite comments/shares)
   • Hashtags (best usage)
   • Question (to spark engagement)
   • Repost/follow-up strategy
   • Timing/frequency
   • Content variation (carousel, polls, stories)
   • Accessibility/alt-text
   • Encouraging community interaction
- tone: "positive", "neutral", or "negative".
- confidence: float between 0 and 1.
- Do NOT add any text outside the JSON.
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
        print("[Gemini raw output]", raw[:300], "..." if len(raw) > 300 else "")

        # Strip markdown fences if present
        if raw.startswith("```"):
            raw = re.sub(r"^```(?:json)?", "", raw)
            raw = raw.strip("` \n")

        return json.loads(raw)
    except Exception as e:
        print("[Gemini ERROR]", e)
        return {}
