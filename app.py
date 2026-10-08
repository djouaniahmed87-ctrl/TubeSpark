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
    seo_description: str = ""
    seo_tags: tuple[str, ...] = ()


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


def _idea_system_prompt(count: int, *, lang: str, short_form: bool, duration: str = "8-10min") -> str:
    rules = AI_LANGUAGE_RULES.get(lang, AI_LANGUAGE_RULES[DEFAULT_LANGUAGE])
    format_rule = (
        "Each idea must fit a video of 60 seconds or less, and its opening frame must already "
        "show the payoff."
        if short_form
        else f"Each idea is a standalone video matching the selected runtime of {duration}, with room for story, examples and a payoff at the end."
    )
    return f"""    You are a content strategist for
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
- Suggest relevant tags and keywords, but do not claim they are trending or have verified search volume.
- Never invent statistics, sources, current trends, search volumes, or performance outcomes.
- When current external evidence is needed, state that it is unavailable; no retrieval source is connected.

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
    duration: str = "8-10min",
    topic: str = "",
    content_type: str = "",
    content_format: str = "",
    additional_context: str = "",
) -> str:
    freshness = (
        "These angles were already suggested, so pick clearly different mechanisms."
        if variant
        else "Make the ideas use clearly different angles and different opening shots."
    )
    return f"""BRIEF
    - Topic: {topic or niche}
    - Channel / content niche: {niche}
- Platform: {option_label("platform", platform, lang)}
- Video format: {t_for(lang, "gen.mode_short") if is_short_form(platform) else t_for(lang, "gen.mode_long")}
- Target duration: {duration}
- Content type: {content_type or 'not specified'}
- Output format: {content_format or 'not specified'}
- Tone and angle: {option_label("vibe", vibe, lang)}
- Target audience: {option_label("audience", audience, lang)}
- Additional user context: {additional_context or 'none'}
- Number of ideas: {count}
- {freshness}

The brief is written in English; write the content in the language demanded by the system
prompt."""


def _evaluation_system_prompt(lang: str) -> str:
    rules = AI_LANGUAGE_RULES.get(lang, AI_LANGUAGE_RULES[DEFAULT_LANGUAGE])
    return f"""You are an expert viral content strategist. You review one video idea from a
creator and assess its creative and production qualities.

You always answer with valid JSON and nothing else: no markdown, no code fences, no
explanation before or after the object.

FIELDS
- "criteria": object with a 0-100 integer score for each of:
  hook_strength, specificity, curiosity, audience_fit, value_payoff, differentiation,
  platform_fit, production_feasibility. Judge only evidence present in the idea and context.
- "improved_criteria": the same eight scores, judging the rewritten idea under the same rubric.
- Do not force the rewritten idea to score higher. It may score lower, equal, or higher.
- "analysis": two or three short sentences of constructive criticism. Name the weakest part
-  and give a concrete fix. No encouragement padding and no invented flaws.
- "strengths": up to three strengths supported by the provided idea/context.
- "weaknesses": up to three specific gaps supported by the provided idea/context.
- "improvement_opportunity": one practical improvement, not a promise of performance.
- "outline": an array with exactly three short steps for the rewritten video. The third step
  must be the call to action.
- "improved": an object with "title" (one punchy line, max 90 characters), "hook" (the first
  two seconds, one or two sentences) and "value" (why it works).
- Never invent statistics, sources, trend claims, search-volume figures or research. If a
  claim cannot be supported by the provided input, omit it or label it as an inference.
- Write no filler: no emoji, no markdown.
- {rules}

OUTPUT
Reply with one valid JSON object using this shape. Criterion objects must contain all eight
named criteria, each with an integer from 0 to 100:

{{"criteria": {{"hook_strength": 0, "specificity": 0, "curiosity": 0, "audience_fit": 0,
"value_payoff": 0, "differentiation": 0, "platform_fit": 0, "production_feasibility": 0}},
"improved_criteria": {{"hook_strength": 0, "specificity": 0, "curiosity": 0,
"audience_fit": 0, "value_payoff": 0, "differentiation": 0, "platform_fit": 0,
"production_feasibility": 0}}, "analysis": "...", "strengths": ["..."],
"weaknesses": ["..."], "improvement_opportunity": "...",
"outline": ["...", "...", "..."], "improved": {{"title": "...", "hook": "...", "value": "..."}}}}"""


def _evaluation_user_prompt(text: str, context: str = "") -> str:
    context_section = f"\n\nEVALUATION CONTEXT\n{context}" if context.strip() else ""
    return f"""IDEA TO REVIEW
{text}
{context_section}

Evaluate the original and rewritten concept independently on all eight criteria. Derive no
claims from outside this supplied information. Return the JSON object described in the system
prompt."""


def _validated_evaluation_criteria(scores: dict[str, Any]) -> dict[str, int]:
    if not isinstance(scores, dict):
        raise GroqFormatError("evaluation criteria must be an object")
    validated: dict[str, int] = {}
    for criterion in EVALUATION_CRITERIA:
        value = scores.get(criterion)
        if isinstance(value, bool):
            raise GroqFormatError(f"invalid score for {criterion}")
        try:
            numeric = float(value)
        except (TypeError, ValueError) as exc:
            raise GroqFormatError(f"missing or invalid score for {criterion}") from exc
        if not 0 <= numeric <= 100:
            raise GroqFormatError(f"score out of range for {criterion}")
        validated[criterion] = int(round(numeric))
    return validated


def _weighted_evaluation_score(scores: dict[str, Any]) -> int:
    """Validates all criterion scores and computes the fixed-weight overall score."""
    validated = _validated_evaluation_criteria(scores)
    return int(round(sum(validated[key] * EVALUATION_WEIGHTS[key] for key in EVALUATION_CRITERIA)))


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

    return f"""    You are a professional YouTube scriptwriter focused on clear, engaging content. You write
    scripts that hook viewers, maintain
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
- "hashtag": an array of 10-15 relevant hashtag suggestions. Mix broad and niche-specific terms;
do not claim current trend status or proven engagement.
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
- Use a pattern interrupt (question or visual change) when it fits; do not invent a statistic.
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
- Tags must include the main keyword and relevant related terms; do not claim they are trending.
- Title must be click-worthy but not clickbait
- Keywords should match actual search intent

RULES
- Target duration: {duration}
- Write in conversational, engaging tone
- No filler words - every line must earn its place
- Use numbers only when supplied by the brief or clearly presented as a suggested creative example.
- Never invent sources, statistics, current trends, search volumes, or performance results.
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
    return f"""    You are a YouTube SEO assistant that creates editorial suggestions from the supplied brief.
    You do not have access to live search or performance data.

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
  * Use common editorial title formats (How-to, List, Guide, Tutorial, Comparison)
  * Have a strong value promise and credibility

- "clickbait_titles": an array of 5 curiosity-driven titles designed for higher CTR.
  They must:
  * Create strong curiosity gaps
  * Use emotional triggers (fear, surprise, curiosity, urgency)
  * Be 50-70 characters ideal (max 100)
  * Maintain credibility and not be misleading

- "seo_description": a polished YouTube description optimized for search and copy-ready.
  It must mention the main keyword in the first 2 lines and have a natural structure.

- "seo_tags": an array of 8-12 keyword tags tied to the main topic and niche.

- "chapters": an array of 5-8 timestamped chapter entries for the video description.
  Each entry should be a concise 2-6 word description of a major section with its
  approximate timestamp (e.g., "0:00 - Hook", "1:30 - Main Point").

RULES
- All text must be in the language demanded by the system prompt
- Thumbnail texts must be ultra-short (2-4 words max)
- SEO titles must include the main keyword naturally
- Clickbait titles must be curiosity-driven but not misleading
- SEO description must be ready to paste into YouTube
- Chapters should follow logical video progression
- Suggest relevant keyword phrases for the supplied topic and likely intent; do not claim search-volume or competition data without a connected source.
- Never invent sources, statistics, current trends, search volume, or verified performance results.
- {rules}

OUTPUT
Reply with one valid JSON object using exactly this shape:

{{
  "thumbnail_texts": ["...", "..."],
  "seo_titles": ["...", "..."],
  "clickbait_titles": ["...", "..."],
  "seo_description": "...",
  "seo_tags": ["...", "..."],
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

    seo_description = _model_text(data.get("seo_description"), 1200)
    raw_tags = data.get("seo_tags")
    seo_tags = (
        tuple(_model_text(tag, 50) for tag in raw_tags if _model_text(tag))[:12]
        if isinstance(raw_tags, list)
        else ()
    )

    return SEOData(
        thumbnail_texts=thumbnail_texts,
        seo_titles=seo_titles,
        clickbait_titles=clickbait_titles,
        chapters=chapters,
        seo_description=seo_description,
        seo_tags=seo_tags,
    )


def _visual_direction_from_groq(
    topic: str,
    *,
    platform: str,
    audience: str,
    direction: str,
    lang: str,
) -> tuple[str, str]:
    """Create a visual brief when available, otherwise return a clearly labeled template."""
    rules = AI_LANGUAGE_RULES.get(lang, AI_LANGUAGE_RULES[DEFAULT_LANGUAGE])
    if _configure_groq() is not None:
        fallback = {
            "en": f"Visual concept for {platform}: {topic}. Direction: {direction or 'Use one clear focal point and readable text.'} This is a prompt only; no image was generated.",
            "ar": f"تصور مرئي لمنصة {platform} حول {topic}. التوجيه: {direction or 'استخدم عنصرًا بصريًا محوريًا ونصًا واضحًا.'} هذا توجيه نصي فقط ولم تُنشأ صورة.",
            "fr": f"Concept visuel pour {platform} : {topic}. Direction : {direction or 'Un point focal clair et un texte lisible.'} Il s'agit uniquement d'un prompt ; aucune image n'a été générée.",
        }[lang]
        return fallback, "local_fallback"
    prompt = f"""You create a truthful, production-ready thumbnail / visual direction as a creative prompt, not an image.
Return only JSON: {{"direction": "..."}}.
Use only the provided topic, platform, audience and user direction. Do not invent factual details, statistics, trends, brands, or promise performance. Do not claim an image was generated. Write every field in the language required here: {rules}"""
    user = json.dumps({
        "topic": topic,
        "platform": platform,
        "audience": audience,
        "user_direction": direction,
    }, ensure_ascii=False)
    result = _groq_json(prompt, user, temperature=0.5)
    visual_direction = _model_text(result.get("direction"), 1500)
    if not visual_direction:
        raise GroqFormatError("visual generator returned no direction")
    return visual_direction, "model"


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
    duration: str = "8-10min",
    topic: str = "",
    content_type: str = "",
    content_format: str = "",
    additional_context: str = "",
) -> list[Idea]:
    count = max(1, min(count, 10))
    data = _groq_json(
        _idea_system_prompt(count, lang=lang, short_form=is_short_form(platform), duration=duration),
        _idea_user_prompt(
            niche,
            count,
            platform=platform,
            vibe=vibe,
            audience=audience,
            lang=lang,
            variant=variant,
            duration=duration,
            topic=topic,
            content_type=content_type,
            content_format=content_format,
            additional_context=additional_context,
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


def _evaluation_from_groq(text: str, lang: str, context: str = "") -> Evaluation:
    data = _groq_json(_evaluation_system_prompt(lang), _evaluation_user_prompt(text, context), temperature=0.6)

    analysis = _model_text(data.get("analysis"), 600)
    if not analysis:
        raise GroqFormatError("no 'analysis' in the answer")

    criteria = _validated_evaluation_criteria(data.get("criteria"))
    improved_criteria = _validated_evaluation_criteria(data.get("improved_criteria"))
    raw_outline = data.get("outline")
    if not isinstance(raw_outline, list) or len(raw_outline) != 3:
        raise GroqFormatError("evaluation outline must contain exactly three steps")
    outline = [_model_text(step, 220) for step in raw_outline if _model_text(step)]
    improved = data.get("improved")
    if not isinstance(improved, dict):
        raise GroqFormatError("no improved idea object in the answer")
    title = _model_text(improved.get("title"), 140)
    hook = _model_text(improved.get("hook"), 400)
    value = _model_text(improved.get("value"), 400)
    if not all((title, hook, value)) or len(outline) != 3 or any(not step for step in outline):
        raise GroqFormatError("incomplete improved idea or outline")

    return Evaluation(
        score=_weighted_evaluation_score(criteria),
        improved_score=_weighted_evaluation_score(improved_criteria),
        analysis=analysis,
        idea=Idea(title, hook, value),
        outline=tuple(outline),
        criterion_scores=criteria,
        improved_criterion_scores=improved_criteria,
        strengths=tuple(_model_text(item, 220) for item in data.get("strengths", [])[:3] if _model_text(item))
        if isinstance(data.get("strengths"), list) else (),
        weaknesses=tuple(_model_text(item, 220) for item in data.get("weaknesses", [])[:3] if _model_text(item))
        if isinstance(data.get("weaknesses"), list) else (),
        improvement_opportunity=_model_text(data.get("improvement_opportunity"), 300),
        score_basis="model",
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
    duration: str = "8-10min",
    topic: str = "",
    content_type: str = "",
    content_format: str = "",
    additional_context: str = "",
) -> list[Idea]:
    """Clearly deterministic offline concepts; no fabricated trend or performance claims."""
    titles = {
        "en": (
            "A practical exploration of {topic}",
            "How to test one approach to {topic}",
            "A beginner-friendly walkthrough of {topic}",
            "Questions to ask before trying {topic}",
        ),
        "ar": (
            "استكشاف عملي لموضوع {topic}",
            "كيف تختبر طريقة واحدة في {topic}",
            "شرح مبسط للمبتدئين عن {topic}",
            "أسئلة ينبغي طرحها قبل تجربة {topic}",
        ),
        "fr": (
            "Explorer {topic} de façon pratique",
            "Tester une approche de {topic}",
            "Un guide accessible de {topic}",
            "Questions à se poser avant d'essayer {topic}",
        ),
    }[lang if lang in SUPPORTED_LANGUAGES else DEFAULT_LANGUAGE]
    hooks = {
        "en": "State one clear question about the topic, then show the steps used to explore it.",
        "ar": "اطرح سؤالًا واضحًا عن الموضوع، ثم اعرض الخطوات المستخدمة لاستكشافه.",
        "fr": "Pose une question claire sur le sujet, puis montre les étapes de son exploration.",
    }[lang if lang in SUPPORTED_LANGUAGES else DEFAULT_LANGUAGE]
    values = {
        "en": "A structured, practical exploration; no outcome or performance result is assumed.",
        "ar": "استكشاف عملي منظم دون افتراض نتيجة أو أداء مسبق.",
        "fr": "Une exploration pratique et structurée, sans supposer de résultat ni de performance.",
    }[lang if lang in SUPPORTED_LANGUAGES else DEFAULT_LANGUAGE]
    localized_platform = option_label("platform", platform, lang)
    localized_vibe = option_label("vibe", vibe, lang) if vibe else ""
    localized_audience = option_label("audience", audience, lang) if audience else ""
    count = max(1, min(count, len(titles)))
    start = variant % len(titles)
    selected = [titles[(start + index) % len(titles)] for index in range(count)]
    ideas = []
    idea_topic = topic.strip() or niche
    for template in selected:
        title = template.format(topic=idea_topic)
        context = " · ".join(part for part in (
            localized_platform,
            localized_audience,
            duration,
            f"Channel niche: {niche}" if niche and niche != idea_topic else "",
            content_type,
            content_format,
            additional_context,
            localized_vibe,
        ) if part)
        ideas.append(Idea(
            title=title,
            hook=hooks,
            value=f"{values} {context}".strip(),
            steps=(
                "State the question and define the scope.",
                "Show the process or comparison using supplied material.",
                "Summarize what was observed and invite a grounded follow-up.",
            ) if lang == "en" else (
                "حدّد السؤال ونطاقه.",
                "اعرض العملية أو المقارنة اعتمادًا على المواد المتاحة.",
                "لخّص ما تمت ملاحظته واقترح متابعة مستندة إلى المعطيات.",
            ) if lang == "ar" else (
                "Pose la question et définis le périmètre.",
                "Montre la démarche ou la comparaison à partir des éléments fournis.",
                "Résume les observations et propose une suite fondée sur les données disponibles.",
            ),
        ))
    return ideas


def generate_ideas(
    niche: str,
    count: int = FREE_IDEAS_COUNT,
    variant: int = 0,
    *,
    platform: str = DEFAULT_PLATFORM,
    vibe: str = "",
    audience: str = "",
    lang: str | None = None,
    duration: str = "8-10min",
    topic: str = "",
    content_type: str = "",
    content_format: str = "",
    additional_context: str = "",
) -> list[Idea]:
    """Generates ideas with Groq, falling back to the built-in pools when it is down.

    Variables driving the prompt: niche, platform, output language, vibe, target audience,
    the re-roll `variant`, and the selected video `duration`.
    """
    clean_niche = niche.strip()
    if not clean_niche:
        return []
    clean_topic = topic.strip() or clean_niche

    lang = lang if lang in SUPPORTED_LANGUAGES else current_lang()
    normalized_duration = normalize_duration_value(duration)

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
                duration=normalized_duration,
                topic=clean_topic,
                content_type=content_type,
                content_format=content_format,
                additional_context=additional_context,
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
        duration=normalized_duration,
        topic=clean_topic,
        content_type=content_type,
        content_format=content_format,
        additional_context=additional_context,
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
    criterion_scores: dict[str, int] | None = None
    improved_criterion_scores: dict[str, int] | None = None
    strengths: tuple[str, ...] = ()
    weaknesses: tuple[str, ...] = ()
    improvement_opportunity: str = ""
    score_basis: str = "model"


EVALUATION_CRITERIA: tuple[str, ...] = (
    "hook_strength",
    "specificity",
    "curiosity",
    "audience_fit",
    "value_payoff",
    "differentiation",
    "platform_fit",
    "production_feasibility",
)
EVALUATION_WEIGHTS: dict[str, float] = {
    "hook_strength": 0.16,
    "specificity": 0.14,
    "curiosity": 0.14,
    "audience_fit": 0.14,
    "value_payoff": 0.14,
    "differentiation": 0.10,
    "platform_fit": 0.10,
    "production_feasibility": 0.08,
}


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


def _offline_criterion_scores(text: str, context: str = "") -> dict[str, int]:
    """Transparent local rubric estimate; this is not model reasoning or audience research."""
    clean = " ".join(text.lower().split())
    context_lower = " ".join(context.lower().split())
    has_question = any(mark in clean for mark in ("?", "؟"))
    has_detail = any(char.isdigit() for char in clean) or len(clean.split()) >= 8
    has_audience = any(term in clean + " " + context_lower for term in (
        "audience", "for ", "beginners", "students", "creators", "pour ", "للجمهور", "للمبتدئين", "للطلاب"
    ))
    has_payoff = any(term in clean for term in (
        "learn", "build", "make", "compare", "test", "how to", "learn", "apprendre", "tester", "compare",
        "تعلم", "اصنع", "قارن", "جرّب", "جرب"
    ))
    has_contrast = any(term in clean for term in (" vs ", "instead", "before", "after", "versus", "avant", "après", "بدل", "قبل", "بعد"))
    platform = context_lower
    has_platform = any(term in platform for term in ("youtube", "tiktok", "reels", "shorts", "podcast", "blog"))
    has_action = any(term in clean for term in ("test", "build", "make", "show", "compare", "try", "tester", "montrer", "اصنع", "اختبر", "اعرض"))
    return {
        "hook_strength": 70 if has_question else 52 if len(clean.split()) >= 6 else 38,
        "specificity": 68 if has_detail else 40,
        "curiosity": 70 if has_question else 45,
        "audience_fit": 68 if has_audience else 42,
        "value_payoff": 68 if has_payoff else 42,
        "differentiation": 68 if has_contrast else 43,
        "platform_fit": 68 if has_platform else 50,
        "production_feasibility": 68 if has_action else 52,
    }


def _template_evaluation(text: str, lang: str, context: str = "") -> Evaluation:
    """Offline rubric fallback, explicitly presented as a heuristic estimate."""
    clean = " ".join(text.split())
    core = _idea_core(clean)
    localized = {
        "en": {
            "title": f"A practical test of {core}",
            "hook": f"Show the starting point, test one specific change to {core}, and record what happens.",
            "value": f"Give viewers a repeatable way to assess {core}, without promising a particular result.",
            "analysis": "Offline heuristic estimate only; no AI reasoning, audience data, or external research was available.",
            "outline": ("State the question and starting point.", "Demonstrate one concrete test and show the observed result.", "Summarize the limitation and invite viewers to share their own test."),
        },
        "ar": {
            "title": f"اختبار عملي لـ {core}",
            "hook": f"اعرض نقطة البداية، واختبر تغييرًا محددًا متعلقًا بـ{core}، ثم وثّق ما يحدث.",
            "value": f"قدّم للمشاهد طريقة قابلة للتكرار لفحص {core} دون ضمان نتيجة مسبقة.",
            "analysis": "هذا تقدير إرشادي محلي فقط؛ لم يتوفر استدلال من نموذج أو بيانات جمهور أو بحث خارجي.",
            "outline": ("حدّد السؤال ونقطة البداية.", "نفّذ اختبارًا محددًا واعرض النتيجة المرصودة.", "لخّص حدود الاختبار وادعُ المشاهد لمشاركة تجربته."),
        },
        "fr": {
            "title": f"Un test pratique de {core}",
            "hook": f"Montre le point de départ, teste un changement précis lié à {core} et observe le résultat.",
            "value": f"Propose aux spectateurs une façon reproductible d'évaluer {core}, sans promettre de résultat.",
            "analysis": "Estimation heuristique locale uniquement : aucun raisonnement IA, donnée d'audience ou recherche externe n'était disponible.",
            "outline": ("Pose la question et montre le point de départ.", "Réalise un test concret et présente le résultat observé.", "Résume les limites du test et invite le public à partager son expérience."),
        },
    }[lang if lang in SUPPORTED_LANGUAGES else DEFAULT_LANGUAGE]
    criteria = _offline_criterion_scores(clean, context)
    improved = Idea(localized["title"], localized["hook"], localized["value"])
    improved_criteria = _offline_criterion_scores(" ".join((improved.title, improved.hook, improved.value)), context)
    weak = sorted(criteria, key=criteria.get)[:3]
    strong = sorted(criteria, key=criteria.get, reverse=True)[:3]
    criterion_labels = {
        "hook_strength": "hook", "specificity": "specificity", "curiosity": "curiosity",
        "audience_fit": "audience fit", "value_payoff": "value/payoff",
        "differentiation": "differentiation", "platform_fit": "platform fit",
        "production_feasibility": "production feasibility",
    }
    analysis = localized["analysis"]
    if context.strip():
        analysis += f"\n\n{t_for(lang, 'eval.context_considered')}: {context.strip()}"
    return Evaluation(
        score=_weighted_evaluation_score(criteria),
        improved_score=_weighted_evaluation_score(improved_criteria),
        analysis=analysis,
        idea=improved,
        outline=localized["outline"],
        criterion_scores=criteria,
        improved_criterion_scores=improved_criteria,
        strengths=tuple(f"{criterion_labels[key]} signal in the supplied text" for key in strong if criteria[key] >= 60),
        weaknesses=tuple(f"{criterion_labels[key]} is not explicit in the supplied text" for key in weak if criteria[key] < 60),
        improvement_opportunity=localized["value"],
        score_basis="heuristic",
    )


def evaluate_idea(text: str, lang: str | None = None, *, context: str = "") -> Evaluation:
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
            result = _evaluation_from_groq(clean, lang, context)
        except Exception as exc:
            _set_ai_error(_classify_ai_error(exc), _ai_error_detail(exc))
        else:
            _clear_ai_error()
            return result
    else:
        _set_ai_error(problem)

    return _template_evaluation(clean, lang, context)


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


def _artifact_key(value: str) -> str:
    clean = re.sub(r"[^a-zA-Z0-9_-]+", "_", value or "artifact").strip("_")
    return clean.lower() or "artifact"


def _selected_meta_html(selected: bool, label: str = "Selected") -> str:
    if not selected:
        return ""
    return (
        '<span class="badge" style="background: rgba(16,185,129,0.12); '
        'color: #A7F3D0; border-color: rgba(52,211,153,0.28);">'
        f'{html_escape(label)}</span>'
    )


def _render_chip_row(values: tuple[str, ...], *, limit: int = 8) -> str:
    if not values:
        return ""
    chips = " ".join(f"<span class='tag'>{html_escape(value)}</span>" for value in values[:limit])
    return f'<div class="tags">{chips}</div>'


def _script_idea_seed(title: str, project_idea: str, topic: str) -> str:
    return title.strip() or project_idea.strip() or topic.strip()


def _seo_generation_inputs(
    *,
    title: str,
    description: str,
    niche: str,
    primary_keyword: str,
    audience: str,
    platform: str = "",
) -> tuple[str, str]:
    topic = title.strip() or niche.strip() or primary_keyword.strip() or description.strip() or "topic"
    generation_context = [
        f"Target platform: {platform.strip()}" if platform.strip() else "",
        f"Niche / category: {niche.strip()}" if niche.strip() else "",
        f"Existing description: {description.strip()}" if description.strip() else "",
        f"Primary keyword: {primary_keyword.strip()}" if primary_keyword.strip() else "",
        f"Target audience: {audience.strip()}" if audience.strip() else "",
    ]
    return topic, "\n".join(part for part in generation_context if part) or "content"


def _evaluation_generation_context(
    *,
    platform: str,
    audience: str,
    niche: str,
    content_type: str,
    title: str,
) -> str:
    fields = (
        ("Platform", platform),
        ("Audience", audience),
        ("Niche", niche),
        ("Content type", content_type),
        ("Requested title", title),
    )
    return "\n".join(f"{label}: {value.strip()}" for label, value in fields if value.strip())


def _render_seo_title_suggestions(data: SEOData) -> None:
    for heading, titles in (
        ("SEO title suggestions", data.seo_titles),
        ("Curiosity-driven title suggestions", data.clickbait_titles),
    ):
        if titles:
            st.markdown(f"#### {heading}")
            st.markdown("\n".join(f"- {html_escape(title)}" for title in titles))


def _render_idea_result(
    ideas: list[Idea],
    niche: str,
    *,
    platform: str,
    details: dict[str, str] | None = None,
) -> None:
    with st.container(border=True):
        st.markdown(f"### {t('result.ideas')}")
        if details:
            visible_details = [
                f"{t(f'result.{key}')}: {LANGUAGE_LABELS.get(value, value) if key == 'language' else value}"
                for key, value in details.items()
                if value and key in {"platform", "audience", "duration", "content_type", "language"}
            ]
            if visible_details:
                st.caption(" · ".join(visible_details))
        render_idea_cards(ideas, niche, platform=platform)


def _render_script_result(result: Script, *, details: dict[str, str] | None = None) -> None:
    with st.container(border=True):
        st.markdown(f"### {t('result.script')}")
        st.markdown(f"#### {html_escape(result.title)}", unsafe_allow_html=True)
        if details:
            visible_details = [
                f"{t(f'result.{key}')}: {value}"
                for key, value in details.items()
                if value and key in {"platform", "audience", "duration", "content_type", "style", "language"}
            ]
            if visible_details:
                st.caption(" · ".join(visible_details))

        if result.description:
            render_artifact_card(t("result.description"), result.description, badge=t("result.description"))
        if result.sections:
            st.markdown(f"#### {t('result.sections')}")
            for idx, section in enumerate(result.sections, start=1):
                section_name = section.get("name") or f"Section {idx}"
                content = section.get("content") or ""
                notes = section.get("notes") or ""
                body = "\n\n".join(part for part in (content, notes) if part)
                render_artifact_card(
                    section_name,
                    body,
                    badge=section.get("time") or f"#{idx}",
                    meta=t("result.sections"),
                )
        if result.keywords:
            st.markdown(f"#### {t('result.keywords')}")
            st.markdown(_render_chip_row(result.keywords, limit=8), unsafe_allow_html=True)
        if result.hashtags:
            st.markdown(f"#### {t('result.hashtags')}")
            st.markdown(_render_chip_row(result.hashtags, limit=15), unsafe_allow_html=True)


def _render_seo_result(data: SEOData, *, details: dict[str, str] | None = None) -> None:
    with st.container(border=True):
        st.markdown(f"### {t('result.seo')}")
        if details:
            labels = (
                ("topic", t("result.topic")),
                ("niche", t("result.niche")),
                ("platform", t("result.platform")),
            )
            visible_details = [f"{label}: {details[key]}" for key, label in labels if details.get(key)]
            if visible_details:
                st.caption(" · ".join(visible_details))
        if data.seo_description:
            render_artifact_card(
                t("result.description"),
                data.seo_description,
                badge=t("result.description"),
                meta="SEO",
            )
        _render_seo_title_suggestions(data)
        if data.seo_tags:
            st.markdown(f"#### {t('result.keywords')}")
            st.markdown(_render_chip_row(data.seo_tags, limit=12), unsafe_allow_html=True)
        if data.chapters:
            st.markdown(f"#### {t('result.chapters')}")
            for idx, chapter in enumerate(data.chapters, start=1):
                render_artifact_card(
                    f"#{idx}",
                    chapter,
                    badge=t("result.chapters"),
                    meta=t("result.chapters"),
                )
        if data.thumbnail_texts:
            st.markdown(f"#### {t('result.thumbnail_texts')}")
            st.markdown(_render_chip_row(data.thumbnail_texts, limit=8), unsafe_allow_html=True)


def _render_visual_result(title: str, body: str, *, meta: str = "") -> None:
    if not body:
        return
    with st.container(border=True):
        st.markdown(f"### {t('result.visual')}")
        render_artifact_card(title, body, badge=title, meta=meta)


def render_artifact_card(title: str, body: str, *, badge: str = "Artifact", meta: str = "") -> None:
    """Shared visual wrapper for AI-generated output so each result feels like a product artifact."""
    if not body:
        return
    meta_html = f'<span class="artifact-meta">{html_escape(meta)}</span>' if meta else ""
    render_html(
        f"""
        <div class="artifact-shell">
            <div class="artifact-header">
                <span class="artifact-badge">{html_escape(badge)}</span>
                {meta_html}
            </div>
            <div class="artifact-body">{html_escape(body)}</div>
        </div>
        """,
    )


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
    --bg: #090D16;
    --surface-1: #121A29;
    --surface-2: #192438;
    --surface-3: #202D43;
    --surface-input: #1B2940;

    --text-primary: #F5F7FB;
    --text-secondary: #CBD5E1;
    --text-muted: #94A3B8;
    --text-subtle: #64748B;

    --primary: #8B5CF6;
    --primary-hover: #A78BFA;
    --primary-soft: rgba(139, 92, 246, 0.10);
    --primary-border: rgba(139, 92, 246, 0.24);
    --primary-glow: rgba(139, 92, 246, 0.12);

    --success: #22C55E;
    --warning: #F59E0B;
    --error: #F43F5E;
    --info: #38BDF8;

    --border-subtle: rgba(148, 163, 184, 0.10);
    --border-default: rgba(148, 163, 184, 0.18);
    --border-strong: rgba(139, 92, 246, 0.28);

    --primary-1: #8B5CF6;
    --primary-2: #EC4899;
    --accent: #A855F7;
    --primary-gradient: linear-gradient(135deg, var(--primary), var(--accent));
    --bg-dark: var(--bg);
    --bg-gradient: linear-gradient(180deg, #090D16 0%, #101827 100%);
    --surface: var(--surface-1);
    --surface-soft: var(--surface-2);
    --panel: var(--surface-1);
    --panel-soft: var(--surface-2);
    --border: var(--border-default);
    --ink: var(--text-primary);
    --muted: var(--text-muted);
    --accent-soft: var(--primary-soft);
    --card-bg: var(--surface-1);
    --card-border: var(--border-default);
    --glow: var(--primary-glow);
    --shadow: rgba(2, 6, 23, 0.42);
}

* {
    font-family: __FONT__;
    box-sizing: border-box;
}

html, body, .stApp {
    direction: __DIRECTION__;
    text-align: __ALIGN__;
    background: var(--bg-gradient);
    background-attachment: fixed;
    min-height: 100vh;
    color: var(--text-primary);
}

h1, h2, h3, h4, h5, h6 {
    color: var(--text-primary) !important;
}

label, [data-testid="stBaseWidgetLabel"], .stMarkdown p, .stCaption {
    color: var(--text-secondary) !important;
    font-weight: 600 !important;
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
    background: var(--surface-input) !important;
    color: var(--text-primary) !important;
    border: 1px solid rgba(167, 139, 250, 0.24) !important;
    border-radius: 14px !important;
    font-size: 0.98rem;
    line-height: 1.6;
    box-shadow: none !important;
    transition: border-color 0.2s ease, background-color 0.2s ease, box-shadow 0.2s ease;
}

div[data-testid="stSelectbox"] [role="group"],
div[data-testid="stMultiSelect"] [role="group"] {
    background: var(--surface-input) !important;
    color: var(--text-primary) !important;
    border: 1px solid rgba(167, 139, 250, 0.24) !important;
    border-radius: 14px !important;
    box-shadow: none !important;
    transition: border-color 0.2s ease, background-color 0.2s ease, box-shadow 0.2s ease;
}

div[data-testid="stSelectbox"] [role="group"]:focus-within,
div[data-testid="stMultiSelect"] [role="group"]:focus-within {
    background: var(--surface-2) !important;
    border-color: rgba(167, 139, 250, 0.58) !important;
    box-shadow: 0 0 0 2px rgba(139, 92, 246, 0.12), 0 0 14px rgba(139, 92, 246, 0.08) !important;
}

div[data-testid="stSelectbox"] [role="group"]:hover,
div[data-testid="stMultiSelect"] [role="group"]:hover {
    border-color: rgba(167, 139, 250, 0.38) !important;
}

div[data-testid="stSelectbox"] [role="group"] input,
div[data-testid="stMultiSelect"] [role="group"] input {
    background: transparent !important;
    color: var(--text-primary) !important;
    border: 0 !important;
    box-shadow: none !important;
}

div[data-baseweb="input"] input::placeholder,
textarea::placeholder {
    color: var(--text-muted) !important;
    opacity: 0.8 !important;
}

div[data-baseweb="input"]:focus-within input,
div[data-baseweb="select"]:focus-within select,
textarea:focus {
    border-color: rgba(167, 139, 250, 0.58) !important;
    box-shadow: 0 0 0 2px rgba(139, 92, 246, 0.12), 0 0 14px rgba(139, 92, 246, 0.08) !important;
    outline: none !important;
    background: var(--surface-2) !important;
}

div[data-testid="stTextInput"] input,
div[data-testid="stTextArea"] textarea,
div[data-testid="stNumberInput"] input,
div[data-testid="stDateInput"] input,
div[data-testid="stTimeInput"] input {
    background: linear-gradient(135deg, rgba(139, 92, 246, 0.035), var(--surface-input)) !important;
}

div[data-testid="stTextInput"]:hover input,
div[data-testid="stTextArea"]:hover textarea,
div[data-testid="stNumberInput"]:hover input,
div[data-testid="stDateInput"]:hover input,
div[data-testid="stTimeInput"]:hover input {
    border-color: rgba(167, 139, 250, 0.38) !important;
}

div[data-testid="stTextInput"]:focus-within input,
div[data-testid="stTextArea"]:focus-within textarea,
div[data-testid="stNumberInput"]:focus-within input,
div[data-testid="stDateInput"]:focus-within input,
div[data-testid="stTimeInput"]:focus-within input {
    background: var(--surface-2) !important;
    border-color: rgba(167, 139, 250, 0.58) !important;
    box-shadow: 0 0 0 2px rgba(139, 92, 246, 0.12), 0 0 14px rgba(139, 92, 246, 0.08) !important;
    outline: none !important;
}

[data-testid="stPills"] button,
[data-testid="stRadio"] > div > label {
    background: var(--surface-2) !important;
    color: var(--text-primary) !important;
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
    box-shadow: 0 3px 12px rgba(139, 92, 246, 0.2);
}

div.stButton > button {
    border: none !important;
    background: linear-gradient(135deg, var(--primary-1), var(--primary-2)) !important;
    color: #FFFFFF !important;
    font-weight: 800;
    font-size: 0.98rem;
    border-radius: 50px !important;
    padding: 0.8rem 2rem;
    box-shadow: 0 6px 18px rgba(139, 92, 246, 0.18);
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
    filter: brightness(1.06);
    transform: translateY(-1px);
    box-shadow: 0 8px 20px rgba(139, 92, 246, 0.24);
}

.artifact-shell {
    background: linear-gradient(145deg, var(--surface-2), var(--surface-1));
    border: 1px solid var(--border-default);
    border-radius: 18px;
    padding: 1rem 1rem 0.9rem;
    margin: 0.75rem 0 1rem;
    box-shadow: 0 8px 24px rgba(2, 6, 23, 0.16);
    position: relative;
    overflow: hidden;
}

.artifact-shell::before {
    content: '';
    position: absolute;
    inset: 0 auto auto 0;
    width: 100%;
    height: 2px;
    background: linear-gradient(90deg, rgba(139, 92, 246, 0.72), rgba(168, 85, 247, 0.48));
}

.artifact-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 0.65rem;
    flex-wrap: wrap;
    margin-bottom: 0.75rem;
}

.artifact-badge {
    display: inline-flex;
    align-items: center;
    gap: 0.35rem;
    min-height: 28px;
    padding: 0.38rem 0.72rem;
    border-radius: 999px;
    background: rgba(139, 92, 246, 0.12);
    border: 1px solid rgba(139, 92, 246, 0.26);
    color: #C4B5FD;
    font-size: 0.72rem;
    font-weight: 800;
    letter-spacing: 0.08em;
    text-transform: uppercase;
}

.artifact-meta {
    color: #CBD5E1;
    font-size: 0.76rem;
    letter-spacing: 0.04em;
    text-transform: uppercase;
}

.artifact-body {
    color: var(--text-secondary);
    font-size: 0.96rem;
    line-height: 1.8;
    white-space: pre-wrap;
    word-break: break-word;
}

.artifact-actions {
    display: flex;
    flex-wrap: wrap;
    gap: 0.55rem;
    margin-top: 0.9rem;
}

div[data-testid="stChatMessage"] {
    background: var(--surface-1);
    border: 1px solid var(--border-default);
    border-radius: 16px;
    padding: 0.8rem 0.9rem;
    box-shadow: 0 4px 14px rgba(2, 6, 23, 0.12);
}

.premium-card {
    background: var(--surface-1);
    border-radius: 20px;
    border: 1px solid var(--border-default);
    box-shadow: 0 6px 22px rgba(0, 0, 0, 0.18);
    padding: 28px;
    margin-bottom: 20px;
    transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
    text-align: __ALIGN__;
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
    transform: translateY(-3px);
    box-shadow: 0 10px 28px rgba(0, 0, 0, 0.22);
    border-color: var(--primary-border);
}

.premium-card h3 {
    margin: 0 0 16px 0;
    font-size: 1.2rem;
    font-weight: 800;
    color: var(--text-primary);
    line-height: 1.6;
    text-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
}

.premium-card .meta {
    color: var(--text-secondary);
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
    padding-inline-start: 24px;
    color: var(--text-secondary);
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
    color: var(--text-primary) !important;
}

.ts-hero .accent {
    color: var(--primary-hover);
    background: linear-gradient(135deg, #A78BFA 0%, #8B5CF6 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

.ts-workspace-header {
    position: relative;
    margin: 0 0 1.25rem;
    padding: 1.35rem 1.5rem 1.3rem;
    overflow: hidden;
    text-align: __ALIGN__;
    border: 1px solid var(--primary-border);
    border-radius: 18px;
    background: linear-gradient(120deg, rgba(139, 92, 246, 0.07), var(--surface-3) 42%, var(--surface-2));
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.14);
}

.ts-workspace-header::before {
    position: absolute;
    inset-block: 0;
    inset-inline-start: 0;
    width: 3px;
    content: "";
    background: linear-gradient(180deg, var(--primary-hover), rgba(139, 92, 246, 0.18));
}

.ts-workspace-header .ts-workspace-kicker {
    margin: 0 0 0.45rem;
    color: var(--primary-hover);
    font-size: 0.7rem;
    font-weight: 800;
    letter-spacing: 0.11em;
    text-transform: uppercase;
}

.ts-workspace-header .ts-workspace-title {
    margin: 0 0 0.4rem;
    color: var(--text-primary);
    font-size: clamp(1.55rem, 2.8vw, 2rem);
    font-weight: 800;
    line-height: 1.25;
}

.ts-workspace-header .ts-workspace-description {
    margin: 0;
    color: var(--text-secondary);
    font-size: 0.96rem;
    line-height: 1.65;
}

.ts-section h2 {
    color: var(--text-primary) !important;
}

.ts-paywall {
    background: linear-gradient(135deg, var(--primary-soft), rgba(168, 85, 247, 0.06));
    border: 1px solid var(--primary-border);
    border-radius: 24px;
    padding: 4px;
    box-shadow: 0 12px 32px rgba(0, 0, 0, 0.2);
}

.ts-paywall-inner {
    background: var(--surface-1);
    border-radius: 20px;
    padding: 2.5rem;
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
    background: var(--surface-1);
    border: 1px solid var(--card-border);
    border-radius: 24px;
    padding: 2.5rem;
    text-align: center;
    transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
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
    transform: translateY(-4px);
    box-shadow: 0 12px 32px rgba(0, 0, 0, 0.22);
    border-color: var(--primary-border);
}

.ts-pricing-card.featured {
    border: 1px solid var(--primary-border);
    box-shadow: 0 8px 26px rgba(0, 0, 0, 0.2);
}

.ts-pricing-card.featured:hover {
    transform: translateY(-4px);
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
    text-align: __ALIGN__;
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
    border: 1px solid var(--card-border);
    background: rgba(15, 23, 42, 0.7);
    color: var(--muted);
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
    box-shadow: 0 6px 18px rgba(139, 92, 246, 0.18);
}

.ts-pricing-btn.primary:hover {
    filter: brightness(1.06);
    transform: translateY(-1px);
    box-shadow: 0 8px 20px rgba(139, 92, 246, 0.24);
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
    background: var(--surface-1);
    border: 1px solid var(--card-border);
    border-radius: 20px;
    padding: 2rem;
    margin-top: 2rem;
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
    background: var(--surface-1);
    border: 1px solid var(--card-border);
    border-radius: 20px;
    padding: 2rem;
    margin-top: 2rem;
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
    background: var(--surface-2);
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
    background: var(--surface-1);
    border-radius: 20px;
    border: 1px solid var(--card-border);
    box-shadow: 0 6px 22px rgba(0, 0, 0, 0.18);
    padding: 24px;
    transition: all 0.3s ease;
}

.ts-card:hover {
    transform: translateY(-3px);
    box-shadow: 0 10px 28px rgba(0, 0, 0, 0.22);
    border-color: var(--primary-border);
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
    border: 1px solid var(--primary-border);
    box-shadow: 0 8px 26px rgba(0, 0, 0, 0.2);
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
    padding-inline-start: 20px;
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
    display: flex;
    align-items: center;
    justify-content: flex-start;
    gap: 0.5rem;
    margin: 0 0 0.75rem;
    padding-top: 0.15rem;
    text-align: __ALIGN__;
}

.ts-lang-bar .label {
    display: inline-block;
    font-size: 0.72rem;
    font-weight: 700;
    color: var(--text-secondary);
    margin-bottom: 0;
    letter-spacing: 0.06em;
    text-transform: uppercase;
}

.ts-chips-label {
    text-align: center;
    color: var(--muted);
    font-size: 0.85rem;
    margin: 1rem 0 0.5rem;
    font-weight: 700;
}

.ts-input-container {
    background: var(--surface-2);
    border: 1px solid rgba(167, 139, 250, 0.2);
    border-radius: 16px;
    padding: 1.25rem;
    margin-bottom: 1.5rem;
    box-shadow: 0 0 16px rgba(139, 92, 246, 0.06);
    transition: border-color 0.2s ease, box-shadow 0.2s ease;
}

.ts-input-container:focus-within {
    border-color: rgba(167, 139, 250, 0.48);
    box-shadow: 0 0 0 2px rgba(139, 92, 246, 0.1), 0 0 16px rgba(139, 92, 246, 0.08);
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
    """Landing header only; app navigation is rendered via the app shell and sidebar."""
    if st.session_state.get("app_mode") == "app":
        render_html(
            """
            <style>
            .stApp { padding-top: 0 !important; }
            header { display: none !important; }
            footer { display: none !important; }
            [data-testid="stToolbar"] { display: none !important; }
            </style>
            """
        )
        return

    nav_home = t("nav.home")
    nav_tools = t("nav.tools")
    nav_how = t("nav.how")
    nav_pricing = t("nav.pricing")
    nav_faq = t("nav.faq")
    render_html(
        f"""
        <style>
        .ts-topbar {{
            position: sticky;
            top: 0;
            z-index: 9999;
            width: 100%;
            background: rgba(9, 14, 24, 0.72);
            border-bottom: 1px solid rgba(148, 163, 184, 0.12);
            backdrop-filter: blur(16px);
            -webkit-backdrop-filter: blur(16px);
            margin: 0;
            padding: 0.8rem 0;
        }}

        .ts-topbar-shell {{
            max-width: 1280px;
            margin: 0 auto;
            padding: 0 1.5rem;
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 1rem;
        }}

        .ts-brand-wrap {{
            display: flex;
            align-items: center;
            gap: 0.8rem;
            min-width: 0;
        }}

        .ts-brand-mark {{
            width: 34px;
            height: 34px;
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            background: linear-gradient(135deg, #8B5CF6, #7C3AED);
            color: white;
            font-weight: 800;
            box-shadow: 0 8px 18px rgba(124, 58, 237, 0.22);
        }}

        .ts-brand-text {{
            font-size: 1.05rem;
            font-weight: 800;
            color: #F8FAFC;
            letter-spacing: 0.02em;
        }}

        .ts-topbar-nav {{
            display: flex;
            align-items: center;
            gap: 1.3rem;
            color: rgba(226, 232, 240, 0.82);
            font-size: 0.88rem;
            font-weight: 600;
        }}

        .ts-topbar-nav a {{
            display: inline-flex;
            align-items: center;
            justify-content: center;
            min-height: 2.2rem;
            color: rgba(226, 232, 240, 0.82);
            text-decoration: none;
            font-weight: 600;
            transition: color 0.2s ease;
        }}

        .ts-topbar-nav a:hover {{
            color: #F8FAFC;
        }}

        .ts-topbar-actions {{
            display: flex;
            align-items: center;
            gap: 0.6rem;
        }}

        @media (max-width: 760px) {{
            .ts-topbar-shell {{
                flex-wrap: wrap;
                gap: 0.55rem 0.75rem;
                padding: 0 1rem;
            }}

            .ts-brand-wrap {{
                order: 1;
                flex: 1 1 auto;
            }}

            .ts-topbar-actions {{
                order: 2;
                margin-inline-start: auto;
            }}

            .ts-topbar-nav {{
                order: 3;
                flex: 1 1 100%;
                justify-content: flex-start;
                gap: 1rem;
                overflow-x: auto;
                white-space: nowrap;
                scrollbar-width: none;
            }}

            .ts-topbar-nav::-webkit-scrollbar {{
                display: none;
            }}
        }}

        @media (max-width: 420px) {{
            .ts-topbar-shell {{
                padding-inline: 0.7rem;
            }}

            .ts-brand-wrap {{
                gap: 0.5rem;
            }}

            .ts-brand-text {{
                font-size: 0.95rem;
            }}

            .ts-topbar-actions {{
                gap: 0.35rem;
            }}

            .ts-pill-btn {{
                min-height: 34px;
                padding: 0.45rem 0.65rem;
                font-size: 0.72rem;
            }}
        }}

        .ts-pill-btn {{
            display: inline-flex;
            align-items: center;
            justify-content: center;
            min-height: 38px;
            padding: 0.55rem 0.9rem;
            border-radius: 999px;
            border: 1px solid rgba(148, 163, 184, 0.15);
            background: rgba(15, 23, 42, 0.6);
            color: #E2E8F0;
            font-size: 0.78rem;
            font-weight: 700;
            text-decoration: none;
        }}

        .ts-pill-btn.primary {{
            border: none;
            background: linear-gradient(135deg, #8B5CF6, #7C3AED);
            color: #ffffff;
        }}

        html {{
            scroll-behavior: smooth;
            scroll-padding-top: 88px;
        }}

        .stApp {{
            padding-top: 0 !important;
        }}
        header {{
            display: none !important;
        }}
        footer {{
            display: none !important;
        }}
        [data-testid="stToolbar"] {{
            display: none !important;
        }}
        </style>
        <div class="ts-topbar" id="top">
            <div class="ts-topbar-shell">
                <div class="ts-brand-wrap">
                    <div class="ts-brand-mark">T</div>
                    <div class="ts-brand-text">TubeSpark</div>
                </div>
                <div class="ts-topbar-nav">
                    <a href="#home">{html_escape(nav_home)}</a>
                    <a href="#tools">{html_escape(nav_tools)}</a>
                    <a href="#how-it-works">{html_escape(nav_how)}</a>
                    <a href="#pricing">{html_escape(nav_pricing)}</a>
                    <a href="#faq">{html_escape(nav_faq)}</a>
                </div>
                <div class="ts-topbar-actions">
                    <a href="#lang-switcher" class="ts-pill-btn">{html_escape(t('lang.switch'))}</a>
                    <a href="#workspace" class="ts-pill-btn primary">{html_escape(t('nav.start'))}</a>
                </div>
            </div>
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
        * {
            box-sizing: border-box;
        }

        html, body {
            background: var(--bg) !important;
        }

        .stApp {
            background: var(--bg-gradient) !important;
            background-attachment: fixed !important;
            min-height: 100vh;
        }

        .stTextInput > div > div > input,
        .stSelectbox > div > div > select,
        .stTextArea > div > div > textarea {
            background: var(--surface-input) !important;
            color: var(--text-primary) !important;
            border: 1px solid rgba(167, 139, 250, 0.24) !important;
            border-radius: 14px !important;
            box-shadow: none !important;
        }

        .stTextInput > div,
        .stSelectbox > div,
        .stTextArea > div {
            background: transparent !important;
        }

        .stTextInput input:focus,
        .stSelectbox input:focus,
        .stTextArea textarea:focus,
        div[data-testid="stTextInput"]:focus-within input,
        div[data-testid="stTextArea"]:focus-within textarea,
        div[data-testid="stNumberInput"]:focus-within input,
        div[data-testid="stDateInput"]:focus-within input,
        div[data-testid="stTimeInput"]:focus-within input {
            border-color: rgba(167, 139, 250, 0.58) !important;
            box-shadow: 0 0 0 2px rgba(139, 92, 246, 0.12), 0 0 14px rgba(139, 92, 246, 0.08) !important;
        }

        .stTextInput input:hover,
        .stTextArea textarea:hover {
            border-color: rgba(167, 139, 250, 0.38) !important;
        }

        .stTextInput > div > div > input::placeholder,
        .stTextArea > div > div > textarea::placeholder {
            color: var(--text-muted) !important;
        }

        .stButton > button {
            background: var(--primary-gradient) !important;
            color: #FFFFFF !important;
            font-size: 0.9rem !important;
            font-weight: 700 !important;
            border: none !important;
            border-radius: 12px !important;
            min-height: 38px !important;
            padding: 0.5rem 0.9rem !important;
            width: auto !important;
            text-align: center !important;
            box-shadow: 0 8px 24px rgba(139, 92, 246, 0.18) !important;
        }

        .stButton > button:hover {
            filter: brightness(1.04);
            box-shadow: 0 8px 20px rgba(139, 92, 246, 0.24) !important;
        }

        .ts-hero-actions a.ts-primary-btn {
            background: var(--primary-gradient) !important;
            color: var(--text-primary) !important;
            border-color: transparent !important;
        }

        .ts-hero-actions a.ts-secondary-btn {
            background: var(--surface-2) !important;
            color: var(--text-primary) !important;
            border-color: var(--border-default) !important;
        }

        .ts-topbar-nav a {
            color: var(--text-secondary) !important;
        }

        .ts-topbar-nav a:hover {
            color: var(--text-primary) !important;
        }

        .ts-tool-surface,
        [data-testid="stChatMessage"] {
            background: var(--surface-1) !important;
            border-color: var(--border-default) !important;
            box-shadow: 0 6px 22px rgba(0, 0, 0, 0.18) !important;
        }

        .ts-workspace-preview {
            background: var(--surface-2) !important;
            border-color: var(--border-default) !important;
        }

        .ts-chat-shell {
            background: var(--surface-1) !important;
            border-color: var(--border-default) !important;
        }

        .block-container {
            width: 100%;
            max-width: 1440px;
            padding: clamp(1.25rem, 2.5vw, 2.25rem) clamp(1rem, 3vw, 2.5rem) 3rem;
        }

        .st-key-app_toolbar [data-testid="stHorizontalBlock"] {
            align-items: center;
            gap: 0.75rem;
        }

        .st-key-app_toolbar [data-testid="stColumn"] {
            min-width: 0;
        }

        .st-key-app_navigation {
            position: sticky;
            top: 1rem;
            min-height: fit-content;
            padding: 1.1rem;
            border: 1px solid rgba(167, 139, 250, 0.18);
            border-radius: 18px;
            background: linear-gradient(155deg, rgba(32, 45, 67, 0.94), rgba(18, 26, 41, 0.96));
            box-shadow: 0 12px 32px rgba(2, 6, 23, 0.2), 0 0 22px rgba(139, 92, 246, 0.035);
        }

        .st-key-app_navigation h3 {
            margin: 0.25rem 0 0.9rem;
            font-size: 1.05rem;
            letter-spacing: 0.01em;
        }

        .st-key-app_navigation hr {
            margin: 0.85rem 0;
            border-color: rgba(148, 163, 184, 0.12);
        }

        .st-key-app_navigation .stButton > button {
            width: 100% !important;
            min-height: 44px !important;
            justify-content: flex-start !important;
            text-align: start !important;
            padding-inline: 0.9rem !important;
            border: 1px solid transparent !important;
            border-radius: 11px !important;
            background: transparent !important;
            color: var(--text-secondary) !important;
            box-shadow: none !important;
            transform: none !important;
        }

        .st-key-app_navigation .stButton > button:hover {
            background: rgba(139, 92, 246, 0.09) !important;
            border-color: rgba(167, 139, 250, 0.18) !important;
            color: var(--text-primary) !important;
            filter: none;
            box-shadow: none !important;
        }

        .st-key-app_navigation .stButton > button[kind="primary"] {
            background: linear-gradient(110deg, rgba(139, 92, 246, 0.2), rgba(168, 85, 247, 0.1)) !important;
            border-color: rgba(167, 139, 250, 0.3) !important;
            border-inline-start: 3px solid rgba(167, 139, 250, 0.85) !important;
            color: #F5F3FF !important;
            box-shadow: none !important;
        }

        .st-key-app_navigation .stButton > button[kind="primary"]:hover {
            background: linear-gradient(110deg, rgba(139, 92, 246, 0.25), rgba(168, 85, 247, 0.13)) !important;
            border-color: rgba(167, 139, 250, 0.4) !important;
        }

        .st-key-lang {
            width: 100%;
        }

        .st-key-lang [role="radiogroup"] {
            display: flex;
            flex-wrap: wrap;
            justify-content: flex-end;
            gap: 0.35rem;
        }

        .st-key-lang [role="radiogroup"] button {
            min-height: 36px;
            padding: 0.35rem 0.7rem;
            white-space: nowrap;
        }

        .stApp:has(#home) .premium-card,
        .stApp:has(#home) .ts-pricing-card,
        .stApp:has(#home) .ts-proof,
        .stApp:has(#home) .ts-pricing-footer,
        .stApp:has(#home) .ts-footer,
        .stApp:has(#home) .ts-tool-surface {
            border-color: rgba(167, 139, 250, 0.18);
            box-shadow: 0 10px 28px rgba(2, 6, 23, 0.16), 0 0 22px rgba(139, 92, 246, 0.045);
        }

        .stApp:has(#home) .premium-card {
            padding: clamp(1.2rem, 2vw, 1.7rem) !important;
            background: linear-gradient(145deg, rgba(32, 45, 67, 0.92), rgba(18, 26, 41, 0.96));
        }

        .stApp:has(#home) .premium-card::before {
            opacity: 0.22;
        }

        .stApp:has(#home) .premium-card:hover {
            border-color: rgba(167, 139, 250, 0.32);
            box-shadow: 0 12px 30px rgba(2, 6, 23, 0.18), 0 0 24px rgba(139, 92, 246, 0.065);
        }

        .stApp:has(#home) .ts-pricing-card {
            padding: clamp(1.5rem, 2.5vw, 2.25rem);
            background: linear-gradient(155deg, rgba(32, 45, 67, 0.92), rgba(18, 26, 41, 0.96));
        }

        .stApp:has(#home) .ts-pricing-card.featured {
            border-color: rgba(167, 139, 250, 0.34);
            box-shadow: 0 12px 30px rgba(2, 6, 23, 0.18), 0 0 24px rgba(139, 92, 246, 0.07);
        }

        .stApp:has(#home) .ts-proof,
        .stApp:has(#home) .ts-pricing-footer {
            padding: 1.1rem 1.35rem;
            background: linear-gradient(120deg, rgba(32, 45, 67, 0.72), rgba(25, 36, 56, 0.68));
        }

        .stApp:has(#home) .ts-tool-surface {
            background: linear-gradient(145deg, rgba(32, 45, 67, 0.94), rgba(18, 26, 41, 0.98)) !important;
            padding: 1.35rem;
        }

        .stApp:has(#home) .ts-workspace-preview {
            padding: clamp(1.2rem, 2.2vw, 1.8rem);
        }

        .stApp:has(#home) .ts-footer {
            padding-block: 2.5rem;
            background: linear-gradient(180deg, rgba(25, 36, 56, 0.68), rgba(18, 26, 41, 0.76));
        }

        .stApp:has(#home) .ts-footer-content,
        .stApp:has(#home) .ts-footer-bottom {
            padding-inline: clamp(1rem, 3vw, 2rem);
        }

        .stApp:has(#home) .ts-footer-brand p,
        .stApp:has(#home) .ts-footer-bottom p {
            line-height: 1.7;
        }

        .st-key-app_workspace {
            min-width: 0;
        }

        [data-testid="stSidebarCollapsedControl"] {
            position: fixed !important;
            right: 0.85rem !important;
            top: 0.85rem !important;
            z-index: 1001 !important;
            background: transparent !important;
            border: none !important;
            box-shadow: none !important;
        }

        [data-testid="stSidebarCollapsedControl"] > button {
            width: 42px !important;
            height: 42px !important;
            min-width: 42px !important;
            min-height: 42px !important;
            padding: 0 !important;
            border-radius: 12px !important;
            background: rgba(15, 23, 42, 0.88) !important;
            border: 1px solid rgba(148, 163, 184, 0.18) !important;
            color: #F8FAFC !important;
            box-shadow: 0 8px 18px rgba(15, 23, 42, 0.2) !important;
            display: inline-flex !important;
            align-items: center !important;
            justify-content: center !important;
            transform: none !important;
        }

        [data-testid="stSidebarCollapsedControl"] > button:hover {
            background: linear-gradient(135deg, rgba(139, 92, 246, 0.2), rgba(168, 85, 247, 0.18)) !important;
            border-color: rgba(139, 92, 246, 0.35) !important;
            box-shadow: 0 10px 24px rgba(124, 58, 237, 0.18) !important;
        }

        @media (max-width: 1100px) {
            .st-key-app_navigation {
                padding: 0.85rem;
            }
        }

        @media (max-width: 768px) {
            .block-container {
                padding: 1rem 0.9rem 2rem;
            }

            .st-key-app_navigation {
                position: static;
                min-height: 0;
                margin-bottom: 0.75rem;
            }

            .st-key-lang [role="radiogroup"] {
                justify-content: flex-start;
            }

            .stApp:has(#home) .ts-pricing-grid {
                gap: 1rem;
            }

            .stApp:has(#home) .ts-proof {
                display: flex;
                flex-direction: column;
                gap: 0.35rem;
            }
        }

        @media (max-width: 520px) {
            .block-container {
                padding: 0.75rem 0.65rem 1.5rem;
            }

            .stApp:has(#home) .ts-pricing-card {
                padding: 1.35rem 1.1rem;
            }

            .stApp:has(#home) .ts-footer-content,
            .stApp:has(#home) .ts-footer-bottom {
                padding-inline: 0.75rem;
            }

            .st-key-app_navigation .stButton > button {
                min-height: 42px !important;
            }
        }

        .ts-shell {
            max-width: 1280px;
            margin: 0 auto;
            padding: 1.5rem 1.25rem 3rem;
        }

        .ts-hero-panel {
            display: flex;
            flex-direction: column;
            justify-content: center;
            min-height: 100%;
            padding: 1rem 0.5rem 1rem 0.25rem;
        }

        .ts-hero-kicker {
            display: inline-flex;
            align-items: center;
            width: fit-content;
            padding: 0.42rem 0.75rem;
            border-radius: 999px;
            background: rgba(124, 58, 237, 0.12);
            border: 1px solid rgba(124, 58, 237, 0.18);
            color: #C4B5FD;
            font-size: 0.7rem;
            font-weight: 800;
            letter-spacing: 0.08em;
            text-transform: uppercase;
        }

        .ts-hero-title {
            margin: 1.1rem 0 1rem;
            font-size: clamp(2.2rem, 4vw, 4rem);
            line-height: 1.06;
            letter-spacing: -0.05em;
            font-weight: 900;
            color: #F8FAFC;
        }

        .ts-hero-title .accent {
            color: #C4B5FD;
        }

        .ts-hero-copy {
            max-width: 620px;
            margin: 0 0 1.5rem;
            color: #E2E8F0;
            font-size: 1.02rem;
            line-height: 1.7;
        }

        .ts-hero-actions {
            display: flex;
            flex-wrap: wrap;
            gap: 0.8rem;
            margin-bottom: 1.2rem;
        }

        .ts-primary-btn,
        .ts-secondary-btn {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            min-height: 46px;
            border-radius: 12px;
            padding: 0.8rem 1.15rem;
            font-size: 0.93rem;
            font-weight: 700;
            text-decoration: none;
            border: 1px solid transparent;
            transition: transform 0.2s ease, opacity 0.2s ease;
        }

        .ts-primary-btn {
            background: var(--primary-gradient);
            color: #FFFFFF;
            box-shadow: 0 8px 18px var(--primary-glow);
        }

        .ts-secondary-btn {
            background: var(--surface-2);
            color: var(--text-primary);
            border-color: var(--border-default);
        }

        .ts-hero-stats {
            display: flex;
            flex-wrap: wrap;
            gap: 1.4rem;
            margin-top: 0.2rem;
            color: #E2E8F0;
        }

        .ts-stat {
            display: flex;
            flex-direction: column;
            gap: 0.15rem;
            min-width: 120px;
        }

        .ts-stat strong {
            font-size: 1.35rem;
            font-weight: 800;
            color: #F8FAFC;
        }

        .ts-stat span {
            font-size: 0.76rem;
            color: #A6B0C3;
        }

        .ts-tool-surface {
            background: var(--surface-1);
            border: 1px solid var(--border-default);
            border-radius: 22px;
            box-shadow: 0 8px 24px rgba(2, 6, 23, 0.16);
            overflow: hidden;
            min-height: 100%;
        }

        .ts-workspace-preview {
            padding: 1rem;
            border-radius: 20px;
            background: var(--surface-2);
            border: 1px solid var(--border-default);
            box-shadow: 0 6px 18px rgba(2, 6, 23, 0.14);
        }

        .ts-workspace-kicker {
            font-size: 0.68rem;
            font-weight: 800;
            letter-spacing: 0.12em;
            text-transform: uppercase;
            color: #C4B5FD;
            margin-bottom: 0.55rem;
        }

        .ts-workspace-title {
            margin: 0 0 0.45rem;
            font-size: 1.3rem;
            font-weight: 800;
            color: #F8FAFC;
        }

        .ts-workspace-copy {
            margin: 0;
            color: #DCE5F5;
            line-height: 1.65;
            font-size: 0.94rem;
        }

        .ts-preview-chip-row {
            display: flex;
            flex-wrap: wrap;
            gap: 0.5rem;
            margin-top: 1rem;
        }

        .ts-preview-chip {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            min-height: 32px;
            padding: 0.45rem 0.75rem;
            border-radius: 999px;
            background: rgba(15, 23, 42, 0.7);
            border: 1px solid rgba(148, 163, 184, 0.16);
            color: #E2E8F0;
            font-size: 0.74rem;
            font-weight: 700;
            letter-spacing: 0.02em;
        }

        .ts-chat-shell {
            display: flex;
            flex-direction: column;
            gap: 0.75rem;
            padding: 1.15rem;
            background: var(--surface-2);
            min-height: 100%;
        }

        .ts-badges-row {
            display: flex;
            flex-wrap: wrap;
            gap: 0.5rem;
            margin: 0.5rem 0 1rem;
        }

        .ts-badge-pill {
            display: inline-flex;
            align-items: center;
            padding: 0.35rem 0.7rem;
            border-radius: 999px;
            font-size: 0.72rem;
            font-weight: 700;
            border: 1px solid rgba(255,255,255,0.08);
        }

        .ts-badge-pill.seo { background: rgba(96, 165, 250, 0.12); color: #bfdbfe; }
        .ts-badge-pill.ctr { background: rgba(52, 211, 153, 0.10); color: #bbf7d0; }
        .ts-badge-pill.comp { background: rgba(250, 204, 21, 0.10); color: #fde68a; }

        .ts-auto-report {
            display: flex;
            flex-direction: column;
            gap: 0.8rem;
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
        f'<div id="lang-switcher" class="ts-lang-bar"><span class="label">{html_escape(t("lang.label"))}</span></div>'
    )
    st.pills(
        t("lang.switch"),
        options=list(SUPPORTED_LANGUAGES),
        format_func=lambda code: LANGUAGE_LABELS[code],
        selection_mode="single",
        key="lang",
        label_visibility="visible",
        on_change=_regenerate_on_mode_change,
    )


def render_hero() -> None:
    """Premium SaaS hero section with crisp headline and clear calls to action."""
    render_html(
        f"""
        <div class="ts-hero-panel">
            <div class="ts-hero-kicker">{html_escape(t("brand.badge"))}</div>
            <h1 class="ts-hero-title">{html_escape(t("hero.title_pre"))}<span class="accent"> {html_escape(t("hero.title_accent"))}</span></h1>
            <p class="ts-hero-copy">{html_escape(t("hero.subtitle"))}</p>
            <div class="ts-hero-actions">
                <a href="#workspace" class="ts-primary-btn">{html_escape(t("nav.start"))}</a>
                <a href="#how-it-works" class="ts-secondary-btn">{html_escape(t("nav.how"))}</a>
            </div>
            <div class="ts-hero-stats">
                <div class="ts-stat"><strong>AI-powered</strong><span>content creation</span></div>
                <div class="ts-stat"><strong>3+ tools</strong><span>core workflows</span></div>
                <div class="ts-stat"><strong>Fast</strong><span>generation</span></div>
            </div>
        </div>
        """
    )


def render_landing_tool_cards() -> None:
    """Adds a compact SaaS-style tools overview section without creating new backend logic."""
    render_html(
        f"""
        <section id="tools" style="margin-top: 2rem; margin-bottom: 2rem;">
            <div style="margin-bottom: 1.2rem;">
                <div style="font-size: 0.7rem; letter-spacing: 0.12em; text-transform: uppercase; color: #C4B5FD; font-weight: 800;">{html_escape(t("landing.tools.kicker"))}</div>
                <h2 style="margin: 0.5rem 0 0; font-size: clamp(1.7rem, 2.5vw, 2.5rem); color: #F8FAFC; font-weight: 800;">{html_escape(t("landing.tools.title"))}</h2>
            </div>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 1rem;">
                <div class="premium-card" style="padding: 1.25rem; margin: 0; min-height: 180px;">
                    <div class="badge">01</div>
                    <h3>{html_escape(t("tool.idea.title"))}</h3>
                    <div class="meta">{html_escape(t("tool.idea.copy"))}</div>
                    <a href="#workspace" class="ts-primary-btn" style="margin-top: 0.5rem;">{html_escape(t("tool.use"))}</a>
                </div>
                <div class="premium-card" style="padding: 1.25rem; margin: 0; min-height: 180px;">
                    <div class="badge">02</div>
                    <h3>{html_escape(t("tool.script.title"))}</h3>
                    <div class="meta">{html_escape(t("tool.script.copy"))}</div>
                    <a href="#workspace" class="ts-primary-btn" style="margin-top: 0.5rem;">{html_escape(t("tool.use"))}</a>
                </div>
                <div class="premium-card" style="padding: 1.25rem; margin: 0; min-height: 180px;">
                    <div class="badge">03</div>
                    <h3>{html_escape(t("tool.seo.title"))}</h3>
                    <div class="meta">{html_escape(t("tool.seo.copy"))}</div>
                    <a href="#workspace" class="ts-primary-btn" style="margin-top: 0.5rem;">{html_escape(t("tool.use"))}</a>
                </div>
                <div class="premium-card" style="padding: 1.25rem; margin: 0; min-height: 180px;">
                    <div class="badge">04</div>
                    <h3>{html_escape(t("tool.thumbnail.title"))}</h3>
                    <div class="meta">{html_escape(t("tool.thumbnail.copy"))}</div>
                    <a href="#workspace" class="ts-primary-btn" style="margin-top: 0.5rem;">{html_escape(t("tool.use"))}</a>
                </div>
            </div>
        </section>
        """
    )


def render_how_it_works() -> None:
    """Simple three-step process section for the landing page."""
    render_html(
        f"""
        <section id="how-it-works" style="margin: 2.5rem 0;">
            <div style="margin-bottom: 1.3rem;">
                <div style="font-size: 0.7rem; letter-spacing: 0.12em; text-transform: uppercase; color: #C4B5FD; font-weight: 800;">{html_escape(t("landing.how.kicker"))}</div>
                <h2 style="margin: 0.5rem 0 0; font-size: clamp(1.7rem, 2.5vw, 2.5rem); color: #F8FAFC; font-weight: 800;">{html_escape(t("landing.how.title"))}</h2>
            </div>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 1rem;">
                <div class="premium-card" style="padding: 1.25rem; margin: 0; min-height: 160px;">
                    <div class="badge">01</div>
                    <h3>{html_escape(t("how.idea.title"))}</h3>
                    <div class="meta">{html_escape(t("how.idea.copy"))}</div>
                </div>
                <div class="premium-card" style="padding: 1.25rem; margin: 0; min-height: 160px;">
                    <div class="badge">02</div>
                    <h3>{html_escape(t("how.create.title"))}</h3>
                    <div class="meta">{html_escape(t("how.create.copy"))}</div>
                </div>
                <div class="premium-card" style="padding: 1.25rem; margin: 0; min-height: 160px;">
                    <div class="badge">03</div>
                    <h3>{html_escape(t("how.optimize.title"))}</h3>
                    <div class="meta">{html_escape(t("how.optimize.copy"))}</div>
                </div>
            </div>
        </section>
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


def render_metric_badges(*, seo_score: int = 85, ctr: str = "High", competition: str = "Medium") -> None:
    """Shows compact quality badges used alongside generated ideas and titles."""
    st.markdown(
        f"""
        <div class="ts-badges-row">
            <span class="ts-badge-pill seo">SEO: {seo_score}/100</span>
            <span class="ts-badge-pill ctr">CTR: {ctr}</span>
            <span class="ts-badge-pill comp">Competition: {competition}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _sync_chat_state(payload: dict[str, str]) -> None:
    """Compatibility bridge: sync legacy chat payloads into the project-context model."""
    if not payload:
        return

    ctx = ensure_project_context()
    if payload.get("niche"):
        st.session_state["niche"] = payload["niche"]
        st.session_state["ideas_niche"] = payload["niche"]
        ctx["topic"] = payload["niche"]
        ctx["idea"] = payload["niche"]
        ctx["project_idea"] = payload["niche"]
    if payload.get("script_niche"):
        st.session_state["script_niche"] = payload["script_niche"]
    if payload.get("script_idea"):
        st.session_state["script_idea"] = payload["script_idea"]
        ctx["idea"] = payload["script_idea"]
        ctx["project_idea"] = payload["script_idea"]
        ctx["topic"] = payload["script_idea"]
    if payload.get("seo_topic"):
        st.session_state["seo_topic"] = payload["seo_topic"]
        ctx["topic"] = payload["seo_topic"]
        ctx["project_idea"] = payload["seo_topic"]
    if payload.get("seo_niche"):
        st.session_state["seo_niche"] = payload["seo_niche"]
        ctx["platform"] = payload["seo_niche"]
        ctx["selected_platform"] = payload["seo_niche"]
    if payload.get("video_topic"):
        st.session_state["seo_topic"] = payload["video_topic"]
        ctx["topic"] = payload["video_topic"]
        ctx["project_idea"] = payload["video_topic"]


def _extract_topic_from_prompt(prompt: str) -> str:
    """Extract a plausible topic from a natural-language prompt using a light heuristic."""
    text = (prompt or "").strip()
    if not text:
        return ""
    lower = text.lower()
    markers = (
        "about ", "regarding ", "topic:", "subject:", "sur ", "à propos de ",
        "sujet:", "عن ", "حول ", "موضوع:",
    )
    candidate = ""
    explicit_topic = False
    for marker in markers:
        idx = lower.find(marker)
        if idx >= 0:
            explicit_topic = True
            candidate = text[idx + len(marker):].strip()
            break
    if not candidate and _is_contextual_follow_up(text):
        return ""
    if not candidate:
        candidate = re.sub(
            r"^(?:please\s+)?(?:generate|create|give me|suggest|brainstorm)\s+(?:some\s+)?(?:ideas?|titles?)\s+(?:for\s+)?",
            "",
            text,
            flags=re.IGNORECASE,
        )
        if candidate == text and not explicit_topic:
            if re.match(r"^(?:i prefer|i like|please use|keep it|je préfère|j'aime|utilise|أفضل|أفضّل|أحب|استخدم)\b", lower):
                return ""
            if len(candidate.split()) > 5:
                return ""
    candidate = candidate.strip("\"'` ")
    candidate = re.split(
        r"\s*(?:,\s*(?:shorts?|short-form|then|and then|evaluate|analyze|analyse|"
        r"évalue|analyse|قيّم|تقييم)|\b(?:shorts|short-form|tiktok|youtube|instagram reels|"
        r"on tiktok|on youtube|for beginners|for students|for creators|للطلاب|للمبتدئين)\b)",
        candidate,
        maxsplit=1,
        flags=re.IGNORECASE,
    )[0]
    candidate = re.sub(r"\s+\d+\s*(?:\+?\s*)?(?:minutes?|mins?|seconds?|secs?).*$", "", candidate, flags=re.IGNORECASE)
    audience = _chat_requested_audience(text, "")
    if audience:
        candidate = re.sub(rf"\s+for\s+{re.escape(audience)}\b", "", candidate, flags=re.IGNORECASE)
    candidate = candidate.strip(" \t,;:-")
    return candidate[:120]


def _detect_platform(prompt: str, fallback: str = DEFAULT_PLATFORM) -> str:
    """Identify the current platform from the prompt or the project context."""
    text = (prompt or "").lower()
    platform_map = {
        "youtube": "YouTube",
        "يوتيوب": "YouTube",
        "shorts": "YouTube Shorts",
        "tiktok": "TikTok",
        "تيك توك": "TikTok",
        "reels": "Instagram Reels",
        "instagram": "Instagram",
        "facebook": "Facebook",
        "linkedin": "LinkedIn",
        "x": "X / Twitter",
        "twitter": "X / Twitter",
        "podcast": "Podcast",
        "blog": "Blog",
    }
    for key, value in platform_map.items():
        if key in text:
            return value
    return fallback or DEFAULT_PLATFORM


def _detect_content_type(prompt: str, fallback: str = "video") -> str:
    """Determine the type of asset the user is asking for."""
    text = (prompt or "").lower()
    mapping = {
        "seo": "seo",
        "keyword": "seo",
        "mots-clés": "seo",
        "référencement": "seo",
        "search": "seo",
        "سيو": "seo",
        "كلمات مفتاحية": "seo",
        "thumbnail": "thumbnail",
        "miniature": "thumbnail",
        "صورة مصغرة": "thumbnail",
        "visual": "visual",
        "visuel": "visual",
        "مرئي": "visual",
        "script": "script",
        "سكريبت": "script",
        "سيناريو": "script",
        "title": "title",
        "titre": "title",
        "عنوان": "title",
        "idea": "idea",
        "idée": "idea",
        "فكرة": "idea",
        "hook": "idea",
        "description": "description",
        "hashtag": "hashtags",
        "podcast": "podcast",
        "بودكاست": "podcast",
        "guide": "guide",
        "short": "short",
        "series": "series",
    }
    for key, value in mapping.items():
        if key in text:
            return value
    return fallback


def _apply_prompt_to_project_context(prompt: str) -> dict[str, Any]:
    """Capture explicit project fields without replacing context with follow-up wording."""
    cleaned = (prompt or "").strip()
    if not cleaned:
        return {}

    ctx = ensure_project_context()
    extracted_topic = _extract_topic_from_prompt(cleaned)
    is_follow_up = _is_contextual_follow_up(cleaned)
    topic = (ctx.get("topic") or ctx.get("idea") or "") if is_follow_up else (extracted_topic or ctx.get("topic") or ctx.get("idea") or "")
    platform = _detect_platform(cleaned, ctx.get("platform") or ctx.get("selected_platform") or DEFAULT_PLATFORM)
    content_type = _detect_content_type(cleaned, ctx.get("content_type") or "video")

    updates: dict[str, Any] = {
        "platform": platform,
        "selected_platform": platform,
        "niche": ctx.get("niche") or topic,
    }
    if topic:
        updates.update(topic=topic, idea=ctx.get("idea") or topic, project_idea=ctx.get("project_idea") or topic)
    if not is_follow_up:
        updates["content_type"] = content_type
    duration = _chat_requested_duration(cleaned, "")
    if duration:
        updates["duration"] = duration
    audience = _chat_requested_audience(cleaned, "")
    if audience:
        updates["audience"] = audience
    vibe = _chat_requested_vibe(cleaned, "")
    if vibe:
        updates["vibe"] = vibe
    if _is_explicit_project_preference(cleaned):
        preferences = list(ctx.get("preferences") or [])
        if cleaned not in preferences:
            preferences.append(cleaned[:200])
        updates["preferences"] = preferences
    update_project_context(**updates)

    return {
        "topic": topic,
        "platform": platform,
        "content_type": content_type,
    }


CHAT_INTENTS = frozenset({
    "IDEATE", "EVALUATE", "COMPARE", "REWRITE", "SCRIPT", "SEO",
    "VISUAL", "ANALYZE", "RESEARCH", "GENERAL_CHAT",
})


def _is_contextual_follow_up(prompt: str) -> bool:
    text = (prompt or "").lower()
    phrases = (
        "make it", "make this", "shorten it", "rewrite it", "improve it", "more exciting",
        "more engaging", "turn it into", "convert it to", "write the script", "improve the title",
        "rends-le", "raccourcis", "améliore", "transforme-le", "اختصرها", "حسّنها", "اجعلها",
        "حوّلها", "اكتب السكريبت", "حسن العنوان", "i prefer", "i like", "please use",
        "je préfère", "j'aime", "أفضل", "أفضّل", "أحب", "استخدم",
    )
    return any(phrase in text for phrase in phrases)


def _is_explicit_project_preference(prompt: str) -> bool:
    text = (prompt or "").strip().lower()
    return text.startswith((
        "i prefer", "i like", "please use", "keep it",
        "je préfère", "j'aime", "utilise",
        "أفضل", "أفضّل", "أحب", "استخدم",
    ))


def _rule_classify_chat_intent(prompt: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
    """Conservative local fallback used when model-based intent classification is unavailable."""
    text = (prompt or "").lower()
    context = context or {}
    checks = (
        ("RESEARCH", ("research", "latest", "current trend", "source", "بحث", "مصدر", "ترند", "tendance actuelle")),
        ("COMPARE", ("compare", "versus", " vs ", "which is better", "comparez", "قارن", "مقارنة")),
        ("SEO", ("seo", "keyword", "search tags", "metadata", "référencement", "mots-clés", "سيو", "كلمات مفتاحية")),
        ("SCRIPT", ("script", "voiceover", "narration", "scénario", "voix off", "سكريبت", "سيناريو")),
        ("VISUAL", ("thumbnail", "visual", "cover image", "miniature", "visuel", "صورة مصغرة", "مرئي")),
        ("EVALUATE", ("evaluate", "evaluation", "rate this", "score this", "évalue", "noter", "قيّم", "تقييم")),
        ("ANALYZE", ("analyze", "analyse", "analysis", "explain why", "analyser", "حلل", "تحليل")),
        ("REWRITE", ("rewrite", "improve", "shorten", "make it more", "make it less", "turn it into", "convert it to",
                     "réécris", "améliore", "raccourcis", "اختصر", "حسّن", "اجعلها", "حوّلها")),
        ("IDEATE", ("idea", "ideas", "brainstorm", "ideate", "idée", "أفكار", "فكرة", "اقترح")),
    )
    matches = [intent for intent, phrases in checks if any(phrase in text for phrase in phrases)]
    if "IDEATE" in matches and "EVALUATE" in matches:
        intents = ["IDEATE", "EVALUATE"]
    elif matches:
        intents = [matches[0]]
    elif _is_contextual_follow_up(prompt) and context.get("last_artifact"):
        intents = ["REWRITE"]
    else:
        intents = ["GENERAL_CHAT"]
    return {"intents": intents, "source": "local_rules"}


def _classify_chat_intent(
    prompt: str,
    lang: str,
    context: dict[str, Any],
    history: list[dict[str, Any]],
) -> dict[str, Any]:
    """Classify intent with Groq when configured; disclose and use local rules on failure."""
    fallback = _rule_classify_chat_intent(prompt, context)
    if _configure_groq() is not None:
        return fallback
    recent_history = [
        {"role": item.get("role", ""), "content": str(item.get("content", ""))[:600]}
        for item in history[-8:]
        if item.get("role") in {"user", "assistant"}
    ]
    classifier_prompt = """Classify the user's current intent using the current message, recent conversation, and project context.
Return only JSON with: intents (one to three ordered values from IDEATE,EVALUATE,COMPARE,REWRITE,SCRIPT,SEO,VISUAL,ANALYZE,RESEARCH,GENERAL_CHAT), topic, niche, audience, platform, duration, content_type, format, vibe, preferences.
Keep existing project values when the user refers to it with "it/this". Return only values explicit or strongly implied by the conversation; otherwise empty strings/lists.
Do not answer the user, invent facts, or infer live research. An explicit request for research is RESEARCH even when no retrieval tool is available."""
    user_prompt = json.dumps({
        "message": prompt,
        "language": lang,
        "project_context": {
            key: context.get(key) for key in (
                "topic", "niche", "platform", "content_type", "format", "duration",
                "vibe", "audience", "idea", "titles", "selected_title", "preferences",
                "last_artifact",
            ) if context.get(key) is not None
        },
        "recent_messages": recent_history,
    }, ensure_ascii=False)
    try:
        result = _groq_json(classifier_prompt, user_prompt, temperature=0.0)
        raw_intents = result.get("intents")
        if not isinstance(raw_intents, list) or not raw_intents:
            raise GroqFormatError("intent classifier returned no intents")
        intents = []
        for intent in raw_intents[:3]:
            normalized = str(intent).strip().upper()
            if normalized not in CHAT_INTENTS:
                raise GroqFormatError("intent classifier returned an unknown intent")
            if normalized not in intents:
                intents.append(normalized)
        if not intents:
            raise GroqFormatError("intent classifier returned no valid intents")
        slots = {}
        for field in ("topic", "niche", "audience", "platform", "duration", "content_type", "format", "vibe"):
            value = result.get(field)
            slots[field] = _model_text(value, 240) if isinstance(value, str) else ""
        preferences = result.get("preferences", [])
        if not isinstance(preferences, list) or any(not isinstance(value, str) for value in preferences):
            raise GroqFormatError("intent classifier returned invalid preferences")
        slots["preferences"] = [_model_text(value, 200) for value in preferences[:8] if _model_text(value)]
        slots["intents"] = intents
        slots["source"] = "model"
        return slots
    except Exception as exc:
        fallback["fallback_reason"] = _classify_ai_error(exc)
        return fallback


def _validate_chat_response(
    value: dict[str, Any],
    *,
    default_intent: str = "GENERAL_CHAT",
) -> dict[str, Any]:
    """Validate and normalize the UI-facing structured response contract."""
    intent = str(value.get("intent") or default_intent).upper()
    if intent not in CHAT_INTENTS:
        raise GroqFormatError("chat response has an invalid intent")
    answer = _model_text(value.get("answer"), 4000)
    if not answer:
        raise GroqFormatError("chat response is missing its answer")
    list_fields = ("facts", "inferences", "assumptions", "actions")
    normalized: dict[str, Any] = {
        "intent": intent,
        "answer": answer,
        "analysis": _model_text(value.get("analysis"), 3000),
        "facts": [],
        "inferences": [],
        "assumptions": [],
        "score": None,
        "artifacts": {},
        "actions": [],
        "next_step": _model_text(value.get("next_step"), 500),
        "source": str(value.get("source") or "model"),
    }
    for field in list_fields:
        items = value.get(field, [])
        if not isinstance(items, list) or any(not isinstance(item, str) for item in items):
            raise GroqFormatError(f"chat response field {field} must be a string array")
        normalized[field] = [_model_text(item, 400) for item in items[:8] if _model_text(item)]
    artifacts = value.get("artifacts", {})
    if not isinstance(artifacts, dict):
        raise GroqFormatError("chat response artifacts must be an object")
    normalized["artifacts"] = _validated_json_payload(artifacts)
    score = value.get("score")
    if score is not None:
        if isinstance(score, bool) or not isinstance(score, (int, float)) or not 0 <= score <= 100:
            raise GroqFormatError("chat response score must be null or a number from 0 to 100")
        normalized["score"] = int(round(score))
    return normalized


def _validated_json_payload(value: Any, depth: int = 0) -> Any:
    if depth > 6:
        raise GroqFormatError("chat artifact nesting is too deep")
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, list):
        if len(value) > 40:
            raise GroqFormatError("chat artifact contains too many items")
        return [_validated_json_payload(item, depth + 1) for item in value]
    if isinstance(value, dict):
        if len(value) > 40 or any(not isinstance(key, str) for key in value):
            raise GroqFormatError("chat artifact object is invalid")
        return {key: _validated_json_payload(item, depth + 1) for key, item in value.items()}
    raise GroqFormatError("chat artifact contains a non-JSON value")


def _idea_payload(idea: Idea) -> dict[str, Any]:
    return {
        "title": idea.title, "hook": idea.hook, "value": idea.value,
        "steps": list(idea.steps), "tags": list(idea.tags), "keywords": list(idea.keywords),
    }


def _script_payload(script: Script) -> dict[str, Any]:
    return {
        "title": script.title,
        "description": script.description,
        "hashtags": list(script.hashtags),
        "keywords": list(script.keywords),
        "sections": [dict(section) for section in script.sections],
    }


def _seo_payload(data: SEOData) -> dict[str, Any]:
    return {
        "thumbnail_texts": list(data.thumbnail_texts),
        "seo_titles": list(data.seo_titles),
        "clickbait_titles": list(data.clickbait_titles),
        "chapters": list(data.chapters),
        "seo_description": data.seo_description,
        "seo_tags": list(data.seo_tags),
    }


def _evaluation_payload(result: Evaluation) -> dict[str, Any]:
    return {
        "score": result.score,
        "improved_score": result.improved_score,
        "analysis": result.analysis,
        "idea": _idea_payload(result.idea),
        "outline": list(result.outline),
        "criterion_scores": dict(result.criterion_scores or {}),
        "improved_criterion_scores": dict(result.improved_criterion_scores or {}),
        "strengths": list(result.strengths),
        "weaknesses": list(result.weaknesses),
        "improvement_opportunity": result.improvement_opportunity,
        "score_basis": result.score_basis,
    }


def _chat_artifact_payload(kind: str, data: Any) -> Any:
    if kind == "ideas":
        return [_idea_payload(idea) for idea in data if isinstance(idea, Idea)]
    if kind == "script" and isinstance(data, Script):
        return _script_payload(data)
    if kind == "seo" and isinstance(data, SEOData):
        return _seo_payload(data)
    if kind == "evaluation" and isinstance(data, Evaluation):
        return _evaluation_payload(data)
    return _validated_json_payload(data)


def _sync_chat_artifacts_to_project(artifacts: dict[str, Any]) -> None:
    """Persist model-produced edits so the focused workspaces reuse the same project artifacts."""
    updates: dict[str, Any] = {}
    title = artifacts.get("title")
    if isinstance(title, str) and title.strip():
        updates["selected_title"] = title.strip()
        updates["titles"] = list(dict.fromkeys([title.strip(), *(ensure_project_context().get("titles") or [])]))
    idea = artifacts.get("idea")
    if isinstance(idea, dict) and isinstance(idea.get("title"), str):
        idea_payload = _validated_json_payload(idea)
        updates.update(
            idea=idea_payload["title"],
            selected_title=idea_payload["title"],
            titles=list(dict.fromkeys([idea_payload["title"], *(ensure_project_context().get("titles") or [])])),
            last_artifact={"kind": "idea", "data": idea_payload},
        )
    script = artifacts.get("script")
    if isinstance(script, dict) and isinstance(script.get("title"), str):
        script_payload = _validated_json_payload(script)
        updates.update(
            script=script_payload.get("description", ""),
            script_artifact=script_payload,
            description=script_payload.get("description", ""),
            hashtags=script_payload.get("hashtags", []),
            keywords=script_payload.get("keywords", []),
            last_artifact={"kind": "script", "data": script_payload},
        )
    seo = artifacts.get("seo")
    if isinstance(seo, dict):
        seo_payload = _validated_json_payload(seo)
        updates.update(
            seo=seo_payload.get("seo_description", ""),
            seo_artifact=seo_payload,
            keywords=seo_payload.get("seo_tags", []),
            search_tags=seo_payload.get("seo_tags", []),
            last_artifact={"kind": "seo", "data": seo_payload},
        )
    visual = artifacts.get("visual")
    if isinstance(visual, (str, dict)):
        visual_payload = _validated_json_payload(visual)
        direction = visual_payload if isinstance(visual_payload, str) else str(visual_payload.get("direction") or "")
        if direction:
            updates.update(visual_direction=direction, last_artifact={"kind": "visual", "data": visual_payload})
    if updates:
        update_project_context(**updates)


def _brain_general_response(
    prompt: str,
    lang: str,
    intent: str,
    context: dict[str, Any],
) -> dict[str, Any]:
    """Produce grounded conversational analysis; never claims to have searched the web."""
    if intent == "RESEARCH":
        return _validate_chat_response({
            "intent": intent,
            "answer": {
                "en": "I can't verify current or external information in this app because no web or retrieval source is connected. Share a source or enable a data source to research this reliably.",
                "ar": "لا أستطيع التحقق من معلومات حديثة أو خارجية لأن التطبيق لا يتصل حاليًا بالويب أو بمصدر استرجاع. أرسل مصدرًا أو اربط مصدر بيانات لإجراء بحث موثوق.",
                "fr": "Je ne peux pas vérifier des informations actuelles ou externes : aucune source Web ou de récupération n'est connectée. Partage une source ou connecte une source de données pour mener une recherche fiable.",
            }[lang],
            "analysis": "No external research was performed.",
            "facts": [],
            "inferences": [],
            "assumptions": [],
            "source": "no_retrieval",
        })

    if _configure_groq() is not None:
        return _validate_chat_response({
            "intent": intent,
            "answer": {
                "en": "I can use the project context, but model reasoning is unavailable right now. Configure the AI service or provide a specific source/input for me to work from.",
                "ar": "يمكنني استخدام سياق المشروع، لكن استدلال النموذج غير متاح حاليًا. أعد تهيئة خدمة الذكاء الاصطناعي أو زوّدني بمصدر/مدخل محدد للعمل عليه.",
                "fr": "Je peux utiliser le contexte du projet, mais le raisonnement du modèle est indisponible. Configure le service IA ou fournis une source/un contenu précis.",
            }[lang],
            "analysis": "Local fallback; no model reasoning was performed.",
            "assumptions": ["No external source is connected."],
            "source": "local_fallback",
        })

    system = f"""You are the central TubeSpark content assistant. Use the current request, project context and recent messages; when the user says "it/this", act on the current artifact rather than starting over.
Return only valid JSON with fields intent, answer, analysis, facts, inferences, assumptions, score, artifacts, actions, next_step.
Use intent {intent}. facts may contain only information explicitly present in the supplied user/project content. Mark uncertain reasoning as inferences or assumptions. Never invent sources, statistics, metrics, current trends, search volume, or claim research was performed. No retrieval/web tool is connected.
For REWRITE, return the complete revised asset in artifacts using a relevant key (idea, title, script, seo, or visual) and preserve the user's constraints. Keep all text in {lang}."""
    user = json.dumps({
        "request": prompt,
        "project_context": context,
        "recent_messages": st.session_state.get("copilot_messages", [])[-8:],
    }, ensure_ascii=False, default=str)
    try:
        raw = _groq_json(system, user, temperature=0.4)
        raw["intent"] = intent
        response = _validate_chat_response(raw, default_intent=intent)
        supplied_text = f"{prompt}\n{user}".casefold()
        grounded_facts = []
        unverified_claims = []
        for fact in response["facts"]:
            if fact.casefold() in supplied_text:
                grounded_facts.append(fact)
            else:
                unverified_claims.append(f"Unverified model inference: {fact}")
        response["facts"] = grounded_facts
        response["inferences"] = (response["inferences"] + unverified_claims)[:8]
        return response
    except Exception as exc:
        _set_ai_error(_classify_ai_error(exc), _ai_error_detail(exc))
        return _validate_chat_response({
            "intent": intent,
            "answer": {
                "en": "I couldn't safely validate the model response, so I haven't presented it as a completed result. Please retry or simplify the request.",
                "ar": "تعذّر التحقق من استجابة النموذج بأمان، لذلك لم أعرضها كنتيجة مكتملة. أعد المحاولة أو بسّط الطلب.",
                "fr": "Je n'ai pas pu valider la réponse du modèle de manière fiable ; je ne la présente donc pas comme un résultat terminé. Réessaie ou simplifie la demande.",
            }[lang],
            "analysis": "The structured response failed validation.",
            "source": "validation_fallback",
        })


def _chat_orchestrator(prompt: str, lang: str) -> str:
    """Classify, execute, and persist a structured response for the current project."""
    cleaned = (prompt or "").strip()
    if not cleaned:
        return "Please tell me what you want to create."

    lang = lang if lang in SUPPORTED_LANGUAGES else current_lang()
    ctx = ensure_project_context()
    classification = _classify_chat_intent(
        cleaned,
        lang,
        ctx,
        st.session_state.get("copilot_messages", []),
    )
    parsed = _apply_prompt_to_project_context(cleaned)
    slots = classification
    topic = slots.get("topic") or parsed.get("topic") or ctx.get("topic") or ctx.get("idea") or ""
    if _is_contextual_follow_up(cleaned) and not slots.get("topic"):
        topic = ctx.get("topic") or ctx.get("idea") or ""
    platform = slots.get("platform") or parsed.get("platform") or ctx.get("platform") or DEFAULT_PLATFORM
    niche = slots.get("niche") or ctx.get("niche") or topic
    duration = _chat_requested_duration(cleaned, slots.get("duration") or ctx.get("duration") or "8-10min")
    audience = slots.get("audience") or _chat_requested_audience(cleaned, ctx.get("audience") or "")
    vibe = slots.get("vibe") or _chat_requested_vibe(cleaned, ctx.get("vibe") or "professional")
    content_type = slots.get("content_type") or parsed.get("content_type") or ctx.get("content_type") or "video"
    format_value = slots.get("format") or ctx.get("format") or ("short-form" if duration == "shorts" else "")
    preferences = list(ctx.get("preferences") or [])
    for preference in slots.get("preferences", []):
        if preference not in preferences:
            preferences.append(preference)
    if _is_explicit_project_preference(cleaned) and cleaned not in preferences:
        preferences.append(cleaned[:200])
    explicit_updates: dict[str, Any] = {
        "platform": platform,
        "niche": niche,
        "duration": duration,
        "audience": audience,
        "vibe": vibe,
        "format": format_value,
        "preferences": preferences,
    }
    if topic:
        explicit_updates["topic"] = topic
    if content_type:
        explicit_updates["content_type"] = content_type
    update_project_context(**explicit_updates)
    ctx = ensure_project_context()
    intents = slots.get("intents") or ["GENERAL_CHAT"]
    if not topic and not ctx.get("last_artifact") and any(value not in {"GENERAL_CHAT", "RESEARCH"} for value in intents):
        response = _validate_chat_response({
            "intent": intents[0],
            "answer": {
                "en": "Tell me the topic or share the idea you want me to work on.",
                "ar": "أخبرني بالموضوع أو شاركني الفكرة التي تريد العمل عليها.",
                "fr": "Indique le sujet ou partage l'idée sur laquelle tu veux travailler.",
            }[lang],
            "assumptions": [],
            "source": classification.get("source", "local_rules"),
        }, default_intent=intents[0])
        st.session_state["chat_response"] = response
        st.session_state["chat_output"] = {"kind": "context", "request": cleaned, "data": {}}
        return response["answer"]

    artifacts: dict[str, Any] = {}
    rendered_artifacts: dict[str, Any] = {}
    messages: list[str] = []
    general_responses: list[dict[str, Any]] = []
    ai_available = _configure_groq() is None
    initial_ai_error = st.session_state.get(AI_ERROR_SESSION_KEY)
    generation_failed = False
    active_idea = ctx.get("selected_title") or ctx.get("idea") or topic
    source = classification.get("source", "local_rules")
    research_requested = "RESEARCH" in intents
    for intent in intents:
        if intent == "RESEARCH":
            response = _brain_general_response(cleaned, lang, intent, ctx)
            messages.append(response["answer"])
            source = response["source"]
            continue
        if intent in {"GENERAL_CHAT", "COMPARE", "REWRITE", "ANALYZE"}:
            response = _brain_general_response(cleaned, lang, intent, ctx)
            messages.append(response["answer"])
            artifacts.update(response.get("artifacts") or {})
            _sync_chat_artifacts_to_project(response.get("artifacts") or {})
            general_responses.append(response)
            source = response.get("source") or source
            continue
        try:
            if intent == "IDEATE":
                ideas = generate_ideas(
                    niche,
                    3,
                    platform=platform,
                    vibe=vibe,
                    audience=audience,
                    lang=lang,
                    duration=duration,
                    topic=topic,
                    content_type=content_type,
                    content_format=format_value,
                    additional_context=cleaned,
                )
                if not ideas:
                    raise GroqFormatError("idea generator returned no ideas")
                rendered_artifacts["ideas"] = ideas
                artifacts["ideas"] = _chat_artifact_payload("ideas", ideas)
                active_idea = ideas[0].title
                titles = [idea.title for idea in ideas]
                update_project_context(
                    topic=topic, niche=niche, idea=active_idea, titles=titles, selected_title=active_idea,
                    platform=platform, audience=audience, duration=duration, vibe=vibe,
                    content_type=content_type, last_artifact={"kind": "ideas", "items": artifacts["ideas"]},
                )
                st.session_state["ideas"] = ideas
                st.session_state["ideas_niche"] = niche
                st.session_state["ideas_generation_context"] = {
                    "topic": topic, "niche": niche, "platform": platform,
                    "audience": audience, "duration": duration,
                    "content_type": content_type, "format": format_value,
                }
                messages.append({
                    "en": "Generated project ideas are shown in this conversation.",
                    "ar": "تظهر أفكار المشروع المُنشأة في هذه المحادثة.",
                    "fr": "Les idées générées pour le projet sont affichées dans cette conversation.",
                }[lang])
            elif intent == "EVALUATE":
                idea_text = active_idea or ctx.get("idea") or topic
                latest_ideas = rendered_artifacts.get("ideas")
                if latest_ideas:
                    first_idea = latest_ideas[0]
                    idea_text = "\n".join(part for part in (first_idea.title, first_idea.hook, first_idea.value) if part)
                evaluation_context = _evaluation_generation_context(
                    platform=platform, audience=audience,
                    niche=ctx.get("niche") or topic, content_type=content_type,
                    title=ctx.get("selected_title") or "",
                )
                result = evaluate_idea(idea_text, lang=lang, context=evaluation_context)
                rendered_artifacts["evaluation"] = result
                artifacts["evaluation"] = _chat_artifact_payload("evaluation", result)
                st.session_state["idea_eval_result"] = result
                update_project_context(
                    evaluation=result.analysis,
                    evaluation_details=artifacts["evaluation"],
                    last_artifact={"kind": "evaluation", "data": artifacts["evaluation"]},
                    platform=platform,
                )
                messages.append({
                    "en": "The idea has been evaluated against the rubric; scores and the revised concept are shown below.",
                    "ar": "تم تقييم الفكرة وفق المعايير؛ تظهر الدرجات والصياغة المنقحة أدناه.",
                    "fr": "L'idée a été évaluée selon la grille ; les notes et la version retravaillée sont affichées ci-dessous.",
                }[lang])
            elif intent == "SCRIPT":
                idea_text = active_idea or ctx.get("idea") or topic
                script = _script_from_groq(
                    niche,                     f"{idea_text}\nContent type: {content_type}\nFormat: {format_value}\nUser request: {cleaned}",
                    platform=platform, vibe=vibe, audience=audience or "general viewers",
                    lang=lang, duration=duration,
                )
                rendered_artifacts["script"] = script
                artifacts["script"] = _chat_artifact_payload("script", script)
                details = {
                    "platform": platform, "audience": audience, "duration": duration,
                    "style": vibe, "content_type": content_type, "language": lang,
                }
                st.session_state["script_result"] = script
                st.session_state["script_result_context"] = details
                update_project_context(
                    script=script.description, script_artifact=artifacts["script"],
                    description=script.description, hashtags=list(script.hashtags),
                    keywords=list(script.keywords), last_artifact={"kind": "script", "data": artifacts["script"]},
                    platform=platform, audience=audience, duration=duration, vibe=vibe, format=format_value,
                )
                messages.append({
                    "en": "The full script and its metadata are shown below.",
                    "ar": "يظهر أدناه السكريبت كاملًا وبياناته.",
                    "fr": "Le script complet et ses métadonnées sont affichés ci-dessous.",
                }[lang])
            elif intent == "SEO":
                _, seo_context = _seo_generation_inputs(
                    title=ctx.get("selected_title") or "",
                    description=ctx.get("description") or ctx.get("seo") or "",
                    niche=niche,
                    primary_keyword=(ctx.get("keywords") or [""])[0] if ctx.get("keywords") else "",
                    audience=audience, platform=platform,
                )
                seo_context += f"\nContent type: {content_type}\nDuration: {duration}\nUser request: {cleaned}"
                result = _seo_from_groq(topic, seo_context, lang=lang)
                rendered_artifacts["seo"] = result
                artifacts["seo"] = _chat_artifact_payload("seo", result)
                st.session_state["seo_result"] = result
                update_project_context(
                    seo=result.seo_description, seo_artifact=artifacts["seo"],
                    keywords=list(result.seo_tags), search_tags=list(result.seo_tags),
                    last_artifact={"kind": "seo", "data": artifacts["seo"]},
                    platform=platform, audience=audience,
                )
                messages.append({
                    "en": "SEO output for the current project is shown below.",
                    "ar": "تظهر أدناه مخرجات SEO للمشروع الحالي.",
                    "fr": "Les résultats SEO du projet actuel sont affichés ci-dessous.",
                }[lang])
            elif intent == "VISUAL":
                visual_prompt, visual_source = _visual_direction_from_groq(
                    topic,
                    platform=platform,
                    audience=audience,
                    direction=cleaned,
                    lang=lang,
                )
                if visual_source == "local_fallback":
                    source = "local_fallback"
                rendered_artifacts["visual"] = visual_prompt
                artifacts["visual"] = {"direction": visual_prompt}
                st.session_state["thumbnail_prompt"] = visual_prompt
                update_project_context(
                    visual_direction=visual_prompt, content_type="visual",
                    last_artifact={"kind": "visual", "data": artifacts["visual"]},
                )
                messages.append({
                    "en": "A visual direction prompt is shown below; this does not generate an image.",
                    "ar": "يظهر أدناه توجيه مرئي؛ هذا لا ينشئ صورة فعلية.",
                    "fr": "Une direction visuelle est affichée ci-dessous ; aucune image n'est générée.",
                }[lang])
        except Exception as exc:
            _set_ai_error(_classify_ai_error(exc), _ai_error_detail(exc))
            generation_failed = True
            messages.append({
                "en": f"I couldn't complete {intent.lower()} because the generation response failed. The project context was kept; please retry.",
                "ar": f"تعذّر إكمال {intent.lower()} بسبب فشل استجابة التوليد. احتفظت بسياق المشروع؛ أعد المحاولة.",
                "fr": f"Je n'ai pas pu terminer {intent.lower()} car la réponse de génération a échoué. Le contexte du projet est conservé ; réessaie.",
            }[lang])

    if research_requested and len(intents) == 1:
        response = _brain_general_response(cleaned, lang, "RESEARCH", ctx)
    elif general_responses and not rendered_artifacts:
        response = _validate_chat_response({
            **general_responses[-1],
            "answer": " ".join(messages),
            "artifacts": artifacts,
            "actions": list(dict.fromkeys(action for item in general_responses for action in item.get("actions", []))),
        }, default_intent=intents[0])
    elif rendered_artifacts or artifacts:
        current_ai_error = st.session_state.get(AI_ERROR_SESSION_KEY)
        if current_ai_error and current_ai_error != initial_ai_error:
            source = "local_fallback"
        response = _validate_chat_response({
            "intent": intents[0],
            "answer": " ".join(messages),
            "analysis": (
                "Intent classification used conservative local rules; generation used the configured model."
                if source == "local_rules" and ai_available else
                "Offline deterministic output was used; it is not live AI reasoning or external research."
                if not ai_available else ""
            ),
            "facts": [],
            "inferences": [],
            "assumptions": [],
            "artifacts": artifacts,
            "actions": ["open_idea_generator", "open_script_writer", "open_seo", "open_visual", "copy"],
            "next_step": "",
            "source": "model" if ai_available and source == "model" else "local_fallback" if not ai_available else source,
        }, default_intent=intents[0])
    elif generation_failed:
        response = _validate_chat_response({
            "intent": intents[0],
            "answer": " ".join(messages),
            "analysis": "The requested artifact was not generated; no success result is being shown.",
            "source": "generation_error",
        }, default_intent=intents[0])
    else:
        response = _brain_general_response(cleaned, lang, intents[0], ctx)
        _sync_chat_artifacts_to_project(response.get("artifacts") or {})

    answer_text = response["answer"]
    output_kind = next(iter(rendered_artifacts)) if len(rendered_artifacts) == 1 else "bundle" if rendered_artifacts else "context"
    output_data: Any = next(iter(rendered_artifacts.values())) if len(rendered_artifacts) == 1 else rendered_artifacts
    output = {
        "kind": output_kind,
        "request": cleaned,
        "data": output_data,
        "response": response,
        "topic": topic,
        "platform": platform,
        "details": {
            "topic": topic, "platform": platform, "audience": audience,
            "duration": duration, "content_type": content_type,
            "format": format_value, "style": vibe, "language": lang,
        },
        "context": {
            "topic": topic, "niche": ctx.get("niche") or topic,
            "platform": platform, "audience": audience,
            "content_type": content_type, "title": ctx.get("selected_title") or "",
        },
    }
    st.session_state["chat_response"] = response
    st.session_state["chat_output"] = output
    st.session_state["last_chat_request"] = cleaned
    st.session_state["last_chat_reply"] = answer_text
    update_project_context(last_artifact={
        "kind": (
            next(iter(artifacts))
            if output_kind == "context" and len(artifacts) == 1
            else output_kind
        ),
        "data": _validated_json_payload(
            next(iter(artifacts.values()))
            if output_kind == "context" and len(artifacts) == 1
            else artifacts
        ),
        "intent": intents[0],
        "response": response,
    })
    return answer_text


def _chat_requested_duration(prompt: str, fallback: str) -> str:
    lower = (prompt or "").lower()
    if any(token in lower for token in ("shorts", "short-form", "شورتس")) or re.search(r"\b(?:60|30)\s*(?:seconds?|secs?)\b", lower):
        return "shorts"
    match = re.search(r"\b(3\s*[-–]\s*5|8\s*[-–]\s*10|15\s*[-–]\s*20|15\+?|20)\s*(?:min(?:ute)?s?)\b", lower)
    if match:
        selected = match.group(1).replace(" ", "")
        if selected in {"15", "20", "15-20"}:
            selected = "15+"
        return normalize_duration_value(selected + "min")
    exact_minutes = re.search(r"\b(\d{1,2})\s*(?:minutes?|mins?)\b", lower)
    if exact_minutes:
        minutes = int(exact_minutes.group(1))
        return "shorts" if minutes <= 1 else "3-5min" if minutes <= 5 else "8-10min" if minutes <= 10 else "15min+"
    if re.search(r"\b8\s+minutes?\b", lower):
        return "8-10min"
    if re.search(r"\b3\s+minutes?\b", lower):
        return "3-5min"
    if not fallback:
        return ""
    return normalize_duration_value(fallback)


def _chat_requested_audience(prompt: str, fallback: str = "") -> str:
    text = (prompt or "").strip()
    patterns = (
        r"(?:target audience|audience)\s*:\s*([^,;\n.]+)",
        r"\bfor\s+(.+?)(?=\s+(?:about|on|regarding)\s+|\s+\d+\s*(?:minutes?|mins?)\b|[,;\n.]|$)",
        r"\bpour\s+(.+?)(?=\s+sur\s+|[,;\n.]|$)",
    )
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            audience = match.group(1).strip()
            if audience:
                return audience
    arabic = re.search(r"(?:للجمهور|الجمهور|لـ)\s*[:：]?\s*([^،؛\n.]+)", text)
    return arabic.group(1).strip() if arabic else fallback


def _chat_requested_vibe(prompt: str, fallback: str = "professional") -> str:
    text = (prompt or "").lower()
    vibes = (
        (("casual", "relaxed", "décontracté", "خفيف", "عفوي"), "casual"),
        (("educational", "pedagogical", "pédagogique", "تعليمي"), "educational"),
        (("story-driven", "storytelling", "narrative", "narratif", "قصصي"), "story-driven"),
        (("energetic", "dynamic", "dynamique", "حماسي"), "energetic"),
        (("professional", "professionnel", "احترافي"), "professional"),
    )
    for tokens, vibe in vibes:
        if any(token in text for token in tokens):
            return vibe
    return fallback


def _copilot_reply(prompt: str, lang: str) -> str:
    """Backwards-compatible Copilot response that routes through the project-aware orchestration logic."""
    cleaned = (prompt or "").strip()
    if not cleaned:
        return "Please tell me what you want to create."

    return _chat_orchestrator(cleaned, lang)


def _chat_output_text(output: dict[str, Any]) -> str:
    response = output.get("response")
    if isinstance(response, dict):
        parts = [str(response.get("answer") or "")]
        artifacts = response.get("artifacts") or {}
        if artifacts:
            parts.append(json.dumps(artifacts, ensure_ascii=False, indent=2, default=str))
        return "\n\n".join(part for part in parts if part)
    kind = output.get("kind")
    data = output.get("data")
    if kind == "ideas":
        return "\n\n".join(idea_to_clipboard(idea) for idea in data or [])
    if kind == "script" and isinstance(data, Script):
        sections = "\n\n".join(section.get("content", "") for section in data.sections)
        return "\n\n".join(part for part in (data.title, data.description, sections, ", ".join(data.keywords), ", ".join(data.hashtags)) if part)
    if kind == "seo" and isinstance(data, SEOData):
        return "\n\n".join(part for part in (
            data.seo_description,
            "\n".join(data.seo_titles),
            "\n".join(data.clickbait_titles),
            ", ".join(data.seo_tags),
            "\n".join(data.chapters),
            ", ".join(data.thumbnail_texts),
        ) if part)
    if kind == "evaluation" and isinstance(data, Evaluation):
        return "\n\n".join(part for part in (
            f"{data.score}% → {data.improved_score}%",
            data.analysis,
            data.idea.title,
            data.idea.hook,
            data.idea.value,
            "\n".join(data.outline),
        ) if part)
    if kind == "visual":
        return str(data or "")
    return "\n".join(f"{key}: {value}" for key, value in (data or {}).items()) if isinstance(data, dict) else str(data or "")


def _render_chat_output(
    output_override: dict[str, Any] | None = None,
    response_override: dict[str, Any] | None = None,
    *,
    key_prefix: str = "chat_latest",
) -> None:
    output = output_override or st.session_state.get("chat_output")
    response = response_override or st.session_state.get("chat_response")
    reply = (response or {}).get("answer") or st.session_state.get("last_chat_reply")
    if not reply:
        return
    if not output:
        ctx = ensure_project_context()
        output = {
            "kind": "context",
            "request": st.session_state.get("last_chat_request", ""),
            "data": {
                "topic": ctx.get("topic") or ctx.get("idea") or "",
                "platform": ctx.get("platform") or DEFAULT_PLATFORM,
                "content_type": ctx.get("content_type") or "video",
            },
        }

    with st.container(border=True):
        st.markdown(f"### {t('chat.latest_result')}")
        st.markdown(f"**{t('chat.user_request')}**")
        st.write(output.get("request") or st.session_state.get("last_chat_request", ""))
        st.markdown(f"**{t('chat.ai_response')}**")
        st.write(reply)
        if response:
            if response.get("analysis"):
                st.caption(response["analysis"])
            if response.get("score") is not None:
                st.metric(t("result.score"), f"{response['score']}/100")
            for field, label in (
                ("facts", t("chat.facts")),
                ("inferences", t("chat.inferences")),
                ("assumptions", t("chat.assumptions")),
            ):
                values = response.get(field) or []
                if values:
                    st.markdown(f"**{label}**")
                    st.write("\n".join(f"- {value}" for value in values))
            if response.get("source") in {"local_rules", "local_fallback", "no_retrieval"}:
                st.caption(t("chat.source_notice"))

        kind = output.get("kind")
        data = output.get("data")
        if kind == "ideas":
            _render_idea_result(
                data or [],
                output.get("topic", ""),
                platform=output.get("platform") or DEFAULT_PLATFORM,
                details=output.get("details"),
            )
        elif kind == "script" and isinstance(data, Script):
            _render_script_result(data, details=st.session_state.get("script_result_context"))
        elif kind == "seo" and isinstance(data, SEOData):
            _render_seo_result(data, details=output.get("context"))
        elif kind == "evaluation" and isinstance(data, Evaluation):
            render_evaluation(data, output.get("original", ""), context=output.get("context"))
        elif kind == "visual":
            _render_visual_result(t("result.visual"), str(data or ""), meta=output.get("platform", ""))
        elif kind == "bundle" and isinstance(data, dict):
            for artifact_kind, artifact_data in data.items():
                if artifact_kind == "ideas":
                    _render_idea_result(
                        artifact_data or [], output.get("topic", ""),
                        platform=output.get("platform") or DEFAULT_PLATFORM,
                        details=output.get("details"),
                    )
                elif artifact_kind == "script" and isinstance(artifact_data, Script):
                    _render_script_result(artifact_data, details=output.get("details"))
                elif artifact_kind == "seo" and isinstance(artifact_data, SEOData):
                    _render_seo_result(artifact_data, details=output.get("context"))
                elif artifact_kind == "evaluation" and isinstance(artifact_data, Evaluation):
                    render_evaluation(artifact_data, output.get("original", ""), context=output.get("context"))
                elif artifact_kind == "visual":
                    _render_visual_result(t("result.visual"), str(artifact_data or ""), meta=output.get("platform", ""))
        elif kind == "context":
            details = data or {}
            for label, key in (
                (t("result.platform"), "platform"),
                (t("result.topic"), "topic"),
                (t("result.content_type"), "content_type"),
            ):
                if details.get(key):
                    st.markdown(f"**{html_escape(label)}:** {html_escape(str(details[key]))}", unsafe_allow_html=True)
        if response and response.get("artifacts") and kind in {"context", "bundle"}:
            if kind == "context" and response["artifacts"]:
                with st.expander(t("chat.structured_artifacts")):
                    st.json(response["artifacts"])

        workspace_by_kind = {
            "ideas": "Idea Generator",
            "evaluation": "Idea Evaluator",
            "script": "Script Writer",
            "seo": "SEO Optimizer",
            "visual": "Visual Prompt Studio",
        }
        target_kind = kind if kind != "bundle" else next(iter(data), "")
        if target_kind == "context" and response:
            artifact_workspace_kinds = {
                "ideas": "ideas",
                "idea": "ideas",
                "title": "ideas",
                "evaluation": "evaluation",
                "script": "script",
                "seo": "seo",
                "visual": "visual",
            }
            target_kind = next(
                (artifact_workspace_kinds[key] for key in artifact_workspace_kinds if key in response.get("artifacts", {})),
                target_kind,
            )
        target_workspace = workspace_by_kind.get(target_kind)
        action_labels = []
        if target_workspace:
            action_labels.append((f"Open in {target_workspace}", target_workspace))
        next_action = {
            "ideas": "Create Script",
            "evaluation": "Create Script",
            "script": "Optimize SEO",
            "seo": "Create Visual",
            "visual": "Improve this direction",
        }.get(target_kind)
        if next_action:
            action_labels.append((next_action, "follow_up"))
        if action_labels:
            action_cols = st.columns(min(3, len(action_labels) + 1))
            for idx, (label, destination) in enumerate(action_labels):
                with action_cols[idx]:
                    if st.button(label, key=f"{key_prefix}_action_{idx}", use_container_width=True):
                        if destination == "follow_up":
                            prompt_by_action = {
                                "Create Script": "Write a complete script for the selected project idea using the saved audience, format, duration, and tone.",
                                "Optimize SEO": "Optimize SEO for the current project and preserve the selected platform and audience.",
                                "Create Visual": "Create a visual direction for the current project.",
                                "Improve this direction": "Rewrite this visual direction to be clearer and more specific.",
                            }
                            st.session_state["main_ai_copilot_input"] = prompt_by_action[label]
                        else:
                            st.session_state["active_workspace"] = destination
                            if destination == "Idea Evaluator":
                                st.session_state["idea_eval_input"] = ensure_project_context().get("selected_title") or ensure_project_context().get("idea") or ""
                        st.rerun()
        copy_idx = len(action_labels)
        with st.columns(min(3, len(action_labels) + 1))[copy_idx]:
            if st.button(t("chat.copy_result"), key=f"{key_prefix}_copy", use_container_width=True):
                st.session_state[f"show_{key_prefix}_copy"] = True
        if st.session_state.get(f"show_{key_prefix}_copy"):
            render_copy_button(_chat_output_text(output))


def render_ai_chat_panel() -> None:
    """AI Chat acts as the central orchestrator for the project; it reads and reuses the current shared context instead of starting from zero."""
    ensure_project_context()
    st.session_state.setdefault("copilot_messages", [
        {"role": "assistant", "content": t("chat.welcome")}
    ])

    ctx = ensure_project_context()
    helpful_actions = []
    topic = ctx.get("topic") or ctx.get("idea") or ctx.get("project_idea")
    if topic and not ctx.get("titles"):
        helpful_actions.append(t("chat.action.generate_ideas"))
        helpful_actions.append(t("chat.action.generate_titles"))
        helpful_actions.append(t("chat.action.create_script"))
    if (ctx.get("script") or st.session_state.get("script_result")) and not (ctx.get("seo") or st.session_state.get("seo_result")):
        helpful_actions.append(t("chat.action.create_seo"))
        helpful_actions.append(t("chat.action.generate_keywords"))
    if topic and not (ctx.get("visual_direction") or st.session_state.get("thumbnail_prompt")):
        helpful_actions.append(t("chat.action.create_visual"))

    if helpful_actions:
        st.caption(t("chat.suggested_actions"))
        cols = st.columns(min(len(helpful_actions), 3))
        for idx, action in enumerate(helpful_actions):
            with cols[idx % min(len(helpful_actions), 3)]:
                if st.button(action, use_container_width=True, key=f"chat_action_{action.replace(' ', '_').lower()}"):
                    platform = ctx.get("platform") or DEFAULT_PLATFORM
                    if action == t("chat.action.generate_ideas"):
                        ideas = generate_ideas(topic, 3, platform=platform, audience=ctx.get("audience") or "", lang=current_lang())
                        st.session_state["ideas"] = ideas
                        st.session_state["ideas_niche"] = topic
                        st.session_state["ideas_generation_context"] = {"platform": platform, "audience": ctx.get("audience") or ""}
                        update_project_context(topic=topic, idea=ideas[0].title if ideas else topic, titles=[idea.title for idea in ideas], selected_title=ideas[0].title if ideas else "", content_type="idea", platform=platform)
                        st.session_state["chat_output"] = {"kind": "ideas", "request": action, "data": ideas, "topic": topic, "platform": platform, "details": {"platform": platform, "audience": ctx.get("audience") or ""}}
                    elif action == t("chat.action.generate_titles"):
                        ideas = generate_ideas(topic, 3, platform=platform, audience=ctx.get("audience") or "", lang=current_lang())
                        titles = [idea.title for idea in ideas]
                        st.session_state["ideas"] = ideas
                        st.session_state["ideas_niche"] = topic
                        update_project_context(topic=topic, titles=titles, selected_title=titles[0] if titles else "", content_type="title", platform=platform)
                        st.session_state["chat_output"] = {"kind": "ideas", "request": action, "data": ideas, "topic": topic, "platform": platform, "details": {"platform": platform, "audience": ctx.get("audience") or ""}}
                    elif action == t("chat.action.create_script"):
                        idea_source = ctx.get("selected_title") or ctx.get("idea") or ctx.get("project_idea") or topic
                        if idea_source:
                            audience = ctx.get("audience") or "general viewers"
                            duration = normalize_duration_value(ctx.get("duration") or "3-5min")
                            result = _script_from_groq(topic, idea_source, platform=platform, vibe=ctx.get("vibe") or "professional", audience=audience, lang=current_lang(), duration=duration)
                            st.session_state["script_result"] = result
                            st.session_state["script_result_context"] = {"platform": platform, "audience": audience, "duration": duration}
                            update_project_context(topic=topic, idea=idea_source, script=result.description, description=result.description, hashtags=list(result.hashtags), keywords=list(result.keywords), content_type="script", platform=platform)
                            st.session_state["chat_output"] = {"kind": "script", "request": action, "data": result}
                    elif action == t("chat.action.create_seo"):
                        _, seo_context = _seo_generation_inputs(title=ctx.get("selected_title") or "", description=ctx.get("description") or "", niche=topic, primary_keyword=(ctx.get("keywords") or [""])[0] if ctx.get("keywords") else "", audience=ctx.get("audience") or "", platform=platform)
                        seo_result = _seo_from_groq(topic, seo_context, lang=current_lang())
                        st.session_state["seo_result"] = seo_result
                        update_project_context(topic=topic, seo=seo_result.seo_description, keywords=list(seo_result.seo_tags), search_tags=list(seo_result.seo_tags), content_type="seo", platform=platform)
                        st.session_state["chat_output"] = {"kind": "seo", "request": action, "data": seo_result, "context": {"topic": topic, "niche": topic, "platform": platform}}
                    elif action == t("chat.action.generate_keywords"):
                        seo_result = st.session_state.get("seo_result")
                        if not isinstance(seo_result, SEOData):
                            _, seo_context = _seo_generation_inputs(title=ctx.get("selected_title") or "", description=ctx.get("description") or "", niche=topic, primary_keyword="", audience=ctx.get("audience") or "", platform=platform)
                            seo_result = _seo_from_groq(topic, seo_context, lang=current_lang())
                            st.session_state["seo_result"] = seo_result
                        update_project_context(topic=topic, seo=seo_result.seo_description, keywords=list(seo_result.seo_tags), search_tags=list(seo_result.seo_tags), content_type="seo", platform=platform)
                        st.session_state["chat_output"] = {"kind": "seo", "request": action, "data": seo_result, "context": {"topic": topic, "niche": topic, "platform": platform}}
                    elif action == t("chat.action.create_visual"):
                        prompt = f"Create a cinematic {platform} visual concept for '{topic}'. Use a clear focal point, readable typography, and a strong curiosity hook."
                        update_project_context(topic=topic, visual_direction=prompt, content_type="visual")
                        st.session_state["thumbnail_prompt"] = prompt
                        st.session_state["chat_output"] = {"kind": "visual", "request": action, "data": prompt, "platform": platform}
                    st.session_state["last_chat_request"] = action
                    st.session_state["last_chat_reply"] = t("chat.result_ready")
                    st.session_state["show_chat_reply_copy"] = False
                    st.rerun()

    action_cols = st.columns(3)
    with action_cols[0]:
        if st.button("Use in Idea Generator", use_container_width=True, key="chat_use_content_studio"):
            st.session_state["active_workspace"] = "Idea Generator"
            update_project_context(topic=ctx.get("topic") or ctx.get("idea") or "", idea=ctx.get("idea") or ctx.get("project_idea") or "", platform=ctx.get("platform") or ctx.get("selected_platform") or DEFAULT_PLATFORM)
            st.rerun()
    with action_cols[1]:
        if st.button("Open Idea Evaluator", use_container_width=True, key="chat_open_idea_evaluator"):
            st.session_state["active_workspace"] = "Idea Evaluator"
            st.session_state["idea_eval_input"] = ctx.get("selected_title") or ctx.get("idea") or ctx.get("topic") or ""
            st.session_state["idea_eval_niche"] = ctx.get("topic") or ctx.get("idea") or ""
            update_project_context(topic=ctx.get("topic") or ctx.get("idea") or "", idea=ctx.get("idea") or ctx.get("project_idea") or "", platform=ctx.get("platform") or ctx.get("selected_platform") or DEFAULT_PLATFORM)
            st.rerun()
    with action_cols[2]:
        if st.button("Send to Script Writer", use_container_width=True, key="chat_send_to_script_writer"):
            st.session_state["active_workspace"] = "Script Writer"
            update_project_context(topic=ctx.get("topic") or ctx.get("idea") or "", idea=ctx.get("idea") or ctx.get("project_idea") or "", platform=ctx.get("platform") or ctx.get("selected_platform") or DEFAULT_PLATFORM)
            st.rerun()
    project_action_cols = st.columns(2)
    with project_action_cols[0]:
        if st.button("Send to SEO Optimizer", use_container_width=True, key="chat_send_to_seo"):
            st.session_state["active_workspace"] = "SEO Optimizer"
            update_project_context(topic=ctx.get("topic") or ctx.get("idea") or "", idea=ctx.get("idea") or ctx.get("project_idea") or "", platform=ctx.get("platform") or ctx.get("selected_platform") or DEFAULT_PLATFORM)
            st.rerun()
    with project_action_cols[1]:
        if st.button(t("workspace.save_to_project"), use_container_width=True):
            prompt = st.session_state.get("main_ai_copilot_input", "")
            if prompt.strip():
                _apply_prompt_to_project_context(prompt)
                st.success("The current request was saved into the project context.")
            else:
                st.info("Type a request first to save it into the project context.")

    st.markdown('<div class="ts-chat-shell">', unsafe_allow_html=True)
    for message_index, message in enumerate(st.session_state["copilot_messages"]):
        with st.chat_message(message["role"]):
            st.caption(t("chat.user_request") if message["role"] == "user" else t("chat.ai_response"))
            st.markdown(message["content"])
            if message["role"] == "assistant" and message.get("response") and message.get("output"):
                _render_chat_output(
                    message["output"],
                    message["response"],
                    key_prefix=f"chat_turn_{message_index}",
                )

    with st.form("ai_chat_form", clear_on_submit=True):
        input_col, send_col = st.columns([9, 3])
        with input_col:
            chat_prompt = st.text_input(
                t("chat.ai_copilot"),
                key="main_ai_copilot_input",
                help="Describe the topic, request, or next step for the active project.",
                label_visibility="collapsed",
                placeholder=t("ui.placeholder"),
            )
            st.caption(t("chat.voice_unavailable"))
        with send_col:
            submitted = st.form_submit_button("🚀", key="copilot_send", help="Send message", use_container_width=True)
    if submitted and chat_prompt.strip():
        prompt = chat_prompt.strip()
        st.session_state["copilot_messages"].append({"role": "user", "content": prompt})
        reply = _copilot_reply(prompt, current_lang())
        st.session_state["copilot_messages"].append({
            "role": "assistant",
            "content": reply,
            "response": st.session_state.get("chat_response"),
            "output": st.session_state.get("chat_output"),
        })
        st.session_state["last_chat_request"] = prompt
        st.session_state["last_chat_reply"] = reply
        st.session_state["show_chat_reply_copy"] = False
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
    latest_message = next(
        (message for message in reversed(st.session_state["copilot_messages"]) if message.get("role") == "assistant"),
        {},
    )
    if st.session_state.get("chat_output") and latest_message.get("output") != st.session_state.get("chat_output"):
        _render_chat_output()


def render_idea_cards(ideas: list[Idea], niche: str, *, platform: str) -> None:
    lang = current_lang()
    core_label = html_escape(t("card.core"))
    why_label = html_escape(t("card.why"))
    plan_label = html_escape(t("card.plan"))
    tags_label = "Tags" if lang == "en" else "الهاشتاغات" if lang == "ar" else "Tags"
    keywords_label = "Keywords" if lang == "en" else "الكلمات المفتاحية" if lang == "ar" else "Mots-clés"
    project_ctx = st.session_state.get("project_context", {})

    offset = 0
    for row in chunked(ideas):
        cols = st.columns(len(row))
        for column, idea in zip(cols, row):
            with column:
                selected = bool(project_ctx.get("selected_title") and idea.title == project_ctx.get("selected_title")) or bool(project_ctx.get("idea") and idea.title == project_ctx.get("idea"))
                selected_badge = _selected_meta_html(selected, label="Selected")
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
                    <div class="premium-card" style="padding: 1rem 1rem 0.9rem; border-color: {'rgba(52,211,153,0.38)' if selected else 'rgba(148,163,184,0.12)'}; background: {'rgba(16,185,129,0.08)' if selected else 'rgba(15,23,42,0.72)'};">
                        <div style="display:flex; align-items:center; justify-content:space-between; gap:0.5rem; margin-bottom:0.8rem; flex-wrap:wrap;">
                            <span class="badge">#{offset + 1} {html_escape(niche or platform)}</span>
                            {selected_badge}
                        </div>
                        <h3 style="margin: 0.1rem 0 0.7rem;">{html_escape(idea.title)}</h3>
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
                    """,
                )
                action_cols = st.columns(4)
                with action_cols[0]:
                    if st.button("Select", key=f"idea_select_{_artifact_key(idea.title)}", use_container_width=True, type="primary" if selected else "secondary"):
                        st.session_state["selected_idea_title"] = idea.title
                        update_project_context(topic=niche or idea.title, idea=idea.title, project_idea=idea.title, titles=[item.title for item in ideas], selected_title=idea.title, content_type="idea", platform=platform)
                with action_cols[1]:
                    if st.button("Save", key=f"idea_save_{_artifact_key(idea.title)}", use_container_width=True):
                        update_project_context(topic=niche or idea.title, idea=idea.title, project_idea=idea.title, titles=[item.title for item in ideas], selected_title=idea.title, content_type="idea", platform=platform)
                        st.success("Idea saved to project context.")
                with action_cols[2]:
                    render_copy_button(idea_to_clipboard(idea))
                with action_cols[3]:
                    if st.button("Evaluate", key=f"idea_eval_{_artifact_key(idea.title)}", use_container_width=True):
                        st.session_state["idea_eval_input"] = idea.title
                        st.session_state["idea_eval_niche"] = niche or project_ctx.get("topic") or idea.title
                        st.session_state["idea_eval_title"] = idea.title
                        st.session_state["content_studio_focus"] = "idea_evaluation"
                        st.session_state["active_workspace"] = "Idea Evaluator"
                        update_project_context(topic=niche or idea.title, idea=idea.title, project_idea=idea.title, titles=[item.title for item in ideas], selected_title=idea.title, content_type="idea", platform=platform)
                        st.rerun()
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


def render_evaluation(
    result: Evaluation,
    original: str,
    *,
    context: dict[str, str] | None = None,
) -> None:
    with st.container(border=True):
        st.markdown(f"### {t('result.evaluation')}")
        if context:
            details = (
                ("platform", t("result.platform")),
                ("audience", t("result.audience")),
                ("niche", t("result.niche")),
                ("content_type", t("result.content_type")),
                ("title", t("result.title")),
            )
            visible_details = [f"{label}: {context[key]}" for key, label in details if context.get(key)]
            if visible_details:
                st.caption(" · ".join(visible_details))
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
            f"{result.improved_score - result.score:+d}",
        )

        if result.score_basis == "heuristic":
            st.info(t("eval.heuristic_notice"))
        if result.criterion_scores:
            with st.expander(t("eval.criteria")):
                for criterion in EVALUATION_CRITERIA:
                    original_score = result.criterion_scores.get(criterion)
                    revised_score = (result.improved_criterion_scores or {}).get(criterion)
                    label = t(f"eval.criterion.{criterion}")
                    score_cols = st.columns([3, 1, 1])
                    score_cols[0].write(label)
                    score_cols[1].metric(t("eval.original"), f"{original_score}/100" if original_score is not None else "—")
                    score_cols[2].metric(t("eval.revised"), f"{revised_score}/100" if revised_score is not None else "—")
        if result.strengths:
            st.markdown(f"**{t('eval.strengths')}**")
            st.write("\n".join(f"- {item}" for item in result.strengths))
        if result.weaknesses:
            st.markdown(f"**{t('eval.weaknesses')}**")
            st.write("\n".join(f"- {item}" for item in result.weaknesses))
        if result.improvement_opportunity:
            st.markdown(f"**{t('eval.opportunity')}**")
            st.write(result.improvement_opportunity)

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
                    <h3>⚡ {html_escape(t('footer.brand'))}</h3>
                    <p>{html_escape(t('footer.tagline'))}</p>
                </div>
                <div class="ts-footer-links">
                    <a href="#" target="_blank">{html_escape(t('footer.terms'))}</a>
                    <a href="#" target="_blank">{html_escape(t('footer.privacy'))}</a>
                    <a href="#" target="_blank">{html_escape(t('footer.support'))}</a>
                </div>
            </div>
            <div class="ts-footer-bottom">
                <p>{html_escape(t(credit))}</p>
            </div>
        </div>
        """
    )


# --------------------------------------------------------------------------------------
# Clean workspace shell
# --------------------------------------------------------------------------------------


def render_generator_tab() -> None:
    """Primary idea-generation tab in the new SaaS workspace."""
    st.markdown(
        """
        <div class="ts-card">
            <div class="ts-card-kicker">Ideas</div>
            <h3>Generate a high-converting content roadmap</h3>
            <p>Pick a niche, create a strong angle, and let the AI shape a fresh set of content ideas.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    niche = st.text_input("مجال القناة", key="workspace_niche", placeholder="مثال: تداول، ألعاب، طبخ")
    if st.button("توليد الأفكار", type="primary"):
        clean = niche.strip()
        if not clean:
            st.warning("يرجى إدخال مجال القناة أولاً.")
        else:
            with st.spinner("جارٍ توليد الأفكار..."):
                st.session_state["ideas"] = generate_ideas(clean, FREE_IDEAS_COUNT, lang=current_lang())
                st.session_state["ideas_niche"] = clean
                update_project_context(
                    topic=clean,
                    idea=st.session_state["ideas"][0].title if st.session_state["ideas"] else clean,
                    project_idea=st.session_state["ideas"][0].title if st.session_state["ideas"] else clean,
                    titles=[idea.title for idea in st.session_state["ideas"]],
                    selected_title=(st.session_state["ideas"][0].title if st.session_state["ideas"] else ""),
                    content_type="idea",
                )

    if st.session_state.get("ideas"):
        render_idea_cards(st.session_state["ideas"], st.session_state.get("ideas_niche", ""), platform=DEFAULT_PLATFORM)


def render_script_tab() -> None:
    """Script tab with compact inputs and preserved Groq generation."""
    st.markdown(
        """
        <div class="ts-card">
            <div class="ts-card-kicker">Script</div>
            <h3>Write a full video script with structure and hooks</h3>
        </div>
        """,
        unsafe_allow_html=True,
    )

    niche = st.text_input("مجال الفيديو", key="workspace_script_niche", placeholder="مثال: تعليم، تداول، تكنولوجيا")
    idea = st.text_area("الفكرة الأساسية", key="workspace_script_idea", height=130, placeholder="اكتب الفكرة الأساسية هنا...")

    if st.button("توليد السكريبت", type="primary"):
        if not niche.strip() or not idea.strip():
            st.warning("يرجى إدخال المجال والفكرة أولاً.")
        else:
            with st.spinner("جارٍ إنشاء السكريبت..."):
                st.session_state["script_result"] = _script_from_groq(
                    niche.strip(),
                    idea.strip(),
                    lang=current_lang(),
                    duration="3-5min",
                )
                result = st.session_state["script_result"]
                update_project_context(
                    topic=niche.strip(),
                    idea=idea.strip(),
                    project_idea=idea.strip(),
                    script=result.description,
                    description=result.description,
                    keywords=list(result.keywords),
                    hashtags=list(result.hashtags),
                    content_type="script",
                )

    result = st.session_state.get("script_result")
    if result:
        st.markdown(f"### {result.title}")
        st.write(result.description)


def render_seo_tab() -> None:
    """SEO optimization tab that keeps the AI backend intact."""
    st.markdown(
        """
        <div class="ts-card">
            <div class="ts-card-kicker">SEO</div>
            <h3>Improve visibility, titles, and CTR</h3>
        </div>
        """,
        unsafe_allow_html=True,
    )

    topic = st.text_input("موضوع الفيديو", key="workspace_seo_topic", placeholder="مثال: كيفية بدء التداول")
    niche = st.text_input("مجال الفيديو", key="workspace_seo_niche", placeholder="مثال: تداول، تعليم")

    if st.button("تحسين SEO", type="primary"):
        if not topic.strip() or not niche.strip():
            st.warning("يرجى إدخال الموضوع والمجال أولاً.")
        else:
            with st.spinner("جارٍ تحسين SEO..."):
                st.session_state["seo_result"] = _seo_from_groq(topic.strip(), niche.strip(), lang=current_lang())
                data = st.session_state["seo_result"]
                update_project_context(
                    topic=topic.strip(),
                    idea=topic.strip(),
                    project_idea=topic.strip(),
                    seo=data.seo_description,
                    keywords=list(data.seo_tags),
                    search_tags=list(data.seo_tags),
                    content_type="seo",
                )

    data = st.session_state.get("seo_result")
    if data:
        st.write(data.seo_description)
        st.write(", ".join(data.seo_tags[:8]))


def render_thumbnail_prompt_tab() -> None:
    """Thumbnail prompt generator using the same core workflow."""
    st.markdown(
        """
        <div class="ts-card">
            <div class="ts-card-kicker">Thumbnail</div>
            <h3>Create a click-worthy visual prompt</h3>
        </div>
        """,
        unsafe_allow_html=True,
    )

    topic = st.text_input("موضوع الفيديو", key="workspace_thumbnail_topic", value=st.session_state.get("seo_topic", ""), placeholder="مثال: أخطاء المبتدئين في التداول")
    niche = st.text_input("مجالك", key="workspace_thumbnail_niche", value=st.session_state.get("seo_niche", ""), placeholder="مثال: تداول")

    if st.button("توليد البرومبت", type="primary"):
        prompt = (
            f"Create a cinematic YouTube thumbnail for a video about '{topic or 'your topic'}' in the niche '{niche or 'your niche'}'. "
            "Use a high-contrast composition, large readable title, clean rich colors, dramatic lighting, and a strong curiosity hook."
        )
        st.session_state["thumbnail_prompt"] = prompt
        update_project_context(
            topic=topic.strip() if topic.strip() else st.session_state.get("project_context", {}).get("topic", ""),
            platform=st.session_state.get("project_context", {}).get("platform", DEFAULT_PLATFORM),
            content_type="visual",
            visual_direction=prompt,
        )

    if st.session_state.get("thumbnail_prompt"):
        st.code(st.session_state["thumbnail_prompt"], language="text")


def render_features_grid() -> None:
    """Marketing feature blocks for the SaaS narrative."""
    render_html(
        f"""
        <section id="features" style="margin: 2.5rem 0;">
            <div style="margin-bottom: 1.3rem;">
                <div style="font-size: 0.7rem; letter-spacing: 0.12em; text-transform: uppercase; color: #C4B5FD; font-weight: 800;">{html_escape(t('landing.features.kicker'))}</div>
                <h2 style="margin: 0.5rem 0 0; font-size: clamp(1.7rem, 2.5vw, 2.5rem); color: #F8FAFC; font-weight: 800;">{html_escape(t('landing.features.title'))}</h2>
            </div>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 1rem;">
                <div class="premium-card" style="padding: 1.25rem; min-height: 180px;">
                    <div class="badge">01</div>
                    <h3>Multi-platform engine</h3>
                    <div class="meta">Plan ideas, scripts, hooks, and SEO across YouTube and adjacent creator channels.</div>
                </div>
                <div class="premium-card" style="padding: 1.25rem; min-height: 180px;">
                    <div class="badge">02</div>
                    <h3>AI workflow hub</h3>
                    <div class="meta">One idea can flow into titles, scripts, descriptions, and optimization in sequence.</div>
                </div>
                <div class="premium-card" style="padding: 1.25rem; min-height: 180px;">
                    <div class="badge">03</div>
                    <h3>Workspace-first UX</h3>
                    <div class="meta">Use focused workspaces for ideas, scripts, SEO, and content generation without losing context.</div>
                </div>
                <div class="premium-card" style="padding: 1.25rem; min-height: 180px;">
                    <div class="badge">04</div>
                    <h3>Creator-ready delivery</h3>
                    <div class="meta">Prepare concepts, prompts, and content pack outputs for weekly publishing and faster turnaround.</div>
                </div>
            </div>
        </section>
        """
    )


def render_pricing_section() -> None:
    """Marketing pricing with real package labels already agreed to by the product scope."""
    render_html(
        f"""
        <section id="pricing" style="margin: 2.5rem 0;">
            <div style="margin-bottom: 1.3rem; text-align: center;">
                <div style="font-size: 0.7rem; letter-spacing: 0.12em; text-transform: uppercase; color: #C4B5FD; font-weight: 800;">{html_escape(t('landing.pricing.kicker'))}</div>
                <h2 style="margin: 0.5rem 0 0; font-size: clamp(1.7rem, 2.5vw, 2.5rem); color: #F8FAFC; font-weight: 800;">{html_escape(t('landing.pricing.title'))}</h2>
            </div>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 1rem;">
                <div class="premium-card" style="padding: 1.4rem; min-height: 220px;">
                    <div class="badge">Free</div>
                    <h3 style="margin-top: 1rem;">Starter</h3>
                    <div class="meta" style="font-size: 2rem; font-weight: 900; color: #F8FAFC; margin: 0.6rem 0 0.8rem;">$0</div>
                    <div class="meta">Basic idea generation and lightweight exploration.</div>
                </div>
                <div class="premium-card" style="padding: 1.4rem; min-height: 220px; background: rgba(124, 58, 237, 0.08); border-color: rgba(196, 181, 253, 0.25);">
                    <div class="badge" style="background: rgba(124, 58, 237, 0.18); color: #E9D5FF;">Popular</div>
                    <h3 style="margin-top: 1rem;">Pro</h3>
                    <div class="meta" style="font-size: 2rem; font-weight: 900; color: #F8FAFC; margin: 0.6rem 0 0.8rem;">$4.97</div>
                    <div class="meta">Core AI workflows with practical output for daily publishing.</div>
                </div>
                <div class="premium-card" style="padding: 1.4rem; min-height: 220px;">
                    <div class="badge">Scale</div>
                    <h3 style="margin-top: 1rem;">Growth</h3>
                    <div class="meta" style="font-size: 2rem; font-weight: 900; color: #F8FAFC; margin: 0.6rem 0 0.8rem;">$9.97</div>
                    <div class="meta">Expanded workflow depth for serious content operations.</div>
                </div>
                <div class="premium-card" style="padding: 1.4rem; min-height: 220px;">
                    <div class="badge">Custom</div>
                    <h3 style="margin-top: 1rem;">Agency</h3>
                    <div class="meta" style="font-size: 1.6rem; font-weight: 900; color: #F8FAFC; margin: 0.6rem 0 0.8rem;">Custom</div>
                    <div class="meta">Final multi-seat pricing and feature scope will be defined in the commercial plan.</div>
                </div>
            </div>
        </section>
        """
    )


def render_faq_section() -> None:
    """FAQ foundation for the marketing site without inventing unsupported product claims."""
    render_html(
        f"""
        <section id="faq" style="margin: 2.5rem 0;">
            <div style="margin-bottom: 1.3rem;">
                <div style="font-size: 0.7rem; letter-spacing: 0.12em; text-transform: uppercase; color: #C4B5FD; font-weight: 800;">{html_escape(t('landing.faq.kicker'))}</div>
                <h2 style="margin: 0.5rem 0 0; font-size: clamp(1.7rem, 2.5vw, 2.5rem); color: #F8FAFC; font-weight: 800;">{html_escape(t('landing.faq.title'))}</h2>
            </div>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 1rem;">
                <div class="premium-card" style="padding: 1.2rem;">
                    <h3>Is TubeSpark only for YouTube?</h3>
                    <div class="meta">The product architecture is being expanded beyond YouTube toward multi-platform content creation workflows.</div>
                </div>
                <div class="premium-card" style="padding: 1.2rem;">
                    <h3>Can I use tools separately?</h3>
                    <div class="meta">Yes. Each core workspace remains usable independently while the AI chat can connect the full workflow.</div>
                </div>
                <div class="premium-card" style="padding: 1.2rem;">
                    <h3>Does the AI chat replace the tools?</h3>
                    <div class="meta">No. The chat acts as a workflow hub, while each tool keeps its own focused workspace and context.</div>
                </div>
                <div class="premium-card" style="padding: 1.2rem;">
                    <h3>Is this still a prototype foundation?</h3>
                    <div class="meta">Yes. This phase focuses on architecture and product presentation without replacing the existing generation logic.</div>
                </div>
            </div>
        </section>
        """
    )


def render_cta_banner() -> None:
    """Final CTA section for marketing conversion surface."""
    render_html(
        f"""
        <section id="cta" style="margin: 2.5rem 0 1rem;">
            <div class="premium-card" style="padding: 1.8rem; text-align: center; background: rgba(124, 58, 237, 0.08); border-color: rgba(196, 181, 253, 0.24);">
                <div style="font-size: 0.7rem; letter-spacing: 0.12em; text-transform: uppercase; color: #C4B5FD; font-weight: 800; margin-bottom: 0.8rem;">{html_escape(t('landing.cta.kicker'))}</div>
                <h2 style="margin: 0; color: #F8FAFC; font-size: clamp(1.8rem, 2.8vw, 2.8rem); font-weight: 900;">{html_escape(t('landing.cta.title'))}</h2>
                <p style="margin: 0.9rem auto 1.4rem; max-width: 600px; color: #E2E8F0; line-height: 1.7;">TubeSpark is structured as a premium content engine for creators, operators, and teams building consistent publishing systems.</p>
                <a href="#workspace" class="ts-primary-btn">{html_escape(t('nav.start'))}</a>
            </div>
        </section>
        """
    )


APP_WORKSPACES = [
    "AI Chat",
    "Idea Generator",
    "Idea Evaluator",
    "Script Writer",
    "SEO Optimizer",
    "Visual Prompt Studio",
]
PROJECT_PLATFORM_OPTIONS = [
    "YouTube",
    "YouTube Shorts",
    "TikTok",
    "Instagram Reels",
    "LinkedIn",
    "Podcast",
    "Blog",
]


def ensure_project_context() -> dict[str, Any]:
    """Shared session-backed project memory used across the workspaces and chat."""
    defaults = {
        "topic": "",
        "niche": "",
        "platform": DEFAULT_PLATFORM,
        "content_type": "video",
        "format": "",
        "duration": "8-10min",
        "vibe": "professional",
        "audience": "",
        "idea": "",
        "titles": [],
        "selected_title": "",
        "evaluation": "",
        "evaluation_details": {},
        "script": "",
        "script_artifact": {},
        "description": "",
        "seo": "",
        "seo_artifact": {},
        "keywords": [],
        "hashtags": [],
        "search_tags": [],
        "visual_direction": "",
        "preferences": [],
        "last_artifact": {},
        # compatibility aliases already used elsewhere in the app
        "project_idea": "",
        "selected_platform": DEFAULT_PLATFORM,
        "visual_concepts": [],
    }
    ctx = st.session_state.setdefault("project_context", defaults.copy())
    for key, value in defaults.items():
        ctx.setdefault(key, value)

    if not ctx.get("topic") and ctx.get("idea"):
        ctx["topic"] = ctx["idea"]
    if not ctx.get("idea") and ctx.get("project_idea"):
        ctx["idea"] = ctx["project_idea"]
    if not ctx.get("project_idea") and ctx.get("idea"):
        ctx["project_idea"] = ctx["idea"]
    if not ctx.get("platform") and ctx.get("selected_platform"):
        ctx["platform"] = ctx["selected_platform"]
    if not ctx.get("selected_platform"):
        ctx["selected_platform"] = ctx.get("platform") or DEFAULT_PLATFORM
    if not ctx.get("platform"):
        ctx["platform"] = ctx.get("selected_platform") or DEFAULT_PLATFORM
    if not ctx.get("content_type"):
        ctx["content_type"] = "video"
    if not ctx.get("niche") and ctx.get("topic"):
        ctx["niche"] = ctx["topic"]

    return ctx


def update_project_context(**kwargs: Any) -> None:
    ctx = ensure_project_context()
    for key, value in kwargs.items():
        if value is None:
            continue
        ctx[key] = value

        if key == "topic":
            ctx["project_idea"] = value
            if "niche" not in kwargs:
                ctx["niche"] = value
            if not ctx.get("idea"):
                ctx["idea"] = value
        if key == "idea":
            ctx["project_idea"] = value
            if not ctx.get("topic"):
                ctx["topic"] = value
        if key == "project_idea":
            ctx["idea"] = value
            if not ctx.get("topic"):
                ctx["topic"] = value
        if key == "platform":
            ctx["selected_platform"] = value
        if key == "selected_platform":
            ctx["platform"] = value
        if key == "selected_title":
            ctx["selected_title"] = value


def normalize_duration_value(duration: str | None) -> str:
    """Normalize user-facing duration labels into the canonical backend values."""
    value = (duration or "8-10min").strip().lower().replace(" ", "")
    mapping = {
        "short-form": "shorts",
        "shorts": "shorts",
        "3-5min": "3-5min",
        "3-5": "3-5min",
        "8-10min": "8-10min",
        "8-10": "8-10min",
        "15-20min": "15min+",
        "15min": "15min+",
        "15+min": "15min+",
        "15min+": "15min+",
        "15-20": "15min+",
        "15+": "15min+",
    }
    return mapping.get(value, "8-10min")


def render_workspace_header(title: str, description: str) -> None:
    """Render a consistent, softly accented heading for each workspace."""
    st.markdown(
        f"""
        <div class="ts-workspace-header">
            <div class="ts-workspace-kicker">{html_escape(t('workspace.label'))}</div>
            <h3 class="ts-workspace-title">{html_escape(title)}</h3>
            <p class="ts-workspace-description">{html_escape(description)}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_project_context_card() -> None:
    """Project context summary intentionally kept out of the main workspace flow to avoid the repeated decorative top cards."""
    return None


def render_platform_picker(*, key: str = "project_platform_picker", default: str | None = None) -> str:
    """Project-level platform selector to keep the app multi-platform without implying unsupported integrations."""
    ctx = ensure_project_context()
    selected = st.selectbox(
        "Platform",
        PROJECT_PLATFORM_OPTIONS,
        index=PROJECT_PLATFORM_OPTIONS.index((default or ctx.get("platform") or ctx.get("selected_platform") or DEFAULT_PLATFORM)) if (default or ctx.get("platform") or ctx.get("selected_platform") or DEFAULT_PLATFORM) in PROJECT_PLATFORM_OPTIONS else 0,
        key=key,
    )
    update_project_context(platform=selected, selected_platform=selected)
    return selected


def render_landing_page() -> None:
    """Marketing landing page only; app navigation lives in the app shell."""
    st.markdown('<div id="home" class="ts-shell">', unsafe_allow_html=True)
    landing_action_col, language_col = st.columns([1, 1])
    with landing_action_col:
        if st.button(t("nav.open_app"), key="landing_open_app"):
            st.session_state["app_mode"] = "app"
            st.session_state["active_workspace"] = "AI Chat"
            st.rerun()
    with language_col:
        render_language_switcher()

    hero_col, tool_col = st.columns([1.18, 1.02], gap="large")
    with hero_col:
        render_hero()

    with tool_col:
        st.markdown(
            f"""
            <div class="ts-tool-surface ts-workspace-preview" id="workspace">
                <div class="ts-workspace-kicker">{html_escape(t('landing.workspace.kicker'))}</div>
                <h3 class="ts-workspace-title">{html_escape(t('landing.workspace.title'))}</h3>
                <p class="ts-workspace-copy">{html_escape(t('landing.workspace.copy'))}</p>
                <div class="ts-preview-chip-row">
                    <span class="ts-preview-chip">Ideas</span>
                    <span class="ts-preview-chip">Script</span>
                    <span class="ts-preview-chip">SEO</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    render_landing_tool_cards()
    render_features_grid()
    render_how_it_works()
    render_pricing_section()
    render_faq_section()
    render_cta_banner()
    render_footer()
    st.markdown('</div>', unsafe_allow_html=True)


def render_app_navigation() -> None:
    """Custom sidebar navigation for the product workspaces without using the four primary workspaces as tabs."""
    with st.container(key="app_navigation"):
        st.session_state.setdefault("active_workspace", "AI Chat")
        workspace_labels = {
            "AI Chat": t("workspace.ai_chat"),
            "Idea Generator": t("workspace.idea_generator"),
            "Idea Evaluator": t("workspace.idea_evaluator"),
            "Script Writer": t("workspace.script_writer"),
            "SEO Optimizer": t("workspace.seo_optimizer"),
            "Visual Prompt Studio": t("workspace.visual_prompt_studio"),
        }
        st.markdown("### TubeSpark")
        st.markdown("---")
        for workspace in APP_WORKSPACES:
            if st.button(
                workspace_labels.get(workspace, workspace),
                key=f"app_nav_{workspace}",
                use_container_width=True,
                type="primary" if st.session_state.get("active_workspace") == workspace else "secondary",
            ):
                st.session_state["active_workspace"] = workspace
                st.rerun()
        st.markdown("---")
        if st.button(t("nav.back_to_landing"), key="app_back_to_landing", use_container_width=True):
            st.session_state["app_mode"] = "landing"
            st.rerun()


def render_ai_chat_workspace() -> None:
    """AI Chat workspace with project context summary and direct project prompt flow."""
    render_workspace_header(t("workspace.ai_chat"), t("workspace.ai_chat_desc"))
    render_ai_chat_panel()


def render_idea_generator_workspace() -> None:
    """Professional idea generation workspace using the existing idea engine without changing backend logic."""
    render_content_studio_workspace()


def render_idea_evaluator_workspace() -> None:
    """Standalone idea evaluation page backed by the existing evaluation engine and result structures."""
    render_workspace_header("Idea Evaluator", "Evaluate any idea manually using the existing evaluation workflow.")
    project_platform = render_platform_picker(key="idea_evaluator_platform")

    with st.container(border=True):
        st.markdown("### Idea Evaluation")
        st.caption("Evaluate an idea before it becomes a title, script, or SEO strategy.")
        idea_input = st.text_area("Idea", value=st.session_state.get("project_context", {}).get("idea") or st.session_state.get("project_context", {}).get("project_idea") or "", key="idea_eval_input", height=140)
        eval_platform = st.selectbox("Target platform", PROJECT_PLATFORM_OPTIONS, index=PROJECT_PLATFORM_OPTIONS.index(project_platform) if project_platform in PROJECT_PLATFORM_OPTIONS else 0, key="idea_eval_platform")
        eval_audience = st.text_input("Audience", value=st.session_state.get("project_context", {}).get("audience") or "", key="idea_eval_audience")
        eval_niche = st.text_input("Niche", value=st.session_state.get("project_context", {}).get("topic") or st.session_state.get("project_context", {}).get("idea") or "", key="idea_eval_niche")
        eval_content_type = st.selectbox("Content type", ["Video", "Short", "Podcast", "Guide", "Series"], index=0, key="idea_eval_content_type")
        eval_title = st.text_input("Optional title", value=st.session_state.get("project_context", {}).get("selected_title") or "", key="idea_eval_title")
        evaluate_clicked = st.button("Evaluate Idea", key="idea_eval_button", type="primary")

    if evaluate_clicked:
        if idea_input.strip():
            evaluation_context = _evaluation_generation_context(
                platform=eval_platform,
                audience=eval_audience,
                niche=eval_niche,
                content_type=eval_content_type,
                title=eval_title,
            )
            with st.spinner("Evaluating idea..."):
                result = evaluate_idea(idea_input.strip(), lang=current_lang(), context=evaluation_context)
                st.session_state["idea_eval_result"] = result
                st.session_state["idea_eval_original"] = idea_input.strip()
                st.session_state["idea_eval_context"] = {
                    "platform": eval_platform,
                    "audience": eval_audience,
                    "niche": eval_niche,
                    "content_type": eval_content_type,
                    "title": eval_title,
                }
                update_project_context(
                    idea=idea_input.strip(),
                    topic=eval_niche.strip() or idea_input.strip(),
                    platform=eval_platform,
                    selected_title=eval_title.strip() or result.idea.title,
                    evaluation=result.analysis,
                    content_type=eval_content_type.lower(),
                    audience=eval_audience.strip(),
                )
                st.success("Idea evaluated and saved to the project context.")
        else:
            st.warning("Please provide an idea to evaluate.")

    if st.session_state.get("idea_eval_result"):
        result = st.session_state["idea_eval_result"]
        render_evaluation(
            result,
            st.session_state.get("idea_eval_original") or idea_input,
            context=st.session_state.get("idea_eval_context"),
        )
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            if st.button("Use Improved Idea", key="idea_eval_use_idea", use_container_width=True):
                improved = result.idea.title or idea_input.strip()
                update_project_context(topic=improved, idea=improved, project_idea=improved, selected_title=improved, titles=[improved], content_type="idea", platform=eval_platform)
                st.session_state["workspace_script_idea"] = improved
                st.session_state["workspace_script_niche"] = eval_niche.strip() or improved
                st.success("Improved idea saved to project context.")
        with c2:
            if st.button("Send to Script Writer", key="idea_eval_continue_script", use_container_width=True):
                st.session_state["active_workspace"] = "Script Writer"
                st.rerun()
        with c3:
            if st.button("Save", key="idea_eval_save", use_container_width=True):
                update_project_context(evaluation=result.analysis, content_type="evaluation")
                st.success("Evaluation saved.")
        with c4:
            render_copy_button(result.idea.title or idea_input)


def render_script_writer_workspace() -> None:
    """Standalone script writer that can be used without any prior idea generation or project state."""
    render_workspace_header("Script Writer", "Create a polished script from a topic, title, audience, platform, and runtime context.")
    with st.container(border=True):
        project_platform = render_platform_picker(key="script_writer_platform")
        title_input = st.text_input("Working title", value=st.session_state.get("project_context", {}).get("selected_title") or st.session_state.get("project_context", {}).get("idea") or "", key="script_writer_title")
        topic_input = st.text_input("Topic / idea", value=st.session_state.get("workspace_script_idea") or st.session_state.get("project_context", {}).get("topic") or st.session_state.get("project_context", {}).get("idea") or "", key="workspace_script_topic")
        audience = st.text_input("Audience", value=st.session_state.get("project_context", {}).get("audience") or "general viewers", key="script_writer_audience")
        content_type = st.selectbox("Content type", ["Video", "Short", "Podcast", "Guide", "Series"], index=0, key="script_writer_content_type")
        duration_choice = st.selectbox("Video duration", ["Shorts", "3-5 min", "8-10 min", "15+ min"], index=1, key="script_writer_duration")
        speaking_style = st.selectbox("Speaking style", ["professional", "casual", "educational", "story-driven", "energetic"], index=0, key="script_writer_vibe")
        script_lang = st.selectbox("Language", list(SUPPORTED_LANGUAGES), index=list(SUPPORTED_LANGUAGES).index(current_lang()), key="script_writer_language")
        key_points = st.text_area("Key points", value="", key="script_writer_key_points", height=100)
        additional_context = st.text_area("Additional context", value="", key="script_writer_context", height=90)
        generate_clicked = st.button("Generate Script", type="primary", key="content_script_generate")

    if generate_clicked:
        project_context = st.session_state.get("project_context", {})
        topic_seed = topic_input.strip() or title_input.strip() or project_context.get("topic") or project_context.get("idea") or ""
        idea_seed = _script_idea_seed(
            title_input,
            project_context.get("idea") or "",
            topic_seed,
        )
        if topic_seed:
            context_parts = [f"Topic: {topic_seed}", f"Core idea: {idea_seed}"]
            if key_points.strip():
                context_parts.append(f"Key points: {key_points.strip()}")
            if additional_context.strip():
                context_parts.append(f"Additional context: {additional_context.strip()}")
            if content_type:
                context_parts.append(f"Content type: {content_type}")
            idea_text = "\n".join(part for part in context_parts if part and str(part).strip())
            normalized_duration = normalize_duration_value(duration_choice)
            effective_audience = audience.strip() or "general viewers"
            with st.spinner("Generating script..."):
                result = _script_from_groq(
                    topic_seed,
                    idea_text,
                    platform=project_platform,
                    vibe=speaking_style,
                    audience=effective_audience,
                    lang=script_lang,
                    duration=normalized_duration,
                )
                st.session_state["script_result"] = result
                st.session_state["script_result_context"] = {
                    "platform": project_platform,
                    "audience": effective_audience,
                    "duration": normalized_duration,
                    "content_type": content_type,
                    "style": speaking_style,
                }
                update_project_context(
                    topic=topic_seed,
                    idea=idea_text,
                    selected_title=title_input.strip() or idea_seed,
                    script=result.description,
                    description=result.description,
                    hashtags=list(result.hashtags),
                    keywords=list(result.keywords),
                    content_type=content_type.lower(),
                    platform=project_platform,
                    audience=effective_audience,
                )
                st.success("Script generated and saved.")
        else:
            st.warning("Please provide a topic or title before generating.")
    result = st.session_state.get("script_result")
    if result:
        _render_script_result(result, details=st.session_state.get("script_result_context"))
        copy_text = _chat_output_text({"kind": "script", "data": result})
        with st.container(border=True):
            c1, c2 = st.columns(2)
            with c1:
                render_copy_button(copy_text)
            with c2:
                if st.button("Save", key="content_script_save", use_container_width=True):
                    update_project_context(script=result.description, description=result.description, hashtags=list(result.hashtags), keywords=list(result.keywords), content_type="script")
                    st.success("Script is now part of the shared project context.")


def render_content_studio_workspace() -> None:
    """Focused Idea Generator page built from the existing generation workflow without mixing in unrelated tool tabs."""
    render_workspace_header("Idea Generator", "Generate strong content ideas and title options for the active project.")
    project_platform = render_platform_picker(key="content_studio_platform")

    tabs = st.tabs(["Ideas", "Titles"])

    with tabs[0]:
        with st.container(border=True):
            niche = st.text_input("Channel / content niche", value=st.session_state.get("project_context", {}).get("topic") or st.session_state.get("project_context", {}).get("idea") or "", key="content_ideas_niche")
            audience = st.text_input("Target audience", value=st.session_state.get("project_context", {}).get("audience") or "", key="content_ideas_audience")
            platform = st.selectbox("Platform", PROJECT_PLATFORM_OPTIONS, index=PROJECT_PLATFORM_OPTIONS.index(project_platform) if project_platform in PROJECT_PLATFORM_OPTIONS else 0, key="content_ideas_platform")
            content_type = st.selectbox("Content type", ["Video", "Short", "Podcast", "Guide", "Series"], index=0, key="content_ideas_type")
            duration_choice = st.selectbox("Video duration", ["3-5 min", "8-10 min", "15-20 min", "Short-form"], index=1, key="content_ideas_duration")
            lang = st.selectbox("Language", list(SUPPORTED_LANGUAGES), index=list(SUPPORTED_LANGUAGES).index(current_lang()), key="content_ideas_lang")
            notes = st.text_area("Additional context", value="", key="content_ideas_context", height=100)
            generate_clicked = st.button("Generate Ideas", type="primary", key="content_ideas_generate")

        if generate_clicked:
            if niche.strip():
                prompt_vibe = st.session_state.get("project_context", {}).get("vibe") or "practical"
                with st.spinner("Generating ideas..."):
                    normalized_duration = normalize_duration_value(duration_choice)
                    items = generate_ideas(
                        niche.strip(),
                        FREE_IDEAS_COUNT,
                        platform=platform,
                        vibe=prompt_vibe,
                        audience=audience,
                        lang=lang,
                        duration=normalized_duration,
                        content_type=content_type,
                        content_format=content_type,
                        additional_context=notes,
                    )
                    st.session_state["ideas"] = items
                    st.session_state["ideas_niche"] = niche.strip()
                    st.session_state["ideas_generation_context"] = {
                        "platform": platform,
                        "audience": audience,
                        "duration": normalized_duration,
                        "content_type": content_type,
                        "language": lang,
                    }
                    update_project_context(
                        topic=niche.strip(),
                        idea=items[0].title if items else niche.strip(),
                        titles=[idea.title for idea in items],
                        selected_title=items[0].title if items else "",
                        content_type="idea",
                        platform=platform,
                        audience=audience,
                    )
                    st.success("Ideas generated and saved to the project context.")
            else:
                st.warning("Please enter a niche or topic first.")

        if st.session_state.get("ideas"):
            generated_context = st.session_state.get("ideas_generation_context") or {"platform": platform}
            generated_platform = generated_context.get("platform") or platform
            _render_idea_result(
                st.session_state["ideas"],
                st.session_state.get("ideas_niche", ""),
                platform=generated_platform,
                details=generated_context,
            )
            with st.container(border=True):
                if st.button("Save ideas to project", key="content_ideas_save"):
                    update_project_context(topic=(st.session_state.get("ideas_niche") or niche), titles=[idea.title for idea in st.session_state["ideas"]], selected_title=st.session_state["ideas"][0].title, content_type="idea", platform=generated_platform)
                    st.success("Saved to project context.")

    with tabs[1]:
        with st.container(border=True):
            base_idea = st.text_input("Base idea", value=st.session_state.get("project_context", {}).get("idea") or st.session_state.get("project_context", {}).get("project_idea") or "", key="content_title_base")
            manual_titles = st.text_area("Title variants", value="\n".join(st.session_state.get("project_context", {}).get("titles", [])), height=150, key="content_title_variants")
            col_a, col_b = st.columns(2)
            with col_a:
                generate_titles_clicked = st.button("Generate Title Ideas", key="content_titles_generate")
            with col_b:
                save_titles_clicked = st.button("Save titles to project", key="save_content_titles")
        if generate_titles_clicked and base_idea.strip():
            with st.spinner("Creating title variants..."):
                generated = generate_ideas(
                    base_idea.strip(),
                    3,
                    platform=project_platform,
                    audience=st.session_state.get("project_context", {}).get("audience") or "",
                    lang=current_lang(),
                )
                titles = [idea.title for idea in generated]
                update_project_context(topic=base_idea.strip(), idea=base_idea.strip(), titles=titles, selected_title=titles[0] if titles else "", content_type="title", platform=project_platform)
                st.success("Title ideas generated.")
        if save_titles_clicked:
            saved = [line.strip() for line in manual_titles.splitlines() if line.strip()]
            update_project_context(titles=saved, selected_title=saved[0] if saved else "", content_type="title")
            st.success("Titles saved to project context.")
        if st.session_state.get("project_context", {}).get("titles"):
            with st.container(border=True):
                st.markdown(f"### {t('result.title')}")
                selected_title = st.session_state.get("project_context", {}).get("selected_title")
                for idx, title in enumerate(st.session_state["project_context"]["titles"]):
                    is_selected = title == selected_title
                    st.markdown(
                        f"""
                        <div class="premium-card" style="padding: 1rem; border-color: {'rgba(52,211,153,0.38)' if is_selected else 'rgba(148,163,184,0.12)'}; background: {'rgba(16,185,129,0.08)' if is_selected else 'rgba(15,23,42,0.72)'}; margin-bottom: .8rem;">
                            <div style="display:flex; justify-content:space-between; align-items:center; gap:.5rem; margin-bottom: .5rem; flex-wrap: wrap;">
                                <span class="badge">#{idx + 1}</span>
                                {_selected_meta_html(is_selected, label='Selected')}
                            </div>
                            <h4 style="margin: 0; color: #F8FAFC;">{html_escape(title)}</h4>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                    c1, c2, c3, c4 = st.columns(4)
                    with c1:
                        if st.button("Use", key=f"title_use_{_artifact_key(title)}", use_container_width=True, type="primary" if is_selected else "secondary"):
                            update_project_context(selected_title=title, titles=st.session_state["project_context"].get("titles", []), content_type="title")
                            st.success("Title selected.")
                    with c2:
                        if st.button("Save", key=f"title_save_{_artifact_key(title)}", use_container_width=True):
                            update_project_context(titles=st.session_state["project_context"].get("titles", []), selected_title=title, content_type="title")
                            st.success("Title saved.")
                    with c3:
                        render_copy_button(title)
                    with c4:
                        if st.button("Evaluate", key=f"title_eval_{_artifact_key(title)}", use_container_width=True):
                            st.session_state["idea_eval_input"] = title
                            st.session_state["idea_eval_title"] = title
                            st.session_state["active_workspace"] = "Idea Evaluator"
                            update_project_context(selected_title=title, titles=st.session_state["project_context"].get("titles", []), content_type="title")
                            st.rerun()
                    st.markdown("<div style='margin-bottom: 0.5rem;'></div>", unsafe_allow_html=True)


def render_seo_workspace() -> None:
    """SEO & Discovery workspace: direct-use sections built from the existing SEO functions without inventing unsupported metrics."""
    render_workspace_header("SEO Optimizer", "One professional SEO page for discovery, title optimization, keywords, tags, and related outputs.")
    project_platform = render_platform_picker(key="seo_workspace_platform")

    tabs = st.tabs(["SEO Overview", "Keyword Research", "SEO Optimizer", "Search Tags", "Discovery"])

    with tabs[0]:
        with st.container(border=True):
            st.markdown("### SEO Overview")
            st.caption("High-level optimization output for the active topic.")
            topic = st.text_input("Video topic", value=st.session_state.get("project_context", {}).get("topic") or st.session_state.get("project_context", {}).get("idea") or "", key="workspace_seo_topic")
            niche = st.text_input("Niche / category", value=st.session_state.get("project_context", {}).get("topic") or st.session_state.get("project_context", {}).get("idea") or "", key="workspace_seo_niche")
            overview_clicked = st.button("Generate SEO Overview", type="primary", key="seo_workspace_generate")
        if overview_clicked:
            if topic.strip() and niche.strip():
                with st.spinner("Generating SEO output..."):
                    _, seo_context = _seo_generation_inputs(
                        title=topic,
                        description=st.session_state.get("project_context", {}).get("description") or "",
                        niche=niche,
                        primary_keyword=(st.session_state.get("project_context", {}).get("keywords") or [""])[0] if st.session_state.get("project_context", {}).get("keywords") else "",
                        audience=st.session_state.get("project_context", {}).get("audience") or "",
                        platform=project_platform,
                    )
                    result = _seo_from_groq(topic.strip(), seo_context, lang=current_lang())
                    st.session_state["seo_result"] = result
                    st.session_state["seo_result_context"] = {"platform": project_platform, "topic": topic.strip(), "niche": niche.strip()}
                    update_project_context(topic=topic.strip(), idea=topic.strip(), seo=result.seo_description, keywords=list(result.seo_tags), search_tags=list(result.seo_tags), content_type="seo", platform=project_platform)
                    st.success("SEO data generated and saved to the project context.")
            else:
                st.warning("Please provide both the topic and niche.")
        data = st.session_state.get("seo_result")
        if isinstance(data, SEOData):
            _render_seo_result(data, details=st.session_state.get("seo_result_context"))
            with st.container(border=True):
                c1, c2 = st.columns(2)
                with c1:
                    render_copy_button(_chat_output_text({"kind": "seo", "data": data}))
                with c2:
                    if st.button("Save SEO to project", key="seo_workspace_save", use_container_width=True):
                        update_project_context(seo=data.seo_description, keywords=list(data.seo_tags), search_tags=list(data.seo_tags), content_type="seo")
                        st.success("SEO saved to project context.")

    with tabs[1]:
        st.markdown("### Keyword Research")
        st.caption("Keyword-focused output using the active SEO data and project context.")
        if st.session_state.get("seo_result"):
            tags = st.session_state["seo_result"].seo_tags
            with st.container(border=True):
                st.markdown(f"### {t('result.keywords')}")
                if tags:
                    st.markdown(_render_chip_row(tags, limit=12), unsafe_allow_html=True)
                else:
                    st.info("The SEO result did not include keyword tags.")
                if st.button("Save keywords to project", key="seo_keywords_save"):
                    update_project_context(keywords=list(tags), search_tags=list(tags), content_type="keyword")
                    st.success("Keywords saved.")
        else:
            st.info("No SEO keywords generated yet. Use the SEO Overview tab to create them.")

    with tabs[2]:
        with st.container(border=True):
            st.markdown("### SEO Optimizer")
            st.caption("Optimize title, description, and keyword output using the existing SEO backend.")
            seo_title = st.text_input("Title", value=st.session_state.get("project_context", {}).get("selected_title") or "", key="seo_optimizer_title")
            seo_description = st.text_area("Description", value=st.session_state.get("project_context", {}).get("seo") or st.session_state.get("project_context", {}).get("description") or "", key="seo_optimizer_description", height=130)
            seo_niche = st.text_input("Niche", value=st.session_state.get("project_context", {}).get("topic") or st.session_state.get("project_context", {}).get("idea") or "", key="seo_optimizer_niche")
            seo_keyword = st.text_input("Primary keyword", value=(st.session_state.get("project_context", {}).get("keywords") or [""])[0] if st.session_state.get("project_context", {}).get("keywords") else "", key="seo_optimizer_keyword")
            seo_audience = st.text_input("Audience", value=st.session_state.get("project_context", {}).get("audience") or "", key="seo_optimizer_audience")
            optimize_clicked = st.button("Optimize SEO", type="primary", key="seo_optimizer_button")
        if optimize_clicked:
            if any(value.strip() for value in (seo_title, seo_description, seo_niche, seo_keyword)):
                with st.spinner("Optimizing SEO..."):
                    seo_topic, seo_context = _seo_generation_inputs(
                        title=seo_title,
                        description=seo_description,
                        niche=seo_niche,
                        primary_keyword=seo_keyword,
                        audience=seo_audience,
                        platform=project_platform,
                    )
                    result = _seo_from_groq(seo_topic, seo_context, lang=current_lang())
                    st.session_state["seo_result"] = result
                    st.session_state["seo_result_context"] = {"platform": project_platform, "topic": seo_topic, "niche": seo_niche.strip()}
                    update_project_context(seo=result.seo_description, keywords=list(result.seo_tags), search_tags=list(result.seo_tags), selected_title=seo_title.strip() or st.session_state.get("project_context", {}).get("selected_title", ""), content_type="seo", platform=project_platform)
                    st.success("SEO optimization produced and saved.")
            else:
                st.warning("Add a title or topic before optimizing SEO.")
        data = st.session_state.get("seo_result")
        if isinstance(data, SEOData):
            _render_seo_result(data, details=st.session_state.get("seo_result_context"))

    with tabs[3]:
        st.markdown("### Search Tags")
        st.caption("Search tags and keyword reuse for discovery and SEO placement.")
        if st.session_state.get("seo_result"):
            tags = st.session_state["seo_result"].seo_tags
            with st.container(border=True):
                st.markdown("### Search tags")
                if tags:
                    st.markdown(_render_chip_row(tags, limit=12), unsafe_allow_html=True)
                else:
                    st.info("The SEO result did not include search tags.")
                if st.button("Save tags to project", key="seo_tags_save"):
                    update_project_context(search_tags=list(tags), keywords=list(tags), content_type="tags")
                    st.success("Tags saved.")
        else:
            st.info("Generate SEO output to populate tags.")

    with tabs[4]:
        with st.container(border=True):
            st.markdown("### Discovery")
            st.caption("Discovery-ready inputs prepared for continued keyword expansion while preserving the current working SEO functions.")
            discovery_topic = st.text_input("Discovery topic", value=st.session_state.get("project_context", {}).get("topic") or st.session_state.get("project_context", {}).get("idea") or "", key="seo_discovery_topic")
            discovery_niche = st.text_input("Discovery niche", value=project_platform, key="seo_discovery_niche")
            discovery_clicked = st.button("Prepare discovery brief", key="seo_discovery_run")
        if discovery_clicked:
            if discovery_topic.strip():
                update_project_context(topic=discovery_topic.strip(), platform=discovery_niche.strip() or project_platform, content_type="discovery")
                with st.container(border=True):
                    st.markdown("### Discovery brief")
                    st.markdown(f"**{t('result.topic')}:** {html_escape(discovery_topic.strip())}", unsafe_allow_html=True)
                    st.markdown(f"**{t('result.platform')}:** {html_escape(discovery_niche.strip() or project_platform)}", unsafe_allow_html=True)
                    st.info("Discovery brief prepared in the current project context.")
            else:
                st.warning("Enter a discovery topic to prepare the context.")


def render_visual_prompt_studio_workspace() -> None:
    """Visual Prompt Studio: keeping visual concepting and prompt guidance in one product page without claiming unsupported image generation."""
    render_visual_workspace()


def render_visual_workspace() -> None:
    """Visual Studio workspace for concepts, prompts, and visual direction, without claiming unsupported image generation."""
    render_workspace_header("Visual Prompt Studio", "Generate visual concepts, thumbnail direction, and prompt guidance without claiming unsupported final-image generation.")
    project_platform = render_platform_picker(key="visual_workspace_platform")

    tabs = st.tabs(["Visual Concept", "Thumbnail Direction", "Image Prompt", "Saved Visual Direction"])

    with tabs[0]:
        with st.container(border=True):
            st.markdown("### Visual Concept")
            st.caption("A single clear concept for the project that can be reused across thumbnail and campaign work.")
            visual_topic = st.text_input("Concept topic", value=st.session_state.get("project_context", {}).get("topic") or st.session_state.get("project_context", {}).get("selected_title") or st.session_state.get("project_context", {}).get("idea") or "", key="visual_concept_topic")
            create_concept_clicked = st.button("Create concept", key="visual_concept_create")
        if create_concept_clicked:
            if visual_topic.strip():
                concept = f"High-contrast {project_platform} visual concept for '{visual_topic.strip()}': clear focal point, readable typography, dramatic lighting, and a curiosity-driven headline."
                update_project_context(topic=visual_topic.strip(), visual_direction=concept, content_type="visual", platform=project_platform)
                st.session_state["thumbnail_prompt"] = concept
                st.success("Visual concept created and saved to project context.")
        if st.session_state.get("thumbnail_prompt"):
            brief_text = st.session_state.get("thumbnail_prompt") or st.session_state.get("project_context", {}).get("visual_direction") or ""
            _render_visual_result("Visual Brief", brief_text, meta="Thumbnail concept")
            if st.button("Send concept to Chat", key="visual_concept_send_to_chat"):
                st.session_state["main_ai_copilot_input"] = str(st.session_state["thumbnail_prompt"])
                st.session_state["active_workspace"] = "AI Chat"
                st.rerun()

    with tabs[1]:
        with st.container(border=True):
            st.markdown("### Thumbnail Direction")
            st.caption("Thumbnail-ready direction based on the current topic and platform.")
            direction = st.text_area("Visual direction", value=st.session_state.get("project_context", {}).get("visual_direction") or st.session_state.get("thumbnail_prompt") or (f"{st.session_state.get('project_context', {}).get('selected_title') or st.session_state.get('project_context', {}).get('idea') or st.session_state.get('project_context', {}).get('topic') or 'your topic'} on {project_platform} with strong hook, readable headline, and cinematic framing."), key="visual_direction_input", height=150)
            save_direction_clicked = st.button("Save direction", key="visual_direction_save")
        if save_direction_clicked:
            update_project_context(visual_direction=direction.strip(), content_type="visual", platform=project_platform)
            st.success("Direction saved to project context.")
        if direction.strip():
            _render_visual_result("Direction", direction, meta=project_platform)

    with tabs[2]:
        with st.container(border=True):
            st.markdown("### Image Prompt / Visual Prompt")
            st.caption("Prompt text ready for future design or generation workflows without claiming unsupported generation features.")
            prompt = st.text_area("Prompt", value=st.session_state.get("thumbnail_prompt") or "", key="visual_prompt_input", height=170)
            generate_prompt_clicked = st.button("Generate prompt", key="visual_prompt_generate")
        if generate_prompt_clicked:
            project_topic = st.session_state.get("project_context", {}).get("topic") or visual_topic.strip()
            if project_topic or prompt.strip():
                topic_for_prompt = project_topic or prompt.strip()
                user_direction = f" User-provided direction: {prompt.strip()}" if prompt.strip() else ""
                prompt_text = f"Create a cinematic {project_platform} thumbnail concept for '{topic_for_prompt}'. Use a bold headline, high contrast, readable type, strong focal point, and premium storytelling composition.{user_direction}"
                update_project_context(topic=project_topic or topic_for_prompt, visual_direction=prompt_text, content_type="visual", platform=project_platform)
                st.session_state["thumbnail_prompt"] = prompt_text
                st.success("Prompt generated.")
            else:
                st.warning("Add a topic first to create a valid prompt.")
        if st.session_state.get("thumbnail_prompt"):
            _render_visual_result("Prompt", st.session_state["thumbnail_prompt"], meta=project_platform)
            render_copy_button(st.session_state["thumbnail_prompt"])

    with tabs[3]:
        with st.container(border=True):
            st.markdown("### Saved Visual Direction")
            st.caption("Reusable visual direction stored in the project context.")
        stored = st.session_state.get("project_context", {}).get("visual_direction") or st.session_state.get("thumbnail_prompt") or ""
        if stored:
            brief = {
                "Concept": st.session_state.get("project_context", {}).get("visual_direction") or "",
                "Subject": st.session_state.get("project_context", {}).get("topic") or st.session_state.get("project_context", {}).get("idea") or "",
                "Composition": "Strong focal point, clear hierarchy, readable headline placement.",
                "Style": "Premium, cinematic, curiosity-driven.",
                "Text direction": "Headline-first with high contrast and legibility.",
                "Prompt": stored,
            }
            with st.container(border=True):
                st.markdown(f"### {t('result.visual')}")
                for label, value in brief.items():
                    if value:
                        render_artifact_card(label, value, badge=label, meta=project_platform)
            if st.button("Save to project", key="visual_saved_save"):
                update_project_context(visual_direction=stored, content_type="visual")
                st.success("Saved to project context.")
        else:
            st.info("No visual direction saved yet. Create one from the other tabs.")


def render_app_shell() -> None:
    """ChatGPT/Gemini-style shell with a collapsible sidebar and a single active workspace view."""
    st.session_state.setdefault("app_sidebar_open", True)
    st.session_state.setdefault("active_workspace", "AI Chat")

    with st.container(key="app_toolbar"):
        left_col, middle_col, right_col = st.columns([0.08, 0.42, 0.5])
        with left_col:
            if st.button("☰", key="app_sidebar_toggle", help="Toggle sidebar", use_container_width=True):
                st.session_state["app_sidebar_open"] = not st.session_state.get("app_sidebar_open", True)
                st.rerun()
        with middle_col:
            current_workspace = st.session_state.get("active_workspace", "AI Chat")
            st.markdown(
                f"<div style='display:flex; align-items:center; min-height: 38px; color: #F8FAFC; font-size: 0.96rem; font-weight: 700; letter-spacing: 0.02em;'>{html_escape(current_workspace)}</div>",
                unsafe_allow_html=True,
            )
        with right_col:
            render_language_switcher()

    if st.session_state.get("app_sidebar_open", True):
        sidebar_col, main_col = st.columns([0.28, 0.72], gap="medium")
        with sidebar_col:
            render_app_navigation()
        with main_col, st.container(key="app_workspace"):
            workspace = st.session_state.get("active_workspace", "AI Chat")
            if workspace == "AI Chat":
                render_ai_chat_workspace()
            elif workspace == "Idea Generator":
                render_idea_generator_workspace()
            elif workspace == "Idea Evaluator":
                render_idea_evaluator_workspace()
            elif workspace == "Script Writer":
                render_script_writer_workspace()
            elif workspace == "SEO Optimizer":
                render_seo_workspace()
            elif workspace == "Visual Prompt Studio":
                render_visual_prompt_studio_workspace()
    else:
        with st.container(key="app_workspace"):
            workspace = st.session_state.get("active_workspace", "AI Chat")
            if workspace == "AI Chat":
                render_ai_chat_workspace()
            elif workspace == "Idea Generator":
                render_idea_generator_workspace()
            elif workspace == "Idea Evaluator":
                render_idea_evaluator_workspace()
            elif workspace == "Script Writer":
                render_script_writer_workspace()
            elif workspace == "SEO Optimizer":
                render_seo_workspace()
            elif workspace == "Visual Prompt Studio":
                render_visual_prompt_studio_workspace()
    render_ai_error()


def render_workspace_layout() -> None:
    """Landing-page-only layout retained for the current marketing experience."""
    render_landing_page()


def main() -> None:
    init_session_state()
    st.session_state.setdefault("app_mode", "landing")
    st.set_page_config(
        page_title=t("page.title"),
        page_icon="⚡",
        layout="wide",
    )

    inject_custom_header()
    inject_styles()

    if st.session_state.get("app_mode") == "app":
        render_app_shell()
    else:
        render_workspace_layout()


if __name__ == "__main__":
    main()
