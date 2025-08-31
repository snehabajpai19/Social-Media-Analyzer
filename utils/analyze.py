import re
from collections import Counter
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

from utils.gemini_client import generate_insights_with_gemini


CTA = re.compile(r"\b(join|try|download|watch|read more|learn more|sign up|subscribe|buy now|check out|link in bio)\b", re.I)


def tokenize(text: str):
    return re.findall(r"[A-Za-z0-9_']+", text)


def analyze_text(text: str) -> dict:
    text = (text or "").strip()
    if not text:
        return {"summary": {}, "engagement": [], "ai_generated": {}}

    # numeric/statistical summary (local, fast)
    sid = SentimentIntensityAnalyzer()
    sentiment = sid.polarity_scores(text)

    words = tokenize(text)
    wc = len(words)
    hashtags = re.findall(r"#\w+", text)
    mentions = re.findall(r"@\w+", text)
    urls = re.findall(r"https?://\S+", text)
    top = Counter([w.lower() for w in words if len(w) > 2]).most_common(8)

    # Tone label from local sentiment (fallback)
    compound = sentiment["compound"]
    if compound > 0.05:
        local_tone = "Positive"
    elif compound < -0.05:
        local_tone = "Negative"
    else:
        local_tone = "Neutral"

    # Inline summaries (plain ASCII to avoid encoding issues)
    if wc < 50:
        word_msg = f"{wc} (very short - may lack context)"
    elif wc > 300:
        word_msg = f"{wc} (long - consider trimming for attention)"
    else:
        word_msg = f"{wc} (medium length - good for LinkedIn)"

    avg_len = round(sum(len(w) for w in words) / max(1, wc), 2)
    if avg_len < 5:
        avg_len_msg = f"{avg_len} - Easy to read"
    elif avg_len < 7:
        avg_len_msg = f"{avg_len} - Moderate complexity"
    else:
        avg_len_msg = f"{avg_len} - Complex, may reduce engagement"

    hashtag_msg = f"{len(hashtags)}"
    if len(hashtags) == 0:
        hashtag_msg += " - Missing hashtags"
    elif len(hashtags) < 3:
        hashtag_msg += " - Could add more for reach"
    else:
        hashtag_msg += " - Good use"

    mention_msg = f"{len(mentions)}"
    if len(mentions) > 0:
        mention_msg += " - Strong collaboration tagging"

    url_msg = f"{len(urls)}"
    if len(urls) > 2:
        url_msg += " - May appear promotional if all are kept"

    sentiment_msg = {
        "compound": f"{sentiment['compound']} (Overall tone: {local_tone})",
        "pos": f"{sentiment['pos']}" + (" - Slightly positive" if sentiment['pos'] > 0 else ""),
        "neu": f"{sentiment['neu']}" + (" - Mostly neutral" if sentiment['neu'] > 0.7 else ""),
        "neg": f"{sentiment['neg']}" + (" - No negativity" if sentiment['neg'] == 0 else ""),
    }

    # Gemini generation (best-effort, optional)
    g = generate_insights_with_gemini(text)

    ai_caption = (g.get("caption") if isinstance(g, dict) else None) or "Add a concise, benefit-led caption."
    ai_hashtags = (g.get("hashtags") if isinstance(g, dict) else None) or []
    ai_suggestions = (g.get("suggestions") if isinstance(g, dict) else None) or []
    gemini_tone = (g.get("tone") if isinstance(g, dict) else None)
    gemini_conf = (g.get("confidence") if isinstance(g, dict) else None)

    display_tone = (gemini_tone.capitalize() if isinstance(gemini_tone, str) and gemini_tone else local_tone)

    # Use Gemini suggestions directly as Engagement list
    engagement = ai_suggestions

    return {
        "summary": {
            "words": word_msg,
            "chars": f"{len(text)}",
            "avg_word_len": avg_len_msg,
            "hashtags": hashtag_msg,
            "mentions": mention_msg,
            "urls": url_msg,
            "tone": display_tone,
            "sentiment": sentiment_msg,
            "top_keywords": top,
            "gemini_confidence": gemini_conf if gemini_conf is not None else ""
        },
        "engagement": engagement,
        "ai_generated": {
            "caption": ai_caption,
            "recommended_hashtags": ai_hashtags
        }
    }

