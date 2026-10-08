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
    "nav.home": {
        "en": "Home",
        "ar": "الرئيسية",
        "fr": "Accueil",
    },
    "nav.tools": {
        "en": "Tools",
        "ar": "الأدوات",
        "fr": "Outils",
    },
    "nav.how": {
        "en": "How it works",
        "ar": "كيف يعمل",
        "fr": "Comment ça marche",
    },
    "nav.pricing": {
        "en": "Pricing",
        "ar": "الأسعار",
        "fr": "Tarifs",
    },
    "nav.start": {
        "en": "Start free",
        "ar": "ابدأ مجانًا",
        "fr": "Commencer gratuitement",
    },
    "nav.open_app": {
        "en": "Open App",
        "ar": "افتح التطبيق",
        "fr": "Ouvrir l'app",
    },
    "nav.back_to_landing": {
        "en": "Back to landing",
        "ar": "العودة إلى الصفحة الرئيسية",
        "fr": "Retour à l'accueil",
    },
    "nav.faq": {
        "en": "FAQ",
        "ar": "الأسئلة الشائعة",
        "fr": "FAQ",
    },
    "landing.workspace.kicker": {
        "en": "WORKSPACE",
        "ar": "مساحة العمل",
        "fr": "ESPACE DE TRAVAIL",
    },
    "landing.workspace.title": {
        "en": "Choose a tool",
        "ar": "اختر أداة",
        "fr": "Choisis un outil",
    },
    "landing.workspace.copy": {
        "en": "Switch between the core generation workflows and build your next YouTube asset from the same live workspace.",
        "ar": "بدّل بين سير العمل الرئيسي لبناء المحتوى وابنِ أصلًا جديدًا من نفس مساحة العمل الحالية.",
        "fr": "Passe d'un workflow de génération à l'autre et construis ton prochain asset YouTube dans le même espace de travail.",
    },
    "landing.features.kicker": {
        "en": "Features",
        "ar": "المميزات",
        "fr": "Fonctionnalités",
    },
    "landing.features.title": {
        "en": "Built for modern content operations",
        "ar": "مصمم لعمليات المحتوى الحديثة",
        "fr": "Conçu pour les opérations de contenu modernes",
    },
    "landing.process.kicker": {
        "en": "Process",
        "ar": "العملية",
        "fr": "Processus",
    },
    "landing.process.title": {
        "en": "A simple workflow from idea to publish",
        "ar": "تدفق بسيط من الفكرة إلى النشر",
        "fr": "Un workflow simple de l'idée à la publication",
    },
    "landing.pricing.kicker": {
        "en": "Pricing",
        "ar": "الأسعار",
        "fr": "Tarifs",
    },
    "landing.pricing.title": {
        "en": "Simple pricing for creators at every stage",
        "ar": "أسعار بسيطة للمبدعين في كل مرحلة",
        "fr": "Des tarifs simples pour les créateurs à chaque étape",
    },
    "landing.faq.kicker": {
        "en": "FAQ",
        "ar": "الأسئلة الشائعة",
        "fr": "FAQ",
    },
    "landing.faq.title": {
        "en": "Everything you need to know",
        "ar": "كل ما تحتاج معرفته",
        "fr": "Tout ce qu'il faut savoir",
    },
    "landing.cta.kicker": {
        "en": "Launch faster",
        "ar": "ابدأ بسرعة",
        "fr": "Lancez-vous vite",
    },
    "landing.cta.title": {
        "en": "Turn one idea into a full content workflow.",
        "ar": "حوّل فكرة واحدة إلى سير عمل كامل للمحتوى.",
        "fr": "Transforme une idée en workflow de contenu complet.",
    },
    "workspace.app_shell_title": {
        "en": "Product Workspace",
        "ar": "مساحة العمل",
        "fr": "Espace de travail",
    },
    "workspace.ai_chat": {
        "en": "AI Chat",
        "ar": "دردشة الذكاء الاصطناعي",
        "fr": "Chat IA",
    },
    "workspace.idea_generator": {
        "en": "Idea Generator",
        "ar": "مولد الأفكار",
        "fr": "Générateur d'idées",
    },
    "workspace.idea_evaluator": {
        "en": "Idea Evaluator",
        "ar": "مقيّم الفكرة",
        "fr": "Évaluateur d'idées",
    },
    "workspace.script_writer": {
        "en": "Script Writer",
        "ar": "كاتب السيناريو",
        "fr": "Rédacteur de script",
    },
    "workspace.seo_optimizer": {
        "en": "SEO Optimizer",
        "ar": "محسن السيو",
        "fr": "Optimiseur SEO",
    },
    "workspace.visual_prompt_studio": {
        "en": "Visual Prompt Studio",
        "ar": "استوديو تعليمات المرئيات",
        "fr": "Studio de prompts visuels",
    },
    "workspace.content_studio": {
        "en": "Content Studio",
        "ar": "استوديو المحتوى",
        "fr": "Studio de contenu",
    },
    "workspace.seo_discovery": {
        "en": "SEO & Discovery",
        "ar": "السيو والاكتشاف",
        "fr": "SEO & Découverte",
    },
    "workspace.visual_studio": {
        "en": "Visual Studio",
        "ar": "استوديو المرئيات",
        "fr": "Studio visuel",
    },
    "workspace.label": {
        "en": "Workspace",
        "ar": "مساحة العمل",
        "fr": "Espace de travail",
    },
    "workspace.project_context": {
        "en": "Current Project Context",
        "ar": "سياق المشروع الحالي",
        "fr": "Contexte du projet",
    },
    "workspace.project": {
        "en": "Project",
        "ar": "المشروع",
        "fr": "Projet",
    },
    "workspace.platform": {
        "en": "Platform",
        "ar": "المنصة",
        "fr": "Plateforme",
    },
    "workspace.content_type": {
        "en": "Content Type",
        "ar": "نوع المحتوى",
        "fr": "Type de contenu",
    },
    "workspace.assets": {
        "en": "Assets",
        "ar": "الأصول",
        "fr": "Ressources",
    },
    "workspace.titles": {
        "en": "Titles",
        "ar": "العناوين",
        "fr": "Titres",
    },
    "workspace.seo": {
        "en": "SEO",
        "ar": "السيو",
        "fr": "SEO",
    },
    "workspace.visual": {
        "en": "Visual",
        "ar": "مرئي",
        "fr": "Visuel",
    },
    "workspace.ready": {
        "en": "ready",
        "ar": "جاهز",
        "fr": "prêt",
    },
    "workspace.not_generated": {
        "en": "not generated",
        "ar": "غير مُولَّد",
        "fr": "non généré",
    },
    "workspace.partial": {
        "en": "partial",
        "ar": "جزئي",
        "fr": "partiel",
    },
    "workspace.not_set": {
        "en": "Not set yet",
        "ar": "غير محدد بعد",
        "fr": "Pas encore défini",
    },
    "workspace.use_content_studio": {
        "en": "Use in Content Studio",
        "ar": "استخدم في استوديو المحتوى",
        "fr": "Utiliser dans le studio de contenu",
    },
    "workspace.send_to_seo": {
        "en": "Send to SEO",
        "ar": "إرسال إلى السيو",
        "fr": "Envoyer au SEO",
    },
    "workspace.send_to_visual": {
        "en": "Send to Visual",
        "ar": "إرسال إلى المرئي",
        "fr": "Envoyer au visuel",
    },
    "workspace.save_to_project": {
        "en": "Save to Project",
        "ar": "حفظ في المشروع",
        "fr": "Enregistrer dans le projet",
    },
    "workspace.ai_chat_desc": {
        "en": "A centralized workspace to guide the user into the appropriate product workflow without forcing a single path.",
        "ar": "مساحة عمل مركزية لتوجيه المستخدم إلى سير العمل المناسب دون إجباره على مسار واحد.",
        "fr": "Un espace de travail centralisé pour guider l'utilisateur vers le bon workflow sans le forcer dans un seul chemin.",
    },
    "workspace.content_studio_desc": {
        "en": "The primary content creation workspace where idea generation, titles, evaluation, scripts, descriptions, hashtags, and discovery tags work together.",
        "ar": "مساحة العمل الأساسية لإنشاء المحتوى حيث تعمل توليد الأفكار، العناوين، التقييم، السكريبتات، الأوصاف، الهاشتاغات، وعلامات الاكتشاف معًا.",
        "fr": "Le workspace principal de création de contenu où génération d'idées, titres, évaluation, scripts, descriptions, hashtags et tags de découverte travaillent ensemble.",
    },
    "workspace.seo_discovery_desc": {
        "en": "Search optimization and discovery workflows for the current project, grouped into concrete tool sections.",
        "ar": "سير عمل تحسين محركات البحث والاكتشاف للمشروع الحالي، مُجمّع في أقسام أدوات محددة.",
        "fr": "Les workflows de SEO et de découverte du projet actuel, regroupés dans des sections d'outils concrètes.",
    },
    "workspace.visual_studio_desc": {
        "en": "A dedicated visual content workspace for thumbnail concepts, image prompts, and saved visual direction.",
        "ar": "مساحة عمل مرئية مخصصة لمفاهيم الصور المصغرة، برومبت الصور، والتوجيه البصري المحفوظ.",
        "fr": "Un espace de travail visuel dédié aux concepts de miniatures, prompts d'images et direction visuelle enregistrée.",
    },
    "chat.welcome": {
        "en": "Welcome. Tell me the topic or request and I will read the current project context before routing it to the right workflow.",
        "ar": "مرحبًا. أخبرني بعنوان المشروع أو طلبك وسأقرأ سياق المشروع الحالي قبل توجيهه إلى سير العمل المناسب.",
        "fr": "Bienvenue. Donne-moi le sujet ou la demande et je lirai le contexte actuel du projet avant de le diriger vers le bon workflow.",
    },
    "chat.suggested_actions": {
        "en": "Suggested Actions",
        "ar": "إجراءات مقترحة",
        "fr": "Actions suggérées",
    },
    "chat.action.generate_ideas": {
        "en": "Generate Ideas",
        "ar": "إنشاء أفكار",
        "fr": "Générer des idées",
    },
    "chat.action.generate_titles": {
        "en": "Generate Titles",
        "ar": "إنشاء عناوين",
        "fr": "Générer des titres",
    },
    "chat.action.create_script": {
        "en": "Create Script",
        "ar": "إنشاء Script",
        "fr": "Créer un script",
    },
    "chat.action.create_seo": {
        "en": "Create SEO",
        "ar": "إنشاء سيو",
        "fr": "Créer le SEO",
    },
    "chat.action.generate_keywords": {
        "en": "Generate Keywords",
        "ar": "إنشاء كلمات مفتاحية",
        "fr": "Générer des mots-clés",
    },
    "chat.action.create_visual": {
        "en": "Create Visual",
        "ar": "إنشاء مرئي",
        "fr": "Créer un visuel",
    },
    "chat.ai_copilot": {
        "en": "AI Copilot",
        "ar": "مساعد الذكاء الاصطناعي",
        "fr": "Assistant IA",
    },
    "chat.user_request": {
        "en": "User request",
        "ar": "طلب المستخدم",
        "fr": "Demande utilisateur",
    },
    "chat.ai_response": {
        "en": "AI response",
        "ar": "رد الذكاء الاصطناعي",
        "fr": "Réponse de l'IA",
    },
    "chat.latest_result": {
        "en": "Structured result",
        "ar": "النتيجة المنظمة",
        "fr": "Résultat structuré",
    },
    "chat.result_ready": {
        "en": "The generated result is shown below and saved to the project.",
        "ar": "تظهر النتيجة المُنشأة أدناه وحُفظت في المشروع.",
        "fr": "Le résultat généré est affiché ci-dessous et enregistré dans le projet.",
    },
    "chat.copy_result": {
        "en": "Copy result",
        "ar": "نسخ النتيجة",
        "fr": "Copier le résultat",
    },
    "chat.voice_unavailable": {
        "en": "Voice input is unavailable in this chat. Use the text field to send your request.",
        "ar": "الإدخال الصوتي غير متاح في هذه المحادثة. استخدم حقل النص لإرسال طلبك.",
        "fr": "La saisie vocale n'est pas disponible dans ce chat. Utilisez le champ texte pour envoyer votre demande.",
    },
    "result.ideas": {
        "en": "Generated ideas",
        "ar": "الأفكار المُنشأة",
        "fr": "Idées générées",
    },
    "result.script": {
        "en": "Generated script",
        "ar": "السكريبت المُنشأ",
        "fr": "Script généré",
    },
    "result.seo": {
        "en": "SEO results",
        "ar": "نتائج تحسين محركات البحث",
        "fr": "Résultats SEO",
    },
    "result.evaluation": {
        "en": "Evaluation result",
        "ar": "نتيجة التقييم",
        "fr": "Résultat de l'évaluation",
    },
    "result.visual": {
        "en": "Visual result",
        "ar": "النتيجة المرئية",
        "fr": "Résultat visuel",
    },
    "result.description": {
        "en": "Description",
        "ar": "الوصف",
        "fr": "Description",
    },
    "result.sections": {
        "en": "Script sections",
        "ar": "أقسام السكريبت",
        "fr": "Sections du script",
    },
    "result.keywords": {
        "en": "Keywords",
        "ar": "الكلمات المفتاحية",
        "fr": "Mots-clés",
    },
    "result.hashtags": {
        "en": "Hashtags",
        "ar": "الوسوم",
        "fr": "Hashtags",
    },
    "result.chapters": {
        "en": "Chapters",
        "ar": "الفصول",
        "fr": "Chapitres",
    },
    "result.thumbnail_texts": {
        "en": "Thumbnail text",
        "ar": "نصوص الصورة المصغرة",
        "fr": "Textes de miniature",
    },
    "result.platform": {
        "en": "Platform",
        "ar": "المنصة",
        "fr": "Plateforme",
    },
    "result.audience": {
        "en": "Audience",
        "ar": "الجمهور",
        "fr": "Public",
    },
    "result.topic": {
        "en": "Topic",
        "ar": "الموضوع",
        "fr": "Sujet",
    },
    "result.content_type": {
        "en": "Content type",
        "ar": "نوع المحتوى",
        "fr": "Type de contenu",
    },
    "result.language": {
        "en": "Language",
        "ar": "اللغة",
        "fr": "Langue",
    },
    "result.style": {
        "en": "Style",
        "ar": "الأسلوب",
        "fr": "Style",
    },
    "result.niche": {
        "en": "Niche",
        "ar": "المجال",
        "fr": "Niche",
    },
    "result.title": {
        "en": "Title",
        "ar": "العنوان",
        "fr": "Titre",
    },
    "result.duration": {
        "en": "Target duration",
        "ar": "المدة المستهدفة",
        "fr": "Durée cible",
    },
    "footer.brand": {
        "en": "TubeSpark",
        "ar": "TubeSpark",
        "fr": "TubeSpark",
    },
    "footer.tagline": {
        "en": "Smart YouTube idea generator",
        "ar": "مولّد أفكار يوتيوب الذكي",
        "fr": "Générateur d'idées YouTube intelligent",
    },
    "footer.terms": {
        "en": "Terms",
        "ar": "الشروط",
        "fr": "Conditions",
    },
    "footer.privacy": {
        "en": "Privacy",
        "ar": "الخصوصية",
        "fr": "Confidentialité",
    },
    "footer.support": {
        "en": "Support",
        "ar": "الدعم",
        "fr": "Support",
    },
    "metric.ai_powered": {
        "en": "AI-powered",
        "ar": "مدعوم بالذكاء الاصطناعي",
        "fr": "Piloté par l'IA",
    },
    "metric.content_creation": {
        "en": "content creation",
        "ar": "إنشاء المحتوى",
        "fr": "création de contenu",
    },
    "metric.tools": {
        "en": "3+ tools",
        "ar": "أكثر من 3 أدوات",
        "fr": "3+ outils",
    },
    "metric.workflow": {
        "en": "core workflows",
        "ar": "سير عمل أساسي",
        "fr": "workflows principaux",
    },
    "metric.fast": {
        "en": "Fast",
        "ar": "سريع",
        "fr": "Rapide",
    },
    "metric.generation": {
        "en": "generation",
        "ar": "التوليد",
        "fr": "génération",
    },
    "metric.core": {
        "en": "core workflows",
        "ar": "سير العمل الأساسي",
        "fr": "workflows centraux",
    },
    "metric.content": {
        "en": "content creation",
        "ar": "إنشاء المحتوى",
        "fr": "création de contenu",
    },
    "metric.ready": {
        "en": "ready",
        "ar": "جاهز",
        "fr": "prêt",
    },
    "metric.not_generated": {
        "en": "not generated",
        "ar": "غير مُنشأ",
        "fr": "non généré",
    },
    "metric.none": {
        "en": "None",
        "ar": "لا شيء",
        "fr": "Aucun",
    },
    "metric.assets": {
        "en": "Assets Available",
        "ar": "الأصول المتاحة",
        "fr": "Ressources disponibles",
    },
    "metric.video": {
        "en": "video",
        "ar": "فيديو",
        "fr": "vidéo",
    },
    "ui.placeholder": {
        "en": "Example: I want to create content about AI productivity...",
        "ar": "مثال: أريد إنشاء محتوى حول إنتاجية الذكاء الاصطناعي...",
        "fr": "Exemple : je veux créer du contenu sur la productivité IA...",
    },
    "metric.not_set": {
        "en": "Not set yet",
        "ar": "غير محدد بعد",
        "fr": "Pas encore défini",
    },
    "metric.idea": {
        "en": "Idea",
        "ar": "الفكرة",
        "fr": "Idée",
    },
    "metric.title": {
        "en": "Title",
        "ar": "العنوان",
        "fr": "Titre",
    },
    "metric.script": {
        "en": "Script",
        "ar": "سكريبت",
        "fr": "Script",
    },
    "metric.seo": {
        "en": "SEO",
        "ar": "السيو",
        "fr": "SEO",
    },
    "metric.visual": {
        "en": "Visual",
        "ar": "مرئي",
        "fr": "Visuel",
    },
    "metric.created": {
        "en": "created",
        "ar": "تم إنشاؤه",
        "fr": "créé",
    },
    "metric.saved": {
        "en": "saved",
        "ar": "تم حفظه",
        "fr": "enregistré",
    },
    "metric.use": {
        "en": "Use",
        "ar": "استخدام",
        "fr": "Utiliser",
    },
    "metric.select": {
        "en": "Select",
        "ar": "تحديد",
        "fr": "Sélectionner",
    },
    "metric.generate": {
        "en": "Generate",
        "ar": "إنشاء",
        "fr": "Générer",
    },
    "metric.save": {
        "en": "Save",
        "ar": "حفظ",
        "fr": "Enregistrer",
    },
    "metric.current": {
        "en": "Current",
        "ar": "الحالي",
        "fr": "Actuel",
    },
    "metric.project": {
        "en": "Project",
        "ar": "المشروع",
        "fr": "Projet",
    },
    "metric.ideas": {
        "en": "ideas generated",
        "ar": "أفكار تم توليدها",
        "fr": "idées générées",
    },
    "metric.rating": {
        "en": "creator rating",
        "ar": "تقييم المبدعين",
        "fr": "note des créateurs",
    },
    "metric.workflow": {
        "en": "to workflow",
        "ar": "إلى سير العمل",
        "fr": "vers le workflow",
    },
    "landing.tools.kicker": {
        "en": "Tools",
        "ar": "الأدوات",
        "fr": "Outils",
    },
    "landing.tools.title": {
        "en": "Everything needed to publish stronger content",
        "ar": "كل ما تحتاجه لنشر محتوى أقوى",
        "fr": "Tout ce qu'il faut pour publier un contenu plus fort",
    },
    "landing.how.kicker": {
        "en": "Process",
        "ar": "العملية",
        "fr": "Processus",
    },
    "landing.how.title": {
        "en": "A simple workflow from idea to publish",
        "ar": "تدفق بسيط من الفكرة إلى النشر",
        "fr": "Un workflow simple de l'idée à la publication",
    },
    "tool.idea.title": {
        "en": "Content Ideas",
        "ar": "أفكار المحتوى",
        "fr": "Idées de contenu",
    },
    "tool.idea.copy": {
        "en": "Generate high-converting video angles and niche hooks.",
        "ar": "أنشئ زوايا فيديو قوية ومخططات تنافسية مناسبة لنشاطك.",
        "fr": "Génère des angles vidéo et des accroches adaptées à ta niche.",
    },
    "tool.script.title": {
        "en": "Script Writer",
        "ar": "كاتب السكريبت",
        "fr": "Rédacteur de script",
    },
    "tool.script.copy": {
        "en": "Turn your idea into a clean and engaging video script.",
        "ar": "حوّل فكرتك إلى سكريبت فيديو منظم وجذاب.",
        "fr": "Transforme ton idée en script vidéo clair et engageant.",
    },
    "tool.seo.title": {
        "en": "SEO Booster",
        "ar": "محسن السيو",
        "fr": "Boost SEO",
    },
    "tool.seo.copy": {
        "en": "Improve titles, tags, descriptions, and reach.",
        "ar": "حسّن العناوين، الوسوم، والوصف للوصول الأفضل.",
        "fr": "Améliore titres, tags et descriptions pour plus de visibilité.",
    },
    "tool.thumbnail.title": {
        "en": "Thumbnail Prompt",
        "ar": "برومبت الصورة المصغرة",
        "fr": "Prompt miniature",
    },
    "tool.thumbnail.copy": {
        "en": "Build punchy thumbnail concepts with strong visual hooks.",
        "ar": "أنشئ أفكاراً قوية لصورة مصغرة ذات جاذبية مرئية عالية.",
        "fr": "Crée des concepts de miniature percutants et visuellement forts.",
    },
    "tool.use": {
        "en": "Use tool",
        "ar": "استخدم الأداة",
        "fr": "Utiliser",
    },
    "how.idea.title": {
        "en": "Idea",
        "ar": "الفكرة",
        "fr": "Idée",
    },
    "how.idea.copy": {
        "en": "Start from a valuable niche or hook.",
        "ar": "ابدأ من فكرة أو زاوية ذات قيمة.",
        "fr": "Commence par une niche ou une accroche utile.",
    },
    "how.create.title": {
        "en": "Create",
        "ar": "الإنشاء",
        "fr": "Créer",
    },
    "how.create.copy": {
        "en": "Generate the script, outline, and concept.",
        "ar": "أنشئ السكريبت، المخطط، والفكرة الأساسية.",
        "fr": "Génère le script, le plan et le concept.",
    },
    "how.optimize.title": {
        "en": "Optimize",
        "ar": "التحسين",
        "fr": "Optimiser",
    },
    "how.optimize.copy": {
        "en": "Sharpen titles, SEO, and engagement.",
        "ar": "حسّن العناوين، السيو، والتفاعل.",
        "fr": "Affine les titres, le SEO et l'engagement.",
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
    "eval.context_considered": {
        "en": "Context considered",
        "ar": "السياق الذي أُخذ في الاعتبار",
        "fr": "Contexte pris en compte",
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