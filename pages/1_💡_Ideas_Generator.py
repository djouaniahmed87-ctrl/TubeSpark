from __future__ import annotations

import streamlit as st

from app import (
    DEFAULT_PLATFORM,
    generate_ideas,
    render_idea_cards,
    current_lang,
    option_formatter,
    PLATFORM_KEYS,
    VIBE_KEYS,
    AUDIENCE_KEYS,
)

st.set_page_config(page_title="Ideas Generator", page_icon="💡", layout="wide")

st.markdown('<div dir="rtl">', unsafe_allow_html=True)

st.title("💡 Ideas Generator")

col1, col2, col3 = st.columns(3)
with col1:
    platform = st.selectbox(
        "Platform",
        options=list(PLATFORM_KEYS),
        format_func=option_formatter("platform", current_lang()),
        index=0,
    )
with col2:
    vibe = st.selectbox(
        "Vibe",
        options=list(VIBE_KEYS),
        format_func=option_formatter("vibe", current_lang()),
        index=0,
    )
with col3:
    audience = st.selectbox(
        "Audience",
        options=list(AUDIENCE_KEYS),
        format_func=option_formatter("audience", current_lang()),
        index=0,
    )

niche = st.text_input("Niche / Topic", placeholder="مثال: تداول، طبخ، ألعاب")

if st.button("Generate ideas", type="primary"):
    if niche.strip():
        with st.spinner("Generating ideas with Groq..."):
            ideas = generate_ideas(
                niche.strip(),
                3,
                platform=platform,
                vibe=vibe,
                audience=audience,
                lang=current_lang(),
            )
        st.session_state["idea_page_results"] = ideas
    else:
        st.warning("Please enter a niche before generating ideas.")

results = st.session_state.get("idea_page_results")
if results:
    render_idea_cards(results, niche.strip() or "your niche", platform=platform)

st.markdown('</div>', unsafe_allow_html=True)
