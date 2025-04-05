import streamlit as st
from difflib import SequenceMatcher
import os

# ---------- CONFIG ----------
with open("system_prompt.txt", "r") as f:
    system_prompt = f.read().strip()

# ---------- FUNCTIONS ----------

def read_api_key(path: str) -> str:
    try:
        with open(path.strip(), 'r') as f:
            return f.read().strip()
    except Exception as e:
        st.error(f"Error reading API key file: {e}")
        return ""
    
def post_process_groq(text: str) -> str:
    # remove everything between <think> and </think>
    start_tag = "<think>"
    end_tag = "</think>"
    start_index = text.find(start_tag)
    end_index = text.find(end_tag, start_index)
    if start_index != -1 and end_index != -1:
        text = text[:start_index] + text[end_index + len(end_tag):]
    text = text.replace("<think>", "").replace("</think>", "")
    return text.strip()


def generate_diff_html(left: str, right: str) -> str:
    sm = SequenceMatcher(None, left, right)
    html = '<div style="font-family:monospace; line-height:1.6;">'
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == 'equal':
            html += f"<span style='background-color:#f0f0f0; color:#555;'>{left[i1:i2]}</span>"
        elif tag == 'delete':
            html += f"<span style='background-color:#ffdddd; color:#a00; text-decoration:line-through;'>{left[i1:i2]}</span>"
        elif tag == 'insert':
            html += f"<span style='background-color:#ddffdd; color:#0a0;'>{right[j1:j2]}</span>"
        elif tag == 'replace':
            html += f"<span style='background-color:#ffdddd; color:#a00; text-decoration:line-through;'>{left[i1:i2]}</span>"
            html += f"<span style='background-color:#ddffdd; color:#0a0;'>{right[j1:j2]}</span>"
    html += "</div>"
    return html

from openai import OpenAI

def call_groq(api_key: str, model: str, system_prompt: str, user_text: str) -> str:
    client = OpenAI(api_key=api_key, base_url="https://api.groq.com/openai/v1")
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_text},
            ]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        st.error(f"Groq API error: {e}")
        return ""

# ---------- UI ----------

st.set_page_config(layout="wide")
st.title("🧠 AI Text Improver with Diff")

groq_models = [
    "allam-2-7b",
    "deepseek-r1-distill-llama-70b",
    "deepseek-r1-distill-qwen-32b",
    "gemma2-9b-it",
    "llama-3.1-8b-instant",
    "llama-3.2-11b-vision-preview",
    "llama-3.2-1b-preview",
    "llama-3.2-3b-preview",
    "llama-3.2-90b-vision-preview",
    "llama-3.3-70b-specdec",
    "llama-3.3-70b-versatile",
    "llama-guard-3-8b",
    "llama3-70b-8192",
    "llama3-8b-8192",
    "mistral-saba-24b",
    "qwen-2.5-32b",
    "qwen-2.5-coder-32b",
    "qwen-qwq-32b",
]

with st.sidebar:
    model = st.selectbox("Groq Model", groq_models)
    st.text_area("System Prompt", value=system_prompt, height=250, disabled=True)

api_key = read_api_key("./groq_api.txt")

user_text = st.text_area("User Input", height=250)
if st.button("Submit"):
    if not user_text.strip():
        st.warning("Please enter some text.")
    elif not api_key:
        st.warning("Invalid API key.")
    else:
        with st.spinner("Calling Groq..."):
            ai_text = call_groq(api_key, model, system_prompt, user_text)
            processed_ai_text = post_process_groq(ai_text)

            if ai_text:
                st.text_area("AI Output", value=ai_text, height=250, disabled=True)
                st.markdown("### AI's additions and deletions:")
                diff_html = generate_diff_html(user_text, processed_ai_text)
                st.markdown(diff_html, unsafe_allow_html=True)