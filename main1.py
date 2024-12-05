import os
import streamlit as st
from dotenv import load_dotenv
import requests
from bs4 import BeautifulSoup
import google.generativeai as gen_ai

# Load environment variables
load_dotenv()

# Configure Streamlit page settings
st.set_page_config(
    page_title="OpenBot Chat - Perplexity Style",
    page_icon="🔍",
    layout="centered",
)

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
gen_ai.configure(api_key=GOOGLE_API_KEY)
model = gen_ai.GenerativeModel('gemini-pro')

README_URL = "https://github.com/isl-org/OpenBot/blob/master/README.md"

@st.cache_resource
def fetch_readme_content(url):
    response = requests.get(url)
    if response.status_code != 200:
        st.error("Failed to fetch README content. Please check the URL.")
        return None

    soup = BeautifulSoup(response.content, 'html.parser')
    readme_section = soup.find("article", {"class": "markdown-body"})
    if not readme_section:
        st.error("Could not extract README content.")
        return None

    return readme_section.get_text(strip=True)

readme_content = fetch_readme_content(README_URL)
if not readme_content:
    st.stop()

# Initialize session state for chat history
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Header section
st.markdown("""
    <style>
        .main-container {
            max-width: 750px;
            margin: 0 auto;
        }
        .search-bar {
            width: 100%;
            margin-top: 20px;
            margin-bottom: 20px;
        }
        .response-card {
            background-color: #f9f9f9;
            border: 1px solid #ddd;
            border-radius: 8px;
            padding: 15px;
            margin-top: 10px;
            color: #333; /* Set text color to a readable dark shade */
        }
        .reference-text {
            font-size: 12px;
            color: #555;
        }
    </style>
    """, unsafe_allow_html=True)


st.title("🔍 OpenBot Chat - Perplexity Style")

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
    # Save user input to chat history
    st.session_state.chat_history.append(("user", user_input))

    # Generate response using Google Gemini
    contextual_prompt = f"Based on the following README content, answer the question:\n\n{readme_content}\n\nQuestion: {user_input}"
    response = model.start_chat(history=[]).send_message(contextual_prompt)

    # Save response to chat history
    st.session_state.chat_history.append(("assistant", response.text))

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
                <strong>Gemini-Pro:</strong>
                <p>{message}</p>
                <div class="reference-text">
                    Based on the README content from <a href="{README_URL}" target="_blank">OpenBot GitHub</a>.
                </div>
            </div>
            """, unsafe_allow_html=True)
