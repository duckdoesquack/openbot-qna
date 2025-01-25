import streamlit as st
import google.generativeai as gen_ai
import json
from datetime import datetime

gen_ai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
model = gen_ai.GenerativeModel('gemini-pro')

@st.cache_data
def load_readme_data():
    try:
        with open('readme_summaries.json', 'r') as f:
            data = json.load(f)
        return data["summaries"], datetime.fromtimestamp(data["last_updated"])
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        return [], datetime.now()

st.set_page_config(page_title="OpenBot Chat", page_icon="🔍", layout="centered")

st.markdown("""
<style>
    .response-card {
        background-color: #f9f9f9;
        border: 1px solid #ddd;
        border-radius: 8px;
        padding: 15px;
        margin: 10px 0;
    }
    .user-message { background-color: #e3f2fd; }
    .bot-message { background-color: #f5f5f5; }
    .source-citation {
        font-size: 0.85em;
        color: #666;
        border-top: 1px solid #eee;
        margin-top: 10px;
        padding-top: 5px;
    }
</style>
""", unsafe_allow_html=True)

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

readme_data, last_updated = load_readme_data()
st.sidebar.info(f"Data last updated: {last_updated.strftime('%Y-%m-%d %H:%M:%S')}")

st.title("🔍 OpenBot Chat")

with st.form("chat_form"):
    user_input = st.text_input("Ask about OpenBot", placeholder="e.g., What is OpenBot?")
    submit = st.form_submit_button("Ask")

if submit and user_input:
    st.session_state.chat_history.append(("user", user_input))
    
    prompt = f"""Based on these OpenBot documentation summaries, answer the question. 
Include [SourceName] tags to indicate which README files contributed to your answer.

Documentation:
{' '.join([f'[{name}]: {summary}' for name, summary in readme_data])}

Question: {user_input}"""

    try:
        response = model.start_chat(history=[]).send_message(
            prompt,
            generation_config={"temperature": 0.3, "max_output_tokens": 1000}
        ).text
        st.session_state.chat_history.append(("assistant", response))
    except Exception as e:
        st.error(f"Error generating response: {str(e)}")

for role, message in st.session_state.chat_history:
    css_class = "user-message" if role == "user" else "bot-message"
    speaker = "You" if role == "user" else "Assistant"
    
    if role == "assistant":
        message_parts = message.split("[Source")
        main_message = message_parts[0]
        sources = " [Source".join(message_parts[1:]) if len(message_parts) > 1 else ""
        
        st.markdown(f"""
            <div class="response-card {css_class}">
                <strong>{speaker}:</strong>
                <p>{main_message}</p>
                <div class="source-citation">{sources}</div>
            </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
            <div class="response-card {css_class}">
                <strong>{speaker}:</strong>
                <p>{message}</p>
            </div>
        """, unsafe_allow_html=True)
