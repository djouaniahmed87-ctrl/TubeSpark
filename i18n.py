"""Localization layer for TubeSpark.

Holds every interface string in three languages plus the small helpers the app uses to
read them. The active language lives in `st.session_state["lang"]` and defaults to English.

Add a new language by:
  1. adding its code to `SUPPORTED_LANGUAGES` (and to `RTL_LANGUAGES` for right-to-left),
  2. adding a label in `LANGUAGE_LABELS`,
  3. filling the missing keys of `I18N` for that code,
  4. adding the matching content pool in `app.py` (`TEMPLATE_POOLS`, `UPGRADE_PATTERNS`,
     `PLATFORM_FLAVOR` / `VIBE_FLAVOR` / `AUDIENCE_FLAVOR`, `NICHE_EXAMPLES`,
     `QUESTION_WORDS` / `CURIOSITY_WORDS` / `SPECIFIC_WORDS`) and its font in the app CSS map.
"""

from __future__ import annotations

from typing import Any

import streamlit as st

DEFAULT_LANGUAGE = "en"
SUPPORTED_LANGUAGES: tuple[str, ...] = ("en", "ar", "fr")
RTL_LANGUAGES: frozenset[str] = frozenset({"ar"})

LANGUAGE_LABELS: dict[str, str] = {
    "ar": "العربية 🇸🇦",
    "en": "English 🇺🇸",
    "fr": "Français 🇫🇷",
}

ARROW_RIGHT = "→"
ARROW_LEFT = "←"


def init_session_state() -> None:
    """Seeds session state so a brand new visitor gets the English interface."""
    if "lang" not in st.session_state:
        st.session_state["lang"] = DEFAULT_LANGUAGE


def current_lang() -> str:
    lang = st.session_state.get("lang", DEFAULT_LANGUAGE)
    return lang if lang in SUPPORTED_LANGUAGES else DEFAULT_LANGUAGE


def is_rtl(lang: str | None = None) -> bool:
    return (lang or current_lang()) in RTL_LANGUAGES


def text_direction() -> str:
    return "rtl" if is_rtl() else "ltr"


def t(key: str, **kwargs: Any) -> str:
    """Returns the interface string for `key` in the active session language."""
    return t_for(current_lang(), key, **kwargs)


def t_for(lang: str, key: str, **kwargs: Any) -> str:
    """Returns the interface string for `key` in an explicit language."""
    entry = I18N.get(key)
    if entry is None:
        return key
    value = entry.get(lang if lang in SUPPORTED_LANGUAGES else DEFAULT_LANGUAGE) or entry.get(
        DEFAULT_LANGUAGE, key
    )
    return value.format(**kwargs) if kwargs else value


def option_label(group: str, key: str, lang: str | None = None) -> str:
    """Localized label of an option that is stored under a stable internal key."""
    lang = lang if lang in SUPPORTED_LANGUAGES else current_lang()
    entry = I18N.get(f"{group}.{key}")
    if not entry:
        return key
    return entry.get(lang) or entry.get(DEFAULT_LANGUAGE, key)


def flavor(flavors: dict[str, dict[str, str]], key: str, lang: str | None = None) -> str:
    """Localized targeting note for a platform / vibe / audience key."""
    lang = lang if lang in SUPPORTED_LANGUAGES else current_lang()
    entry = flavors.get(key)
    if not entry:
        return ""
    return entry.get(lang) or entry.get(DEFAULT_LANGUAGE, "")


I18N: dict[str, dict[str, str]] = {
    # ---- brand / hero --------------------------------------------------------------
    "brand.badge": {
        "en": "TubeSpark · Idea Generator",
        "ar": "TubeSpark · مولّد أفكار",
        "fr": "TubeSpark · Générateur d'idées",
    },
    "hero.title_pre": {
        "en": "Ready-to-post video ideas for ",
        "ar": "أفكار يوتيوب جاهزة للنشر في ",
        "fr": "Des idées vidéo prêtes à publier pour ",
    },
    "hero.title_accent": {
        "en": "your niche",
        "ar": "مجالك",
        "fr": "votre niche",
    },
    "hero.subtitle": {
        "en": "Type your channel niche and get ideas with proven titles and hooks — free to try.",
        "ar": "اكتب مجال قناتك، واحصل على أفكار تحتوي عناوين وخطافات مثبتة — مجاناً للتجربة.",
        "fr": "Saisis le thème de ta chaîne et reçois des idées avec des titres et accroches éprouvés — gratuitement.",
    },
    "page.title": {
        "en": "TubeSpark — YouTube idea generator",
        "ar": "TubeSpark — مولّد أفكار يوتيوب",
        "fr": "TubeSpark — Générateur d'idées YouTube",
    },
    # ---- language switcher ---------------------------------------------------------
    "lang.label": {
        "en": "🌐 Interface language",
        "ar": "🌐 لغة الواجهة",
        "fr": "🌐 Langue de l'interface",
    },
    "lang.switch": {
        "en": "Language",
        "ar": "اللغة",
        "fr": "Langue",
    },
    # ---- tabs ----------------------------------------------------------------------
    "tab.ideas": {
        "en": "⚡ Inspire me with new ideas",
        "ar": "⚡ ألهمني بأفكار جديدة",
        "fr": "⚡ Inspirez-moi de nouvelles idées",
    },
    "tab.evaluate": {
        "en": "🎯 Rate & upgrade my idea",
        "ar": "🎯 قيّم وطوّر فكرتي",
        "fr": "🎯 Notez et améliorez mon idée",
    },
    "tab.script": {
        "en": "✍️ Quick script writer",
        "ar": "✍️ كاتب السكريبت السريع",
        "fr": "✍️ Scénariste rapide",
    },
    "tab.seo": {
        "en": "🚀 SEO booster",
        "ar": "🚀 مُحسّن السيو",
        "fr": "🚀 Booster SEO",
    },
    "tab.analyzer": {
        "en": "🔍 Smart analyzer & rating",
        "ar": "🔍 المحلل الذكي والتقييم",
        "fr": "🔍 Analyseur intelligent",
    },
    "tab.thumbnails": {
        "en": "🖼️ Thumbnail ideas",
        "ar": "🖼️ أفكار الصورة المصغرة",
        "fr": "🖼️ Idées de miniatures",
    },
    "tab.all": {
        "en": "✨ All-in-one",
        "ar": "✨ منصة متكاملة",
        "fr": "✨ Tout-en-un",
    },
    # ---- generator fields ----------------------------------------------------------
    "gen.niche_label": {
        "en": "What is your channel niche?",
        "ar": "ما مجال قناتك؟",
        "fr": "Quel est le thème de ta chaîne ?",
    },
    "gen.niche_placeholder": {
        "en": "e.g. trading, gaming, cooking",
        "ar": "مثال: تداول، ألعاب، طبخ",
        "fr": "ex. : trading, gaming, cuisine",
    },
    "gen.vibe_label": {
        "en": "Video style",
        "ar": "أسلوب الفيديو",
        "fr": "Style de vidéo",
    },
    "gen.platform_label": {
        "en": "Target platform",
        "ar": "المنصة المستهدفة",
        "fr": "Plateforme ciblée",
    },
    "gen.audience_label": {
        "en": "Target audience",
        "ar": "الجمهور المستهدف",
        "fr": "Audience ciblée",
    },
    "gen.generate_btn": {
        "en": "⚡ Generate ideas",
        "ar": "⚡ ولّد الأفكار",
        "fr": "⚡ Générer les idées",
    },
    "gen.empty_niche_warning": {
        "en": "Enter your channel niche first, for example: gaming or cooking.",
        "ar": "اكتب مجال قناتك أولاً، مثل: ألعاب أو طبخ.",
        "fr": "Saisis d'abord le thème de ta chaîne, par exemple : gaming ou cuisine.",
    },
    "gen.more_btn": {
        "en": "More ideas",
        "ar": "أفكار أخرى",
        "fr": "Plus d'idées",
    },
    "gen.clear_btn": {
        "en": "Clear",
        "ar": "مسح",
        "fr": "Effacer",
    },
    "gen.chips_label": {
        "en": "Or pick a ready niche:",
        "ar": "أو اختر مجالاً جاهزاً:",
        "fr": "Ou choisis un thème prêt :",
    },
    "gen.niche_pills": {
        "en": "Suggested niches",
        "ar": "مجالات مقترحة",
        "fr": "Thèmes suggérés",
    },
    "gen.empty_note": {
        "en": "No ideas yet — enter your channel niche and press the button to start. "
        "This demo runs on mock data.",
        "ar": "لم تُولّد الأفكار بعد — أدخل مجال قناتك واضغط على الزر للبدء. "
        "هذه نسخة تجريبية تعمل ببيانات وهمية (Mock Data).",
        "fr": "Aucune idée pour l'instant — saisis le thème de ta chaîne et clique sur le bouton "
        "pour commencer. Cette démo utilise des données fictives.",
    },
    "gen.section_title": {
        "en": "Free sample for niche: {niche}",
        "ar": "عينة مجانية لمجال: {niche}",
        "fr": "Échantillon gratuit pour le thème : {niche}",
    },
    "gen.count_badge": {
        "en": "{n} ideas",
        "ar": "{n} أفكار",
        "fr": "{n} idées",
    },
    "gen.mode_short": {
        "en": "short",
        "ar": "قصير",
        "fr": "court",
    },
    "gen.mode_long": {
        "en": "long",
        "ar": "طويل",
        "fr": "long",
    },
    # ---- platform options ----------------------------------------------------------
    "platform.youtube_long": {
        "en": "YouTube (long-form)",
        "ar": "يوتيوب (فيديو طويل)",
        "fr": "YouTube (format long)",
    },
    "platform.youtube_shorts": {
        "en": "YouTube Shorts",
        "ar": "يوتيوب Shorts",
        "fr": "YouTube Shorts",
    },
    "platform.tiktok": {
        "en": "TikTok",
        "ar": "تيك توك",
        "fr": "TikTok",
    },
    "platform.reels": {
        "en": "Instagram Reels",
        "ar": "إنستغرام Reels",
        "fr": "Instagram Reels",
    },
    "platform.facebook": {
        "en": "Facebook",
        "ar": "فيسبوك",
        "fr": "Facebook",
    },
    # ---- video style options -------------------------------------------------------
    "vibe.comedy": {
        "en": "Comedy",
        "ar": "كوميدي",
        "fr": "Humour",
    },
    "vibe.serious_edu": {
        "en": "Serious educational",
        "ar": "تعليمي جاد",
        "fr": "Éducatif sérieux",
    },
    "vibe.story": {
        "en": "Story & experience",
        "ar": "قصة وتجربة",
        "fr": "Récit et expérience",
    },
    "vibe.challenge": {
        "en": "Challenge & adventure",
        "ar": "تحدي ومغامرة",
        "fr": "Défi et aventure",
    },
    "vibe.contrarian": {
        "en": "Bold & controversial",
        "ar": "صادم ومثير للجدل",
        "fr": "Audacieux et provocateur",
    },
    # ---- audience options ----------------------------------------------------------
    "audience.beginners": {
        "en": "Beginners",
        "ar": "مبتدئين",
        "fr": "Débutants",
    },
    "audience.pros": {
        "en": "Professionals",
        "ar": "محترفين",
        "fr": "Professionnels",
    },
    "audience.teens": {
        "en": "Teens",
        "ar": "مراهقين",
        "fr": "Ados",
    },
    "audience.kids": {
        "en": "Kids",
        "ar": "أطفال",
        "fr": "Enfants",
    },
    "audience.general": {
        "en": "General audience",
        "ar": "عامة الناس",
        "fr": "Grand public",
    },
    # ---- niche chips ---------------------------------------------------------------
    "niche.trading": {
        "en": "trading",
        "ar": "تداول",
        "fr": "trading",
    },
    "niche.gaming": {
        "en": "gaming",
        "ar": "ألعاب",
        "fr": "gaming",
    },
    "niche.cooking": {
        "en": "cooking",
        "ar": "طبخ",
        "fr": "cuisine",
    },
    "niche.fitness": {
        "en": "fitness",
        "ar": "تمارين",
        "fr": "fitness",
    },
    "niche.tech": {
        "en": "tech",
        "ar": "تكنولوجيا",
        "fr": "tech",
    },
    # ---- idea cards ----------------------------------------------------------------
    "card.core": {
        "en": "Core idea",
        "ar": "الفكرة الأساسية",
        "fr": "Idée principale",
    },
    "card.why": {
        "en": "Why it works",
        "ar": "سبب النجاح",
        "fr": "Pourquoi ça marche",
    },
    "card.hook": {
        "en": "First 3 seconds",
        "ar": "الخطاف لأول 3 ثوانٍ",
        "fr": "Les 3 premières secondes",
    },
    "card.angle": {
        "en": "Presentation angle",
        "ar": "زاوية التقديم",
        "fr": "Angle de présentation",
    },
    "card.outline": {
        "en": "Quick outline",
        "ar": "الهيكل السريع",
        "fr": "Plan rapide",
    },
    "card.plan": {
        "en": "How to film it",
        "ar": "كيف تصوّرها",
        "fr": "Comment la filmer",
    },
    "card.improved": {
        "en": "Upgraded idea",
        "ar": "الفكرة المطوّرة",
        "fr": "Idée améliorée",
    },
    "card.analysis": {
        "en": "Analysis card",
        "ar": "بطاقة التحليل",
        "fr": "Carte d'analyse",
    },
    "card.original": {
        "en": "Your original idea",
        "ar": "فكرتك الأصلية",
        "fr": "Ton idée d'origine",
    },
    "card.why_needs_work": {
        "en": "Why does this idea need work?",
        "ar": "لماذا تحتاج هذه الفكرة تطويراً؟",
        "fr": "Pourquoi cette idée mérite-t-elle des améliorations ?",
    },
    # ---- social proof --------------------------------------------------------------
    "proof.generated": {
        "en": "🔥 Over <b>{n}</b> ideas generated this week",
        "ar": "🔥 تم توليد أكثر من <b>{n}</b> فكرة هذا الأسبوع",
        "fr": "🔥 Plus de <b>{n}</b> idées générées cette semaine",
    },
    "proof.rating": {
        "en": "⭐⭐⭐⭐⭐ <b>({score}/5)</b> from {creators} creators",
        "ar": "⭐⭐⭐⭐⭐ <b>({score}/5)</b> من {creators} صانع محتوى",
        "fr": "⭐⭐⭐⭐⭐ <b>({score}/5)</b> de {creators} créateurs",
    },
    # ---- evaluate tab --------------------------------------------------------------
    "eval.note": {
        "en": "Write your idea in two lines: we rate how strong it is and upgrade it into a "
        "ready-to-post title and hook.",
        "ar": "اكتب فكرتك في سطرين، وسنخبرك بمدى قوتها ونطوّرها إلى عنوان وخطاف جاهز للنشر.",
        "fr": "Écris ton idée en deux lignes : nous évaluons sa solidité et la transformons en "
        "titre et accroche prêts à publier.",
    },
    "eval.label": {
        "en": "Your idea",
        "ar": "فكرتك",
        "fr": "Ton idée",
    },
    "eval.placeholder": {
        "en": "Write your idea here... e.g. a video about a 24-hour food challenge",
        "ar": "اكتب فكرتك هنا... مثال: فيديو عن تحدي الأكل السريع",
        "fr": "Écris ton idée ici... ex. : une vidéo sur un défi culinaire de 24 heures",
    },
    "eval.max_chars": {
        "en": "Character limit reached ({n}). Trim your idea down to its core for a more accurate score.",
        "ar": "وصلت للحد الأقصى ({n} حرف). اقتطع الفكرة إلى جوهرها للحصول على تقييم أدق.",
        "fr": "Limite de caractères atteinte ({n}). Résume ton idée pour obtenir une note plus précise.",
    },
    "eval.empty_warning": {
        "en": "Write your idea first so we can rate it.",
        "ar": "اكتب فكرتك أولاً حتى نتمكن من تقييمها.",
        "fr": "Écris d'abord ton idée pour que nous puissions l'évaluer.",
    },
    "eval.button": {
        "en": "Rate & upgrade now",
        "ar": "قيّم وطوّر الآن",
        "fr": "Noter et améliorer",
    },
    "eval.section": {
        "en": "Your idea score",
        "ar": "تقييم فكرتك",
        "fr": "Note de ton idée",
    },
    "eval.before": {
        "en": "Before upgrade",
        "ar": "قبل التطوير",
        "fr": "Avant amélioration",
    },
    "eval.analyzed": {
        "en": "Analyzed",
        "ar": "تم التحليل",
        "fr": "Analysée",
    },
    "eval.progress": {
        "en": "Original idea strength: {n}%",
        "ar": "قوة الفكرة الأصلية: {n}%",
        "fr": "Force de l'idée d'origine : {n} %",
    },
    "eval.original_score": {
        "en": "Original score",
        "ar": "التقييم الأصلي",
        "fr": "Note initiale",
    },
    "eval.improved_score": {
        "en": "After suggested upgrade",
        "ar": "بعد التطوير المقترح",
        "fr": "Après amélioration proposée",
    },
    "eval.empty": {
        "en": "There is no text to rate.",
        "ar": "لم يُكتب أي نص لتقييمه.",
        "fr": "Il n'y a aucun texte à noter.",
    },
    "eval.step_placeholder": {
        "en": "Step {n}",
        "ar": "النقطة {n}",
        "fr": "Étape {n}",
    },
    "eval.issues_prefix": {
        "en": "This idea needs work before publishing: ",
        "ar": "الفكرة تحتاج معالجة قبل النشر: ",
        "fr": "Cette idée doit être travaillée avant publication : ",
    },
    "eval.strong": {
        "en": "Strong, publish-ready idea, but it still needs a sharper hook in the first 3 seconds. "
        "The suggested upgrade adds a clear curiosity element and sets expectations from the first frame.",
        "ar": "الفكرة قوية وجاهزة للنشر، لكنها تحتاج خطافاً أحدّ في أول 3 ثوانٍ. "
        "التطوير المقترح يضيف عنصر تشويق واضحاً ويضبط التوقع من أول إطار.",
        "fr": "Idée solide et publiable, mais elle manque d'une accroche plus tranchante dans les 3 premières "
        "secondes. L'amélioration proposée ajoute un vrai déclencheur de curiosité et pose l'attente dès "
        "la première image.",
    },
    "eval.check.length_short": {
        "en": "The idea is too short to reveal its angle. Add one sentence that says exactly what happens on screen.",
        "ar": "الفكرة مختصرة جداً، المشاهد لن يستنتج زاويتها. اكتب جملة توضح ماذا سيحدث بالضبط.",
        "fr": "L'idée est trop courte pour révéler son angle. Ajoute une phrase qui décrit exactement ce qui se passe à l'écran.",
    },
    "eval.check.length_long": {
        "en": "The idea is longer than needed. Condense it into one clear sentence.",
        "ar": "الفكرة مطوّلة أكثر من اللازم، لخّصها في جملة واحدة واضحة.",
        "fr": "L'idée est trop longue. Résume-la en une seule phrase claire.",
    },
    "eval.check.number": {
        "en": "No number or duration. Add one (30 seconds, 5 steps, 3 days) to build credibility.",
        "ar": "لا يوجد رقم أو مدة زمنية. أضف رقماً (30 ثانية، 5 خطوات، 3 أيام) ليعطي مصداقية.",
        "fr": "Aucun chiffre ni aucune durée. Ajoutes-en un (30 secondes, 5 étapes, 3 jours) pour crédibiliser.",
    },
    "eval.check.question": {
        "en": "No question or curiosity gap. Open with a question that creates a gap the viewer needs to close.",
        "ar": "لا يوجد سؤال أو فضول. ابدأ بسؤال يخلق فراغاً ذهنياً يدفع المشاهد للإكمال.",
        "fr": "Aucune question ni vide de curiosité. Commence par une question qui crée un manque que le spectateur veut combler.",
    },
    "eval.check.curiosity": {
        "en": "No curiosity trigger (shock, secret, unexpected result) in the first 3 seconds.",
        "ar": "لا يوجد عنصر تشويق (صدمة، سر، أو نتيجة غير متوقعة) في أول 3 ثوانٍ.",
        "fr": "Aucun déclencheur de curiosité (choc, secret, résultat inattendu) dans les 3 premières secondes.",
    },
    "eval.check.specific": {
        "en": "The idea is generic and names no audience or channel. Tie it to a specific niche or audience.",
        "ar": "الفكرة عامة ولا تذكر جمهوراً أو قناة محددة. اربطها بمجال أو جمهور بعينه.",
        "fr": "L'idée est générique et ne cite ni audience ni chaîne. Lie-la à un thème ou une audience précise.",
    },
    # ---- clipboard -----------------------------------------------------------------
    "copy.idea": {
        "en": "Copy idea 📋",
        "ar": "نسخ الفكرة 📋",
        "fr": "Copier l'idée 📋",
    },
    "copy.done": {
        "en": "Copied ✓",
        "ar": "تم النسخ ✓",
        "fr": "Copié ✓",
    },
    "copy.manual": {
        "en": "Copy manually",
        "ar": "انسخ النص يدوياً",
        "fr": "Copie manuellement",
    },
    "clip.title": {
        "en": "Title",
        "ar": "العنوان",
        "fr": "Titre",
    },
    "clip.hook": {
        "en": "Hook",
        "ar": "الخطاف",
        "fr": "Accroche",
    },
    "clip.angle": {
        "en": "Angle",
        "ar": "الزاوية",
        "fr": "Angle",
    },
    # ---- paywall -------------------------------------------------------------------
    "pay.generate_headline": {
        "en": "Liked these ideas? Unlock everything: multi-platform ideas in 3 languages plus "
        "unlimited rating and upgrading of your own ideas for {price} only!",
        "ar": "هل أعجبتك هذه الأفكار؟ افتح كل الأدوات: أفكار لمنصات متعددة وب3 لغات "
        "+ تقييم وتطوير أفكارك مقابل {price} فقط!",
        "fr": "Ces idées t'ont plu ? Débloque tout : des idées multi-plateformes en 3 langues, plus "
        "la notation et l'amélioration illimitées de tes idées pour {price} seulement !",
    },
    "pay.evaluate_headline": {
        "en": "Your idea deserves a much stronger version. Unlock unlimited rating and upgrading "
        "plus ideas for 5 platforms in 3 languages for {price} only!",
        "ar": "فكرتك تستحق نسخة أقوى بكثير. افتح التقييم والتطوير غير المحدود + "
        "أفكار لـ 5 منصات و3 لغات مقابل {price} فقط!",
        "fr": "Ton idée mérite une version bien plus forte. Débloque la notation et l'amélioration "
        "illimitées, plus des idées pour 5 plateformes en 3 langues, pour {price} seulement !",
    },
    "pay.price_suffix": {
        "en": "one-time payment · lifetime access",
        "ar": "دفعة واحدة مدى الحياة",
        "fr": "paiement unique · accès à vie",
    },
    "pay.b1": {
        "en": "Unlimited idea generation for your niche",
        "ar": "توليد أفكار غير محدود لمجالك",
        "fr": "Génération d'idées illimitée pour ton thème",
    },
    "pay.b2": {
        "en": "5 platforms: YouTube, Shorts, TikTok, Reels, Facebook",
        "ar": "5 منصات: يوتيوب، Shorts، تيك توك، Reels، فيسبوك",
        "fr": "5 plateformes : YouTube, Shorts, TikTok, Reels, Facebook",
    },
    "pay.b3": {
        "en": "3 interface languages: English, Arabic, French",
        "ar": "3 لغات للواجهة: العربية، الإنجليزية، الفرنسية",
        "fr": "3 langues d'interface : français, anglais, arabe",
    },
    "pay.b4": {
        "en": "Unlimited rating and upgrading of your own ideas",
        "ar": "تقييم وتطوير لا محدود لأفكارك الشخصية",
        "fr": "Notation et amélioration illimitées de tes idées",
    },
    "pay.b5": {
        "en": "Audience and style targeting on every idea",
        "ar": "تخصيص الجمهور والأسلوب لكل فكرة",
        "fr": "Ciblage de l'audience et du style pour chaque idée",
    },
    "pay.b6": {
        "en": "Title + hook + angle + quick outline",
        "ar": "عنوان + خطاف + زاوية + هيكل سريع",
        "fr": "Titre + accroche + angle + plan rapide",
    },
    "pay.cta_generate": {
        "en": "Unlock all tools now →",
        "ar": "افتح كل الأدوات الآن ←",
        "fr": "Débloque tous les outils →",
    },
    "pay.cta_evaluate": {
        "en": "Upgrade your ideas without limits →",
        "ar": "طوّر أفكارك بلا حدود ←",
        "fr": "Améliore tes idées sans limite →",
    },
    "pay.fine": {
        "en": "Secure payment through an external link (Whop / Gumroad) · 7-day refund",
        "ar": "دفع آمن عبر رابط خارجي (Whop / Gumroad) · استرجاع خلال 7 أيام",
        "fr": "Paiement sécurisé via un lien externe (Whop / Gumroad) · remboursement sous 7 jours",
    },
# ---- Groq backend ---------------------------------------------------------------
    "ai.missing_library": {
        "en": (
            "The Groq library is not installed, so live AI is off. "
            "Run `pip install groq` and restart. Built-in sample ideas are shown meanwhile."
        ),
        "ar": (
            "مكتبة Groq غير مثبّتة، لذلك توليد الأفكار بالذكاء الاصطناعي متوقف. "
            "نفّذ `pip install groq` ثم أعد تشغيل التطبيق. تُعرض أفكار جاهزة مؤقتاً."
        ),
        "fr": (
            "La bibliothèque Groq n'est pas installée, l'IA en direct est désactivée. "
            "Lance `pip install groq` puis redémarre. Des idées exemples s'affichent entre-temps."
        ),
    },
    "ai.missing_key": {
        "en": (
            "Groq API key not found. Add GROQ_API_KEY to .streamlit/secrets.toml "
            "(or set it as an environment variable) and check your settings. "
            "Built-in sample ideas are shown meanwhile."
        ),
        "ar": (
            "لم يتم العثور على مفتاح Groq. أضف GROQ_API_KEY إلى ملف .streamlit/secrets.toml "
            "(أو عيّنه كمتغير بيئة) وتحقق من إعداداتك. تُعرض أفكار جاهزة مؤقتاً."
        ),
        "fr": (
            "Clé API Groq introuvable. Ajoute GROQ_API_KEY dans .streamlit/secrets.toml "
            "(ou définis-la comme variable d'environnement) et vérifie ta configuration. "
            "Des idées exemples s'affichent entre-temps."
        ),
    },
    "ai.invalid_key": {
        "en": (
            "Groq rejected this API key (HTTP 401). Generate a fresh key at console.groq.com/keys "
            "and put it in .streamlit/secrets.toml as GROQ_API_KEY. "
            "Built-in sample ideas are shown meanwhile."
        ),
        "ar": (
            "رفض Groq مفتاح الـ API هذا (خطأ 401). أنشئ مفتاحاً جديداً من console.groq.com/keys "
            "وضعه في ملف .streamlit/secrets.toml باسم GROQ_API_KEY. تُعرض أفكار جاهزة مؤقتاً."
        ),
        "fr": (
            "Groq a refusé cette clé API (HTTP 401). Génère une nouvelle clé sur console.groq.com/keys "
            "et place-la dans .streamlit/secrets.toml sous GROQ_API_KEY. "
            "Des idées exemples s'affichent entre-temps."
        ),
    },
    "ai.request_failed": {
        "en": (
            "Groq could not be reached. Check your connection and try again. "
            "Built-in sample ideas are shown meanwhile."
        ),
        "ar": (
            "تعذّر الوصول إلى Groq. تحقق من اتصالك ثم أعد المحاولة. تُعرض أفكار جاهزة مؤقتاً."
        ),
        "fr": (
            "Groq est injoignable. Vérifie ta connexion puis réessaie. "
            "Des idées exemples s'affichent entre-temps."
        ),
    },
    "ai.bad_response": {
        "en": (
            "Groq replied in an unexpected format, so the answer was discarded. "
            "Please try again. Built-in sample ideas are shown meanwhile."
        ),
        "ar": (
            "أعاد Groq تنسيقاً غير متوقع، لذلك تم تجاهل الرد. أعد المحاولة من فضلك. "
            "تُعرض أفكار جاهزة مؤقتاً."
        ),
        "fr": (
            "Groq a répondu dans un format inattendu, la réponse a été ignorée. "
            "Réessaie. Des idées exemples s'affichent entre-temps."
        ),
    },
    "ai.quota_exceeded": {
        "en": (
            "The Groq rate limit was hit (HTTP 429). Wait a few seconds, or switch to a smaller "
            "model by setting GROQ_MODEL in .streamlit/secrets.toml. "
            "Built-in sample ideas are shown meanwhile."
        ),
        "ar": (
            "تم بلوغ حد طلبات Groq (خطأ 429). انتظر بضع ثوانٍ، أو انتقل إلى نموذج أصغر بعيّن "
            "GROQ_MODEL في ملف .streamlit/secrets.toml. تُعرض أفكار جاهزة مؤقتاً."
        ),
        "fr": (
            "La limite de débit Groq est atteinte (HTTP 429). Patiente quelques secondes ou passe à un "
            "modèle plus léger via GROQ_MODEL dans .streamlit/secrets.toml. "
            "Des idées exemples s'affichent entre-temps."
        ),
    },
    "ai.model_unavailable": {
        "en": (
            "This Groq model is not available (HTTP 404). Set GROQ_MODEL in .streamlit/secrets.toml "
            "to a model your plan can call, such as openai/gpt-oss-20b or openai/gpt-oss-120b. "
            "Built-in sample ideas are shown meanwhile."
        ),
        "ar": (
            "نموذج Groq هذا غير متاح (خطأ 404). عيّن GROQ_MODEL في ملف .streamlit/secrets.toml "
            "إلى نموذج يدعمه حسابك، مثل openai/gpt-oss-20b أو openai/gpt-oss-120b. "
            "تُعرض أفكار جاهزة مؤقتاً."
        ),
        "fr": (
            "Ce modèle Groq n'est pas disponible (HTTP 404). Définis GROQ_MODEL dans "
            ".streamlit/secrets.toml avec un modèle accessible à ton compte, par exemple "
            "openai/gpt-oss-20b ou openai/gpt-oss-120b. Des idées exemples s'affichent entre-temps."
        ),
    },
    "ai.thinking": {
        "en": "Groq is writing your ideas…",
        "ar": "Groq يكتب أفكارك…",
        "fr": "Groq rédige tes idées…",
    },
    "ai.analyzing": {
        "en": "Groq is analysing your idea…",
        "ar": "Groq يحلّل فكرتك…",
        "fr": "Groq analyse ton idée…",
    },
    "ai.detail": {
        "en": "Technical detail",
        "ar": "التفاصيل التقنية",
        "fr": "Détail technique",
    },
    # ---- footer --------------------------------------------------------------------
    "footer.title": {
        "en": "Other tools that will multiply your views:",
        "ar": "أدوات أخرى ستضاعف مشاهداتك:",
        "fr": "D'autres outils qui multiplieront tes vues :",
    },
    "footer.tool1": {
        "en": "Title & SEO writing tool",
        "ar": "أداة كتابة العناوين والـ SEO",
        "fr": "Outil de rédaction de titres et SEO",
    },
    "footer.tool2": {
        "en": "Auto subtitles tool",
        "ar": "أداة التفريغ الصوتي التلقائي",
        "fr": "Outil de sous-titrage automatique",
    },
    "footer.copy": {
        "en": "© 2026 TubeSpark — ideas powered by Groq.",
        "ar": "© 2026 TubeSpark — أفكار مدعومة من Groq.",
        "fr": "© 2026 TubeSpark — idées propulsées par Groq.",
    },
    "footer.copy_fallback": {
        "en": "© 2026 TubeSpark — AI not configured, showing built-in sample data.",
        "ar": "© 2026 TubeSpark — الذكاء الاصطناعي غير مُعد، تُعرض بيانات تجريبية جاهزة.",
        "fr": "© 2026 TubeSpark — IA non configurée, données exemples intégrées.",
    },
}