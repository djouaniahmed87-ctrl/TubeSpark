from __future__ import annotations

import streamlit as st

from app import _seo_from_groq, current_lang

st.set_page_config(page_title="SEO Optimizer", page_icon="🔍", layout="wide")

st.markdown('<div dir="rtl">', unsafe_allow_html=True)
st.title("🔍 SEO Optimizer")

topic = st.text_input("Video topic", placeholder="مثال: كيف تبدأ في التداول")
niche = st.text_input("Niche / category", placeholder="مثال: تداول، تعليم، تكنولوجيا")

if st.button("Optimize SEO", type="primary"):
    if topic.strip() and niche.strip():
        with st.spinner("Running SEO analysis with Groq..."):
            data = _seo_from_groq(topic.strip(), niche.strip(), lang=current_lang())
        st.session_state["seo_page_result"] = data
    else:
        st.warning("Please enter both the topic and niche.")

result = st.session_state.get("seo_page_result")
if result:
    st.markdown("### Thumbnail text")
    st.write(" | ".join(result.thumbnail_texts))

    st.markdown("### SEO titles")
    for item in result.seo_titles:
        st.write(f"- {item}")

    st.markdown("### SEO description")
    st.write(result.seo_description)

    st.markdown("### SEO tags")
    st.write(", ".join(result.seo_tags))

    st.markdown("### Chapter list")
    for chapter in result.chapters:
        st.write(f"- {chapter}")

st.markdown('</div>', unsafe_allow_html=True)
