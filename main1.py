import json
import os
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

#debug
summarized_readme_contents = load_preprocessed_summaries()
st.write("Debug - Content loaded:", bool(summarized_readme_contents))
st.write("Debug - Number of sources:", len(summarized_readme_contents))
if summarized_readme_contents:
    st.write("Debug - Available sources:", list(summarized_readme_contents.keys()))

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

import json
import os
import re
import streamlit as st
import google.generativeai as gen_ai
from dotenv import load_dotenv

def generate_improved_prompt(content_chunk, user_question):
    return f"""You are an expert assistant for OpenBot. When answering, follow these rules:

1. Always check the provided content thoroughly for ANY relevant information
2. If you find information, provide it in a clear format
3. Include the URL/source where you found the information
4. Never say there's no information if you find even partially relevant details

Content: {content_chunk}

Question: {user_question}

Format your response like this if you find information:
[Main answer with details]
Source: [source URL where information was found]

Only say you don't have information if there's absolutely nothing relevant in the content."""

def clean_response(response):
    """Clean up the response while preserving source information"""
    # Check if response contains actual information
    if len(response.strip()) < 50 and "apologize" in response.lower():
        return None
        
    # Preserve source information
    source_match = re.search(r'Source: (.*?)(?:\n|$)', response)
    source = source_match.group(1) if source_match else None
    
    # Clean the main content
    content = response
    if source:
        content = response.replace(f"Source: {source}", "").strip()
    
    # Remove common disclaimers
    cleanup_patterns = {
        r"^Based on .*?, ": "",
        r"^According to .*?, ": "",
        r"^The documentation shows that ": "",
        r"^I can tell you that ": "",
        r"^Let me explain ": "",
    }
    
    for pattern, replacement in cleanup_patterns.items():
        content = re.sub(pattern, content, flags=re.IGNORECASE)
    
    # Return both content and source
    return {
        'content': content.strip(),
        'source': source
    } if content.strip() else None

def process_chunk_response(chunk, user_input):
    """Process a single chunk and return its cleaned response with source"""
    try:
        improved_prompt = generate_improved_prompt(chunk, user_input)
        response = model.start_chat(history=[]).send_message(improved_prompt)
        return clean_response(response.text)
    except Exception as e:
        st.error(f"Error processing chunk: {e}")
        return None

# [Previous configurations remain the same...]

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

    # Process all chunks and collect valid responses
    valid_responses = []
    for chunk in readme_chunks:
        response = process_chunk_response(chunk, user_input)
        if response:
            valid_responses.append(response)

    # Combine responses and format with sources
    if valid_responses:
        # Combine unique content and collect sources
        combined_content = []
        sources = set()
        
        for response in valid_responses:
            if response['content']:
                combined_content.append(response['content'])
            if response['source']:
                sources.add(response['source'])
        
        final_response = "\n\n".join(combined_content)
        if sources:
            final_response += "\n\nSources:\n" + "\n".join(f"- {source}" for source in sources)
    else:
        final_response = "I apologize, but I don't have enough information about that specific topic in my current knowledge base."
    
    st.session_state.chat_history.append(("assistant", final_response))

# Display chat history with improved formatting
for role, message in st.session_state.chat_history:
    if role == "user":
        st.markdown(f"""
            <div class="response-card">
                <strong>You:</strong>
                <p>{message}</p>
            </div>
            """, unsafe_allow_html=True)
    else:
        # Split message into content and sources for better formatting
        parts = message.split("\n\nSources:")
        content = parts[0]
        sources = parts[1] if len(parts) > 1 else ""
        
        st.markdown(f"""
            <div class="response-card">
                <strong>Gemini-Pro:</strong>
                <p>{content}</p>
                {f'<p class="reference-text">{sources}</p>' if sources else ''}
            </div>
            """, unsafe_allow_html=True)
