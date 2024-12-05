import os
import streamlit as st
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import google.generativeai as gen_ai

# Load environment variables
load_dotenv()

# Configure Streamlit page settings
st.set_page_config(
    page_title="Chat with Gemini-Pro!",
    page_icon=":brain:",
    layout="centered",
)

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# Set up Google Gemini-Pro AI model
gen_ai.configure(api_key=GOOGLE_API_KEY)
model = gen_ai.GenerativeModel('gemini-pro')

# URL of the README file
README_URL = "https://github.com/isl-org/OpenBot/blob/master/README.md"

# Function to fetch and clean README content
@st.cache_resource
def fetch_readme_content(url):
    response = requests.get(url)
    if response.status_code != 200:
        st.error("Failed to fetch the README file. Please check the URL.")
        return None

    # Parse HTML content
    soup = BeautifulSoup(response.content, 'html.parser')

    # Find the README content section
    readme_section = soup.find("article", {"class": "markdown-body"})
    if not readme_section:
        st.error("Could not find the answer.")
        return None

    # Get the text content from the README section
    readme_text = readme_section.get_text(strip=True)
    return readme_text

# Load README content
readme_content = fetch_readme_content(README_URL)
if not readme_content:
    st.stop()  # Stop the app if the README can't be fetched or cleaned

# Initialize chat session in Streamlit if not already present
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []  # To store user and assistant messages

# Display the chatbot's title on the page
st.title("🤖 Gemini Pro - OpenBot README ChatBot")

# Display the chat history
for message in st.session_state.chat_history:
    role, text = message
    with st.chat_message(role):
        st.markdown(text)

# Input field for user's message
user_prompt = st.chat_input("Ask Gemini-Pro about OpenBot...")
if user_prompt:
    # Add user's message to chat and display it
    st.session_state.chat_history.append(("user", user_prompt))
    st.chat_message("user").markdown(user_prompt)

    # Create contextual prompt using cleaned README content
    contextual_prompt = f"Based on the following README content, answer the question:\n\n{readme_content}\n\nQuestion: {user_prompt}"
    gemini_response = model.start_chat(history=[]).send_message(contextual_prompt)

    # Add assistant's response to chat history
    st.session_state.chat_history.append(("assistant", gemini_response.text))

    # Display assistant's response
    with st.chat_message("assistant"):
        st.markdown(gemini_response.text)
