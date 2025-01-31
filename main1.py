import json
import os
import re
import streamlit as st
import google.generativeai as gen_ai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure Streamlit page settings
st.set_page_config(
    page_title="OpenBot Chat",
    page_icon="🔍",
    layout="centered",
)

# Set up the Generative AI model
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
gen_ai.configure(api_key=GOOGLE_API_KEY)
model = gen_ai.GenerativeModel('gemini-pro')

# Load preprocessed summarized README content
@st.cache_resource
def load_preprocessed_summaries():
    try:
        with open('summarized_readmes.json', 'r') as f:
            return json.load(f)
    except Exception as e:
        st.error(f"Error loading preprocessed summaries: {e}")
        return {}

# Load the summarized content
summarized_readme_contents = load_preprocessed_summaries()

# Combine all the summarized content into one string
combined_summary_content = "\n\n---\n\n".join([f"Summary from {url}:\n{summary}"
                                                  for url, summary in summarized_readme_contents.items()])

# Initialize session state for chat history if not already present
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Header section with CSS for formatting the chat
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

# Title of the Streamlit app
st.title("🔍 OpenBot Chat")

# Checkbox for debugging and displaying the combined summary content
if st.checkbox("Show Summarized README Content"):
    st.text_area("Combined Summarized README Content", combined_summary_content, height=200)

# User input area in the form
with st.form(key="user_input_form"):
    user_input = st.text_input(
        "Ask a question about OpenBot",
        placeholder="e.g., What is OpenBot?",
        key="user_input"
    )
    submit_button = st.form_submit_button("Ask")

# Process user input and generate response
def generate_improved_prompt(content_chunk, user_question):
    return f"""You are an expert assistant for OpenBot. Answer questions naturally as if you're 
having a conversation. Focus on providing helpful, practical information.

If you can answer the question based on the content below, provide a clear step-by-step response.
If you cannot answer the question based on the content, simply say "I apologize, but I don't have 
enough information about that specific topic in my current knowledge base."

Content: {content_chunk}

Question: {user_question}

Remember:
- Be direct and practical
- Give clear steps when possible
- Don't mention documentation unless citing specific technical details
- Don't add disclaimers about what you can or cannot find"""

def clean_response(response):
    """Clean up the response to make it more natural"""
    # Remove common disclaimers and awkward transitions
    cleanup_patterns = {
        r"Based on .*?, ": "",
        r"According to .*?, ": "",
        r"The documentation shows .*?: ": "",
        r"The provided context .*?: ": "",
        r"I can tell you that ": "",
        r"Let me explain ": "",
        r"This question cannot be answered.*": "I apologize, but I don't have enough information about that specific topic in my current knowledge base.",
        r"I cannot provide.*": "I apologize, but I don't have enough information about that specific topic in my current knowledge base."
    }
    
    cleaned = response
    for pattern, replacement in cleanup_patterns.items():
        cleaned = re.sub(pattern, replacement, cleaned, flags=re.IGNORECASE)
    
    # Remove duplicate sentences
    sentences = cleaned.split('. ')
    unique_sentences = list(dict.fromkeys(sentences))
    cleaned = '. '.join(unique_sentences)
    
    return cleaned.strip()

# Process user input and generate response
if submit_button and user_input:
    if not combined_summary_content:
        st.error("Could not load summarized README contents.")
        st.stop()

    st.session_state.chat_history.append(("user", user_input))

    # Split content into chunks if necessary
    CHUNK_SIZE = 15000
    readme_chunks = [combined_summary_content[i:i + CHUNK_SIZE] 
                    for i in range(0, len(combined_summary_content), CHUNK_SIZE)]

    responses = []
    for chunk in readme_chunks:
        try:
            improved_prompt = generate_improved_prompt(chunk, user_input)
            response = model.start_chat(history=[]).send_message(improved_prompt)
            cleaned_response = clean_response(response.text)
            if cleaned_response and not cleaned_response.isspace():
                responses.append(cleaned_response)
        except Exception as e:
            st.error(f"Error generating response: {e}")
            continue

    # Combine and clean the final response
    if responses:
        final_response = " ".join(responses)
        final_response = clean_response(final_response)  # Clean one final time
    else:
        final_response = "I apologize, but I don't have enough information about that specific topic in my current knowledge base."
    
    st.session_state.chat_history.append(("assistant", final_response))

# Display chat history (user and assistant messages)
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
