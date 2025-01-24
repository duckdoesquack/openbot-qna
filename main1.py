import streamlit as st
import json
import os
from dotenv import load_dotenv
import google.generativeai as gen_ai

# Load environment variables
load_dotenv()

# Configure Streamlit page settings
st.set_page_config(
    page_title="OpenBot Chat",
    page_icon="🔍",
    layout="centered",
)

# Configure Google AI
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
gen_ai.configure(api_key=GOOGLE_API_KEY)
model = gen_ai.GenerativeModel('gemini-pro')

# Load pre-processed summaries
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

# Initialize session state for chat history
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Load the pre-processed summaries
summaries = load_summaries()

# Combine all summaries
combined_summary_content = "\n\n---\n\n".join(
    f"Summary from {url}:\n{data['summary']}" 
    for url, data in summaries.items()
)

# Header and CSS
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

# User input area
with st.form(key="user_input_form"):
    user_input = st.text_input(
        "Ask a question about OpenBot",
        placeholder="e.g., What is OpenBot?",
        key="user_input"
    )
    submit_button = st.form_submit_button("Ask")

# Process user input
if submit_button and user_input:
    if not combined_summary_content:
        st.error("Could not load summarized README contents.")
        st.stop()

    st.session_state.chat_history.append(("user", user_input))

    contextual_prompt = f"""Based on the README content below, answer this question: {user_input}

IMPORTANT: For any information you quote or reference, you must include the EXACT source URL from where the information was found (one of the GitHub README URLs preceding each summary).

Content:
{combined_summary_content}

End your response with:
Source(s): [List the exact GitHub URLs used]"""

    try:
        response = model.start_chat(history=[]).send_message(contextual_prompt)
        st.session_state.chat_history.append(("assistant", response.text))
    except Exception as e:
        st.error(f"Error generating response: {e}")

# Display chat history
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
