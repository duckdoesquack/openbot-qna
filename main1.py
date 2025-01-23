import os
import streamlit as st
from dotenv import load_dotenv
import requests
import google.generativeai as gen_ai
import time
import random

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
    "https://github.com/ob-f/OpenBot/blob/master/body/diy/cad/block_body/README.md":
        "https://raw.githubusercontent.com/ob-f/OpenBot/master/body/diy/cad/block_body/README.md",
    "https://github.com/ob-f/OpenBot/blob/master/body/diy/cad/glue_body/README.md":
        "https://raw.githubusercontent.com/ob-f/OpenBot/master/body/diy/cad/glue_body/README.md",
    "https://github.com/ob-f/OpenBot/blob/master/body/diy/cad/regular_body/README.md":
        "https://raw.githubusercontent.com/ob-f/OpenBot/master/body/diy/cad/regular_body/README.md",
    "https://github.com/ob-f/OpenBot/blob/master/body/diy/cad/slim_body/README.md":
        "https://raw.githubusercontent.com/ob-f/OpenBot/master/body/diy/cad/slim_body/README.md",
    "https://github.com/ob-f/OpenBot/blob/master/body/diy/pcb/README.md":
        "https://raw.githubusercontent.com/ob-f/OpenBot/master/body/diy/pcb/README.md",
    "https://github.com/ob-f/OpenBot/blob/master/body/diy/README.md":
        "https://raw.githubusercontent.com/ob-f/OpenBot/master/body/diy/README.md",
    "https://github.com/ob-f/OpenBot/blob/master/body/lite/README.md":
        "https://raw.githubusercontent.com/ob-f/OpenBot/master/body/lite/README.md",
    "https://github.com/ob-f/OpenBot/blob/master/body/mtv/pcb/README.md":
        "https://raw.githubusercontent.com/ob-f/OpenBot/master/body/mtv/pcb/README.md",
    "https://github.com/ob-f/OpenBot/blob/master/body/mtv/README.md":
        "https://raw.githubusercontent.com/ob-f/OpenBot/master/body/mtv/README.md",
    "https://github.com/ob-f/OpenBot/blob/master/body/rc_truck/README.md":
        "https://raw.githubusercontent.com/ob-f/OpenBot/master/body/rc_truck/README.md",
    "https://github.com/ob-f/OpenBot/blob/master/body/rtr/README.md":
        "https://raw.githubusercontent.com/ob-f/OpenBot/master/body/rtr/README.md",
    "https://github.com/ob-f/OpenBot/blob/master/controller/flutter/ios/Runner/Assets.xcassets/LaunchImage.imageset/README.md":
        "https://raw.githubusercontent.com/ob-f/OpenBot/master/controller/flutter/ios/Runner/Assets.xcassets/LaunchImage.imageset/README.md",
    "https://github.com/ob-f/OpenBot/blob/master/controller/flutter/README.md":
        "https://raw.githubusercontent.com/ob-f/OpenBot/master/controller/flutter/README.md",
    "https://github.com/ob-f/OpenBot/blob/master/firmware/README.md":
        "https://raw.githubusercontent.com/ob-f/OpenBot/master/firmware/README.md",
    "https://github.com/ob-f/OpenBot/blob/master/ios/OpenBot/OpenBot/Authentication/README.md":
        "https://raw.githubusercontent.com/ob-f/OpenBot/master/ios/OpenBot/OpenBot/Authentication/README.md",
    "https://github.com/ob-f/OpenBot/blob/master/ios/OpenBot/README.md":
        "https://raw.githubusercontent.com/ob-f/OpenBot/master/ios/OpenBot/README.md",
    "https://github.com/ob-f/OpenBot/blob/master/open-code/src/components/blockly/README.md":
        "https://raw.githubusercontent.com/ob-f/OpenBot/master/open-code/src/components/blockly/README.md",
    "https://github.com/ob-f/OpenBot/blob/master/open-code/src/services/README.md":
        "https://raw.githubusercontent.com/ob-f/OpenBot/master/open-code/src/services/README.md",
    "https://github.com/ob-f/OpenBot/blob/master/open-code/README.md":
        "https://raw.githubusercontent.com/ob-f/OpenBot/master/open-code/README.md",
    "https://github.com/ob-f/OpenBot/blob/master/policy/frontend/README.md":
        "https://raw.githubusercontent.com/ob-f/OpenBot/master/policy/frontend/README.md",
    "https://github.com/ob-f/OpenBot/blob/master/policy/README.md":
        "https://raw.githubusercontent.com/ob-f/OpenBot/master/policy/README.md",
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

def smart_summarize(content, model):
    """Intelligent summary generation with fallback"""
    try:
        summary_response = model.start_chat(history=[]).send_message(
            f"Extract the most crucial 2-3 sentences describing the core purpose and functionality:\n\n{content[:3000]}"
        )
        return summary_response.text
    except Exception as e:
        # Fallback summary generation
        if len(content) > 500:
            return content[:500] + "... (truncated)"
        return content

def summarize_readmes():
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    gen_ai.configure(api_key=GOOGLE_API_KEY)
    model = gen_ai.GenerativeModel('gemini-pro')
    
    summarized_contents = []
    for display_url, raw_url in README_URLS.items():
        content = fetch_readme_content(display_url, raw_url)
        if content:
            summary = smart_summarize(content, model)
            summarized_contents.append(f"Summary from {display_url}:\n{summary}")
            
            # Gentle rate limit mitigation
            time.sleep(random.uniform(0.5, 1.5))
    
    return "\n\n---\n\n".join(summarized_contents) if summarized_contents else "OpenBot is an open-source robotic platform for mobile robot development."

def main():
    st.title("🔍 OpenBot Chat")

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

   if submit_button and user_input:
    # Check if summarized content is loaded
    if not combined_summary_content:
        st.error("Could not load summarized README contents.")
        st.stop()

    # Save user input to chat history
    st.session_state.chat_history.append(("user", user_input))

    # Split the summarized content into chunks if necessary
    CHUNK_SIZE = 15000  # Adjust chunk size to fit within token limits
    readme_chunks = [combined_summary_content[i:i + CHUNK_SIZE] for i in range(0, len(combined_summary_content), CHUNK_SIZE)]

    responses = []
    for chunk in readme_chunks:
        contextual_prompt = f"""Based on the following summarized README content chunk, please provide a detailed answer to the question. If the information comes from a specific README, include that source in your response:

{chunk}

Question: {user_input}

Please provide a comprehensive answer and cite which README file(s) the information comes from."""
        try:
            response = model.start_chat(history=[]).send_message(contextual_prompt)
            responses.append(response.text)
        except Exception as e:
            st.error(f"Error generating response for a chunk: {e}")
            continue

    # Combine the responses into a single reply
    final_response = "\n\n---\n\n".join(responses)
    st.session_state.chat_history.append(("assistant", final_response))

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

f __name__ == "__main__":
    main()
