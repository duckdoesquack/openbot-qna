import os
import streamlit as st
from dotenv import load_dotenv
import requests
import google.generativeai as gen_ai

# Load environment variables
load_dotenv()

# Configure Streamlit page settings
st.set_page_config(
    page_title="OpenBot Chat",
    page_icon="🔍",
    layout="centered",
)

# GitHub README URLs
README_URLS = {
    "https://github.com/isl-org/OpenBot/blob/master/README.md": 
        "https://raw.githubusercontent.com/isl-org/OpenBot/master/README.md",
    "https://github.com/isl-org/OpenBot/blob/master/android/README.md":
        "https://raw.githubusercontent.com/isl-org/OpenBot/master/android/README.md",
    "https://github.com/ob-f/OpenBot/blob/master/python/README.md":
        "https://raw.githubusercontent.com/ob-f/OpenBot/master/python/README.md"
}

@st.cache_resource
def fetch_readme_content(display_url, raw_url):
    try:
        response = requests.get(raw_url)
        return response.text if response.status_code == 200 else None
    except Exception as e:
        st.error(f"Error fetching README content: {e}")
        return None

def summarize_readmes():
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    gen_ai.configure(api_key=GOOGLE_API_KEY)
    model = gen_ai.GenerativeModel('gemini-pro')
    
    summarized_contents = []
    for display_url, raw_url in README_URLS.items():
        content = fetch_readme_content(display_url, raw_url)
        if content:
            try:
                summary_response = model.start_chat(history=[]).send_message(
                    f"Provide a concise 2-3 sentence summary of this README:\n\n{content}"
                )
                summarized_contents.append(f"Summary from {display_url}:\n{summary_response.text}")
            except Exception as e:
                st.error(f"Summarization error for {display_url}: {e}")
    
    return "\n\n---\n\n".join(summarized_contents)

# CSS Styling
st.markdown("""
    <style>
        .response-card {
            background-color: #f9f9f9;
            border: 1px solid #ddd;
            border-radius: 8px;
            padding: 15px;
            margin-top: 10px;
            color: #333;
        }
        .source-link {
            color: #0366d6;
            text-decoration: none;
        }
    </style>
    """, unsafe_allow_html=True)

def main():
    st.title("🔍 OpenBot Chat")

    # Initialize or load summarized content
    if 'combined_summary' not in st.session_state:
        st.session_state.combined_summary = summarize_readmes()

    # Initialize chat history
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # Optional debug view
    if st.checkbox("Show Summarized README Content"):
        st.text_area("Combined Summarized README Content", 
                     st.session_state.combined_summary, height=200)

    # User input form
    with st.form(key="user_input_form"):
        user_input = st.text_input(
            "Ask a question about OpenBot",
            placeholder="e.g., What is OpenBot?",
            key="user_input"
        )
        submit_button = st.form_submit_button("Ask")

    # Process user input
    if submit_button and user_input:
        GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
        gen_ai.configure(api_key=GOOGLE_API_KEY)
        model = gen_ai.GenerativeModel('gemini-pro')

        # Add user input to chat history
        st.session_state.chat_history.append(("user", user_input))

        # Generate response
        try:
            contextual_prompt = f"""Based on these README summaries:
{st.session_state.combined_summary}

Provide a concise, informative answer to this question: {user_input}

Include references to specific README sources if relevant."""
            
            response = model.start_chat(history=[]).send_message(contextual_prompt)
            
            # Add AI response to chat history
            st.session_state.chat_history.append(("assistant", response.text))
        
        except Exception as e:
            st.error(f"Response generation error: {e}")

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
                </div>
                """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
