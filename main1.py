import os
import streamlit as st
from dotenv import load_dotenv
import requests
import google.generativeai as gen_ai
import time

# Load environment variables
load_dotenv()

# Configure Streamlit page settings
st.set_page_config(
    page_title="OpenBot Chat",
    page_icon="🔍",
    layout="centered",
)

README_URLS = {
    "https://github.com/isl-org/OpenBot/blob/master/README.md": 
        "https://raw.githubusercontent.com/isl-org/OpenBot/master/README.md",
    "https://github.com/isl-org/OpenBot/blob/master/android/README.md":
        "https://raw.githubusercontent.com/isl-org/OpenBot/master/android/README.md",
    "https://github.com/isl-org/OpenBot/blob/master/android/controller/README.md":
        "https://raw.githubusercontent.com/isl-org/OpenBot/master/android/controller/README.md",
    "https://github.com/isl-org/OpenBot/blob/master/android/robot/README.md":
        "https://raw.githubusercontent.com/isl-org/OpenBot/master/android/robot/README.md",
    "https://github.com/isl-org/OpenBot/blob/master/android/robot/src/main/java/org/openbot/googleServices/README.md":
        "https://raw.githubusercontent.com/isl-org/OpenBot/master/android/robot/src/main/java/org/openbot/googleServices/README.md",
    "https://github.com/isl-org/OpenBot/blob/master/android/robot/ContributionGuide.md":
        "https://raw.githubusercontent.com/isl-org/OpenBot/master/android/robot/ContributionGuide.md",
    "https://github.com/ob-f/OpenBot/blob/master/body/README.md":
        "https://raw.githubusercontent.com/ob-f/OpenBot/master/body/README.md",
    "https://github.com/ob-f/OpenBot/blob/master/body/diy/README.md":
        "https://raw.githubusercontent.com/ob-f/OpenBot/master/body/diy/README.md",
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

def summarize_readmes(max_retries=3):
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    gen_ai.configure(api_key=GOOGLE_API_KEY)
    model = gen_ai.GenerativeModel('gemini-pro')
    
    summarized_contents = []
    for display_url, raw_url in README_URLS.items():
        content = fetch_readme_content(display_url, raw_url)
        if content:
            for attempt in range(max_retries):
                try:
                    summary_response = model.start_chat(history=[]).send_message(
                        f"Provide a concise 1-2 sentence summary focusing on key information:\n\n{content[:3000]}"
                    )
                    summarized_contents.append(f"Summary from {display_url}:\n{summary_response.text}")
                    time.sleep(1)  # Rate limit mitigation
                    break
                except Exception as e:
                    if "429" in str(e):
                        st.warning(f"Rate limit hit for {display_url}. Waiting...")
                        time.sleep(2 ** attempt)
                    else:
                        st.error(f"Summarization error: {e}")
                        break
    
    return "\n\n---\n\n".join(summarized_contents) if summarized_contents else "OpenBot is an open-source robotic platform enabling mobile robot development using smartphones."

# Rest of the code remains the same as the previous implementation
# (main function, CSS styling, chat logic)

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

    # Display chat history (unchanged)
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
