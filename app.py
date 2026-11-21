"""Streamlit web UI:  streamlit run app.py"""
import os

import streamlit as st

from smart_notes import organize_notes

st.set_page_config(page_title="Smart Notes Organizer", page_icon="🗂️", layout="wide")
st.title("🗂️ Smart Notes Organizer")
st.caption("Paste scattered notes → get them grouped under topic headings in Markdown.")

with st.sidebar:
    backend = st.radio("Backend", ["auto", "llm", "local"], help="llm = Claude (best headings), local = offline TF-IDF + KMeans")
    key = st.text_input("Anthropic API key (optional)", type="password")
    if key:
        os.environ["ANTHROPIC_API_KEY"] = key

text = st.text_area("Paste your notes (one per line, or separated by blank lines)", height=300)

if st.button("Organize", type="primary"):
    try:
        with st.spinner("Organizing..."):
            md = organize_notes(text, backend=backend)
        left, right = st.columns(2)
        left.subheader("Preview")
        left.markdown(md)
        right.subheader("Markdown")
        right.code(md, language="markdown")
        st.download_button("Download .md", md, file_name="organized_notes.md")
    except Exception as e:
        st.error(str(e))
