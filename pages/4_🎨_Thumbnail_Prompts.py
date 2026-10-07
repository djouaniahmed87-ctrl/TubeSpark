from __future__ import annotations

import streamlit as st

st.set_page_config(page_title="Thumbnail Prompts", page_icon="🎨", layout="wide")

st.markdown('<div dir="rtl">', unsafe_allow_html=True)
st.title("🎨 Thumbnail Prompt Generator")

topic = st.text_input("Video topic", placeholder="مثال: أخطاء المبتدئين في التداول")
niche = st.text_input("Niche", placeholder="مثال: تداول")

if st.button("Generate thumbnail prompt", type="primary"):
    prompt = (
        f"Create a cinematic YouTube thumbnail for a video about '{topic or 'your topic'}' in the niche '{niche or 'your niche'}'. "
        "Use bold contrast, a large readable title, one clear focal object or face, dramatic lighting, premium editorial composition, and a strong curiosity hook optimized for high CTR."
    )
    st.session_state["thumbnail_page_prompt"] = prompt

prompt = st.session_state.get("thumbnail_page_prompt")
if prompt:
    st.code(prompt, language="text")

st.markdown('</div>', unsafe_allow_html=True)
