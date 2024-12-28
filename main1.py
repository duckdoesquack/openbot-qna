import os
import streamlit as st
from dotenv import load_dotenv
import requests
from bs4 import BeautifulSoup
import google.generativeai as gen_ai
import re

# Load environment variables
load_dotenv()

# Configure Streamlit page settings
st.set_page_config(
    page_title="OpenBot Chat",
    page_icon="🔍",
    layout="centered",
)

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
gen_ai.configure(api_key=GOOGLE_API_KEY)
model = gen_ai.GenerativeModel('gemini-pro')

README_URLS = [
    "https://github.com/isl-org/OpenBot/blob/master/README.md",
    "https://github.com/isl-org/OpenBot/blob/master/android/README.md",
]

@st.cache_resource
def fetch_readme_content(url):
    try:
        # Handle GitHub blob URLs
        if "github.com" in url and "/blob/" in url:
            # Convert to raw content URL
            url = url.replace("/blob/", "/raw/")
        
        response = requests.get(url)
        if response.status_code != 200:
            st.error(f"Failed to fetch README content for {url}. Status code: {response.status_code}")
            return None

        soup = BeautifulSoup(response.content, 'html.parser')
        readme_section = soup.find("article", {"class": "markdown-body"})
        if not readme_section:
            # If no markdown-body found, return the full text
            return response.text

        return readme_section.get_text(strip=True)
    except Exception as e:
        st.error(f"Error fetching README content: {e}")
        return None

# Fetch contents of all README URLs
readme_contents = []
for url in README_URLS:
    content = fetch_readme_content(url)
    if content:
        readme_contents.append(f"README from {url}:\n{content}")

# Combine README contents
combined_readme_content = "\n\n---\n\n".join(readme_contents)

# Initialize session state for chat history
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Header section with CSS
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
    # Check if README content is loaded
    if not combined_readme_content:
        st.error("Could not load README contents.")
        st.stop()

    # Save user input to chat history
    st.session_state.chat_history.append(("user", user_input))

    # Generate response using Google Gemini
    contextual_prompt = f"Based on the following combined README contents, answer the question precisely. If information is from a specific README, mention its source:\n\n{combined_readme_content}\n\nQuestion: {user_input}"
    
    try:
        response = model.start_chat(history=[]).send_message(contextual_prompt)

        # Save response to chat history
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
        # Extract links from assistant's response
        links = re.findall(r'\((https?://[^\s]+)\)', message)
        link_html = ""
        if links:
            link_html = " ".join(
                f'<a href="{link}" target="_blank">{link}</a>' for link in links
            )

        # Add assistant's response with dynamically linked sources
        st.markdown(f"""
            <div class="response-card">
                <strong>Gemini-Pro:</strong>
                <p>{message}</p>
                <div class="reference-text">
                    Based on OpenBot README content from {link_html}.
                </div>
            </div>
            """, unsafe_allow_html=True)
