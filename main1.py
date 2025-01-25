import streamlit as st
import json
import os
from dotenv import load_dotenv
import google.generativeai as gen_ai
from tenacity import retry, wait_exponential, stop_after_attempt
import time

load_dotenv()

st.set_page_config(
    page_title="OpenBot Chat",
    page_icon="🔍",
    layout="centered",
)

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
gen_ai.configure(api_key=GOOGLE_API_KEY)
model = gen_ai.GenerativeModel('gemini-pro')

@retry(wait=wait_exponential(min=2, max=120), stop=stop_after_attempt(5))
def get_model_response(prompt):
    try:
        return model.start_chat(history=[]).send_message(prompt)
    except Exception as e:
        if "429" in str(e):
            time.sleep(2)
            raise
        raise

@st.cache_resource
def load_summaries():
    try:
        with open('readme_summaries.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        st.warning("No summaries found. Running initial preprocessing...")
        try:
            import preprocess_readme
            preprocess_readme.fetch_and_summarize()
            with open('readme_summaries.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            st.error(f"Failed to generate summaries: {e}")
            return {}
    except Exception as e:
        st.error(f"Error loading summaries: {e}")
        return {}

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

summaries = load_summaries()
combined_summary_content = "\n\n---\n\n".join(
    f"Summary from {url}:\n{data['summary']}" 
    for url, data in summaries.items()
)

st.markdown("""
    <style>
        .main-container {
            max-width: 750px;
            margin: 0 auto;
        }
        .response-card {
            background-color: #f9f9f9;
            border: 1px solid #ddd;
            border-radius: 8px;
            padding: 15px;
            margin-top: 10px;
            color: #333;
        }
        .reference-text {
            font-size: 12px;
            color: #555;
        }
        .source-link {
            color: #0366d6;
            text-decoration: none;
            margin-right: 10px;
        }
        .source-link:hover {
            text-decoration: underline;
        }
    </style>
    """, unsafe_allow_html=True)

st.title("🔍 OpenBot Chat")

with st.form(key="user_input_form"):
    user_input = st.text_input(
        "Ask a question about OpenBot",
        placeholder="e.g., What is OpenBot?",
        key="user_input"
    )
    submit_button = st.form_submit_button("Ask")

if submit_button and user_input:
    if not combined_summary_content:
        st.error("Could not load summarized README contents.")
        st.stop()

    st.session_state.chat_history.append(("user", user_input))

    contextual_prompt = f"""Based on the following summarized README content, please provide a detailed answer to the question:

{combined_summary_content}

Question: {user_input}

Please provide a comprehensive answer and cite which README file(s) the information comes from."""

    try:
        response = get_model_response(contextual_prompt)
        st.session_state.chat_history.append(("assistant", response.text))
    except Exception as e:
        st.error(f"Error generating response: {e}")

for role, message in st.session_state.chat_history:
    if role == "user":
        st.markdown(f"""
            <div class="response-card">
                <strong>You:</strong>
                <p>{message}</p>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
            <div class="response-card">
                <strong>Assistant:</strong>
                <p>{message}</p>
            </div>
            """, unsafe_allow_html=True)
