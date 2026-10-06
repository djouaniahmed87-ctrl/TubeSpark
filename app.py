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
    """Reads the JSON object out of a model answer, tolerating code fences."""
    text = raw.strip()
    if text.startswith("```"):
        text = re.sub(r"^```[a-zA-Z]*", "", text)
        text = re.sub(r"```$", "", text).strip()
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end <= start:
        raise GroqFormatError("no JSON object in the answer")
    try:
        data = json.loads(text[start : end + 1])
    except json.JSONDecodeError as exc:
        raise GroqFormatError(f"invalid JSON ({exc.msg})") from exc
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
    """
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]
    last: Exception | None = None

    for model in groq_model_candidates():
        for json_mode in (True, False):
            request: dict[str, Any] = {
                "messages": messages,
                "temperature": temperature,
                "max_tokens": 1400,
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
            return _parse_json_object(raw)

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
    return f"""You are an expert viral content strategist with 10 years of experience on
YouTube, TikTok and Instagram Reels. You turn one topic into ready-to-shoot video concepts
that a beginner can film today with a phone.

You always answer with valid JSON and nothing else: no markdown, no code fences, no
explanation before or after the object.

FIELDS
- "title": one punchy line, max 90 characters, specific and honest, no hashtags, no channel
  names, no fake promises.
- "hook": the full opening, not a summary. Describe the exact first two seconds shot by
  shot: what the camera sees, the on-screen text or number, and the line the creator says.
  Three to four concrete sentences a viewer can picture immediately.
- "value": the payoff in detail. What the viewer learns or can do after watching, why this
  angle beats the obvious one, and what makes them stay to the end. Three to four concrete
  sentences.
- "steps": an array with exactly three execution steps, each one a short instruction the
  creator can follow with a phone: the shot to film, the line to say, and the asset or
  screen to record.

DEPTH
- Every idea must be substantial enough to film this week. No thin concepts.
- Prefer a real number, a real tool, a real mistake or a real comparison over a general
  claim. Give the specifics a viewer would screenshot.
- The hook must open on the payoff or the tension, never on an introduction.

RULES
- Return exactly {count} ideas, each one a single shootable video.
- Keep the ideas different from each other, with different angles and opening shots.
- {format_rule}
- Write no filler: no "in this video", no emoji.
- {rules}

OUTPUT
Reply with one valid JSON object using exactly this shape, with exactly {count} items in
the "ideas" array:

{{"ideas": [{{"title": "...", "hook": "...", "value": "...", "steps": ["...", "...", "..."]}}]}}"""


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
        ideas.append(
            Idea(
                title=title,
                hook=_model_text(entry.get("hook"), 400),
                value=_model_text(entry.get("value"), 400),
                steps=steps,
            )
        )
    if not ideas:
        raise GroqFormatError("no usable idea in the answer")
    return ideas


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
        "hook": "لقطة علوية ثابتة مع حركة واحدة واضحة تُنفَّذ بالكامل قبل انتهاء المؤقت.",
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
__FONT_IMPORT__
<style>
:root {
    --brand-1: #ff2e63;
    --brand-2: #7b2ff7;
    --brand-3: #ff8a00;
    --ink: #0f1220;
    --muted: #5b6178;
    --card: #ffffff;
    --line: #e9ebf3;
}

html, body, .stApp, [data-testid="stMarkdownContainer"] p,
.stButton button, .stTextInput input, .stTextArea textarea {
    font-family: __FONT__;
}

.stApp {
    background:
        radial-gradient(900px 500px at 85% -10%, rgba(123,47,247,.16), transparent 60%),
        radial-gradient(700px 420px at 5% 0%, rgba(255,46,99,.14), transparent 60%),
        #f7f8fc;
    direction: __DIRECTION__;
}

.block-container {
    max-width: 1080px;
    padding-top: 1.6rem;
    padding-bottom: 3rem;
}

/* ---------- language switcher ---------- */
.ts-lang-bar {
    display: flex; align-items: center; justify-content: center;
    gap: .6rem; margin-bottom: .3rem;
}
.ts-lang-bar span.label { font-size: .8rem; font-weight: 700; color: var(--muted); }
[data-testid="stPills"] { justify-content: center; gap: .45rem; }
[data-testid="stPills"] button {
    border-radius: 999px; padding: .35rem 1.05rem; font-size: .85rem;
    border: 1.5px solid var(--line); background: #fff; color: var(--ink);
    font-weight: 700; transition: all .15s ease;
}
[data-testid="stPills"] button:hover { border-color: var(--brand-2); color: var(--brand-2); }
[data-testid="stPills"] button[kind="primary"] {
    background: linear-gradient(90deg, var(--brand-1), var(--brand-2));
    border: none; color: #fff;
}

/* ---------- header ---------- */
.ts-hero { text-align: center; margin-bottom: 1.6rem; }
.ts-badge {
    display: inline-block;
    background: linear-gradient(90deg, var(--brand-1), var(--brand-2));
    color: #fff; font-weight: 700; font-size: .82rem;
    padding: .3rem .85rem; border-radius: 999px; margin-bottom: .9rem;
}
.ts-hero h1 {
    font-size: clamp(1.75rem, 5.2vw, 2.9rem);
    line-height: 1.3; margin: 0 0 .5rem; color: var(--ink); font-weight: 800;
}
.ts-hero h1 .accent {
    background: linear-gradient(90deg, var(--brand-1), var(--brand-2));
    -webkit-background-clip: text; background-clip: text; color: transparent;
}
.ts-hero p {
    color: var(--muted); margin: 0 auto; max-width: 46ch;
    font-size: clamp(.95rem, 2.4vw, 1.08rem);
}

/* ---------- inputs ---------- */
.stTextInput input, .stTextArea textarea {
    border-radius: 14px; border: 1.5px solid var(--line);
    padding: .8rem 1rem; font-size: 1rem; background: #fff;
    color: #111111 !important; caret-color: #111111;
    -webkit-text-fill-color: #111111 !important;
}
.stTextInput input:focus, .stTextArea textarea:focus { border-color: var(--brand-2); }
.stTextInput input::placeholder, .stTextArea textarea::placeholder {
    color: #5f6478 !important; opacity: 1 !important;
    -webkit-text-fill-color: #5f6478 !important;
}
.stTextInput input:-webkit-autofill,
.stTextInput input:-webkit-autofill:hover,
.stTextInput input:-webkit-autofill:focus {
    -webkit-text-fill-color: #111111 !important;
    -webkit-box-shadow: 0 0 0 1000px #fff inset !important;
}
[data-baseweb="input"] > input, [data-baseweb="textarea"] > textarea {
    color: #111111 !important;
}

[data-testid="stButton"] button {
    border-radius: 14px; font-weight: 700; font-size: .95rem;
    padding: .6rem 1rem; border: 1.5px solid var(--line);
    background: #fff; color: var(--ink);
    box-shadow: none; transition: all .15s ease; min-height: 0;
}
[data-testid="stButton"] button:hover {
    border-color: var(--brand-2); color: var(--brand-2);
    transform: translateY(-2px);
}
[data-testid="stButton"] button[kind="primary"] {
    border: none; color: #fff; padding: .8rem 1.1rem; font-size: 1.05rem;
    background: linear-gradient(90deg, var(--brand-1), var(--brand-2));
    box-shadow: 0 10px 24px rgba(123,47,247,.28);
}
[data-testid="stButton"] button[kind="primary"]:hover {
    color: #fff; box-shadow: 0 14px 30px rgba(123,47,247,.38);
}

/* ---------- section title ---------- */
.ts-section {
    display: flex; align-items: center; gap: .6rem; margin: 2.2rem 0 1rem;
}
.ts-section h2 { font-size: clamp(1.15rem, 3.4vw, 1.5rem); margin: 0; color: var(--ink); font-weight: 800; }
.ts-section span.count {
    background: rgba(123,47,247,.12); color: var(--brand-2);
    border-radius: 999px; padding: .15rem .6rem; font-size: .8rem; font-weight: 700;
}
.ts-section span.mode {
    border-radius: 999px; padding: .15rem .65rem; font-size: .78rem; font-weight: 700;
    white-space: nowrap;
}
.ts-section span.mode.shorts { background: rgba(255,138,0,.14); color: #c26a00; }
.ts-section span.mode.long { background: rgba(0,132,255,.12); color: #0066cc; }
.ts-section span.mode.lang { background: rgba(0,180,120,.13); color: #00875a; }
@media (max-width: 640px) {
    .ts-section { flex-wrap: wrap; }
}

/* ---------- selectbox ---------- */
.ts-field-label {
    font-size: .78rem; font-weight: 700; color: var(--muted);
    margin-bottom: .3rem; text-align: start;
}
[data-testid="stSelectbox"] div[data-baseweb="select"] > div {
    border-radius: 14px; border: 1.5px solid var(--line);
    background: #fff; min-height: 2.85rem; align-items: center;
    font-weight: 700;
}
[data-testid="stSelectbox"] div[data-baseweb="select"] > div:focus-within {
    border-color: var(--brand-2);
}

/* ---------- chips ---------- */
.ts-chips-label {
    text-align: center; color: var(--muted); font-size: .85rem;
    margin: .9rem 0 .5rem; font-weight: 700;
}

/* ---------- social proof ---------- */
.ts-proof {
    display: flex; flex-wrap: wrap; align-items: center; justify-content: center;
    gap: .5rem; margin: .9rem 0 .2rem; padding: .55rem .9rem;
    background: linear-gradient(90deg, rgba(255,138,0,.10), rgba(123,47,247,.10));
    border: 1.5px solid rgba(123,47,247,.18); border-radius: 999px;
    font-size: .84rem; color: var(--muted); position: relative; overflow: hidden;
}
.ts-proof b { color: var(--ink); font-weight: 800; }
.ts-proof .sep { color: #c3c7d6; }
.ts-proof::after {
    content: ""; position: absolute; inset: 0; pointer-events: none;
    background: linear-gradient(100deg, transparent 35%, rgba(255,255,255,.55) 50%, transparent 65%);
    transform: translateX(-100%);
    animation: ts-shimmer 3.6s ease-in-out infinite;
}
@keyframes ts-shimmer {
    0% { transform: translateX(-100%); }
    55%, 100% { transform: translateX(100%); }
}
@media (prefers-reduced-motion: reduce) {
    .ts-proof::after { animation: none; }
}

/* ---------- mini outline ---------- */
.ts-outline { margin: 0; padding: 0; list-style: none; counter-reset: step; }
.ts-outline li {
    position: relative; padding-block: .35rem; padding-inline: 2rem 0;
    margin-bottom: .35rem; font-size: .88rem; line-height: 1.65; color: #41465c;
    border-bottom: 1px dashed var(--line);
}
.ts-outline li:last-child { border-bottom: none; margin-bottom: 0; }
.ts-outline li::before {
    counter-increment: step; content: counter(step);
    position: absolute; inset-inline-start: 0; top: .45rem;
    width: 20px; height: 20px; border-radius: 50%;
    background: linear-gradient(135deg, var(--brand-1), var(--brand-2));
    color: #fff; font-size: .68rem; font-weight: 800;
    display: flex; align-items: center; justify-content: center;
}
.ts-outline b { color: var(--ink); }

/* ---------- idea cards ---------- */
/* ---------- cards ---------- */
.ts-card {
    background: var(--card); border: 1.5px solid var(--line);
    border-radius: 12px; padding: 20px; display: flex;
    flex-direction: column; gap: .7rem; height: 100%;
    box-shadow: 0 2px 6px rgba(15,18,32,.05), 0 12px 28px rgba(15,18,32,.07);
    transition: transform .15s ease, box-shadow .15s ease;
}
.ts-card:hover {
    transform: translateY(-4px);
    box-shadow: 0 4px 10px rgba(15,18,32,.07), 0 18px 40px rgba(15,18,32,.13);
}
.ts-card .num {
    width: 30px; height: 30px; border-radius: 9px; display: flex;
    align-items: center; justify-content: center; font-weight: 800; font-size: .9rem;
    color: #fff; background: linear-gradient(135deg, var(--brand-1), var(--brand-2));
}
.ts-card h3 { margin: 0; font-size: 1.02rem; line-height: 1.5; color: var(--ink); font-weight: 700; }
.ts-card .row { border-top: 1px dashed var(--line); padding-top: .65rem; }
.ts-card .lbl {
    display: inline-block; font-size: .7rem; font-weight: 800; letter-spacing: .3px;
    padding: .15rem .5rem; border-radius: 6px; margin-bottom: .3rem;
}
.ts-card .lbl.hook { background: rgba(255,46,99,.12); color: var(--brand-1); }
.ts-card .lbl.value { background: rgba(0,180,120,.13); color: #00875a; }
.ts-card .lbl.plan { background: rgba(123,47,247,.13); color: var(--brand-2); }
.ts-card p { margin: 0; font-size: .9rem; line-height: 1.7; color: #41465c; }
.ts-card .ts-steps {
    margin: 0; padding-inline-start: 1.1rem; display: flex;
    flex-direction: column; gap: .35rem;
}
.ts-card .ts-steps li { font-size: .88rem; line-height: 1.65; color: #41465c; }

/* ---------- paywall ---------- */
.ts-paywall {
    margin-top: 2.4rem; border-radius: 24px; padding: 3px;
    background: linear-gradient(120deg, var(--brand-1), var(--brand-3), var(--brand-2));
    box-shadow: 0 18px 44px rgba(123,47,247,.22);
}
.ts-paywall-inner {
    background: #fff; border-radius: 21px; padding: clamp(1.2rem, 4vw, 2.4rem);
    text-align: center;
}
.ts-paywall .lock { font-size: 1.9rem; }
.ts-paywall h2 {
    margin: .5rem 0 .6rem; font-size: clamp(1.15rem, 3.6vw, 1.7rem);
    color: var(--ink); line-height: 1.55; font-weight: 800;
}
.ts-paywall .price {
    display: inline-flex; align-items: center; gap: .4rem; font-weight: 800;
    font-size: 1.05rem; color: var(--brand-1); background: rgba(255,46,99,.09);
    border-radius: 999px; padding: .3rem .9rem; margin-bottom: 1rem;
}
.ts-paywall ul {
    list-style: none; padding: 0; margin: 0 0 1.2rem; color: #41465c;
    display: flex; flex-wrap: wrap; gap: .5rem; justify-content: center;
}
.ts-paywall ul li { font-size: .88rem; }
.ts-paywall ul li::before { content: "\u2713 "; color: #00b478; font-weight: 800; }

/* ---------- CTA button ---------- */
.ts-cta {
    display: block; width: 100%; max-width: 460px; margin: 0 auto;
    text-align: center; text-decoration: none; color: #fff !important;
    font-weight: 800; font-size: clamp(1rem, 3vw, 1.12rem);
    padding: 1rem 1.4rem; border-radius: 16px;
    background: linear-gradient(90deg, var(--brand-1), var(--brand-2));
    box-shadow: 0 14px 30px rgba(255,46,99,.32);
    transition: transform .15s ease, box-shadow .15s ease;
}
.ts-cta:hover { transform: translateY(-3px); box-shadow: 0 20px 40px rgba(255,46,99,.42); }
.ts-fine { font-size: .76rem; color: #8a90a6; margin-top: .8rem; }

/* ---------- cross promo footer ---------- */
.ts-promo { margin-top: 2.6rem; border-top: 1px solid var(--line); padding-top: 1.4rem; text-align: center; }
.ts-promo h3 { margin: 0 0 .9rem; font-size: 1rem; color: var(--ink); font-weight: 800; }
.ts-promo-grid { display: grid; grid-template-columns: 1fr 1fr; gap: .8rem; max-width: 640px; margin: 0 auto; }
@media (max-width: 640px) { .ts-promo-grid { grid-template-columns: 1fr; } }
.ts-promo-item {
    display: flex; align-items: center; justify-content: space-between; gap: .6rem;
    background: #fff; border: 1.5px solid var(--line); border-radius: 14px;
    padding: .8rem 1rem; text-decoration: none; color: var(--ink) !important;
    font-weight: 700; font-size: .9rem; transition: all .15s ease; text-align: start;
}
.ts-promo-item:hover { border-color: var(--brand-3); background: #fffaf3; }
.ts-promo-item .price-tag { color: var(--brand-3); font-weight: 800; white-space: nowrap; }
.ts-promo-item .arrow { color: #b9bed0; }
.ts-copy { font-size: .78rem; color: #8a90a6; margin-top: 1.4rem; }

/* ---------- tabs ---------- */
[data-testid="stTabs"] [data-baseweb="tab-list"] {
    gap: .5rem; justify-content: center; background: transparent;
}
[data-testid="stTabs"] [data-baseweb="tab"] {
    font-weight: 700; font-size: 1rem; border-radius: 999px;
    padding: .55rem 1.2rem;
}
[data-testid="stTabs"] [data-baseweb="tab-highlight"] { border-radius: 999px; }
[data-testid="stTabs"] [data-baseweb="tab-border"] { background-color: var(--line); }
[data-testid="stTabs"] [aria-selected="true"] { color: var(--brand-2); }

/* ---------- evaluation ---------- */
.ts-eval-grid {
    display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-top: 1rem;
}
@media (max-width: 900px) { .ts-eval-grid { grid-template-columns: 1fr; } }

.ts-card.improved {
    border: none; padding: 3px;
    background: linear-gradient(120deg, var(--brand-1), var(--brand-2));
    box-shadow: 0 14px 34px rgba(123,47,247,.24);
}
.ts-card.improved:hover { transform: none; }
.ts-card.improved > .ts-card-body {
    background: #fff; border-radius: 15px; padding: 1.1rem 1.15rem;
    display: flex; flex-direction: column; gap: .7rem; height: 100%;
}
.ts-card.improved .lbl.angle { background: rgba(123,47,247,.12); color: var(--brand-2); }
.ts-card.improved .lbl.outline-lbl { background: rgba(255,138,0,.14); color: #c26a00; }
.ts-flag {
    display: inline-block; background: linear-gradient(90deg, var(--brand-1), var(--brand-2));
    color: #fff; font-size: .72rem; font-weight: 700;
    padding: .2rem .65rem; border-radius: 999px;
}
[data-testid="stMetricValue"] { font-weight: 800; color: var(--ink); }

/* ---------- misc ---------- */
.ts-note {
    text-align: center; color: var(--muted); font-size: .92rem;
    background: #fff; border: 1.5px dashed var(--line); border-radius: 16px;
    padding: 1.4rem; margin-top: 1.5rem;
}
#MainMenu, footer, .stDeployButton { visibility: hidden; }
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


def inject_styles() -> None:
    """Injects the stylesheet, tuned to the active language (font + text direction)."""
    lang = current_lang()
    css = (
        CSS_TEMPLATE.replace("__FONT_IMPORT__", FONT_IMPORTS[lang])
        .replace("__FONT__", FONT_STACKS[lang])
        .replace("__DIRECTION__", text_direction())
    )
    render_html(css)


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
    short_form = is_short_form(platform)
    mode_label = t("gen.mode_short") if short_form else t("gen.mode_long")
    mode_class = "mode shorts" if short_form else "mode long"

    render_html(
        f"""
        <div class="ts-section">
            <h2>{html_escape(t("gen.section_title", niche=niche))}</h2>
            <span class="{mode_class}">{html_escape(option_label("platform", platform, lang))} · {html_escape(mode_label)}</span>
            <span class="mode lang">{html_escape(LANGUAGE_LABELS[lang])}</span>
            <span class="count">{html_escape(t("gen.count_badge", n=len(ideas)))}</span>
        </div>
        """
    )

    core_label = html_escape(t("card.core"))
    why_label = html_escape(t("card.why"))

    offset = 0
    for row in chunked(ideas):
        for column, idea in zip(st.columns(len(row)), row):
            with column:
                steps = "".join(f"<li>{html_escape(step)}</li>" for step in idea.steps)
                plan = (
                    f'<div class="row"><span class="lbl plan">{html_escape(t("card.plan"))}</span>'
                    f'<ol class="ts-steps">{steps}</ol></div>'
                    if steps
                    else ""
                )
                render_html(
                    f"""
                    <div class="ts-card">
                        <div class="num">{offset + 1}</div>
                        <h3>{html_escape(idea.title)}</h3>
                        <div class="row">
                            <span class="lbl hook">{core_label}</span>
                            <p>{html_escape(idea.hook)}</p>
                        </div>
                        <div class="row">
                            <span class="lbl value">{why_label}</span>
                            <p>{html_escape(idea.value)}</p>
                        </div>
                        {plan}
                    </div>
                    """
                )
                render_copy_button(idea_to_clipboard(idea))
        offset += len(row)


def render_paywall(context: str = "generate") -> None:
    generate = context == "generate"
    headline = t("pay.generate_headline" if generate else "pay.evaluate_headline", price=PRICE_LABEL)
    cta = t("pay.cta_generate" if generate else "pay.cta_evaluate")
    benefits = "\n".join(f"<li>{html_escape(t(f'pay.b{index}'))}</li>" for index in range(1, 7))
    render_html(
        f"""
        <div class="ts-paywall">
            <div class="ts-paywall-inner">
                <div class="lock">🔒</div>
                <h2>{html_escape(headline)}</h2>
                <div class="price">{html_escape(PRICE_LABEL)} — {html_escape(t("pay.price_suffix"))}</div>
                <ul>
                    {benefits}
                </ul>
                <a class="ts-cta" href="{CHECKOUT_URL}" target="_blank" rel="noopener">
                    {html_escape(cta)}
                </a>
                <div class="ts-fine">{html_escape(t("pay.fine"))}</div>
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

    # the copy action belongs to the improved card, so it sits in that column
    spacer, holder = st.columns(2)
    with holder:
        render_copy_button(idea_to_clipboard(result.idea))


def render_footer() -> None:
    arrow = ARROW_LEFT if is_rtl() else ARROW_RIGHT
    credit = "footer.copy" if groq_is_ready() else "footer.copy_fallback"
    render_html(
        f"""
        <div class="ts-promo">
            <h3>{html_escape(t("footer.title"))}</h3>
            <div class="ts-promo-grid">
                <a class="ts-promo-item" href="{TITLE_SEO_URL}" target="_blank" rel="noopener">
                    <span>{html_escape(t("footer.tool1"))}</span>
                    <span><span class="price-tag">2.99$</span> <span class="arrow">{arrow}</span></span>
                </a>
                <a class="ts-promo-item" href="{AUTO_SUBTITLE_URL}" target="_blank" rel="noopener">
                    <span>{html_escape(t("footer.tool2"))}</span>
                    <span><span class="price-tag">4.99$</span> <span class="arrow">{arrow}</span></span>
                </a>
            </div>
            <div class="ts-copy">{html_escape(t(credit))}</div>
        </div>
        """
    )


# --------------------------------------------------------------------------------------
# Tabs
# --------------------------------------------------------------------------------------


def render_generator_tab() -> None:
    lang = current_lang()

    col_niche, col_vibe = st.columns([2, 1], gap="small")

    with col_niche:
        render_html(
            f'<div class="ts-field-label">{html_escape(t("gen.niche_label"))}</div>'
        )
        niche = st.text_input(
            t("gen.niche_label"),
            key="niche",
            placeholder=t("gen.niche_placeholder"),
            label_visibility="collapsed",
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

    col_platform, col_audience = st.columns(2, gap="small")

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

    if st.button(t("gen.generate_btn"), type="primary", width="stretch", icon=":material/bolt:"):
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


def main() -> None:
    init_session_state()
    st.set_page_config(
        page_title=t("page.title"),
        page_icon="⚡",
        layout="centered",
    )

    inject_styles()
    render_language_switcher()
    render_hero()

    tab_ideas, tab_evaluate = st.tabs([t("tab.ideas"), t("tab.evaluate")])
    with tab_ideas:
        render_generator_tab()
    with tab_evaluate:
        render_evaluate_tab()

    render_footer()


if __name__ == "__main__":
    main()