import streamlit as st
import json
import os
from dotenv import load_dotenv
import google.generativeai as gen_ai

load_dotenv()

st.set_page_config(
    page_title="OpenBot Chat",
    page_icon="🔍",
    layout="centered",
)

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
gen_ai.configure(api_key=GOOGLE_API_KEY)
model = gen_ai.GenerativeModel('gemini-pro')

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
    f"Content from {url}:\n{data['summary']}" 
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
            margin-top: 8px;
            padding-top: 8px;
            border-top: 1px solid #eee;
        }
        .source-link {
            color: #0366d6;
            text-decoration: none;
            margin-right: 10px;
            padding: 2px 6px;
            background: #f1f8ff;
            border-radius: 3px;
            font-size: 12px;
        }
        .source-link:hover {
            background: #dbedff;
        }
        .summary-text {
            color: #666;
            font-style: italic;
            margin-bottom: 12px;
            padding-bottom: 8px;
            border-bottom: 1px solid #eee;
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

    contextual_prompt = f"""Based on the following content, provide:
1. A one-sentence summary
2. A detailed answer
3. Relevant source URLs

Content:
{combined_summary_content}

Question: {user_input}

Format:
SUMMARY: [one sentence]
ANSWER: [detailed explanation]
SOURCES: [urls]"""

    try:
        response = model.start_chat(history=[]).send_message(contextual_prompt)
        
        sections = {
            'SUMMARY': '',
            'ANSWER': '',
            'SOURCES': []
        }
        
        current_section = None
        for line in response.text.split('\n'):
            if line.startswith('SUMMARY:'):
                current_section = 'SUMMARY'
                sections[current_section] = line.replace('SUMMARY:', '').strip()
            elif line.startswith('ANSWER:'):
                current_section = 'ANSWER'
                sections[current_section] = line.replace('ANSWER:', '').strip()
            elif line.startswith('SOURCES:'):
                current_section = 'SOURCES'
                sources_text = line.replace('SOURCES:', '').strip()
                sections[current_section] = [url.strip() for url in sources_text.split(',')]
            elif current_section and line.strip():
                if current_section == 'SOURCES':
                    sections[current_section].extend([url.strip() for url in line.split(',')])
                else:
                    sections[current_section] += ' ' + line.strip()
        
        st.session_state.chat_history.append(("assistant", sections))
        
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
                <div class="summary-text">{message['SUMMARY']}</div>
                <p>{message['ANSWER']}</p>
                <div class="reference-text">
                    <strong>Sources:</strong><br>
                    {''.join(f'<a href="{url}" class="source-link" target="_blank">📄 Source {i+1}</a>' for i, url in enumerate(message['SOURCES']))}
                </div>
            </div>
            """, unsafe_allow_html=True)
