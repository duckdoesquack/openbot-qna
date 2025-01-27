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
            # Import and run preprocessing
            import preprocess_readme
            preprocess_readme.fetch_and_summarize()
            
            # Try loading again
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

# Combine all summaries with proper source tracking
combined_summary_content = []
for url, data in summaries.items():
    combined_summary_content.append({
        'url': url,
        'summary': data['summary']
    })

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
            margin-top: 8px;
            padding-top: 8px;
            border-top: 1px solid #eee;
        }
        .source-link {
            color: #0366d6;
            text-decoration: none;
            margin-right: 10px;
            display: inline-block;
            padding: 2px 6px;
            background-color: #f1f8ff;
            border-radius: 3px;
        }
        .source-link:hover {
            text-decoration: underline;
            background-color: #e1f0ff;
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

    # Save user input to chat history
    st.session_state.chat_history.append(("user", user_input))

    # Create prompt with pre-processed content
    contextual_prompt = f"""Based on the following summarized README content, please provide a detailed answer to the question:

{[f"Content from {item['url']}:\n{item['summary']}" for item in combined_summary_content]}

Question: {user_input}

Please provide a comprehensive answer and list the source URLs at the end of your response, prefixed with 'Sources:'."""

    try:
        response = model.start_chat(history=[]).send_message(contextual_prompt)
        
        # Extract the main response and sources
        response_text = response.text
        sources = []
        if 'Sources:' in response_text:
            main_response, sources_text = response_text.split('Sources:', 1)
            sources = [url.strip() for url in sources_text.split('\n') if url.strip()]
            response_text = main_response.strip()
        
        # Store the response with sources
        st.session_state.chat_history.append(("assistant", {
            "text": response_text,
            "sources": sources
        }))
    except Exception as e:
        st.error(f"Error generating response: {e}")

# Display chat history with proper source formatting
for role, message in st.session_state.chat_history:
    if role == "user":
        st.markdown(f"""
            <div class="response-card">
                <strong>You:</strong>
                <p>{message}</p>
            </div>
            """, unsafe_allow_html=True)
    else:
        # Handle the new message format with sources
        if isinstance(message, dict):
            response_html = f"""
                <div class="response-card">
                    <strong>Assistant:</strong>
                    <p>{message['text']}</p>
                    """
            if message['sources']:
                response_html += """
                    <div class="reference-text">
                        <strong>Sources:</strong><br>
                        """
                for source in message['sources']:
                    if source.startswith('http'):
                        response_html += f'<a href="{source}" class="source-link" target="_blank">{source.split("/")[-1]}</a>'
                response_html += "</div>"
            response_html += "</div>"
            st.markdown(response_html, unsafe_allow_html=True)
        else:
            # Fallback for old format messages
            st.markdown(f"""
                <div class="response-card">
                    <strong>Assistant:</strong>
                    <p>{message}</p>
                </div>
                """, unsafe_allow_html=True)
