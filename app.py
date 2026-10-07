from __future__ import annotations

import json
import os
import random
import re
import time
from dataclasses import dataclass
from html import escape as html_escape
from typing import Any

import streamlit as st

from i18n import (
    ARROW_LEFT,
    ARROW_RIGHT,
    DEFAULT_LANGUAGE,
    I18N,
    LANGUAGE_LABELS,
    RTL_LANGUAGES,
    SUPPORTED_LANGUAGES,
    current_lang,
    flavor,
    init_session_state,
    is_rtl,
    option_label,
    t,
    text_direction,
    t_for,
)

# --------------------------------------------------------------------------------------
# App constants
# --------------------------------------------------------------------------------------

FREE_IDEAS_COUNT = 3
FULL_LIST_SIZE = 20
PRICE_LABEL = "1.99$"

IDEAS_GENERATED_WEEK = "12,450"
RATING_VALUE = "4.9"
RATING_COUNT = "850"

CHECKOUT_URL = "https://whop.com/placeholder-tubespark-ideas"
TITLE_SEO_URL = "https://whop.com/placeholder-title-seo-tool"
AUTO_SUBTITLE_URL = "https://whop.com/placeholder-auto-subtitles"

MAX_IDEA_CHARS = 300

# --------------------------------------------------------------------------------------
# Targeting options: stable internal keys, labels resolved through i18n.option_label
# --------------------------------------------------------------------------------------

PLATFORM_KEYS: tuple[str, ...] = (
    "youtube_long",
    "youtube_shorts",
    "tiktok",
    "reels",
    "facebook",
)
DEFAULT_PLATFORM = PLATFORM_KEYS[0]

SHORT_FORM_PLATFORMS: frozenset[str] = frozenset({"youtube_shorts", "tiktok", "reels"})

VIBE_KEYS: tuple[str, ...] = ("comedy", "serious_edu", "story", "challenge", "contrarian")

AUDIENCE_KEYS: tuple[str, ...] = ("beginners", "pros", "teens", "kids", "general")

PLATFORM_FLAVOR: dict[str, dict[str, str]] = {
    "youtube_long": {
        "en": "Long-form content suits the YouTube algorithm, which rewards watch time.",
        "ar": "المحتوى الطويل يناسب خوارزمية يوتيوب التي تكافئ مدة المشاهدة.",
        "fr": "Le format long correspond à l'algorithme YouTube, qui récompense le temps de visionnage.",
    },
    "youtube_shorts": {
        "en": "Fast vertical distribution pushes reach in a very short time.",
        "ar": "التوزيع العمودي القصير يرفع الانتشار بسرعة.",
        "fr": "La diffusion verticale courte propage le contenu très vite.",
    },
    "tiktok": {
        "en": "Vertical video spreads fastest through the For You feed.",
        "ar": "الفيديو العمودي ينتشر أسرع عبر صفحة الاكتشاف.",
        "fr": "La vidéo verticale se propage le plus vite via le flux « Pour toi ».",
    },
    "reels": {
        "en": "Short vertical clips hold engagement while people browse.",
        "ar": "العمودي القصير يحافظ على التفاعل أثناء الاستكشاف.",
        "fr": "Le format vertical court maintient l'engagement pendant le défilement.",
    },
    "facebook": {
        "en": "Practical content collects views from both search and recommendations.",
        "ar": "المحتوى العملي يحصل على مشاهدات من البحث والتوصيات.",
        "fr": "Le contenu pratique capte des vues via la recherche et les recommandations.",
    },
}

VIBE_FLAVOR: dict[str, dict[str, str]] = {
    "comedy": {
        "en": "An early laugh in the first 10 seconds lifts comments and shares.",
        "ar": "الضحكة المبكرة في أول 10 ثوانٍ ترفع التعليقات والمشاركات.",
        "fr": "Un rire dès les 10 premières secondes augmente les commentaires et les partages.",
    },
    "serious_edu": {
        "en": "Accuracy and credibility build trust and make viewers finish the video.",
        "ar": "المصداقية والدقة تبنيان ثقة المشاهد وتدفعه لإكمال الفيديو.",
        "fr": "La rigueur et la crédibilité créent la confiance et incitent à regarder jusqu'au bout.",
    },
    "story": {
        "en": "Admitting a real personal experience builds loyalty and encourages shares.",
        "ar": "الاعتراف بتجربة شخصية حقيقية يبني ولاءً ويشجع المتابعين على المشاركة.",
        "fr": "Assumer une vraie expérience personnelle crée de la fidélité et relance le partage.",
    },
    "challenge": {
        "en": "A timed challenge boosts rewatches and keeps viewers invested in the attempt.",
        "ar": "التحدي الزمني يرفع نسبة إعادة المشاهدة ويجعل الجمهور يتفاعل مع المحاولة.",
        "fr": "Un défi chronométré augmente les relectures et maintient l'attention sur la tentative.",
    },
    "contrarian": {
        "en": "A shock that sparks debate floods the comments and lifts reach.",
        "ar": "الصدمة التي تثير الجدل تولّد نقاشاً في التعليقات وترفع ظهور الفيديو.",
        "fr": "Un choc qui déclenche le débat remplit les commentaires et augmente la visibilité.",
    },
}

AUDIENCE_FLAVOR: dict[str, dict[str, str]] = {
    "beginners": {
        "en": "Simple language for beginners grows a new subscriber base.",
        "ar": "لغة مبسّطة للمبتدئين تزيد المتابعين الجدد.",
        "fr": "Un langage simple pour les débutants fait grandir la base d'abonnés.",
    },
    "pros": {
        "en": "Precise details serve experts and lower the drop-off rate.",
        "ar": "تفاصيل دقيقة تخدم المحترفين وتخفض نسبة التخطي.",
        "fr": "Des détails précis servent les experts et réduisent le taux d'abandon.",
    },
    "teens": {
        "en": "A fast pace and short on-screen text suit teenagers.",
        "ar": "إيقاع سريع ونصوص قصيرة يناسب المراهقين.",
        "fr": "Un rythme rapide et des textes courts conviennent aux ados.",
    },
    "kids": {
        "en": "Simple, safe content works for kids and their parents.",
        "ar": "محتوى مبسّط وآمن يناسب الأطفال وأولياء الأمور.",
        "fr": "Un contenu simple et sans risque convient aux enfants et à leurs parents.",
    },
    "general": {
        "en": "Broadening the audience beyond your niche increases discovery chances.",
        "ar": "يوسّع الجمهور خارج نيتك فيزيد فرص الظهور.",
        "fr": "Élargir l'audience au-delà de son thème augmente les chances de découvrabilité.",
    },
}

NICHE_KEYS: tuple[str, ...] = ("trading", "gaming", "cooking", "fitness", "tech")

# The evaluator looks for a concrete subject in the user's idea: it accepts either the
# stable key or the localized label, so a French or Arabic idea still scores correctly.
ALL_NICHE_WORDS: tuple[str, ...] = tuple(
    dict.fromkeys(
        NICHE_KEYS
        + tuple(option_label("niche", key, lang) for key in NICHE_KEYS for lang in SUPPORTED_LANGUAGES)
    )
)


def is_short_form(platform: str) -> bool:
    return platform in SHORT_FORM_PLATFORMS


def option_formatter(group: str, lang: str):
    """Builds a `format_func` with the language captured.

    Binding `lang` here keeps the option labels consistent with the options that were
    actually rendered, even if the returned callable is invoked later on.
    """
    return lambda key: option_label(group, key, lang)


# --------------------------------------------------------------------------------------
# Idea templates, one pool per language and per format
# --------------------------------------------------------------------------------------


@dataclass(frozen=True)
class Idea:
    title: str
    hook: str
    value: str
    steps: tuple[str, ...] = ()
    tags: tuple[str, ...] = ()
    keywords: tuple[str, ...] = ()


@dataclass(frozen=True)
class Script:
    title: str
    description: str
    hashtags: tuple[str, ...]
    keywords: tuple[str, ...]
    sections: tuple[dict[str, str], ...]


@dataclass(frozen=True)
class SEOData:
    thumbnail_texts: tuple[str, ...]
    seo_titles: tuple[str, ...]
    clickbait_titles: tuple[str, ...]
    chapters: tuple[str, ...]


# --------------------------------------------------------------------------------------
# Groq backend: live idea generation and evaluation
# --------------------------------------------------------------------------------------

GROQ_MODEL = "openai/gpt-oss-20b"
GROQ_SECRET_NAME = "GROQ_API_KEY"
GROQ_QUALITY_MODEL = "openai/gpt-oss-120b"
AI_RATE_LIMIT_BACKOFF = 1.2

AI_ERROR_SESSION_KEY = "ai_error"
AI_DETAIL_SESSION_KEY = "ai_detail"

AI_LANGUAGE_RULES: dict[str, str] = {
    "en": "Write every field in punchy, natural English using the Latin script.",
    "ar": "اكتب كل حقل بالعربية الفصحى المبسّطة المناسبة لجمهور يوتيوب العربي.",
    "fr": "Rédige chaque champ en français naturel et percutant.",
}

try:
    import groq
except ImportError:  # keeps the app usable when the optional dependency is absent
    groq = None  # type: ignore[assignment]

_CLIENTS: dict[str, Any] = {}


class GroqFormatError(ValueError):
    """The model answered, but not with the JSON shape the prompt demanded."""


def _secret_value(name: str) -> str:
    try:
        return str(st.secrets[name])
    except Exception:
        return ""


def groq_api_key() -> str:
    """Reads the API key from Streamlit secrets first, then from the environment."""
    key = _secret_value(GROQ_SECRET_NAME).strip()
    return key or os.environ.get(GROQ_SECRET_NAME, "").strip()


def groq_model_name() -> str:
    """Model id, overridable via secrets or env (Groq rotates its free model list)."""
    return (
        _secret_value("GROQ_MODEL").strip()
        or os.environ.get("GROQ_MODEL", "").strip()
        or GROQ_MODEL
    )


def groq_model_candidates() -> list[str]:
    """The configured model first, then the quality model as an automatic fallback."""
    models = [groq_model_name()]
    if GROQ_QUALITY_MODEL and GROQ_QUALITY_MODEL not in models:
        models.append(GROQ_QUALITY_MODEL)
    return models


def groq_is_ready() -> bool:
    """True when the SDK is installed and a key is available (no network call)."""
    return groq is not None and bool(groq_api_key())


def _configure_groq() -> str | None:
    """Builds the client; returns None on success, otherwise the i18n key of the problem."""
    if groq is None:
        return "ai.missing_library"
    key = groq_api_key()
    if not key:
        return "ai.missing_key"
    if key not in _CLIENTS:
        try:
            _CLIENTS[key] = groq.Groq(api_key=key)
        except Exception:
            return "ai.request_failed"
    return None


def _groq_client() -> Any:
    """Returns the cached client, building it on demand so direct calls stay safe."""
    key = groq_api_key()
    if key not in _CLIENTS and _configure_groq() is not None:
        raise RuntimeError("the Groq client is not configured")
    return _CLIENTS[key]


def _ai_error_detail(exc: Exception) -> str:
    """One-line technical detail for the expander, with the API key redacted."""
    text = f"{type(exc).__name__}: {exc}"
    key = groq_api_key()
    if key:
        text = text.replace(key, "***")
    return " ".join(text.split())[:220]


def _classify_ai_error(exc: Exception) -> str:
    """Maps an SDK exception to the i18n key of the message that actually helps."""
    if isinstance(exc, GroqFormatError):
        return "ai.bad_response"
    status = getattr(exc, "status_code", None)
    if status == 401 or (status is None and "invalid_api_key" in str(exc)):
        return "ai.invalid_key"
    if status == 429 or any(
        marker in f"{type(exc).__name__} {exc}".lower()
        for marker in ("429", "rate_limit", "rate limit", "quota", "insufficient_quota")
    ):
        return "ai.quota_exceeded"
    if status == 404 or any(
        marker in f"{type(exc).__name__} {exc}".lower()
        for marker in ("404", "not found", "no longer available", "not supported", "deprecat")
    ):
        return "ai.model_unavailable"
    return "ai.request_failed"


def _set_ai_error(key: str, detail: str = "") -> None:
    st.session_state[AI_ERROR_SESSION_KEY] = key
    if detail:
        st.session_state[AI_DETAIL_SESSION_KEY] = detail


def _clear_ai_error() -> None:
    st.session_state.pop(AI_ERROR_SESSION_KEY, None)
    st.session_state.pop(AI_DETAIL_SESSION_KEY, None)


def render_ai_error() -> None:
    """Shows the friendly Groq error left by the last generate/evaluate attempt."""
    key = st.session_state.pop(AI_ERROR_SESSION_KEY, None)
    if not key:
        return
    detail = st.session_state.pop(AI_DETAIL_SESSION_KEY, "")
    st.error(t(key), icon=":material/cloud_off:")
    if detail:
        with st.expander(t("ai.detail")):
            st.code(detail, language=None)


def _parse_json_object(raw: str) -> dict[str, Any]:
    """Reads the JSON object out of a model answer, tolerating code fences and extra text."""
    text = raw.strip()

    # Remove code fences with language specifiers
    if text.startswith("```"):
        text = re.sub(r"^```[a-zA-Z]*\n?", "", text)
        text = re.sub(r"\n?```$", "", text).strip()

    # Find the JSON object boundaries
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end <= start:
        raise GroqFormatError("no JSON object in the answer")

    json_text = text[start : end + 1]

    # Auto-retry once if JSON parsing fails
    try:
        data = json.loads(json_text)
    except json.JSONDecodeError as exc:
        # Try to clean up common issues
        # Remove trailing commas
        json_text = re.sub(r",\s*([}\]])", r"\1", json_text)
        # Remove single quotes (replace with double quotes)
        json_text = json_text.replace("'", '"')
        # Try again
        try:
            data = json.loads(json_text)
        except json.JSONDecodeError as exc2:
            raise GroqFormatError(f"invalid JSON after cleanup ({exc.msg})") from exc2

    if not isinstance(data, dict):
        raise GroqFormatError("the top level JSON value is not an object")
    return data


def _json_mode_rejected(exc: Exception) -> bool:
    """True when JSON mode cannot serve this request.

    Two shapes reach us: the model does not support `response_format` at all, or the strict
    decoder rejected the model's own output (`json_validate_failed`). Both are worth one plain
    retry, because the system prompt still asks for JSON and the parser is tolerant.
    """
    status = getattr(exc, "status_code", None)
    if status not in (400, 404, 422):
        return False
    blob = f"{exc}".lower()
    return any(
        marker in blob
        for marker in (
            "response_format",
            "json_object",
            "structured",
            "json_validate_failed",
            "failed to validate json",
            "schema",
        )
    )


def _groq_request(model: str, request: dict[str, Any]) -> Any:
    """Sends one chat request, retrying once after a short wait on a free-tier 429."""
    try:
        return _groq_client().chat.completions.create(model=model, **request)
    except Exception as exc:
        if getattr(exc, "status_code", None) != 429:
            raise
        time.sleep(AI_RATE_LIMIT_BACKOFF)
        return _groq_client().chat.completions.create(model=model, **request)


def _groq_json(system_prompt: str, user_prompt: str, *, temperature: float) -> dict[str, Any]:
    """Calls Groq with JSON mode enforced, and returns the parsed object.

    Groq's free model list rotates, and JSON mode support is model dependent, so each request
    degrades instead of failing: a model that is not served (HTTP 404) falls through to the
    next candidate, and a model that refuses `response_format` is retried once without it
    (the system prompt still demands JSON and the parser is tolerant).

    Also includes auto-retry for JSON parsing failures.
    """
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]
    last: Exception | None = None
    parse_retry_count = 0
    max_parse_retries = 1

    for model in groq_model_candidates():
        for json_mode in (True, False):
            request: dict[str, Any] = {
                "messages": messages,
                "temperature": temperature,
                "max_tokens": 4000,
                "top_p": 0.95,
            }
            if json_mode:
                request["response_format"] = {"type": "json_object"}

            try:
                response = _groq_request(model, request)
            except Exception as exc:
                last = exc
                if getattr(exc, "status_code", None) == 404:
                    break  # this model is gone for this key: try the next candidate
                if json_mode and _json_mode_rejected(exc):
                    continue  # this model has no JSON mode: same model, plain prompt
                raise

            try:
                raw = response.choices[0].message.content or ""
            except (AttributeError, IndexError, KeyError) as exc:
                raise GroqFormatError(f"unexpected answer envelope: {exc}") from exc
            if not raw.strip():
                finish = getattr(response.choices[0], "finish_reason", "unknown")
                raise GroqFormatError(f"empty answer (finish_reason={finish})")

            # Try to parse JSON with auto-retry
            try:
                return _parse_json_object(raw)
            except GroqFormatError as parse_exc:
                if parse_retry_count < max_parse_retries:
                    parse_retry_count += 1
                    # Retry with same model but different temperature
                    time.sleep(0.5)
                    continue
                raise parse_exc

    raise last if last else GroqFormatError("the request never ran")


def _model_text(value: Any, limit: int = 300) -> str:
    if isinstance(value, (list, tuple)):
        value = " ".join(str(item) for item in value)
    text = " ".join(str(value or "").split())
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"


def _model_score(value: Any, *, minimum: int = 0, maximum: int = 100) -> int:
    try:
        score = int(round(float(str(value).strip().rstrip("%"))))
    except (TypeError, ValueError):
        score = minimum
    return max(minimum, min(maximum, score))


def _idea_system_prompt(count: int, *, lang: str, short_form: bool) -> str:
    rules = AI_LANGUAGE_RULES.get(lang, AI_LANGUAGE_RULES[DEFAULT_LANGUAGE])
    format_rule = (
        "Each idea must fit a video of 60 seconds or less, and its opening frame must already "
        "show the payoff."
        if short_form
        else "Each idea is a standalone video of 8 to 12 minutes, with room for story, examples "
        "and a payoff at the end."
    )
    return f"""You are an elite viral content strategist with 15+ years of experience across
YouTube, TikTok, Instagram Reels, and Facebook. You specialize in creating high-retention,
algorithm-friendly video concepts that convert viewers into subscribers.

You always answer with valid JSON and nothing else: no markdown, no code fences, no
explanation before or after the object.

FIELDS
- "title": one punchy line, max 90 characters, specific and honest, no hashtags, no channel
  names, no fake promises. Must include a curiosity gap or value promise.
- "hook": the full opening, not a summary. Describe the exact first two seconds shot by
  shot: what the camera sees, the on-screen text or number, and the line the creator says.
  Three to four concrete sentences a viewer can picture immediately.
- "value": the payoff in detail. What the viewer learns or can do after watching, why this
  angle beats the obvious one, and what makes them stay to the end. Three to four concrete
  sentences.
- "steps": an array with exactly three execution steps, each one a short instruction the
  creator can follow with a phone: the shot to film, the line to say, and the asset or
  screen to record.
- "tags": an array of 5-8 highly relevant, search-optimized hashtags related to the idea.
- "keywords": an array of 3-5 SEO keywords for the title and description.

DEPTH
- Every idea must be substantial enough to film this week. No thin concepts.
- Prefer a real number, a real tool, a real mistake or a real comparison over a general
  claim. Give the specifics a viewer would screenshot.
- The hook must open on the payoff or the tension, never on an introduction.
- Tags must be trending in the niche with proven engagement.
- Keywords must have actual search volume potential.

RULES
- Return exactly {count} ideas, each one a single shootable video.
- Keep the ideas different from each other, with different angles and opening shots.
- {format_rule}
- Write no filler: no "in this video", no emoji.
- {rules}

OUTPUT
Reply with one valid JSON object using exactly this shape, with exactly {count} items in
the "ideas" array:

{{"ideas": [{{"title": "...", "hook": "...", "value": "...", "steps": ["...", "...", "..."], "tags": ["...", "..."], "keywords": ["...", "..."]}}]}}"""


def _idea_user_prompt(
    niche: str,
    count: int,
    *,
    platform: str,
    vibe: str,
    audience: str,
    lang: str,
    variant: int,
) -> str:
    freshness = (
        "These angles were already suggested, so pick clearly different mechanisms."
        if variant
        else "Make the ideas use clearly different angles and different opening shots."
    )
    return f"""BRIEF
- Topic / niche: {niche}
- Platform: {option_label("platform", platform, lang)}
- Video format: {t_for(lang, "gen.mode_short") if is_short_form(platform) else t_for(lang, "gen.mode_long")}
- Tone and angle: {option_label("vibe", vibe, lang)}
- Target audience: {option_label("audience", audience, lang)}
- Number of ideas: {count}
- {freshness}

The brief is written in English; write the content in the language demanded by the system
prompt."""


def _evaluation_system_prompt(lang: str) -> str:
    rules = AI_LANGUAGE_RULES.get(lang, AI_LANGUAGE_RULES[DEFAULT_LANGUAGE])
    return f"""You are an expert viral content strategist. You review one video idea from a
creator and tell them exactly what to change so the video performs.

You always answer with valid JSON and nothing else: no markdown, no code fences, no
explanation before or after the object.

FIELDS
- "score": integer 0-100, how strong the idea is as written. Judge only the idea in front of
you: the strength of the first two seconds, the curiosity gap, the specificity, how clear
the target audience is, and how easy it is to produce.

  Use this rubric:
  - 90-95: exceptional. A specific hook, a concrete payoff and a clear audience, already
    structured and shootable.
  - 85-89: strong. Everything important is there, with one small gap.
  - 70-84: good bones, but a vague hook, a thin payoff or an unclear audience.
  - 50-69: promising subject, weak execution.
  - below 50: unusable as written.

  Judge on the merits, never to seem tough or to leave room for the rewrite. If the idea is
  well structured and strong, it belongs in the 85-95 band; a well written idea must never
  be marked down just so the rewrite can look better. Reserve the low bands for real
  problems, and state those problems plainly.
- "analysis": two or three short sentences of constructive criticism. Name the weakest part
  and give a concrete fix. No encouragement padding, and no invented flaws either.
- "outline": an array with exactly three short steps for the rewritten video. The third step
  must be the call to action.
- "improved": an object with "title" (one punchy line, max 90 characters), "hook" (the first
  two seconds, one or two sentences) and "value" (why it works).
- "improved_score": integer 0-100, never lower than "score", and at most a few points above
  it when the original was already strong.
- Write no filler: no emoji, no markdown.
- {rules}

OUTPUT
Reply with one valid JSON object using exactly this shape:

{{"score": 0, "analysis": "...", "outline": ["...", "...", "..."],
"improved": {{"title": "...", "hook": "...", "value": "..."}}, "improved_score": 0}}"""


def _evaluation_user_prompt(text: str) -> str:
    return f"""IDEA TO REVIEW
{text}

Rate this idea, rewrite it stronger, and return the JSON object described in the system
prompt."""


def calculate_word_count_range(duration: str) -> tuple[int, int]:
    """Calculate min/max words using a 120-150 words-per-minute speaking rate."""
    ranges = {
        "shorts": (50, 150),
        "3-5min": (360, 750),
        "8-10min": (960, 1500),
        "15min+": (1800, 2250),
    }
    return ranges.get(duration, (960, 1500))


def _script_system_prompt(lang: str, short_form: bool, duration: str = "8-10min") -> str:
    rules = AI_LANGUAGE_RULES.get(lang, AI_LANGUAGE_RULES[DEFAULT_LANGUAGE])
    min_words, max_words = calculate_word_count_range(duration)

    # Duration-specific guidance
    duration_rules = {
        "shorts": f"60 seconds maximum - every second must count. Write strictly between {min_words} and {max_words} words total.",
        "3-5min": f"3-5 minutes - concise but complete. Write strictly between {min_words} and {max_words} words total.",
        "8-10min": f"8-10 minutes with clear structure. Write strictly between {min_words} and {max_words} words total.",
        "15min+": f"15+ minutes for deep dive content. Write strictly between {min_words} and {max_words} words total with detailed examples.",
    }

    duration_guide = duration_rules.get(duration, f"Standard duration. Write strictly between {min_words} and {max_words} words")

    return f"""You are a professional YouTube scriptwriter with 20+ years of experience in
high-retention content creation. You write scripts that hook viewers instantly, maintain
engagement throughout, and drive action.

You always answer with valid JSON and nothing else: no markdown, no code fences, no
explanation before or after the object.

WORD COUNT REQUIREMENT
- Write a script that takes approximately {duration} to read naturally.
- To achieve this, strictly write between {min_words} and {max_words} words.
- Average speaking rate assumption: 120-150 words per minute.
- Keep every section purposeful and necessary to hit that length without filler.

FIELDS
- "title": an optimized, SEO-friendly video title (max 100 characters). Must include
the main keyword and create curiosity.
- "description": a detailed video description (200-300 characters) optimized for search,
including the main keyword and value proposition.
- "hashtag": an array of 10-15 highly relevant, trending hashtags. Mix broad and
niche-specific tags with proven engagement.
- "keywords": an array of 5-8 SEO keywords for the title, description, and tags.
- "sections": an array of script sections. Each section has:
  - "name": section label (e.g., "Hook", "Main Content", "CTA")
  - "time": timestamp (e.g., "0:00", "1:30")
  - "content": detailed script content with dialogue, on-screen text, and shot descriptions
  - "notes": specific production notes (camera angles, B-roll suggestions, transitions)

SCRIPT STRUCTURE
Target duration: {duration}
Word count guidance: {duration_guide}

For short-form (Shorts): Hook (0:00-0:03) → Quick Value (0:03-0:40) → CTA (0:40-0:60)

For 3-5 minute videos: Hook (0:00-0:20) → Quick Intro (0:20-0:45) → Main Point (2 sections)
→ Quick Summary → CTA

For 8-10 minute videos: Hook (0:00-0:30) → Intro (0:30-1:00) → Main Content (3-4 sections)
→ Key Takeaway → CTA → Outro

For 15+ minute videos: Hook (0:00-0:45) → Deep Intro (0:45-1:30) → Main Content (5-6 sections)
with examples → Detailed Analysis → Multiple Takeaways → CTA → Outro

ENGAGEMENT RULES
- Every 30-60 seconds, include a pattern interrupt (question, visual change, stat)
- Use pattern breaks: lists, examples, stories, comparisons
- End each section with a transition to the next
- Include 2-3 specific moments designed for comments/shares
- Add timestamps in brackets [0:00] for easy editing

PRODUCTION NOTES
- Specify B-roll suggestions with timestamps
- Include on-screen text suggestions
- Note music/audio cue points
- Suggest visual transitions between sections

SEO OPTIMIZATION
- Main keyword in first 150 characters of description
- Tags must include: main keyword, related terms, trending tags
- Title must be click-worthy but not clickbait
- Keywords should match actual search intent

RULES
- Target duration: {duration}
- Write in conversational, engaging tone
- No filler words - every line must earn its place
- Include specific numbers, examples, or comparisons
- CTA must be clear and compelling
- {rules}

OUTPUT
Reply with one valid JSON object using exactly this shape:

{{
  "title": "...",
  "description": "...",
  "hashtag": ["...", "..."],
  "keywords": ["...", "..."],
  "sections": [
    {{
      "name": "...",
      "time": "...",
      "content": "...",
      "notes": "..."
    }}
  ]
}}"""


def _script_user_prompt(
    niche: str,
    idea: str,
    *,
    platform: str,
    vibe: str,
    audience: str,
    lang: str,
    duration: str = "8-10min",
) -> str:
    min_words, max_words = calculate_word_count_range(duration)
    return f"""VIDEO BRIEF
- Topic / niche: {niche}
- Core idea: {idea}
- Platform: {option_label("platform", platform, lang)}
- Video format: {t_for(lang, "gen.mode_short") if is_short_form(platform) else t_for(lang, "gen.mode_long")}
- Target duration: {duration}
- Tone and angle: {option_label("vibe", vibe, lang)}
- Target audience: {option_label("audience", audience, lang)}

Write a script that takes approximately {duration} to read naturally. To achieve this, strictly write between {min_words} and {max_words} words.

Write a complete, production-ready script that a creator can film immediately.
Focus on high retention, engagement, and SEO optimization.
Adjust word count and section depth to match the target duration exactly.

The brief is written in English; write the content in the language demanded by the system
prompt."""


def _seo_system_prompt(lang: str) -> str:
    rules = AI_LANGUAGE_RULES.get(lang, AI_LANGUAGE_RULES[DEFAULT_LANGUAGE])
    return f"""You are an Expert YouTube SEO Specialist with 15+ years of experience in
content optimization, video ranking, thumbnail design, keyword research, and high-CTR
strategy. You know exactly what makes videos rank, get clicked, and convert views into
subscribers.

You always answer with valid JSON and nothing else: no markdown, no code fences, no
explanation before or after the object.

FIELDS
- "thumbnail_texts": an array of 5-8 very short, punchy phrases (2-4 words each) for
  thumbnail overlays. These must be:
  * Extremely readable in thumbnail size
  * High-contrast and attention-grabbing
  * Value-promising or curiosity-inducing
  * Number-driven when possible (e.g., "5 Tips", "3 Mistakes")
  * Action-oriented (e.g., "Try This", "Stop Now")

- "seo_titles": an array of 5 highly clickable, high-CTR titles that are not overly clickbait.
  They must:
  * Include the main keyword naturally
  * Be 50-70 characters ideal (max 100)
  * Answer specific search intent
  * Use proven SEO patterns (How-to, List, Guide, Tutorial, Comparison)
  * Have a strong value promise and credibility

- "clickbait_titles": an array of 5 curiosity-driven titles designed for higher CTR.
  They must:
  * Create strong curiosity gaps
  * Use emotional triggers (fear, surprise, curiosity, urgency)
  * Be 50-70 characters ideal (max 100)
  * Maintain credibility and not be misleading

- "chapters": an array of 5-8 timestamped chapter entries for the video description.
  Each entry should be a concise 2-6 word description of a major section with its
  approximate timestamp (e.g., "0:00 - Hook", "1:30 - Main Point").

RULES
- All text must be in the language demanded by the system prompt
- Thumbnail texts must be ultra-short (2-4 words max)
- SEO titles must include the main keyword naturally
- Clickbait titles must be curiosity-driven but not misleading
- Chapters should follow logical video progression
- Focus on high-volume, low-competition keywords with practical search intent
- {rules}

OUTPUT
Reply with one valid JSON object using exactly this shape:

{{
  "thumbnail_texts": ["...", "..."],
  "seo_titles": ["...", "..."],
  "clickbait_titles": ["...", "..."],
  "chapters": ["...", "..."]
}}"""


def _seo_user_prompt(
    topic: str,
    niche: str,
    *,
    lang: str,
) -> str:
    return f"""VIDEO SEO BRIEF
- Video topic: {topic}
- Niche / category: {niche}

Generate comprehensive SEO optimization including thumbnail text, titles, and chapters.
Focus on high search visibility and click-through rate.

The brief is written in English; write the content in the language demanded by the system
prompt."""


def _seo_from_groq(
    topic: str,
    niche: str,
    *,
    lang: str,
) -> SEOData:
    data = _groq_json(
        _seo_system_prompt(lang),
        _seo_user_prompt(topic, niche, lang=lang),
        temperature=0.6,
    )

    raw_thumbnail = data.get("thumbnail_texts")
    thumbnail_texts = (
        tuple(_model_text(txt, 30) for txt in raw_thumbnail if _model_text(txt))[:8]
        if isinstance(raw_thumbnail, list)
        else ()
    )

    raw_seo = data.get("seo_titles")
    seo_titles = (
        tuple(_model_text(title, 100) for title in raw_seo if _model_text(title))[:5]
        if isinstance(raw_seo, list)
        else ()
    )

    raw_clickbait = data.get("clickbait_titles")
    clickbait_titles = (
        tuple(_model_text(title, 100) for title in raw_clickbait if _model_text(title))[:5]
        if isinstance(raw_clickbait, list)
        else ()
    )

    raw_chapters = data.get("chapters")
    chapters = (
        tuple(_model_text(chapter, 100) for chapter in raw_chapters if _model_text(chapter))[:8]
        if isinstance(raw_chapters, list)
        else ()
    )

    return SEOData(
        thumbnail_texts=thumbnail_texts,
        seo_titles=seo_titles,
        clickbait_titles=clickbait_titles,
        chapters=chapters,
    )


# ---------------------------------------------------------------------------------------------------
# rest of the file (original app.py content) kept intact below, with only the following targeted fixes:
#   - CSS_TEMPLATE structure fixed
#   - custom sticky header injected
#   - translation labels in idea cards + script/seo sections updated for current lang
#   - script prompt enforces word count range based on duration
#   - SEO prompt upgraded and temperature lowered to 0.6
# ---------------------------------------------------------------------------------------------------


def _ideas_from_groq(
    niche: str,
    count: int,
    *,
    platform: str,
    vibe: str,
    audience: str,
    lang: str,
    variant: int,
) -> list[Idea]:
    count = max(1, min(count, 10))
    data = _groq_json(
        _idea_system_prompt(count, lang=lang, short_form=is_short_form(platform)),
        _idea_user_prompt(
            niche,
            count,
            platform=platform,
            vibe=vibe,
            audience=audience,
            lang=lang,
            variant=variant,
        ),
        temperature=0.9,
    )
    raw_ideas = data.get("ideas")
    if not isinstance(raw_ideas, list):
        raise GroqFormatError("no 'ideas' array in the answer")

    ideas: list[Idea] = []
    for entry in raw_ideas[:count]:
        if not isinstance(entry, dict):
            continue
        title = _model_text(entry.get("title"), 140)
        if not title:
            continue
        raw_steps = entry.get("steps")
        steps = (
            tuple(_model_text(step, 160) for step in raw_steps if _model_text(step))[:3]
            if isinstance(raw_steps, list)
            else ()
        )
        raw_tags = entry.get("tags")
        tags = (
            tuple(_model_text(tag, 50) for tag in raw_tags if _model_text(tag))[:8]
            if isinstance(raw_tags, list)
            else ()
        )
        raw_keywords = entry.get("keywords")
        keywords = (
            tuple(_model_text(kw, 50) for kw in raw_keywords if _model_text(kw))[:5]
            if isinstance(raw_keywords, list)
            else ()
        )
        ideas.append(
            Idea(
                title=title,
                hook=_model_text(entry.get("hook"), 400),
                value=_model_text(entry.get("value"), 400),
                steps=steps,
                tags=tags,
                keywords=keywords,
            )
        )
    if not ideas:
        raise GroqFormatError("no usable idea in the answer")
    return ideas


def _script_from_groq(
    niche: str,
    idea: str,
    *,
    platform: str,
    vibe: str,
    audience: str,
    lang: str,
    duration: str = "8-10min",
) -> Script:
    data = _groq_json(
        _script_system_prompt(lang, short_form=is_short_form(platform), duration=duration),
        _script_user_prompt(
            niche,
            idea,
            platform=platform,
            vibe=vibe,
            audience=audience,
            lang=lang,
            duration=duration,
        ),
        temperature=0.7,
    )

    title = _model_text(data.get("title"), 140)
    if not title:
        raise GroqFormatError("no 'title' in the answer")

    description = _model_text(data.get("description"), 500)
    raw_hashtags = data.get("hashtag")
    hashtags = (
        tuple(_model_text(tag, 50) for tag in raw_hashtags if _model_text(tag))[:15]
        if isinstance(raw_hashtags, list)
        else ()
    )
    raw_keywords = data.get("keywords")
    keywords = (
        tuple(_model_text(kw, 50) for kw in raw_keywords if _model_text(kw))[:8]
        if isinstance(raw_keywords, list)
        else ()
    )
    raw_sections = data.get("sections")
    if not isinstance(raw_sections, list):
        raise GroqFormatError("no 'sections' array in the answer")

    sections = []
    for sec in raw_sections:
        if isinstance(sec, dict):
            sections.append({
                "name": _model_text(sec.get("name"), 50),
                "time": _model_text(sec.get("time"), 20),
                "content": _model_text(sec.get("content"), 1000),
                "notes": _model_text(sec.get("notes"), 300),
            })

    return Script(
        title=title,
        description=description,
        hashtags=hashtags,
        keywords=keywords,
        sections=tuple(sections),
    )


def _evaluation_from_groq(text: str, lang: str) -> Evaluation:
    data = _groq_json(_evaluation_system_prompt(lang), _evaluation_user_prompt(text), temperature=0.6)

    analysis = _model_text(data.get("analysis"), 600)
    if not analysis:
        raise GroqFormatError("no 'analysis' in the answer")

    raw_outline = data.get("outline")
    if not isinstance(raw_outline, list):
        raise GroqFormatError("no 'outline' array in the answer")
    outline = [_model_text(step, 220) for step in raw_outline if _model_text(step)]
    outline = outline[:3]
    while len(outline) < 3:
        outline.append(t_for(lang, "eval.step_placeholder", n=len(outline) + 1))

    score = _model_score(data.get("score"))
    improved_score = max(score, _model_score(data.get("improved_score"), minimum=score))

    idea = _template_evaluation(text, lang).idea
    improved = data.get("improved")
    if isinstance(improved, dict):
        title = _model_text(improved.get("title"), 140)
        if title:
            idea = Idea(
                title=title,
                hook=_model_text(improved.get("hook"), 400),
                value=_model_text(improved.get("value"), 400),
            )

    return Evaluation(
        score=score,
        improved_score=improved_score,
        analysis=analysis,
        idea=idea,
        outline=tuple(outline),
    )


LONG_TEMPLATES_AR: tuple[dict[str, str], ...] = (
    {
        "title": "أخطاء {n} يرتكبها 90% من المبتدئين… توقف عنها الآن",
        "hook": "مقارنة قبل/بعد في أول 20 ثانية تُظهر كيف يفقد المشاهد نفسه بسبب خطأ واحد في بنية الفيديو.",
        "value": "محتوى تصحيحي سهل الحفظ يجعل قناتك مصدراً مرجعياً في مجالك.",
    },
    {
        "title": "خطأ واحد في {n} يستهلك وقتك بدون نتيجة",
        "hook": "مشهد صادم بلا مقدمة: أخسر أسبوعاً ثم أحذفه بالكامل وأساعدك على تكراره بخطوتين.",
        "value": "يضعك في موقف الخبير العملي ويمنحك سبباً واضحاً للمشاركة والحفظ.",
    },
    {
        "title": "بدأت في {n} من الصفر… والنتيجة بعد 30 يوماً",
        "hook": "تحدٍ زمني مباشر مع عدّاد على الشاشة يجعل المشاهد يتابع حتى النهاية.",
        "value": "قصة تحول حقيقية ترفع مدة المشاهدة وتقترح فيديوهات لاحقة تلقائياً.",
    },
    {
        "title": "أسرار {n} لا يخبرك بها أحد (اختبرتها بنفسي)",
        "hook": "تجارب شخصية مدعومة بأرقام ونتائج قبل/بعد تمنحك مصداقية عالية من أول دقيقة.",
        "value": "يوحي بأن هناك محتوى أعمق في الانتظار، وهو بالضبط ما يدفع للاشتراك.",
    },
    {
        "title": "كيف تتقن {n} في 10 دقائق يومياً",
        "hook": "روتين عملي مُصوَّر بخطوات سريعة مع قائمة تحقق يراها المشاهد على الشاشة.",
        "value": "محتوى قابل للتنفيذ يجذب جمهوراً مهتماً بالنتائج السريعة.",
    },
    {
        "title": "5 أفكار {n} تكسر المشاهد في أول 3 ثوانٍ",
        "hook": "تحليل سريع لبدايات شائعة مع إعادة كتابة مباشرة تُحوّلها إلى عنوان وخطاف أقوى.",
        "value": "أسلوب تحليل عملي يجذب صنّاع المحتوى والمبتدئين على حد سواء.",
    },
    {
        "title": "قالب {n} جاهز: انسخه وابدأ النشر اليوم",
        "hook": "مشاركة ملف أو هيكل واضح يجعل التحميل سهلاً ومباشراً من الشاشة.",
        "value": "محتوى عملي عالي الحفظ ومصدر ممتاز للروابط الصادرة.",
    },
    {
        "title": "قبل أن تدخل {n}… شاهد هذا الفيديو (يوفّر عليك شهراً)",
        "hook": "فتح بسؤال مباشر ثم كشف الفكرة الأقوى بعد تحذير صادق من تجربة شخصية.",
        "value": "يوازن بين الترهيب والحل، فتدفع جمهوراً مهتماً بالوضوح والصدق.",
    },
    {
        "title": "أغلى درس تعلّمته في {n} (كنت أتمنى سماعه مبكراً)",
        "hook": "قصة شخصية تبدأ بالنتيجة السلبية قبل أن تنتقل إلى الدرس العملي.",
        "value": "المصداقية العاطفية ترفع التعليقات ومعدل المشاركة بشكل ملحوظ.",
    },
    {
        "title": "{n} للمبتدئين: كل ما تحتاجه في فيديو واحد",
        "hook": "وعد واضح بمحتوى شامل مع فهرس على الشاشة يقلل فقدان المشاهد.",
        "value": "يجذب البحث الطويل ويعمل كمحتوى مرجعي دائم.",
    },
    {
        "title": "قارنت أفضل 3 طرق في {n}… الفرق صادم",
        "hook": "مقارنة جنباً إلى جنب لنفس المهمة مع عرض النتائج في النهاية.",
        "value": "هيكل المقارنة يولّد نقاشاً في التعليقات ويعزّز الظهور في الخوارزمية.",
    },
    {
        "title": "7 أيام في {n}: يوم بيوم بلا تجميل",
        "hook": "سلسلة يومية تنشئ سبباً للعودة كل يوم (habit loop).",
        "value": "سلسلة محتوى تبني ولاءً وتدفع للمشاهدة المتكررة للفيديوهات السابقة.",
    },
    {
        "title": "أدوات {n} مجانية أفضل من المدفوعة",
        "hook": "مقارنة ميزانية مع بدائل مجانية حقيقية مثبتة عبر تجربة عملية.",
        "value": "يجذب جمهوراً يبحث عن حلول اقتصادية ويرفع التعليقات.",
    },
    {
        "title": "كيف تختار {n} المناسب لك؟ (شجرة قرار بسيطة)",
        "hook": "أسئلة متسلسلة على الشاشة تقود المشاهد لاختيار واحد بوضوح.",
        "value": "أسلوب تفاعلي يرفع مدة المشاهدة ويسهل حفظ الفيديو.",
    },
)

SHORT_TEMPLATES_AR: tuple[dict[str, str], ...] = (
    {
        "title": "تحدي الـ 30 ثانية في {n}",
        "hook": "النتيجة النهائية تظهر في أول إطار ثم انتقال سريع بلا أي مقدمة.",
        "value": "بنية تشويقية تجعل المشاهد يعيد المقطع تلقائياً لمشاهدة بدايته.",
    },
    {
        "title": "كيف تُنجز {n} في 15 ثانية؟",
        "hook": "حركة بصرية متسارعة كل ثانية مع نص كبير على الشاشة يُقرأ بدون صوت.",
        "value": "نسبة إكمال مرتفعة لأن المشاهد لا يحتاج الصوت، فتتضاعف المشاهدات المتكررة.",
    },
    {
        "title": "اختبار {n} في 10 ثوانٍ… هل تستطيع؟",
        "hook": "سؤال صادم في الشاشة الأولى ثم مؤقت ظاهر يخلق توتراً حتى الثانية الأخيرة.",
        "value": "التوتر الزمني يرفع إعادة المشاهدة ويشجّع تعليقاً يسأل عن بقية الفيديو.",
    },
    {
        "title": "أسرار {n} في 20 ثانية (الأخطر في النهاية)",
        "hook": "ثلاث لقطات سريعة ثم كشف مفاجئ في آخر ثانيتين قبل الانتقال.",
        "value": "مفاجأة النهاية تجعل المشاهد يعيد المقطع ليتأكد من المعلومة.",
    },
    {
        "title": "من {n} قبل وبعد… الفرق في نصف ثانية",
        "hook": "انتقال بصري مفاجئ بين حالتين يكفي لفهم الفكرة كاملة بلا كلام.",
        "value": "تباين قوي يرفع مدة المشاهدة ويجعل الفيديو قابلاً للإعادة السريعة.",
    },
    {
        "title": "أسرع طريقة في {n}… هل تنتهي قبلي؟",
        "hook": "تحدٍّ مباشر مع مؤقت كبير في زاوية الكاميرا القريبة تشد الانتباه فوراً.",
        "value": "المنافسة الزمنية تولّد حلقة مشاهدة متكررة تدفع الخوارزمية لتكرار الفيديو.",
    },
    {
        "title": "3 أشياء لا يقولها أحد في {n}",
        "hook": "نص ضخم يملأ الشاشة مع قطع سريع كل ثانية ونصف بلا أي لقطة تمهيدية.",
        "value": "الإيقاع السريع يقلل نسبة التخطي ويبقي الجمهور حتى آخر إطار.",
    },
    {
        "title": "معلومة {n} ستصدمك خلال 3 ثوانٍ",
        "hook": "رقم ضخم يظهر على الشاشة قبل النطق، فيخلق فضولاً فورياً بلا مقدمة.",
        "value": "الفضول غير المكتمل يرفع نسبة الإعادة ويملأ التعليقات بالأسئلة.",
    },
    {
        "title": "خطأ {n} الذي ينهي الفيديو فوراً",
        "hook": "لحظة فشل حقيقية بلا مونتاج طويل مع صوت مؤثر واضح في الإطار الأول.",
        "value": "الخسارة السريعة تخلق ترقّباً وتُبقي المشاهد حتى نهاية المقطع.",
    },
    {
        "title": "من الصفر إلى احتراف في {n} — النسخة المصغّرة",
        "hook": "النتيجة النهائية القوية تُعرض أولاً ثم تُفكَّك إلى ثلاث خطوات فقط.",
        "value": "محتوى مُكثّف عالي الإعادة يناسب توزيع الشورتس بشكل ممتاز.",
    },
    {
        "title": "اختر واحدة: أسرع طريقتين في {n}",
        "hook": "شاشة تعرض خيارين لثانيتين فقط مع مؤقت يخلق قراراً متعجلاً.",
        "value": "السؤال الثنائي يرفع التعليقات ومعدلات المشاركة.",
    },
    {
        "title": "أول 3 ثوانٍ في {n} تغيّر كل شيء",
        "hook": "مونتاج سريع يحاكي بداية سيئة ثم بداية ناجحة لنفس الفكرة جنباً إلى جنب.",
        "value": "المقارنة المباشرة ترفع مدة المشاهدة وتُشعل النقاش في التعليقات.",
    },
    {
        "title": "{n} بسكينة واحدة في 25 ثانية",
        "hook": "لقطة علوية ثابتة مع حركة واحدة واضحة تُنفّذ بالكامل قبل انتهاء المؤقت.",
        "value": "الفيديو القصير القابل للتكرار يرفع المشاهدات المتكررة للمقطع.",
    },
)

LONG_TEMPLATES_EN: tuple[dict[str, str], ...] = (
    {
        "title": "The {n} mistakes 90% of beginners make… stop right now",
        "hook": "A before/after comparison in the first 20 seconds shows how one structural mistake loses you the viewer.",
        "value": "Easy-to-save corrective content that positions your channel as the reference in your niche.",
    },
    {
        "title": "One {n} mistake that wastes your time with zero results",
        "hook": "A shocking clip with no intro: I lose a full week, delete it all, then show you how to repeat it in two steps.",
        "value": "Positions you as the practical expert and gives viewers a clear reason to share and save.",
    },
    {
        "title": "I started {n} from zero… here's the result after 30 days",
        "hook": "A live 30-day challenge with an on-screen counter that keeps viewers watching to the end.",
        "value": "A real transformation story that lifts watch time and naturally suggests the next videos.",
    },
    {
        "title": "{n} secrets nobody tells you (I tested them all)",
        "hook": "Personal experiments backed by numbers and before/after results that buy credibility in the first minute.",
        "value": "Implies deeper content is waiting, which is exactly what drives subscriptions.",
    },
    {
        "title": "Master {n} in 10 minutes a day",
        "hook": "A practical routine shot as fast steps with an on-screen checklist viewers can follow.",
        "value": "Actionable content that attracts an audience obsessed with fast results.",
    },
    {
        "title": "5 {n} hooks that break viewers in the first 3 seconds",
        "hook": "A fast breakdown of common openings plus a live rewrite into a stronger title and hook.",
        "value": "A practical analysis style that appeals to creators and beginners alike.",
    },
    {
        "title": "{n} template ready: copy it and publish today",
        "hook": "Sharing a file or a clear structure makes it easy to grab straight from the screen.",
        "value": "Highly saveable practical content and a great source of outbound links.",
    },
    {
        "title": "Before you get into {n}… watch this (saves you a month)",
        "hook": "Open with a direct question, then reveal the strongest idea after an honest warning from personal experience.",
        "value": "Balances urgency with the fix, pulling in viewers who value clarity and honesty.",
    },
    {
        "title": "The most expensive {n} lesson I learned (I wish I heard it sooner)",
        "hook": "A personal story that starts with the bad result before moving to the practical lesson.",
        "value": "Emotional credibility lifts comments and sharing rates noticeably.",
    },
    {
        "title": "{n} for beginners: everything you need in one video",
        "hook": "A clear promise of complete content with an on-screen index that reduces viewer drop-off.",
        "value": "Attracts long-tail search and works as permanent reference content.",
    },
    {
        "title": "I compared the 3 best ways to do {n}… the difference is shocking",
        "hook": "A side-by-side comparison of the same task with the results revealed at the end.",
        "value": "The comparison structure sparks comment debates and boosts algorithmic reach.",
    },
    {
        "title": "7 days of {n}: day by day, no edits",
        "hook": "A daily series that creates a reason to come back every single day.",
        "value": "A content series that builds loyalty and drives repeat views on earlier videos.",
    },
)

SHORT_TEMPLATES_EN: tuple[dict[str, str], ...] = (
    {
        "title": "The 30-second {n} challenge",
        "hook": "The final result lands in the very first frame, then an instant cut with no intro.",
        "value": "A curiosity structure that makes viewers replay the clip to catch the opening.",
    },
    {
        "title": "How do you do {n} in 15 seconds?",
        "hook": "A visual beat every second with big on-screen text that reads without sound.",
        "value": "High completion because no audio is needed, which doubles repeat views.",
    },
    {
        "title": "{n} tested in 10 seconds… can you do it?",
        "hook": "A shocking question on the first frame plus a visible timer that builds tension to the last second.",
        "value": "Time pressure drives rewatches and prompts a comment asking for the full video.",
    },
    {
        "title": "{n} secrets in 20 seconds (the twist at the end)",
        "hook": "Three quick cuts, then a sudden reveal in the final two seconds before the cut.",
        "value": "The ending surprise makes viewers rewatch to double-check the fact.",
    },
    {
        "title": "{n} before and after… the difference is half a second",
        "hook": "A sharp visual jump between two states that explains the whole idea without a word.",
        "value": "Strong contrast lifts watch time and makes the clip easy to replay.",
    },
    {
        "title": "The fastest way to do {n}… can you beat it?",
        "hook": "A direct challenge with a big timer in a close camera corner that grabs attention instantly.",
        "value": "Time competition creates a rewatch loop that pushes the algorithm to resurface it.",
    },
    {
        "title": "3 things nobody mentions about {n}",
        "hook": "Huge text filling the screen with a cut every 1.5 seconds and zero establishing shots.",
        "value": "The fast pace lowers drop-off and holds the audience to the final frame.",
    },
    {
        "title": "A {n} fact that will shock you within 3 seconds",
        "hook": "A massive number appears on screen before it is spoken, creating instant curiosity with no intro.",
        "value": "Unfinished curiosity lifts rewatches and floods the comments with questions.",
    },
    {
        "title": "The {n} mistake that kills the video instantly",
        "hook": "A real failure moment with no long montage and a clear sound effect on the first frame.",
        "value": "The fast loss builds suspense and holds the viewer until the end of the clip.",
    },
    {
        "title": "Zero to expert in {n} — the mini version",
        "hook": "The strong final result is shown first, then broken down into only three steps.",
        "value": "Dense, highly replayable content that suits short-form distribution perfectly.",
    },
)

LONG_TEMPLATES_FR: tuple[dict[str, str], ...] = (
    {
        "title": "Les {n} erreurs que 90 % des débutants commettent… arrête tout",
        "hook": "Une comparaison avant / après dans les 20 premières secondes montre comment une seule erreur de structure fait perdre le spectateur.",
        "value": "Un contenu correctif facile à sauvegarder qui positionne ta chaîne comme la référence du thème.",
    },
    {
        "title": "Une seule erreur en {n} qui te fait perdre ton temps sans résultat",
        "hook": "Une scène choc sans intro : je perds une semaine entière, je supprime tout, puis je te montre comment reproduire ça en deux étapes.",
        "value": "Tu passes pour l'expert pratique et tu donnes au spectateur une vraie raison de partager et d'enregistrer.",
    },
    {
        "title": "J'ai commencé {n} de zéro… voici le résultat après 30 jours",
        "hook": "Un défi de 30 jours en direct avec un compteur à l'écran qui garde le spectateur jusqu'au bout.",
        "value": "Une vraie histoire de transformation qui augmente le temps de visionnage et suggère naturellement la suite.",
    },
    {
        "title": "Les secrets de {n} que personne ne te dit (je les ai tous testés)",
        "hook": "Des expériences personnelles appuyées sur des chiffres et des résultats avant / après qui achètent ta crédibilité dès la première minute.",
        "value": "L'idée qu'il existe un contenu plus profond en attente est exactement ce qui déclenche l'abonnement.",
    },
    {
        "title": "Maîtrise {n} en 10 minutes par jour",
        "hook": "Une routine pratique filmée en étapes rapides avec une check-list visible à l'écran.",
        "value": "Du contenu actionnable qui attire une audience obsédée par les résultats rapides.",
    },
    {
        "title": "5 accroches sur {n} qui cassent l'attention en 3 secondes",
        "hook": "Une analyse rapide d'ouvertures courantes suivie d'une réécriture en direct vers un titre et une accroche plus forts.",
        "value": "Un style d'analyse pratique qui parle aussi bien aux créateurs qu'aux débutants.",
    },
    {
        "title": "Modèle {n} prêt à l'emploi : copie et publie aujourd'hui",
        "hook": "Le partage d'un fichier ou d'une structure claire rend la copie immédiate depuis l'écran.",
        "value": "Un contenu très sauvegardable et une excellente source de liens sortants.",
    },
    {
        "title": "Avant de te lancer en {n}… regarde cette vidéo (tu gagnes un mois)",
        "hook": "Ouverture sur une question directe, puis révélation de la meilleure idée après un avertissement honnête tiré d'une expérience personnelle.",
        "value": "Un équilibre entre urgence et solution, qui attire les spectateurs qui cherchent de la clarté et de l'honnêteté.",
    },
)

SHORT_TEMPLATES_FR: tuple[dict[str, str], ...] = (
    {
        "title": "Le défi des 30 secondes sur {n}",
        "hook": "Le résultat final s'affiche dès la première image, puis coupe immédiate sans intro.",
        "value": "Une structure curieuse qui pousse les spectateurs à revoir le début du clip.",
    },
    {
        "title": "Comment réussir {n} en 15 secondes ?",
        "hook": "Un mouvement visuel chaque seconde avec un gros texte à l'écran, lisible sans le son.",
        "value": "Un taux de complétion élevé puisque le son est inutile, ce qui double les vues répétées.",
    },
    {
        "title": "{n} testé en 10 secondes… tu en es capable ?",
        "hook": "Une question choc dès la première image et un minuteur visible qui crée la tension jusqu'à la dernière seconde.",
        "value": "La pression du temps pousse au visionnage répété et génère un commentaire demandant la vidéo complète.",
    },
    {
        "title": "Les secrets de {n} en 20 secondes (la fin surprend)",
        "hook": "Trois coupes rapides, puis une révélation surprise dans les deux dernières secondes.",
        "value": "La chute inattendue incite à revoir la vidéo pour vérifier l'information.",
    },
    {
        "title": "{n} avant / après… la différence tient en une demi-seconde",
        "hook": "Un saut visuel net entre deux situations qui explique l'idée entière sans un mot.",
        "value": "Un contraste fort augmente le temps de visionnage et rend le clip facile à revoir.",
    },
    {
        "title": "Le moyen le plus rapide en {n}… tu me bats ?",
        "hook": "Un défi direct avec un gros minuteur dans un coin rapproché qui accroche l'attention immédiatement.",
        "value": "La compétition chronométrée crée une boucle de relecture que l'algorithme pousse à recommander.",
    },
    {
        "title": "3 choses que personne ne dit sur {n}",
        "hook": "Un texte énorme qui remplit l'écran, avec une coupe toutes les 1,5 seconde et zéro plan d'établissement.",
        "value": "Le rythme rapide réduit le taux d'abandon et garde l'audience jusqu'à la dernière image.",
    },
    {
        "title": "Un fait sur {n} qui va te choquer en 3 secondes",
        "hook": "Un chiffre géant s'affiche avant d'être prononcé, créant une curiosité immédiate sans intro.",
        "value": "La curiosité inachevée augmente les relectures et remplit les commentaires de questions.",
    },
)

TEMPLATE_POOLS: dict[str, dict[str, tuple[dict[str, str], ...]]] = {
    "en": {"long": LONG_TEMPLATES_EN, "short": SHORT_TEMPLATES_EN},
    "ar": {"long": LONG_TEMPLATES_AR, "short": SHORT_TEMPLATES_AR},
    "fr": {"long": LONG_TEMPLATES_FR, "short": SHORT_TEMPLATES_FR},
}


def template_pool(lang: str, *, short_form: bool) -> tuple[dict[str, str], ...]:
    pools = TEMPLATE_POOLS.get(lang, TEMPLATE_POOLS[DEFAULT_LANGUAGE])
    return pools["short" if short_form else "long"]


def _template_ideas(
    niche: str,
    count: int,
    variant: int,
    *,
    platform: str,
    vibe: str,
    audience: str,
    lang: str,
) -> list[Idea]:
    """Offline generator: builds niche-specific ideas from the active language pool.

    Used as the fallback whenever Groq is unavailable, so the page never goes blank.
    """
    short_form = is_short_form(platform)
    mode = "short" if short_form else "long"
    pool = template_pool(lang, short_form=short_form)

    rng = random.Random(f"{mode}|{vibe}|{audience}|{lang}|{niche}|{variant}")
    notes = " ".join(
        part
        for part in (
            flavor(VIBE_FLAVOR, vibe, lang),
            flavor(PLATFORM_FLAVOR, platform, lang),
            flavor(AUDIENCE_FLAVOR, audience, lang),
        )
        if part
    )
    templates = rng.sample(pool, k=min(count, len(pool)))
    return [
        Idea(
            title=tpl["title"].format(n=niche),
            hook=tpl["hook"],
            value=f"{tpl['value']} {notes}".strip(),
        )
        for tpl in templates
    ]


def generate_ideas(
    niche: str,
    count: int = FREE_IDEAS_COUNT,
    variant: int = 0,
    *,
    platform: str = DEFAULT_PLATFORM,
    vibe: str = "",
    audience: str = "",
    lang: str | None = None,
) -> list[Idea]:
    """Generates ideas with Groq, falling back to the built-in pools when it is down.

    Variables driving the prompt: niche, platform, output language, vibe, target audience and
    the re-roll `variant`. Failures never raise: a friendly message is stored for
    `render_ai_error()` and the offline templates are returned instead.
    """
    clean_niche = niche.strip()
    if not clean_niche:
        return []

    lang = lang if lang in SUPPORTED_LANGUAGES else current_lang()

    problem = _configure_groq()
    if problem is None:
        try:
            ideas = _ideas_from_groq(
                clean_niche,
                count,
                platform=platform,
                vibe=vibe,
                audience=audience,
                lang=lang,
                variant=variant,
            )
        except Exception as exc:
            _set_ai_error(_classify_ai_error(exc), _ai_error_detail(exc))
        else:
            _clear_ai_error()
            return ideas
    else:
        _set_ai_error(problem)

    return _template_ideas(
        clean_niche,
        count,
        variant,
        platform=platform,
        vibe=vibe,
        audience=audience,
        lang=lang,
    )


# --------------------------------------------------------------------------------------
# Mock evaluator
# --------------------------------------------------------------------------------------


@dataclass(frozen=True)
class Evaluation:
    score: int
    improved_score: int
    analysis: str
    idea: Idea
    outline: tuple[str, str, str] = ("", "", "")


CHECK_POINTS: dict[str, int] = {
    "length": 15,
    "number": 12,
    "question": 12,
    "curiosity": 14,
    "specific": 12,
}

QUESTION_WORDS: dict[str, tuple[str, ...]] = {
    "en": ("how", "why", "what", "which", "where", "when", "who", "can", "does"),
    "ar": ("كيف", "لماذا", "ما هو", "ما هي", "ما الذي", "هل", "أين", "متى", "كم"),
    "fr": ("comment", "pourquoi", "quel", "quelle", "où", "quand", "qui", "est-ce", "peut-on"),
}

CURIOSITY_WORDS: dict[str, tuple[str, ...]] = {
    "en": (
        "shocking", "shock", "secret", "nobody", "mistake", "free", "fastest", "worst",
        "hidden", "truth", "never", "stop", "wrong", "nobody tells",
    ),
    "ar": (
        "صادم", "مفاجأة", "لا أحد", "أسرار", "جربت", "أخطر", "أسرع", "أول مرة", "جديد",
        "أخفى", "الحقيقة", "خطأ", "بدون", "مجانا",
    ),
    "fr": (
        "choc", "secret", "personne", "erreur", "gratuit", "rapide", "pire", "caché",
        "vérité", "jamais", "arrête", "faux", "personne ne dit",
    ),
}

SPECIFIC_WORDS: dict[str, tuple[str, ...]] = {
    "en": ("video", "channel", "watcher", "subscriber", "episode", "stream", "reel", "short", "youtube"),
    "ar": ("فيديو", "قناة", "مشاهد", "متابع", "حلقة", "بث", "ريلز", "شورتس"),
    "fr": ("vidéo", "chaîne", "spectateur", "abonné", "épisode", "reel", "short", "youtube"),
}

QUESTION_MARKS: dict[str, tuple[str, ...]] = {
    "en": ("?",),
    "ar": ("؟",),
    "fr": ("?",),
}

UPGRADE_PATTERNS: dict[str, tuple[dict[str, Any], ...]] = {
    "ar": (
        {
            "title": "«{idea}» — والنتيجة تظهر في أول 3 ثوانٍ",
            "hook": "ابدأ بلقطة النتيجة النهائية صامتة مع نص كبير على الشاشة، ثم انتقل مباشرة إلى المشكلة.",
            "angle": "مونتاج سريع بقطع كل ثانية ونصف مع مؤقت صغير يخلق تحدياً زمنياً.",
            "outline": (
                "المقدمة: اعرض النتيجة النهائية صامتة في أول إطار، ثم سؤال مباشر: كيف وصلت إلى هنا؟",
                "صلب الموضوع: خطوتان فقط باللقطة العلوية مع عدّاد تنازلي على الشاشة.",
                "دعوة لاتخاذ إجراء: اطلب الحفظ والمشاركة، وأشِر إلى الجولة القادمة في آخر ثانية.",
            ),
        },
        {
            "title": "الخطأ الذي يوقف نمو قناتك في «{idea}»",
            "hook": "سؤال صادم على الشاشة الأولى ثم مشهد الفشل الحقيقي قبل أي شرح.",
            "angle": "تناقض بين الوعد والنتيجة: ابدأ بالخسارة ثم اعرض الحل خطوة بخطوة.",
            "outline": (
                "المقدمة: مشهد الفشل الحقيقي مع سؤال مباشر: كم خسرت قبل أن تفهم هذا؟",
                "صلب الموضوع: اشرح سبب الخطأ في 3 نقاط قصيرة مع لقطة توضح حجم الضرر.",
                "دعوة لاتخاذ إجراء: اطلب من المشاهد كتابة الخطأ الذي وقع فيه في التعليق.",
            ),
        },
        {
            "title": "«{idea}» في 60 ثانية — اختبار سريع قبل النشر",
            "hook": "عدّاد تنازلي من أول إطار مع نص كبير يُقرأ بالكامل بدون صوت.",
            "angle": "تحدٍ زمني مع مقارنة قبل وبعد في النهاية لتثبيت النتيجة.",
            "outline": (
                "المقدمة: عدّاد تنازلي من 60 مع نص كبير: هل تنجح قبل أن ينتهي الوقت؟",
                "صلب الموضوع: نفّذ المهمة كاملة بلا مونتاج طويل واذكر الزمن في كل خطوة.",
                "دعوة لاتخاذ إجراء: اعرض النتيجة قبل وبعد ثم اطلب تصويتاً: نجحت أم فشلت؟",
            ),
        },
        {
            "title": "أحدهم جرّب «{idea}» والنتيجة صدمت الجميع",
            "hook": "لقطة رد فعل أو اقتباس صوتي سريع يُعرض قبل أي سياق.",
            "angle": "سرد قصير بضمير المتابع مع كشف الفكرة في آخر عشر ثوانٍ.",
            "outline": (
                "المقدمة: رد فعل صادم أو اقتباس صوتي قصير، ثم سؤال: كيف انتهت المحاولة؟",
                "صلب الموضوع: راوِ القصة بضمير المتابع مع لقطة واحدة لكل خطوة رئيسية.",
                "دعوة لاتخاذ إجراء: اطلب من المشاهد أن يجرّبها ويشارك نتيجته في التعليق.",
            ),
        },
        {
            "title": "3 تغييرات ترفع «{idea}» إلى مستوى آخر",
            "hook": "ثلاث لقطات سريعة مرقّمة 1-2-3 تمنح المشاهد توقعاً واضحاً حتى النهاية.",
            "angle": "قائمة مرئية بنص كبير على الشاشة، فيفهمها المشاهد صامتاً ويرتفع معدل إكماله.",
            "outline": (
                "المقدمة: ثلاث لقطات مرقّمة 1-2-3 في أول 3 ثوانٍ مع نص كبير على الشاشة.",
                "صلب الموضوع: اشرح كل تغيير في 5 ثوانٍ مع مثال عملي قبل وبعد.",
                "دعوة لاتخاذ إجراء: اطلب اختيار التغيير الأقوى في التعليق ليكون موضوع فيديو قادم.",
            ),
        },
        {
            "title": "لماذا «{idea}» لا يعمل معك؟ السبب واحد",
            "hook": "سؤال مباشر ثم رقم صادم يظهر على الشاشة خلال أول ثانيتين.",
            "angle": "تشخيص ثم وصفة: قسّم الفيديو إلى مشكلة ثم حل سريع قابل للتطبيق.",
            "outline": (
                "المقدمة: سؤال مباشر ثم رقم صادم على الشاشة خلال أول ثانيتين.",
                "صلب الموضوع: شخّص السبب في جملة واحدة ثم قدّم الحل القابل للتطبيق فوراً.",
                "دعوة لاتخاذ إجراء: اطلب تطبيق الحل الآن ومشاركة النتيجة في التعليق.",
            ),
        },
    ),
    "en": (
        {
            "title": "\"{idea}\" — the result lands in the first 3 seconds",
            "hook": "Open on the final result in silence with big on-screen text, then jump straight to the problem.",
            "angle": "Fast cuts every 1.5 seconds with a small timer that creates time pressure.",
            "outline": (
                "Intro: show the final result silently in the first frame, then ask: how did I get here?",
                "Body: only two steps, shot top-down with an on-screen countdown.",
                "CTA: ask for the save and the share, and tease the next round in the final second.",
            ),
        },
        {
            "title": "The mistake killing your growth in \"{idea}\"",
            "hook": "A shocking question on the first frame, then the real failure on camera before any explanation.",
            "angle": "Promise versus result: start with the loss, then reveal the fix step by step.",
            "outline": (
                "Intro: the real failure on camera with a direct question: how much did this cost you?",
                "Body: explain the mistake in three short points with a shot that shows the damage.",
                "CTA: ask viewers to write the mistake they made in the comments.",
            ),
        },
        {
            "title": "\"{idea}\" in 60 seconds — a quick test before you publish",
            "hook": "A countdown from the first frame with large text that reads fully without sound.",
            "angle": "A timed challenge closing on a before/after comparison to lock in the result.",
            "outline": (
                "Intro: a 60-second countdown with large text: will you make it in time?",
                "Body: run the full task without long cuts and state the time at every step.",
                "CTA: show the before/after, then ask for a vote: win or fail?",
            ),
        },
        {
            "title": "Someone tried \"{idea}\" and the result shocked everyone",
            "hook": "A reaction shot or a short audio quote shown before any context.",
            "angle": "A short second-person narrative that reveals the idea in the last ten seconds.",
            "outline": (
                "Intro: a shocked reaction or a short quote, then ask: how did the attempt end?",
                "Body: tell the story in second person with one shot per key step.",
                "CTA: ask viewers to try it and post their result in the comments.",
            ),
        },
        {
            "title": "3 changes that take \"{idea}\" to another level",
            "hook": "Three quick shots numbered 1-2-3 that set a clear expectation until the end.",
            "angle": "A visual list with large on-screen text, understood with the sound off, which lifts completion.",
            "outline": (
                "Intro: three shots numbered 1-2-3 in the first 3 seconds with large on-screen text.",
                "Body: explain each change in 5 seconds with a practical before/after example.",
                "CTA: ask viewers to pick the strongest change in the comments to shape the next video.",
            ),
        },
        {
            "title": "Why \"{idea}\" doesn't work for you? There is one reason",
            "hook": "A direct question, then a shocking number on screen within the first two seconds.",
            "angle": "Diagnosis then prescription: split the video into the problem and a quick, applicable fix.",
            "outline": (
                "Intro: a direct question, then a shocking number on screen within the first two seconds.",
                "Body: name the cause in one sentence, then hand over the applicable fix immediately.",
                "CTA: ask them to apply the fix now and share the result in the comments.",
            ),
        },
    ),
    "fr": (
        {
            "title": "\"{idea}\" — le résultat dès les 3 premières secondes",
            "hook": "Ouvre sur le résultat final en silence avec un gros texte à l'écran, puis enchaîne directement sur le problème.",
            "angle": "Des coupes rapides toutes les 1,5 seconde avec un petit minuteur qui crée une pression temporelle.",
            "outline": (
                "Intro : montre le résultat final en silence dès la première image, puis demande : comment j'en suis arrivé là ?",
                "Corps : deux étapes seulement, filmées en plongée avec un compte à rebours à l'écran.",
                "Appel à l'action : demande l'enregistrement et le partage, et tease l'épisode suivant à la dernière seconde.",
            ),
        },
        {
            "title": "L'erreur qui bloque ta croissance sur \"{idea}\"",
            "hook": "Une question choc dès la première image, puis l'échec réel filmé avant toute explication.",
            "angle": "Promesse contre résultat : commence par la perte, puis révèle la solution étape par étape.",
            "outline": (
                "Intro : l'échec réel filmé avec une question directe : combien ça t'a coûté avant que tu comprennes ?",
                "Corps : explique l'erreur en trois points courts avec un plan qui montre l'ampleur des dégâts.",
                "Appel à l'action : demande aux spectateurs d'écrire leur propre erreur en commentaire.",
            ),
        },
        {
            "title": "\"{idea}\" en 60 secondes — le test avant de publier",
            "hook": "Un compte à rebours dès la première image avec un texte large, entièrement lisible sans le son.",
            "angle": "Un défi chronométré qui se referme sur une comparaison avant / après pour ancrer le résultat.",
            "outline": (
                "Intro : un compte à rebours de 60 secondes avec un gros texte : tu réussis dans le temps imparti ?",
                "Corps : réalise la tâche entière sans coupe longue et annonce la durée à chaque étape.",
                "Appel à l'action : montre le avant / après puis fais voter : réussite ou échec ?",
            ),
        },
        {
            "title": "Quelqu'un a testé \"{idea}\" et le résultat a surpris tout le monde",
            "hook": "Un plan réaction ou une courte citation audio, montré avant tout contexte.",
            "angle": "Un récit court à la deuxième personne qui révèle l'idée dans les dix dernières secondes.",
            "outline": (
                "Intro : une réaction choquée ou une courte citation, puis demande : comment s'est terminée la tentative ?",
                "Corps : raconte l'histoire à la deuxième personne avec un plan par étape clé.",
                "Appel à l'action : demande aux spectateurs d'essayer et de poster leur résultat en commentaire.",
            ),
        },
        {
            "title": "3 changements qui font passer \"{idea}\" au niveau supérieur",
            "hook": "Trois plans rapides numérotés 1-2-3 qui installent une attente claire jusqu'à la fin.",
            "angle": "Une liste visuelle en gros texte à l'écran, comprise sans le son, qui fait monter le taux de complétion.",
            "outline": (
                "Intro : trois plans numérotés 1-2-3 dans les 3 premières secondes avec un gros texte à l'écran.",
                "Corps : explique chaque changement en 5 secondes avec un exemple pratique avant / après.",
                "Appel à l'action : demande de choisir le changement le plus fort en commentaire pour la prochaine vidéo.",
            ),
        },
        {
            "title": "Pourquoi \"{idea}\" ne marche pas pour toi ? La raison est unique",
            "hook": "Une question directe, puis un chiffre choc affiché à l'écran dans les deux premières secondes.",
            "angle": "Diagnostic puis ordonnance : découpe la vidéo entre le problème et la solution rapide et applicable.",
            "outline": (
                "Intro : une question directe, puis un chiffre choc à l'écran dans les deux premières secondes.",
                "Corps : nomme la cause en une phrase, puis livre la solution applicable immédiatement.",
                "Appel à l'action : demande d'appliquer la solution maintenant et de partager le résultat en commentaire.",
            ),
        },
    ),
}


def _idea_core(text: str, limit: int = 55) -> str:
    """Normalizes a user idea into a short quotable phrase for titles."""
    clean = " ".join(text.split()).strip(" .؟?!…،,")
    if len(clean) <= limit:
        return clean
    trimmed = clean[:limit].rsplit(" ", 1)[0]
    return f"{trimmed}…"


def _template_evaluation(text: str, lang: str) -> Evaluation:
    """Offline evaluator: heuristics used when Groq is unavailable.

    Scores length, a number, a question, a curiosity trigger and a concrete audience, then
    returns a localized analysis plus an upgraded idea.
    """
    clean = " ".join(text.split())
    rng = random.Random(f"{lang}|{clean}")
    score = 30
    issues: list[str] = []

    too_long = len(clean) > 160
    for check, points in CHECK_POINTS.items():
        if check == "length":
            passed = 45 <= len(clean) <= 160
        elif check == "number":
            passed = any(ch.isdigit() for ch in clean)
        elif check == "question":
            passed = any(mark in clean for mark in QUESTION_MARKS[lang]) or any(
                word in clean.lower() for word in QUESTION_WORDS[lang]
            )
        elif check == "curiosity":
            passed = any(word in clean.lower() for word in CURIOSITY_WORDS[lang]) or "…" in clean
        else:
            passed = any(word in clean.lower() for word in SPECIFIC_WORDS[lang]) or any(
                niche in clean.lower() for niche in ALL_NICHE_WORDS
            )

        if passed:
            score += points
        elif check == "length" and too_long:
            issues.append(t_for(lang, "eval.check.length_long"))
        else:
            issues.append(t_for(lang, f"eval.check.{check}"))

    score = max(5, min(95, score))
    improved_score = min(97, score + 34)

    if issues:
        analysis = t_for(lang, "eval.issues_prefix") + " ".join(f"• {issue}" for issue in issues[:3])
    else:
        analysis = t_for(lang, "eval.strong")

    pattern = rng.choice(UPGRADE_PATTERNS[lang])
    return Evaluation(
        score=score,
        improved_score=improved_score,
        analysis=analysis,
        idea=Idea(
            title=pattern["title"].format(idea=_idea_core(clean)),
            hook=pattern["hook"],
            value=pattern["angle"],
        ),
        outline=pattern["outline"],
    )


def evaluate_idea(text: str, lang: str | None = None) -> Evaluation:
    """Reviews a user idea with Groq, falling back to the local heuristics when it is down.

    `lang` decides the language of the critique and of the outline. Failures never raise: a
    friendly message is stored for `render_ai_error()` and the offline score is returned.
    """
    lang = lang if lang in SUPPORTED_LANGUAGES else current_lang()
    clean = " ".join(text.split())
    if not clean:
        return Evaluation(0, 0, t_for(lang, "eval.empty"), Idea("", "", ""))

    problem = _configure_groq()
    if problem is None:
        try:
            result = _evaluation_from_groq(clean, lang)
        except Exception as exc:
            _set_ai_error(_classify_ai_error(exc), _ai_error_detail(exc))
        else:
            _clear_ai_error()
            return result
    else:
        _set_ai_error(problem)

    return _template_evaluation(clean, lang)


# --------------------------------------------------------------------------------------
# Clipboard helpers
# --------------------------------------------------------------------------------------


def idea_to_clipboard(idea: Idea) -> str:
    lines = [
        f"{t('clip.title')}: {idea.title}",
        f"{t('clip.hook')}: {idea.hook}",
        f"{t('clip.angle')}: {idea.value}",
    ]
    if idea.steps:
        plan = "\n".join(f"{index}. {step}" for index, step in enumerate(idea.steps, start=1))
        lines.append(f"{t('card.plan')}:\n{plan}")
    return "\n".join(lines)


def _copy_iframe(text: str, label: str) -> str:
    """Builds a tiny iframe that copies `text` to the clipboard on click."""
    payload = json.dumps(text, ensure_ascii=True).replace("</", "<\\/")
    caption = json.dumps(label, ensure_ascii=True).replace("</", "<\\/")
    done_msg = json.dumps(t("copy.done"), ensure_ascii=True).replace("</", "<\\/")
    manual_msg = json.dumps(t("copy.manual"), ensure_ascii=True).replace("</", "<\\/")
    return f"""
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            html, body {{ margin: 0; padding: 0; background: transparent; }}
            button {{
                width: 100%; cursor: pointer; direction: {text_direction()};
                font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
                font-size: .84rem; font-weight: 700; color: #5b6178;
                background: #fff; border: 1.5px solid #e9ebf3; border-radius: 12px;
                padding: .42rem .6rem; transition: all .15s ease;
            }}
            button:hover {{ border-color: #7b2ff7; color: #7b2ff7; }}
            button.ok {{
                background: #eafaf3; border-color: #00b478; color: #00875a;
            }}
        </style>
    </head>
    <body>
        <button id="copyBtn">{html_escape(label)}</button>
        <script>
            const text = {payload};
            const label = {caption};
            const doneMsg = {done_msg};
            const manualMsg = {manual_msg};
            const btn = document.getElementById('copyBtn');
            let timer = null;
            const flash = (msg, ok) => {{
                btn.textContent = msg;
                btn.classList.toggle('ok', ok);
                clearTimeout(timer);
                timer = setTimeout(() => {{
                    btn.textContent = label;
                    btn.classList.remove('ok');
                }}, 1800);
            }};
            const fallback = () => {{
                const area = document.createElement('textarea');
                area.value = text;
                area.style.position = 'fixed';
                area.style.opacity = '0';
                document.body.appendChild(area);
                area.focus();
                area.select();
                let done = false;
                try {{ done = document.execCommand('copy'); }} catch (err) {{ done = false; }}
                document.body.removeChild(area);
                flash(done ? doneMsg : manualMsg, done);
            }};
            btn.addEventListener('click', () => {{
                if (navigator.clipboard && window.isSecureContext) {{
                    navigator.clipboard.writeText(text)
                        .then(() => flash(doneMsg, true))
                        .catch(fallback);
                }} else {{
                    fallback();
                }}
            }});
        </script>
    </body>
    </html>
    """


def render_copy_button(text: str) -> None:
    """Renders the copy button that belongs to a single card."""
    if not text:
        return
    st.iframe(_copy_iframe(text, t("copy.idea")), height=46)


def chunked(items: list[Idea], size: int = 3) -> list[list[Idea]]:
    """Splits the ideas into rows so each row can be laid out in columns."""
    return [items[index : index + size] for index in range(0, len(items), size)]


# --------------------------------------------------------------------------------------
# Styling
# --------------------------------------------------------------------------------------

CSS_TEMPLATE = """
<style>
__FONT_IMPORT__
:root {
    --primary-1: #8B5CF6;
    --primary-2: #EC4899;
    --accent: #A855F7;
    --ink: #F1F5F9;
    --muted: #94A3B8;
    --bg-dark: #0F172A;
    --bg-gradient: linear-gradient(135deg, #0F172A 0%, #1E293B 50%, #0F172A 100%);
    --card-bg: rgba(30, 41, 59, 0.7);
    --card-border: rgba(139, 92, 246, 0.3);
    --glow: rgba(139, 92, 246, 0.5);
}

* {
    font-family: __FONT__;
}

html, body, .stApp {
    direction: __DIRECTION__;
    text-align: __ALIGN__;
    background: var(--bg-gradient);
    background-attachment: fixed;
    min-height: 100vh;
}

.stApp::before {
    content: '';
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: 
        radial-gradient(circle at 20% 80%, rgba(139, 92, 246, 0.15) 0%, transparent 50%),
        radial-gradient(circle at 80% 20%, rgba(236, 72, 153, 0.1) 0%, transparent 50%),
        radial-gradient(circle at 40% 40%, rgba(168, 85, 247, 0.08) 0%, transparent 40%);
    pointer-events: none;
    z-index: 0;
}

.block-container {
    max-width: 1080px;
    padding-top: 2rem;
    padding-bottom: 3rem;
    position: relative;
    z-index: 1;
}

div[data-baseweb="input"] input,
div[data-baseweb="select"] select,
textarea {
    background: rgba(30, 41, 59, 0.8) !important;
    color: var(--ink) !important;
    border: 1px solid var(--card-border) !important;
    border-radius: 12px !important;
    font-size: 0.98rem;
    line-height: 1.6;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3), inset 0 1px 0 rgba(255, 255, 255, 0.1) !important;
    backdrop-filter: blur(10px);
    transition: all 0.3s ease;
}

div[data-baseweb="input"] input::placeholder,
textarea::placeholder {
    color: var(--muted) !important;
    opacity: 0.8 !important;
}

div[data-baseweb="input"]:focus-within input,
div[data-baseweb="select"]:focus-within select,
textarea:focus {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 3px rgba(168, 85, 247, 0.3), 0 4px 20px rgba(0, 0, 0, 0.3), inset 0 1px 0 rgba(255, 255, 255, 0.1) !important;
    outline: none !important;
    background: rgba(30, 41, 59, 0.95) !important;
}

[data-testid="stPills"] button,
[data-testid="stRadio"] > div > label {
    background: rgba(30, 41, 59, 0.6) !important;
    color: var(--ink) !important;
    border: 1px solid var(--card-border) !important;
    border-radius: 50px !important;
    backdrop-filter: blur(10px);
    transition: all 0.3s ease;
}

[data-testid="stPills"] button:hover,
[data-testid="stRadio"] > div > label:hover {
    border-color: var(--accent) !important;
    transform: translateY(-2px);
    box-shadow: 0 4px 15px rgba(168, 85, 247, 0.3);
}

[data-testid="stPills"] button[kind="primary"],
[data-testid="stRadio"] > div > label[data-selected="true"] {
    background: linear-gradient(135deg, var(--primary-1), var(--accent)) !important;
    border-color: transparent !important;
    color: #FFFFFF !important;
    box-shadow: 0 4px 20px rgba(139, 92, 246, 0.5);
}

div.stButton > button {
    border: none !important;
    background: linear-gradient(135deg, var(--primary-1), var(--primary-2)) !important;
    color: #FFFFFF !important;
    font-weight: 800;
    font-size: 0.98rem;
    border-radius: 50px !important;
    padding: 0.8rem 2rem;
    box-shadow: 0 8px 25px rgba(139, 92, 246, 0.4), 0 0 40px rgba(139, 92, 246, 0.2);
    transition: all 0.3s ease;
    letter-spacing: 0.3px;
    position: relative;
    overflow: hidden;
}

div.stButton > button::before {
    content: '';
    position: absolute;
    top: 0;
    left: -100%;
    width: 100%;
    height: 100%;
    background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.3), transparent);
    transition: left 0.5s ease;
}

div.stButton > button:hover::before {
    left: 100%;
}

div.stButton > button:hover {
    filter: brightness(1.1);
    transform: translateY(-3px);
    box-shadow: 0 12px 35px rgba(139, 92, 246, 0.6), 0 0 50px rgba(139, 92, 246, 0.3);
}

.premium-card {
    background: var(--card-bg);
    border-radius: 20px;
    border: 1px solid var(--card-border);
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3), 0 0 20px rgba(139, 92, 246, 0.1);
    padding: 28px;
    margin-bottom: 20px;
    transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
    text-align: __ALIGN__;
    backdrop-filter: blur(20px);
    position: relative;
    overflow: hidden;
}

.premium-card::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 3px;
    background: linear-gradient(90deg, var(--primary-1), var(--accent), var(--primary-2));
    opacity: 0;
    transition: opacity 0.3s ease;
}

.premium-card:hover::before {
    opacity: 1;
}

.premium-card:hover {
    transform: translateY(-8px);
    box-shadow: 0 16px 48px rgba(0, 0, 0, 0.4), 0 0 30px rgba(139, 92, 246, 0.3);
    border-color: var(--accent);
}

.premium-card h3 {
    margin: 0 0 16px 0;
    font-size: 1.2rem;
    font-weight: 800;
    color: var(--ink);
    line-height: 1.6;
    text-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
}

.premium-card .meta {
    color: var(--muted);
    font-size: 0.94rem;
    line-height: 1.9;
    margin-bottom: 14px;
}

.premium-card .row {
    margin: 16px 0;
}

.premium-card .badge {
    display: inline-block;
    padding: 8px 16px;
    border-radius: 999px;
    font-size: 0.82rem;
    font-weight: 800;
    background: linear-gradient(135deg, rgba(139, 92, 246, 0.2), rgba(168, 85, 247, 0.2));
    color: var(--accent);
    margin-bottom: 12px;
    border: 1px solid rgba(139, 92, 246, 0.3);
    box-shadow: 0 2px 10px rgba(139, 92, 246, 0.2);
}

.premium-card ol {
    margin: 0;
    padding-right: 24px;
    color: var(--ink);
    line-height: 1.9;
}

.premium-card li + li {
    margin-top: 10px;
}

.premium-card .tags {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
}

.premium-card .tag {
    background: linear-gradient(135deg, rgba(139, 92, 246, 0.2), rgba(168, 85, 247, 0.2));
    color: var(--accent);
    padding: 0.3rem 0.7rem;
    border-radius: 6px;
    font-size: 0.8rem;
    font-weight: 600;
    border: 1px solid rgba(139, 92, 246, 0.3);
}

::-webkit-scrollbar {
    width: 10px;
}

::-webkit-scrollbar-track {
    background: rgba(30, 41, 59, 0.5);
}

::-webkit-scrollbar-thumb {
    background: linear-gradient(135deg, var(--primary-1), var(--accent));
    border-radius: 5px;
}

::-webkit-scrollbar-thumb:hover {
    background: linear-gradient(135deg, var(--accent), var(--primary-2));
}

.ts-hero h1,
.ts-hero p {
    color: var(--ink) !important;
}

.ts-hero .accent {
    background: linear-gradient(90deg, var(--primary-1), var(--accent), var(--primary-2));
    -webkit-background-clip: text;
    background-clip: text;
    color: transparent;
}

.ts-section h2 {
    color: var(--ink) !important;
}

.ts-paywall {
    background: linear-gradient(135deg, rgba(139, 92, 246, 0.15), rgba(236, 72, 153, 0.15));
    border: 2px solid var(--card-border);
    border-radius: 24px;
    padding: 4px;
    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.4), 0 0 40px rgba(139, 92, 246, 0.2);
}

.ts-paywall-inner {
    background: rgba(30, 41, 59, 0.9);
    border-radius: 20px;
    padding: 2.5rem;
    backdrop-filter: blur(20px);
}

.ts-paywall h2 {
    color: var(--ink) !important;
}

.ts-paywall .price {
    color: var(--accent) !important;
}

.ts-paywall ul li {
    color: var(--muted) !important;
}

.ts-pricing-section {
    margin-top: 3rem;
    padding: 3rem 0;
}

.ts-pricing-header {
    text-align: center;
    margin-bottom: 3rem;
}

.ts-pricing-header h2 {
    font-size: clamp(1.8rem, 4vw, 2.5rem);
    font-weight: 800;
    margin-bottom: 0.8rem;
    color: var(--ink);
}

.ts-pricing-header p {
    font-size: 1.1rem;
    color: var(--muted);
}

.ts-pricing-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 2rem;
    max-width: 1200px;
    margin: 0 auto;
}

@media (max-width: 900px) {
    .ts-pricing-grid {
        grid-template-columns: 1fr;
    }
}

.ts-pricing-card {
    background: var(--card-bg);
    border: 2px solid var(--card-border);
    border-radius: 24px;
    padding: 2.5rem;
    text-align: center;
    transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
    backdrop-filter: blur(20px);
    position: relative;
    overflow: hidden;
}

.ts-pricing-card::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 4px;
    background: linear-gradient(90deg, var(--primary-1), var(--accent));
    opacity: 0;
    transition: opacity 0.3s ease;
}

.ts-pricing-card:hover::before {
    opacity: 1;
}

.ts-pricing-card:hover {
    transform: translateY(-10px);
    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.4), 0 0 40px rgba(139, 92, 246, 0.3);
    border-color: var(--accent);
}

.ts-pricing-card.featured {
    border: 2px solid var(--accent);
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3), 0 0 40px rgba(139, 92, 246, 0.4);
    transform: scale(1.05);
}

.ts-pricing-card.featured:hover {
    transform: scale(1.05) translateY(-10px);
}

.ts-pricing-badge {
    display: inline-block;
    background: linear-gradient(135deg, var(--primary-1), var(--accent));
    color: white;
    font-size: 0.75rem;
    font-weight: 800;
    padding: 0.4rem 1rem;
    border-radius: 999px;
    margin-bottom: 1rem;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

.ts-pricing-badge.popular {
    background: linear-gradient(135deg, #F59E0B, #EF4444);
    animation: pulse 2s infinite;
}

@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.8; }
}

.ts-pricing-card h3 {
    font-size: 1.5rem;
    font-weight: 800;
    margin: 0 0 0.5rem;
    color: var(--ink);
}

.ts-price {
    font-size: 2.5rem;
    font-weight: 800;
    color: var(--accent);
    margin-bottom: 2rem;
}

.ts-price span {
    font-size: 1rem;
    color: var(--muted);
    font-weight: 500;
}

.ts-features {
    list-style: none;
    padding: 0;
    margin: 0 0 2rem;
    text-align: right;
}

.ts-features li {
    padding: 0.8rem 0;
    color: var(--muted);
    font-size: 0.95rem;
    border-bottom: 1px solid rgba(139, 92, 246, 0.1);
}

.ts-features li:last-child {
    border-bottom: none;
}

.ts-features li.disabled {
    color: rgba(148, 163, 184, 0.5);
    text-decoration: line-through;
}

.ts-pricing-btn {
    display: block;
    width: 100%;
    padding: 1rem 2rem;
    border-radius: 50px;
    font-weight: 800;
    font-size: 1rem;
    text-decoration: none;
    transition: all 0.3s ease;
    cursor: pointer;
    border: 2px solid var(--card-border);
    background: rgba(30, 41, 59, 0.6);
    color: var(--muted);
    backdrop-filter: blur(10px);
}

.ts-pricing-btn:hover {
    border-color: var(--accent);
    color: var(--accent);
    transform: translateY(-2px);
}

.ts-pricing-btn.primary {
    background: linear-gradient(135deg, var(--primary-1), var(--accent));
    border: none;
    color: white;
    box-shadow: 0 8px 25px rgba(139, 92, 246, 0.4);
}

.ts-pricing-btn.primary:hover {
    filter: brightness(1.1);
    transform: translateY(-3px);
    box-shadow: 0 12px 35px rgba(139, 92, 246, 0.6);
}

.ts-pricing-footer {
    text-align: center;
    margin-top: 2rem;
    padding: 1.5rem;
    background: rgba(30, 41, 59, 0.4);
    border-radius: 12px;
    border: 1px solid var(--card-border);
}

.ts-pricing-footer p {
    color: var(--muted);
    font-size: 0.9rem;
    margin: 0;
}

.ts-script-result {
    background: var(--card-bg);
    border: 2px solid var(--card-border);
    border-radius: 20px;
    padding: 2rem;
    margin-top: 2rem;
    backdrop-filter: blur(20px);
}

.ts-script-header {
    text-align: center;
    margin-bottom: 2rem;
    padding-bottom: 1rem;
    border-bottom: 2px solid var(--card-border);
}

.ts-script-header h3 {
    font-size: 1.8rem;
    font-weight: 800;
    margin: 0;
    color: var(--ink);
}

.ts-script-meta {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 1.5rem;
    margin-bottom: 2rem;
}

@media (max-width: 768px) {
    .ts-script-meta {
        grid-template-columns: 1fr;
    }
}

.ts-meta-item {
    background: rgba(30, 41, 59, 0.6);
    border: 1px solid var(--card-border);
    border-radius: 12px;
    padding: 1rem;
}

.ts-meta-item .label {
    display: block;
    font-size: 0.85rem;
    font-weight: 700;
    color: var(--accent);
    margin-bottom: 0.5rem;
    text-transform: uppercase;
}

.ts-meta-item .value {
    display: block;
    font-size: 1rem;
    color: var(--ink);
    line-height: 1.6;
}

.ts-script-tags,
.ts-script-keywords {
    margin-bottom: 1.5rem;
}

.ts-script-tags .badge,
.ts-script-keywords .badge {
    display: inline-block;
    background: linear-gradient(135deg, var(--primary-1), var(--accent));
    color: white;
    font-size: 0.85rem;
    font-weight: 800;
    padding: 0.4rem 1rem;
    border-radius: 999px;
    margin-bottom: 0.8rem;
}

.ts-script-tags .tags-list,
.ts-script-keywords .keywords-list {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
}

.ts-script-tags .tag {
    background: rgba(139, 92, 246, 0.2);
    color: var(--accent);
    padding: 0.4rem 0.8rem;
    border-radius: 8px;
    font-size: 0.9rem;
    font-weight: 600;
    border: 1px solid rgba(139, 92, 246, 0.3);
}

.ts-script-keywords .keywords-list {
    color: var(--muted);
    font-size: 0.95rem;
    line-height: 1.8;
}

.ts-script-sections {
    margin-top: 2rem;
}

.ts-script-sections h4 {
    font-size: 1.3rem;
    font-weight: 800;
    margin-bottom: 1.5rem;
    color: var(--ink);
}

.ts-script-section {
    background: rgba(30, 41, 59, 0.4);
    border: 1px solid var(--card-border);
    border-radius: 16px;
    padding: 1.5rem;
    margin-bottom: 1.5rem;
    transition: all 0.3s ease;
}

.ts-script-section:hover {
    border-color: var(--accent);
    transform: translateX(5px);
}

.ts-section-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1rem;
    padding-bottom: 0.8rem;
    border-bottom: 1px dashed var(--card-border);
}

.ts-section-header .name {
    font-size: 1.1rem;
    font-weight: 800;
    color: var(--accent);
}

.ts-section-header .time {
    background: linear-gradient(135deg, var(--primary-1), var(--accent));
    color: white;
    font-size: 0.85rem;
    font-weight: 800;
    padding: 0.3rem 0.8rem;
    border-radius: 999px;
}

.ts-section-content {
    color: var(--ink);
    font-size: 1rem;
    line-height: 1.9;
    white-space: pre-wrap;
    margin-bottom: 1rem;
}

.ts-section-notes {
    background: rgba(234, 179, 8, 0.1);
    border: 1px solid rgba(234, 179, 8, 0.3);
    border-radius: 8px;
    padding: 0.8rem 1rem;
    color: #EAB308;
    font-size: 0.9rem;
    font-style: italic;
}

.ts-seo-result {
    background: var(--card-bg);
    border: 2px solid var(--card-border);
    border-radius: 20px;
    padding: 2rem;
    margin-top: 2rem;
    backdrop-filter: blur(20px);
}

.ts-seo-header {
    text-align: center;
    margin-bottom: 2rem;
    padding-bottom: 1rem;
    border-bottom: 2px solid var(--card-border);
}

.ts-seo-header h3 {
    font-size: 1.8rem;
    font-weight: 800;
    margin: 0;
    color: var(--ink);
}

.ts-seo-section {
    margin-bottom: 2rem;
    padding: 1.5rem;
    background: rgba(30, 41, 59, 0.4);
    border: 1px solid var(--card-border);
    border-radius: 16px;
}

.ts-seo-section h4 {
    font-size: 1.2rem;
    font-weight: 800;
    margin: 0 0 1rem;
    color: var(--accent);
}

.ts-seo-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
    gap: 1rem;
}

.ts-seo-item {
    background: linear-gradient(135deg, rgba(139, 92, 246, 0.2), rgba(168, 85, 247, 0.2));
    border: 1px solid rgba(139, 92, 246, 0.3);
    border-radius: 12px;
    padding: 1rem;
    text-align: center;
    font-weight: 700;
    color: var(--accent);
    font-size: 0.95rem;
    transition: all 0.3s ease;
}

.ts-seo-item:hover {
    transform: translateY(-3px);
    box-shadow: 0 8px 20px rgba(139, 92, 246, 0.3);
}

.ts-seo-list {
    display: flex;
    flex-direction: column;
    gap: 0.8rem;
}

.ts-seo-list-item {
    background: rgba(30, 41, 59, 0.6);
    border: 1px solid var(--card-border);
    border-radius: 10px;
    padding: 1rem;
    font-size: 0.95rem;
    color: var(--ink);
    transition: all 0.3s ease;
}

.ts-seo-list-item.seo {
    border-left: 4px solid #22C55E;
}

.ts-seo-list-item.clickbait {
    border-left: 4px solid #F59E0B;
}

.ts-seo-list-item:hover {
    transform: translateX(5px);
    border-color: var(--accent);
}

.ts-seo-chapters {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
}

.ts-chapter-item {
    background: rgba(59, 130, 246, 0.1);
    border: 1px solid rgba(59, 130, 246, 0.3);
    border-radius: 8px;
    padding: 0.8rem 1rem;
    font-family: 'Courier New', monospace;
    font-size: 0.9rem;
    color: var(--ink);
    transition: all 0.3s ease;
}

.ts-chapter-item:hover {
    background: rgba(59, 130, 246, 0.2);
    border-color: #3B82F6;
}

.ts-footer {
    margin-top: 4rem;
    padding: 3rem 0;
    background: rgba(30, 41, 59, 0.4);
    border-top: 1px solid var(--card-border);
    backdrop-filter: blur(10px);
}

.ts-footer-content {
    max-width: 1200px;
    margin: 0 auto;
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 2rem;
    padding: 0 2rem;
}

@media (max-width: 768px) {
    .ts-footer-content {
        grid-template-columns: 1fr;
        text-align: center;
    }
}

.ts-footer-brand h3 {
    font-size: 1.5rem;
    font-weight: 800;
    margin: 0 0 0.5rem;
    color: var(--ink);
}

.ts-footer-brand p {
    color: var(--muted);
    font-size: 0.95rem;
    margin: 0;
}

.ts-footer-links {
    display: flex;
    gap: 2rem;
    align-items: center;
    justify-content: flex-start;
}

@media (max-width: 768px) {
    .ts-footer-links {
        justify-content: center;
        flex-wrap: wrap;
    }
}

.ts-footer-links a {
    color: var(--muted);
    text-decoration: none;
    font-size: 0.9rem;
    font-weight: 600;
    transition: color 0.3s ease;
}

.ts-footer-links a:hover {
    color: var(--accent);
}

.ts-footer-bottom {
    max-width: 1200px;
    margin: 2rem auto 0;
    padding: 1.5rem 2rem;
    border-top: 1px solid var(--card-border);
    text-align: center;
}

.ts-footer-bottom p {
    color: var(--muted);
    font-size: 0.85rem;
    margin: 0;
}

.ts-note {
    background: rgba(30, 41, 59, 0.6) !important;
    border: 2px dashed var(--card-border) !important;
    color: var(--muted) !important;
    backdrop-filter: blur(10px);
}

.ts-hero {
    text-align: center;
    margin-bottom: 2.5rem;
    padding: 2rem 0;
}

.ts-badge {
    display: inline-block;
    background: linear-gradient(135deg, var(--primary-1), var(--accent));
    color: #FFFFFF;
    font-weight: 800;
    font-size: 0.85rem;
    padding: 0.5rem 1.2rem;
    border-radius: 999px;
    margin-bottom: 1.2rem;
    box-shadow: 0 4px 20px rgba(139, 92, 246, 0.4);
    letter-spacing: 0.5px;
}

.ts-hero h1 {
    font-size: clamp(2rem, 5vw, 3.2rem);
    line-height: 1.3;
    margin: 0 0 1rem;
    font-weight: 800;
    text-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
}

.ts-hero p {
    font-size: clamp(1rem, 2.5vw, 1.15rem);
    color: var(--muted);
    max-width: 50ch;
    margin: 0 auto;
    line-height: 1.7;
}

.ts-proof {
    text-align: center;
    margin-bottom: 2rem;
    padding: 1rem;
    background: rgba(30, 41, 59, 0.4);
    border-radius: 12px;
    border: 1px solid var(--card-border);
    backdrop-filter: blur(10px);
}

.ts-proof .item {
    color: var(--muted);
    font-size: 0.9rem;
    font-weight: 600;
}

.ts-proof .sep {
    color: var(--accent);
    margin: 0 0.8rem;
    font-weight: 800;
}

.ts-section {
    display: flex;
    align-items: center;
    gap: 0.8rem;
    margin: 2.5rem 0 1.5rem;
    padding-bottom: 0.8rem;
    border-bottom: 2px solid var(--card-border);
}

.ts-section h2 {
    font-size: clamp(1.3rem, 3.5vw, 1.6rem);
    margin: 0;
    font-weight: 800;
}

.ts-section .count {
    background: linear-gradient(135deg, rgba(139, 92, 246, 0.2), rgba(168, 85, 247, 0.2));
    color: var(--accent);
    border-radius: 999px;
    padding: 0.3rem 0.8rem;
    font-size: 0.85rem;
    font-weight: 800;
    border: 1px solid rgba(139, 92, 246, 0.3);
}

.ts-section .mode {
    background: rgba(30, 41, 59, 0.6);
    color: var(--muted);
    border-radius: 8px;
    padding: 0.3rem 0.8rem;
    font-size: 0.8rem;
    font-weight: 700;
    border: 1px solid var(--card-border);
}

.ts-card {
    background: var(--card-bg);
    border-radius: 20px;
    border: 1px solid var(--card-border);
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
    padding: 24px;
    transition: all 0.3s ease;
    backdrop-filter: blur(20px);
}

.ts-card:hover {
    transform: translateY(-5px);
    box-shadow: 0 16px 48px rgba(0, 0, 0, 0.4), 0 0 30px rgba(139, 92, 246, 0.2);
    border-color: var(--accent);
}

.ts-card .num {
    width: 36px;
    height: 36px;
    border-radius: 10px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 800;
    font-size: 1rem;
    color: #FFFFFF;
    background: linear-gradient(135deg, var(--primary-1), var(--accent));
    box-shadow: 0 4px 15px rgba(139, 92, 246, 0.4);
}

.ts-card h3 {
    margin: 0 0 16px 0;
    font-size: 1.1rem;
    font-weight: 800;
    color: var(--ink);
    line-height: 1.5;
}

.ts-card .row {
    margin: 16px 0;
    padding-top: 16px;
    border-top: 1px dashed var(--card-border);
}

.ts-card .lbl {
    display: inline-block;
    font-size: 0.75rem;
    font-weight: 800;
    letter-spacing: 0.3px;
    padding: 0.4rem 0.8rem;
    border-radius: 8px;
    margin-bottom: 0.5rem;
}

.ts-card .lbl.hook {
    background: linear-gradient(135deg, rgba(236, 72, 153, 0.2), rgba(168, 85, 247, 0.2));
    color: var(--primary-2);
    border: 1px solid rgba(236, 72, 153, 0.3);
}

.ts-card .lbl.value {
    background: linear-gradient(135deg, rgba(34, 197, 94, 0.2), rgba(16, 185, 129, 0.2));
    color: #22C55E;
    border: 1px solid rgba(34, 197, 94, 0.3);
}

.ts-card .lbl.angle {
    background: linear-gradient(135deg, rgba(139, 92, 246, 0.2), rgba(168, 85, 247, 0.2));
    color: var(--accent);
    border: 1px solid rgba(139, 92, 246, 0.3);
}

.ts-card .lbl.outline-lbl {
    background: linear-gradient(135deg, rgba(59, 130, 246, 0.2), rgba(99, 102, 241, 0.2));
    color: #3B82F6;
    border: 1px solid rgba(59, 130, 246, 0.3);
}

.ts-card p {
    margin: 0;
    font-size: 0.94rem;
    line-height: 1.8;
    color: var(--muted);
}

.ts-card.improved {
    border: 2px solid var(--accent);
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3), 0 0 30px rgba(139, 92, 246, 0.3);
}

.ts-flag {
    display: inline-block;
    background: linear-gradient(135deg, var(--primary-1), var(--accent));
    color: #FFFFFF;
    font-size: 0.75rem;
    font-weight: 800;
    padding: 0.4rem 0.8rem;
    border-radius: 6px;
    margin-bottom: 0.8rem;
}

.ts-outline {
    margin: 0;
    padding-right: 20px;
    color: var(--ink);
    line-height: 1.9;
}

.ts-outline li {
    margin-bottom: 0.6rem;
}

.ts-eval-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 1.5rem;
    margin-top: 1.5rem;
}

@media (max-width: 768px) {
    .ts-eval-grid {
        grid-template-columns: 1fr;
    }
}

.ts-lang-bar {
    text-align: center;
    margin-bottom: 1rem;
}

.ts-lang-bar .label {
    display: inline-block;
    font-size: 0.85rem;
    font-weight: 700;
    color: var(--muted);
    margin-bottom: 0.5rem;
}

.ts-chips-label {
    text-align: center;
    color: var(--muted);
    font-size: 0.85rem;
    margin: 1rem 0 0.5rem;
    font-weight: 700;
}

.ts-input-container {
    background: rgba(30, 41, 59, 0.4);
    border: 1px solid var(--card-border);
    border-radius: 20px;
    padding: 2rem;
    margin-bottom: 1.5rem;
    backdrop-filter: blur(10px);
}

.ts-field-label {
    font-size: 0.85rem;
    font-weight: 700;
    color: var(--muted);
    margin-bottom: 0.5rem;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

.ts-copy-btn {
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    padding: 0.5rem 1rem;
    background: rgba(30, 41, 59, 0.6);
    border: 1px solid var(--card-border);
    border-radius: 8px;
    color: var(--muted);
    font-size: 0.85rem;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.3s ease;
    backdrop-filter: blur(10px);
}

.ts-copy-btn:hover {
    background: rgba(139, 92, 246, 0.2);
    border-color: var(--accent);
    color: var(--accent);
    transform: translateY(-2px);
}

[data-testid="column"] {
    padding: 0 0.5rem;
}

[data-testid="stMetricValue"] {
    color: var(--ink) !important;
    font-weight: 800;
}

[data-testid="stMetricDelta"] {
    color: #22C55E !important;
    font-weight: 700;
}

[data-testid="stProgress"] > div > div > div {
    background: linear-gradient(90deg, var(--primary-1), var(--accent)) !important;
}

[data-testid="stExpander"] {
    background: rgba(30, 41, 59, 0.6) !important;
    border: 1px solid var(--card-border) !important;
    border-radius: 12px;
}

[data-testid="stExpander"] > div {
    color: var(--ink) !important;
}

.stSuccess {
    background: rgba(34, 197, 94, 0.2) !important;
    border: 1px solid rgba(34, 197, 94, 0.4) !important;
    border-radius: 12px;
    color: #22C55E !important;
}

.stWarning {
    background: rgba(234, 179, 8, 0.2) !important;
    border: 1px solid rgba(234, 179, 8, 0.4) !important;
    border-radius: 12px;
    color: #EAB308 !important;
}

.stError {
    background: rgba(239, 68, 68, 0.2) !important;
    border: 1px solid rgba(239, 68, 68, 0.4) !important;
    border-radius: 12px;
    color: #EF4444 !important;
}

.stInfo {
    background: rgba(59, 130, 246, 0.2) !important;
    border: 1px solid rgba(59, 130, 246, 0.4) !important;
    border-radius: 12px;
    color: #3B82F6 !important;
}
</style>
"""

FONT_IMPORTS: dict[str, str] = {
    "ar": "@import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@400;500;700;800&display=swap');",
    "en": "@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;700;800&display=swap');",
    "fr": "@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;700;800&display=swap');",
}

FONT_STACKS: dict[str, str] = {
    "ar": "'Tajawal', 'Segoe UI', system-ui, -apple-system, sans-serif",
    "en": "'Inter', 'Segoe UI', system-ui, -apple-system, sans-serif",
    "fr": "'Inter', 'Segoe UI', system-ui, -apple-system, sans-serif",
}


def render_html(markup: str) -> None:
    """Renders a raw HTML block.

    The indentation is stripped on every line because markdown turns any block that starts
    with four or more spaces into a code block, and a blank line closes the surrounding
    HTML block. Left alone, an indented triple-quoted template is displayed as plain text
    instead of being rendered as markup. Leading whitespace between tags is insignificant
    here since the templates contain no ``<pre>`` or ``<textarea>`` elements.
    """
    payload = "\n".join(line.strip() for line in markup.splitlines() if line.strip())
    st.markdown(payload, unsafe_allow_html=True)


def inject_custom_header() -> None:
    """Injects a custom sticky header matching the requested brand and dark theme."""
    render_html(
        """
        <style>
        .ts-sticky-header {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            height: 62px;
            background: linear-gradient(135deg, #0F172A 0%, #1E293B 50%, #0F172A 100%);
            border-bottom: 1px solid rgba(139, 92, 246, 0.35);
            box-shadow: 0 4px 20px rgba(0,0,0,0.25);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 999999;
            backdrop-filter: blur(10px);
        }
        .ts-sticky-header h2 {
            margin: 0;
            font-size: 1.3rem;
            font-weight: 800;
            color: #F8FAFC;
            letter-spacing: 0.02em;
            background: linear-gradient(90deg, #8B5CF6, #A855F7, #EC4899);
            -webkit-background-clip: text;
            background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .stApp {
            padding-top: 72px !important;
        }
        header {
            display: none !important;
        }
        footer {
            display: none !important;
        }
        [data-testid="stToolbar"] {
            display: none !important;
        }
        [data-testid="stSidebar"] {
            display: none !important;
        }
        </style>
        <div class="ts-sticky-header">
            <h2>Mayki Digital Tools</h2>
        </div>
        """
    )


def inject_styles() -> None:
    """Injects the stylesheet, tuned to the active language (font + text direction)."""
    lang = current_lang()
    align = "right" if is_rtl() else "left"
    css = (
        CSS_TEMPLATE.replace("__FONT_IMPORT__", FONT_IMPORTS[lang])
        .replace("__FONT__", FONT_STACKS[lang])
        .replace("__DIRECTION__", text_direction())
        .replace("__ALIGN__", align)
    )
    render_html(css)

    render_html(
        """
        <style>
        .stApp {
            background: linear-gradient(135deg, #0F172A 0%, #1E293B 50%, #0F172A 100%) !important;
            background-attachment: fixed !important;
        }

        .stTextInput > div > div > input,
        .stSelectbox > div > div > select,
        .stTextArea > div > div > textarea {
            background: rgba(30, 41, 59, 0.8) !important;
            color: #F1F5F9 !important;
            border: 1px solid rgba(139, 92, 246, 0.3) !important;
            border-radius: 12px !important;
        }

        .stTextInput > div > div > input::placeholder,
        .stTextArea > div > div > textarea::placeholder {
            color: rgba(241, 245, 249, 0.6) !important;
        }

        .stButton > button {
            background: linear-gradient(135deg, #8B5CF6, #EC4899) !important;
            color: white !important;
        }
        </style>
        """
    )


# --------------------------------------------------------------------------------------
# Callbacks
# --------------------------------------------------------------------------------------


def _set_niche_from_pill() -> None:
    """Callback: fills the niche input with the localized word behind the selected chip."""
    chosen = st.session_state.get("niche_examples")
    if not chosen:
        return
    st.session_state["niche"] = option_formatter("niche", current_lang())(chosen)


def _regenerate_on_mode_change() -> None:
    """Callback: re-rolls the sample when platform, vibe, audience or language changes."""
    niche = st.session_state.get("ideas_niche", "")
    if not niche:
        return
    st.session_state["ideas"] = generate_ideas(
        niche,
        FREE_IDEAS_COUNT,
        variant=st.session_state.get("variant", 0),
        platform=st.session_state.get("platform", DEFAULT_PLATFORM),
        vibe=st.session_state.get("video_vibe", ""),
        audience=st.session_state.get("audience", ""),
        lang=st.session_state.get("lang", DEFAULT_LANGUAGE),
    )


# --------------------------------------------------------------------------------------
# Sections
# --------------------------------------------------------------------------------------


def render_language_switcher() -> None:
    """Language selector pinned at the top of the page; drives the whole interface."""
    render_html(
        f'<div class="ts-lang-bar"><span class="label">{html_escape(t("lang.label"))}</span></div>'
    )
    st.pills(
        t("lang.switch"),
        options=list(SUPPORTED_LANGUAGES),
        format_func=lambda code: LANGUAGE_LABELS[code],
        selection_mode="single",
        key="lang",
        label_visibility="collapsed",
        on_change=_regenerate_on_mode_change,
    )


def render_hero() -> None:
    render_html(
        f"""
        <div class="ts-hero">
            <div class="ts-badge">{html_escape(t("brand.badge"))}</div>
            <h1>{html_escape(t("hero.title_pre"))}<span class="accent">{html_escape(t("hero.title_accent"))}</span></h1>
            <p>{html_escape(t("hero.subtitle"))}</p>
        </div>
        """
    )


def render_social_proof() -> None:
    render_html(
        f"""
        <div class="ts-proof">
            <span class="item">{t("proof.generated", n=IDEAS_GENERATED_WEEK)}</span>
            <span class="sep">·</span>
            <span class="item">{t("proof.rating", score=RATING_VALUE, creators=RATING_COUNT)}</span>
        </div>
        """
    )


def render_idea_cards(ideas: list[Idea], niche: str, *, platform: str) -> None:
    lang = current_lang()
    core_label = html_escape(t("card.core"))
    why_label = html_escape(t("card.why"))
    plan_label = html_escape(t("card.plan"))
    tags_label = "Tags" if lang == "en" else "الهاشتاغات" if lang == "ar" else "Tags"
    keywords_label = "Keywords" if lang == "en" else "الكلمات المفتاحية" if lang == "ar" else "Mots-clés"

    offset = 0
    for row in chunked(ideas):
        cols = st.columns(len(row))
        for column, idea in zip(cols, row):
            with column:
                steps = "".join(f"<li>{html_escape(step)}</li>" for step in idea.steps)
                plan_html = f'<div class="row"><span class="badge">{plan_label}</span><ol>{steps}</ol></div>' if steps else ""

                tags_html = ""
                if idea.tags:
                    tags_list = " ".join(f"<span class='tag'>#{html_escape(tag)}</span>" for tag in idea.tags[:5])
                    tags_html = f'<div class="row"><span class="badge">{tags_label}</span><div class="tags">{tags_list}</div></div>'

                keywords_html = ""
                if idea.keywords:
                    keywords_list = ", ".join(html_escape(kw) for kw in idea.keywords[:3])
                    keywords_html = f'<div class="row"><span class="badge">{keywords_label}</span><div class="meta">{keywords_list}</div></div>'

                render_html(
                    f"""
                    <div class="premium-card">
                        <div class="badge">#{offset + 1} {html_escape(niche)}</div>
                        <h3>{html_escape(idea.title)}</h3>
                        <div class="row">
                            <span class="badge">{core_label}</span>
                            <div class="meta">{html_escape(idea.hook)}</div>
                        </div>
                        <div class="row">
                            <span class="badge">{why_label}</span>
                            <div class="meta">{html_escape(idea.value)}</div>
                        </div>
                        {plan_html}
                        {tags_html}
                        {keywords_html}
                    </div>
                    """
                )
                render_copy_button(idea_to_clipboard(idea))
            offset += 1


def render_paywall(context: str = "generate") -> None:
    generate = context == "generate"
    headline = "اشترك الآن واحصل على الوصول الكامل إلى جميع الأدوات" if generate else "ارتقِ حسابك للحصول على تقييمات متقدمة" 

    render_html(
        f"""
        <div class="ts-pricing-section">
            <div class="ts-pricing-header">
                <h2>{html_escape(headline)}</h2>
                <p>اختر الخطة المناسبة لاحتياجاتك</p>
            </div>

            <div class="ts-pricing-grid">
                <div class="ts-pricing-card free">
                    <div class="ts-pricing-badge">مجاني</div>
                    <h3>البداية</h3>
                    <div class="ts-price">$0 <span>/ شهر</span></div>
                    <ul class="ts-features">
                        <li>✓ 3 أفكار يومياً</li>
                        <li>✓ التوليد الأساسي</li>
                        <li>✓ دعم الفيديو الطويل</li>
                        <li>✓ هاشتاغات أساسية</li>
                        <li>✓ كلمات مفتاحية بسيطة</li>
                        <li class="disabled">✗ سكريبت مفصل</li>
                        <li class="disabled">✗ المقيّم الذكي</li>
                        <li class="disabled">✗ تحسين SEO متقدم</li>
                    </ul>
                    <a class="ts-pricing-btn" href="#" onclick="return false;">الخطة الحالية</a>
                </div>

                <div class="ts-pricing-card pro featured">
                    <div class="ts-pricing-badge popular">الأكثر شعبية</div>
                    <h3>الاحترافي</h3>
                    <div class="ts-price">$9.99 <span>/ شهر</span></div>
                    <ul class="ts-features">
                        <li>✓ 50 فكرة يومياً</li>
                        <li>✓ توليد متقدم مع AI</li>
                        <li>✓ دعم جميع المنصات</li>
                        <li>✓ كاتب السكريبت الذكي</li>
                        <li>✓ سكريبت مفصل بـ timestamps</li>
                        <li>✓ هاشتاغات متخصصة</li>
                        <li>✓ كلمات مفتاحية SEO</li>
                        <li>✓ المقيّم الذكي</li>
                        <li>✓ تحسين SEO متقدم</li>
                    </ul>
                    <a class="ts-pricing-btn primary" href="{CHECKOUT_URL}" target="_blank" rel="noopener">اشترك الآن</a>
                </div>

                <div class="ts-pricing-card enterprise">
                    <div class="ts-pricing-badge">مميز</div>
                    <h3>الذهبي</h3>
                    <div class="ts-price">$19.99 <span>/ شهر</span></div>
                    <ul class="ts-features">
                        <li>✓ أفكار غير محدودة</li>
                        <li>✓ توليد AI متقدم جداً</li>
                        <li>✓ سكريبتات غير محدودة</li>
                        <li>✓ دعم أولوية 24/7</li>
                        <li>✓ API Access كامل</li>
                        <li>✓ تقارير أداء مفصلة</li>
                        <li>✓ حساب مدير للفريق</li>
                        <li>✓ استشارات المحتوى</li>
                        <li>✓ تحليل المنافسين</li>
                    </ul>
                    <a class="ts-pricing-btn" href="{CHECKOUT_URL}" target="_blank" rel="noopener">اشترك الآن</a>
                </div>
            </div>

            <div class="ts-pricing-footer">
                <p>💡 يمكنك إلغاء الاشتراك في أي وقت • دفع آمن عبر Stripe • ضمان استرجاع 7 أيام</p>
            </div>
        </div>
        """
    )


def render_evaluation(result: Evaluation, original: str) -> None:
    render_html(
        f"""
        <div class="ts-section">
            <h2>{html_escape(t("eval.section"))}</h2>
            <span class="mode long">{html_escape(t("eval.before"))}</span>
            <span class="count">{html_escape(t("eval.analyzed"))}</span>
        </div>
        """
    )

    st.progress(result.score / 100, text=t("eval.progress", n=result.score))

    col_a, col_b = st.columns(2)
    col_a.metric(t("eval.original_score"), f"{result.score}%")
    col_b.metric(
        t("eval.improved_score"),
        f"{result.improved_score}%",
        f"+{result.improved_score - result.score}",
    )

    outline_items = "".join(f"<li>{html_escape(step)}</li>" for step in result.outline)
    render_html(
        f"""
        <div class="ts-eval-grid">
            <div class="ts-card">
                <div class="num">؟</div>
                <h3>{html_escape(t("card.why_needs_work"))}</h3>
                <div class="row">
                    <span class="lbl hook">{html_escape(t("card.analysis"))}</span>
                    <p>{html_escape(result.analysis)}</p>
                </div>
                <div class="row">
                    <span class="lbl value">{html_escape(t("card.original"))}</span>
                    <p>{html_escape(original)}</p>
                </div>
            </div>
            <div class="ts-card improved">
                <div class="ts-card-body">
                    <div>
                        <span class="ts-flag">{html_escape(t("card.improved"))}</span>
                    </div>
                    <h3>{html_escape(result.idea.title)}</h3>
                    <div class="row">
                        <span class="lbl hook">{html_escape(t("card.hook"))}</span>
                        <p>{html_escape(result.idea.hook)}</p>
                    </div>
                    <div class="row">
                        <span class="lbl angle">{html_escape(t("card.angle"))}</span>
                        <p>{html_escape(result.idea.value)}</p>
                    </div>
                    <div class="row">
                        <span class="lbl outline-lbl">{html_escape(t("card.outline"))}</span>
                        <ol class="ts-outline">{outline_items}</ol>
                    </div>
                </div>
            </div>
        </div>
        """
    )

    spacer, holder = st.columns(2)
    with holder:
        render_copy_button(idea_to_clipboard(result.idea))


def render_footer() -> None:
    arrow = ARROW_LEFT if is_rtl() else ARROW_RIGHT
    credit = "footer.copy" if groq_is_ready() else "footer.copy_fallback"
    render_html(
        f"""
        <div class="ts-footer">
            <div class="ts-footer-content">
                <div class="ts-footer-brand">
                    <h3>⚡ TubeSpark</h3>
                    <p>مُولّد أفكار يوتيوب الذكي</p>
                </div>
                <div class="ts-footer-links">
                    <a href="#" target="_blank">الشروط والأحكام</a>
                    <a href="#" target="_blank">سياسة الخصوصية</a>
                    <a href="#" target="_blank">الدعم الفني</a>
                </div>
            </div>
            <div class="ts-footer-bottom">
                <p>{html_escape(t(credit))}</p>
            </div>
        </div>
        """
    )


# --------------------------------------------------------------------------------------
# Tabs
# --------------------------------------------------------------------------------------


def render_generator_tab() -> None:
    lang = current_lang()

    render_html('<div class="ts-input-container">')

    render_html(
        f'<div class="ts-field-label">{html_escape(t("gen.niche_label"))}</div>'
    )
    niche = st.text_input(
        t("gen.niche_label"),
        key="niche",
        placeholder=t("gen.niche_placeholder"),
        label_visibility="collapsed",
    )

    col_platform, col_vibe, col_audience = st.columns([1, 1, 1], gap="medium")

    with col_platform:
        render_html(
            f'<div class="ts-field-label">{html_escape(t("gen.platform_label"))}</div>'
        )
        platform = st.selectbox(
            t("gen.platform_label"),
            options=list(PLATFORM_KEYS),
            format_func=option_formatter("platform", lang),
            key="platform",
            label_visibility="collapsed",
            on_change=_regenerate_on_mode_change,
        )

    with col_vibe:
        render_html(
            f'<div class="ts-field-label">{html_escape(t("gen.vibe_label"))}</div>'
        )
        vibe = st.selectbox(
            t("gen.vibe_label"),
            options=list(VIBE_KEYS),
            format_func=option_formatter("vibe", lang),
            key="video_vibe",
            label_visibility="collapsed",
            on_change=_regenerate_on_mode_change,
        )

    with col_audience:
        render_html(
            f'<div class="ts-field-label">{html_escape(t("gen.audience_label"))}</div>'
        )
        audience = st.selectbox(
            t("gen.audience_label"),
            options=list(AUDIENCE_KEYS),
            format_func=option_formatter("audience", lang),
            key="audience",
            label_visibility="collapsed",
            on_change=_regenerate_on_mode_change,
        )

    render_html('</div>')

    render_html('<div style="text-align: center; margin: 2rem 0;">')
    if st.button(t("gen.generate_btn"), type="primary", icon=":material/bolt:"):
        clean_niche = niche.strip()
        if not clean_niche:
            st.warning(t("gen.empty_niche_warning"))
        else:
            with st.spinner(t("ai.thinking")):
                st.session_state["ideas"] = generate_ideas(
                    clean_niche,
                    FREE_IDEAS_COUNT,
                    variant=st.session_state.get("variant", 0),
                    platform=platform,
                    vibe=vibe,
                    audience=audience,
                    lang=lang,
                )
            st.session_state["ideas_niche"] = clean_niche
            st.session_state["variant"] = 0
    st.markdown('</div>', unsafe_allow_html=True)

    render_ai_error()
    render_social_proof()

    render_html(
        f'<div class="ts-chips-label">{html_escape(t("gen.chips_label"))}</div>'
    )
    st.pills(
        t("gen.niche_pills"),
        options=list(NICHE_KEYS),
        format_func=option_formatter("niche", lang),
        selection_mode="single",
        key="niche_examples",
        label_visibility="collapsed",
        on_change=_set_niche_from_pill,
    )

    ideas: list[Idea] = st.session_state.get("ideas", [])

    if not ideas:
        render_html(
            f'<div class="ts-note">{html_escape(t("gen.empty_note"))}</div>'
        )
        return

    render_idea_cards(ideas, st.session_state["ideas_niche"], platform=platform)

    col_a, col_b = st.columns(2)
    if col_a.button(t("gen.more_btn"), width="stretch", icon=":material/casino:"):
        st.session_state["variant"] = st.session_state.get("variant", 0) + 1
        with st.spinner(t("ai.thinking")):
            st.session_state["ideas"] = generate_ideas(
                st.session_state["ideas_niche"],
                FREE_IDEAS_COUNT,
                st.session_state["variant"],
                platform=platform,
                vibe=vibe,
                audience=audience,
                lang=lang,
            )
    if col_b.button(t("gen.clear_btn"), width="stretch", icon=":material/delete_outline:"):
        st.session_state["ideas"] = []
        st.session_state["ideas_niche"] = ""

    render_ai_error()
    render_paywall("generate")


def render_evaluate_tab() -> None:
    render_html(
        f'<div class="ts-note" style="margin-top:.5rem">{html_escape(t("eval.note"))}</div>'
    )

    idea_text = st.text_area(
        t("eval.label"),
        key="idea_text",
        placeholder=t("eval.placeholder"),
        height=140,
        max_chars=MAX_IDEA_CHARS,
        label_visibility="collapsed",
    )

    if idea_text.strip() and len(idea_text) >= MAX_IDEA_CHARS:
        st.warning(
            t("eval.max_chars", n=MAX_IDEA_CHARS),
            icon=":material/content_cut:",
        )

    if st.button(
        t("eval.button"),
        type="primary",
        width="stretch",
        icon=":material/trending_up:",
    ):
        clean_idea = idea_text.strip()
        if not clean_idea:
            st.warning(t("eval.empty_warning"))
        else:
            with st.spinner(t("ai.analyzing")):
                st.session_state["evaluation"] = evaluate_idea(clean_idea, current_lang())
            st.session_state["evaluated_text"] = clean_idea

    render_ai_error()

    result: Evaluation | None = st.session_state.get("evaluation")

    if not result:
        return

    render_evaluation(result, st.session_state["evaluated_text"])
    render_paywall("evaluate")


def render_script_tab() -> None:
    lang = current_lang()
    script_title = "Smart script writer" if lang == "en" else "كاتب السكريبت الذكي" if lang == "ar" else "Rédacteur intelligent"
    script_subtitle = "script with full SEO" if lang == "en" else "سكريبت مفصل مع SEO كامل" if lang == "ar" else "script complet avec SEO"
    video_field = "Video field" if lang == "en" else "مجال الفيديو" if lang == "ar" else "Domaine de la vidéo"
    main_idea = "Core idea" if lang == "en" else "الفكرة الأساسية" if lang == "ar" else "Idée principale"
    platform_label = "Platform" if lang == "en" else "المنصة" if lang == "ar" else "Plateforme"
    vibe_label = "Tone" if lang == "en" else "النبرة" if lang == "ar" else "Ton"
    audience_label = "Audience" if lang == "en" else "الجمهور" if lang == "ar" else "Audience"
    duration_label = "Target video duration" if lang == "en" else "المدة المستهدفة للفيديو" if lang == "ar" else "Durée cible de la vidéo"
    duration_options = {
        "shorts": "Less than 1 minute (Shorts)" if lang == "en" else "أقل من دقيقة (Shorts)" if lang == "ar" else "Moins d'une minute (Shorts)",
        "3-5min": "3 to 5 minutes" if lang == "en" else "من 3 إلى 5 دقائق" if lang == "ar" else "3 à 5 minutes",
        "8-10min": "8 to 10 minutes" if lang == "en" else "من 8 إلى 10 دقائق" if lang == "ar" else "8 à 10 minutes",
        "15min+": "15+ minutes" if lang == "en" else "أكثر من 15 دقيقة" if lang == "ar" else "15+ minutes",
    }
    generate_button = "Generate full script" if lang == "en" else "⚡ توليد السكريبت المفصل" if lang == "ar" else "Générer le script complet"
    empty_warning = "Please enter the niche and idea." if lang == "en" else "الرجاء إدخال المجال والفكرة" if lang == "ar" else "Veuillez saisir le thème et l'idée."
    generate_spinner = "Writing the full script..." if lang == "en" else "جاري كتابة السكريبت المفصل..." if lang == "ar" else "Rédaction du script complet..."
    error_prefix = "Error: " if lang == "en" else "حدث خطأ: " if lang == "ar" else "Erreur : "

    render_html(
        f'<div class="ts-section"><h2>{html_escape(script_title)}</h2><span class="mode long">{html_escape(script_subtitle)}</span></div>'
    )

    render_html('<div class="ts-input-container">')

    render_html(f'<div class="ts-field-label">{html_escape(video_field)}</div>')
    niche = st.text_input(
        video_field,
        key="script_niche",
        placeholder="trading, gaming, cooking" if lang == "en" else "مثال: تداول، ألعاب، طبخ" if lang == "ar" else "ex. trading, gaming, cuisine",
        label_visibility="collapsed",
    )

    render_html(f'<div class="ts-field-label">{html_escape(main_idea)}</div>')
    script_idea = st.text_area(
        main_idea,
        key="script_idea",
        placeholder="Write your idea here..." if lang == "en" else "اكتب فكرتك هنا ليقوم AI بكتابة سكريبت مفصل..." if lang == "ar" else "Écris ton idée ici...",
        height=120,
        label_visibility="collapsed",
    )

    col_platform, col_vibe, col_audience = st.columns([1, 1, 1], gap="medium")

    with col_platform:
        render_html(f'<div class="ts-field-label">{html_escape(platform_label)}</div>')
        platform = st.selectbox(
            platform_label,
            options=list(PLATFORM_KEYS),
            format_func=option_formatter("platform", lang),
            key="script_platform",
            label_visibility="collapsed",
        )

    with col_vibe:
        render_html(f'<div class="ts-field-label">{html_escape(vibe_label)}</div>')
        vibe = st.selectbox(
            vibe_label,
            options=list(VIBE_KEYS),
            format_func=option_formatter("vibe", lang),
            key="script_vibe",
            label_visibility="collapsed",
        )

    with col_audience:
        render_html(f'<div class="ts-field-label">{html_escape(audience_label)}</div>')
        audience = st.selectbox(
            audience_label,
            options=list(AUDIENCE_KEYS),
            format_func=option_formatter("audience", lang),
            key="script_audience",
            label_visibility="collapsed",
        )

    render_html(f'<div class="ts-field-label">{html_escape(duration_label)}</div>')
    duration = st.selectbox(
        duration_label,
        options=list(duration_options.keys()),
        format_func=lambda x: duration_options[x],
        key="script_duration",
        label_visibility="collapsed",
    )

    render_html('</div>')

    render_html('<div style="text-align: center; margin: 2rem 0;">')
    if st.button(generate_button, type="primary", icon=":material/article:"):
        clean_niche = niche.strip()
        clean_idea = script_idea.strip()
        if not clean_niche or not clean_idea:
            st.warning(empty_warning)
        else:
            with st.spinner(generate_spinner):
                try:
                    script = _script_from_groq(
                        clean_niche,
                        clean_idea,
                        platform=platform,
                        vibe=vibe,
                        audience=audience,
                        lang=lang,
                        duration=duration,
                    )
                    st.session_state["script_result"] = script
                except Exception as e:
                    st.error(f"{error_prefix}{str(e)}")
    st.markdown('</div>', unsafe_allow_html=True)

    result = st.session_state.get("script_result")
    if result:
        render_html(
            f"""
            <div class="ts-script-result">
                <div class="ts-script-header">
                    <h3>📄 Script</h3>
                </div>
                <div class="ts-script-meta">
                    <div class="ts-meta-item">
                        <span class="label">Title</span>
                        <span class="value">{html_escape(result.title)}</span>
                    </div>
                    <div class="ts-meta-item">
                        <span class="label">Description</span>
                        <span class="value">{html_escape(result.description)}</span>
                    </div>
                </div>
                <div class="ts-script-tags">
                    <span class="badge">Tags</span>
                    <div class="tags-list">
                        {" ".join(f"<span class='tag'>#{html_escape(tag)}</span>" for tag in result.hashtags)}
                    </div>
                </div>
                <div class="ts-script-keywords">
                    <span class="badge">Keywords</span>
                    <div class="keywords-list">
                        {", ".join(html_escape(kw) for kw in result.keywords)}
                    </div>
                </div>
                <div class="ts-script-sections">
                    <h4>🎬 Script sections</h4>
            """
        )

        for section in result.sections:
            render_html(
                f"""
                <div class="ts-script-section">
                    <div class="ts-section-header">
                        <span class="name">{html_escape(section['name'])}</span>
                        <span class="time">{html_escape(section['time'])}</span>
                    </div>
                    <div class="ts-section-content">{html_escape(section['content'])}</div>
                    {f'<div class="ts-section-notes">📌 {html_escape(section["notes"])}</div>' if section['notes'] else ''}
                </div>
                """
            )

        render_html('</div></div>')

    render_paywall("generate")


def render_analyze_tab() -> None:
    lang = current_lang()
    render_html(
        f'<div class="ts-section"><h2>{html_escape(t("tab.analyzer"))}</h2><span class="mode long">{html_escape(t("eval.section"))}</span></div>'
    )
    idea_text = st.text_area(
        t("eval.label"),
        key="analyze_idea",
        placeholder=t("eval.placeholder"),
        height=140,
        label_visibility="collapsed",
    )
    if st.button(t("tab.analyzer"), type="primary", width="stretch"):
        clean_idea = idea_text.strip()
        if not clean_idea:
            st.warning(t("eval.empty_warning"))
        else:
            with st.spinner(t("ai.analyzing")):
                st.session_state["analyze_eval"] = evaluate_idea(clean_idea, lang)
                st.session_state["analyze_text"] = clean_idea
    result = st.session_state.get("analyze_eval")
    if result:
        render_evaluation(result, st.session_state.get("analyze_text", ""))
    render_paywall("evaluate")


def render_seo_tab() -> None:
    lang = current_lang()
    seo_title = "SEO optimizer" if lang == "en" else "محسن السيو الشامل" if lang == "ar" else "Optimiseur SEO"
    seo_subtitle = "full optimization for visibility and CTR" if lang == "en" else "تحسين كامل للظهور والنقر" if lang == "ar" else "optimisation complète pour visibilité et CTR"
    topic_label = "Video topic" if lang == "en" else "موضوع الفيديو" if lang == "ar" else "Sujet de la vidéo"
    niche_label = "Niche / category" if lang == "en" else "المجال / التصنيف" if lang == "ar" else "Niche / catégorie"
    generate_button = "Optimize SEO" if lang == "en" else "⚡ تحسين السيو بالكامل" if lang == "ar" else "Optimiser le SEO"
    missing_warning = "Please enter both topic and niche." if lang == "en" else "الرجاء إدخال الموضوع والمجال" if lang == "ar" else "Veuillez saisir le sujet et la niche."
    loading_text = "Optimizing SEO..." if lang == "en" else "جاري تحسين السيو..." if lang == "ar" else "Optimisation SEO..."
    error_prefix = "Error: " if lang == "en" else "حدث خطأ: " if lang == "ar" else "Erreur : "

    render_html(
        f'<div class="ts-section"><h2>{html_escape(seo_title)}</h2><span class="mode long">{html_escape(seo_subtitle)}</span></div>'
    )

    render_html('<div class="ts-input-container">')

    render_html(f'<div class="ts-field-label">{html_escape(topic_label)}</div>')
    video_topic = st.text_input(
        topic_label,
        key="seo_topic",
        placeholder="e.g. how to start trading crypto" if lang == "en" else "مثال: كيف تبدأ في تداول العملات الرقمية" if lang == "ar" else "ex. comment commencer le trading crypto",
        label_visibility="collapsed",
    )

    render_html(f'<div class="ts-field-label">{html_escape(niche_label)}</div>')
    video_niche = st.text_input(
        niche_label,
        key="seo_niche",
        placeholder="e.g. trading, education, tech" if lang == "en" else "مثال: تداول، تعليم، تكنولوجيا" if lang == "ar" else "ex. trading, éducation, tech",
        label_visibility="collapsed",
    )

    render_html('</div>')

    render_html('<div style="text-align: center; margin: 2rem 0;">')
    if st.button(generate_button, type="primary", icon=":material/trending_up:"):
        clean_topic = video_topic.strip()
        clean_niche = video_niche.strip()
        if not clean_topic or not clean_niche:
            st.warning(missing_warning)
        else:
            with st.spinner(loading_text):
                try:
                    seo_data = _seo_from_groq(
                        clean_topic,
                        clean_niche,
                        lang=lang,
                    )
                    st.session_state["seo_result"] = seo_data
                except Exception as e:
                    st.error(f"{error_prefix}{str(e)}")
    st.markdown('</div>', unsafe_allow_html=True)

    result = st.session_state.get("seo_result")
    if result:
        render_html(
            f"""
            <div class="ts-seo-result">
                <div class="ts-seo-header">
                    <h3>📊 SEO results</h3>
                </div>

                <div class="ts-seo-section">
                    <h4>🖼️ Thumbnail text</h4>
                    <div class="ts-seo-grid">
                        {" ".join(f"<div class='ts-seo-item'>{html_escape(txt)}</div>" for txt in result.thumbnail_texts)}
                    </div>
                </div>

                <div class="ts-seo-section">
                    <h4>🔍 SEO titles</h4>
                    <div class="ts-seo-list">
                        {"".join(f"<div class='ts-seo-list-item seo'>{html_escape(title)}</div>" for title in result.seo_titles)}
                    </div>
                </div>

                <div class="ts-seo-section">
                    <h4>⚡ Clickable titles</h4>
                    <div class="ts-seo-list">
                        {"".join(f"<div class='ts-seo-list-item clickbait'>{html_escape(title)}</div>" for title in result.clickbait_titles)}
                    </div>
                </div>

                <div class="ts-seo-section">
                    <h4>📑 Chapter list</h4>
                    <div class="ts-seo-chapters">
                        {"".join(f"<div class='ts-chapter-item'>{html_escape(chapter)}</div>" for chapter in result.chapters)}
                    </div>
                </div>
            </div>
            """
        )

    render_paywall("generate")


def main() -> None:
    init_session_state()
    st.set_page_config(
        page_title=t("page.title"),
        page_icon="⚡",
        layout="wide",
    )

    inject_custom_header()
    inject_styles()

    render_html('<div style="display: flex; justify-content: flex-end; margin-bottom: 1rem;">')
    render_language_switcher()
    st.markdown('</div>', unsafe_allow_html=True)

    render_hero()

    tab_ideas, tab_script, tab_analyze, tab_seo = st.tabs([
        "💡 Inspire me with new ideas",
        "📝 Script writer",
        "🎯 Smart analyzer",
        "🚀 SEO optimizer",
    ])

    with tab_ideas:
        render_generator_tab()
    with tab_script:
        render_script_tab()
    with tab_analyze:
        render_analyze_tab()
    with tab_seo:
        render_seo_tab()

    render_footer()


if __name__ == "__main__":
    main()
