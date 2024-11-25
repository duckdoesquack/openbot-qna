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
    page_icon=":brain:",  # Favicon emoji
    layout="centered",  # Page layout option
)

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# Set up Google Gemini-Pro AI model
gen_ai.configure(api_key=GOOGLE_API_KEY)
model = gen_ai.GenerativeModel('gemini-pro')

# URL of the README file
README_URL = "https://github.com/isl-org/OpenBot/blob/master/README.md"

# Function to fetch README content
@st.cache_resource
def fetch_readme_content(url):
    response = requests.get(url)
    if response.status_code != 200:
        st.error("Failed to fetch the README file. Please check the URL.")
        return None

    # Parse README content
    soup = BeautifulSoup(response.content, 'html.parser')
    readme_text = soup.get_text(strip=True)
    return readme_text

# Load README content
readme_content = fetch_readme_content(README_URL)
if not readme_content:
    st.stop()  # Stop the app if the README can't be fetched

# Initialize chat session in Streamlit if not already present
if "chat_session" not in st.session_state:
    st.session_state.chat_session = model.start_chat(history=[])

# Display the chatbot's title on the page
st.title("🤖 Gemini Pro - OpenBot README ChatBot")

# Display the chat history
for message in st.session_state.chat_session.history:
    with st.chat_message("assistant" if message.role == "model" else "user"):
        st.markdown(message.parts[0].text)

# Input field for user's message
user_prompt = st.chat_input("Ask Gemini-Pro about OpenBot...")
if user_prompt:
    # Add user's message to chat and display it
    st.chat_message("user").markdown(user_prompt)

    # Prepend README content to user's prompt
    contextual_prompt = f"Based on the following README content, answer the question:\n\n{readme_content}\n\nQuestion: {user_prompt}"
    gemini_response = st.session_state.chat_session.send_message(contextual_prompt)

    # Display Gemini-Pro's response
    with st.chat_message("assistant"):
        st.markdown(gemini_response.text)
