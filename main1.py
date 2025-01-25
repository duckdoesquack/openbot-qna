import streamlit as st
import json
import os
from dotenv import load_dotenv
import google.generativeai as gen_ai

# Import preprocessing
from preprocess_readme import fetch_and_summarize

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
if not GOOGLE_API_KEY:
    st.error("Please set your GOOGLE_API_KEY in .env file")
    st.stop()

gen_ai.configure(api_key=GOOGLE_API_KEY)
model = gen_ai.GenerativeModel('gemini-pro')

# Load or create summaries
@st.cache_resource
def load_summaries():
    try:
        with open('readme_summaries.json', 'r', encoding='utf-8') as f:
            summaries = json.load(f)
            st.success("Loaded existing README summaries")
            return summaries
    except FileNotFoundError:
        st.warning("Generating initial README summaries... This may take a few minutes.")
        with st.progress(0.0) as progress_bar:
            summaries = fetch_and_summarize(progress_bar)
        st.success("Successfully created README summaries!")
        return summaries
    except Exception as e:
        st.error(f"Error: {e}")
        return {}

# Load the pre-processed summaries
summaries = load_summaries()

# Combine all summaries
combined_summary_content = "\n\n---\n\n".join(
    f"Summary from {url}:\n{data['summary']}" 
    for url, data in summaries.items()
)

# Initialize session state for chat history
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Header section with CSS
st.markdown("""
<style>
    .main-container { max-width: 750px; margin: 0 auto; }
    .response-card { background-color: #f9f9f9; border: 1px solid #ddd; border-radius: 8px; padding: 15px; margin-top: 10px; color: #333; }
    .reference-text { font-size: 12px; color: #555; }
    .source-link { color: #0366d6; text-decoration: none; margin-right: 10px; }
    .source-link:hover { text-decoration: underline; }
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

Quote relevant information directly and always include the source URL.
If information isn't found, say so clearly.
Format your response with the source link at the end like this:
[Source: URL]

Content:
{combined_summary_content}"""

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
