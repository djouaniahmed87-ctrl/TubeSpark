from __future__ import annotations

import streamlit as st

from app import (
    _script_from_groq,
    current_lang,
    option_formatter,
    PLATFORM_KEYS,
    VIBE_KEYS,
    AUDIENCE_KEYS,
)

st.set_page_config(page_title="Script Writer", page_icon="📝", layout="wide")

st.markdown('<div dir="rtl">', unsafe_allow_html=True)
st.title("📝 Script Writer")

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

duration = st.selectbox(
    "Target duration",
    options=["shorts", "3-5min", "8-10min", "15min+"],
    index=2,
)

niche = st.text_input("Niche / Topic", placeholder="مثال: تداول، تعليم، تكنولوجيا")
idea = st.text_area("Core idea", height=140, placeholder="اكتب الفكرة الرئيسية هنا...")

if st.button("Generate script", type="primary"):
    if niche.strip() and idea.strip():
        with st.spinner("Writing full video script with Groq..."):
            script = _script_from_groq(
                niche.strip(),
                idea.strip(),
                platform=platform,
                vibe=vibe,
                audience=audience,
                lang=current_lang(),
                duration=duration,
            )
        st.session_state["script_page_result"] = script
    else:
        st.warning("Please fill in the niche and core idea.")

result = st.session_state.get("script_page_result")
if result:
    st.subheader(result.title)
    st.write(result.description)
    st.markdown("### Hashtags")
    st.write(" ".join(f"#{tag}" for tag in result.hashtags))
    st.markdown("### Keywords")
    st.write(", ".join(result.keywords))
    for section in result.sections:
        st.markdown(f"### {section['name']} — {section['time']}")
        st.write(section["content"])
        if section.get("notes"):
            st.info(section["notes"])

st.markdown('</div>', unsafe_allow_html=True)
