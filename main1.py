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

def validate_response(response_text):
    """
    Improved validation that better preserves useful information
    """
    if not response_text or response_text.isspace():
        return False, "No valid response generated."
    
    # Check for positive information indicators
    info_indicators = ['you can', 'needs', 'requires', 'steps', 'components', 'instructions', 
                      'build', 'hardware', 'software', 'install', 'download', 'available']
    
    has_info = any(indicator in response_text.lower() for indicator in info_indicators)
    
    # If we have actual information, clean up without removing it
    if has_info:
        # Remove only standalone negative statements
        sentences = [s.strip() for s in response_text.split('.') if s.strip()]
        cleaned_sentences = []
        
        for sentence in sentences:
            # Keep sentences with actual information
            if not any(phrase in sentence.lower() for phrase in 
                ["not provided", "does not contain", "not found", "cannot find"]):
                cleaned_sentences.append(sentence)
        
        if cleaned_sentences:
            cleaned_response = '. '.join(cleaned_sentences).strip()
            if not cleaned_response.endswith('.'):
                cleaned_response += '.'
            return True, cleaned_response
    
    # Check if it's just a "no information" response
    if any(phrase in response_text.lower() for phrase in 
           ["cannot find information", "no information available"]):
        return True, response_text
    
    return False, "No valid information found."

@st.cache_resource
def load_preprocessed_summaries():
    """Load and validate preprocessed README summaries"""
    try:
        with open('summarized_readmes.json', 'r') as f:
            summaries = json.load(f)
            if not summaries:
                raise ValueError("Summarized README file is empty")
            return summaries
    except FileNotFoundError:
        st.error("Could not find the summarized README file. Please ensure it exists.")
        return {}
    except json.JSONDecodeError:
        st.error("Invalid JSON format in the summarized README file.")
        return {}
    except Exception as e:
        st.error(f"Unexpected error loading summaries: {e}")
        return {}

def generate_response(user_input, chunk, summarized_contents):
    """
    Improved response generation with better prompting and source tracking
    """
    # Find relevant README files based on user input
    relevant_files = []
    for url, content in summarized_contents.items():
        if any(term in url.lower() or term in content.lower() for term in user_input.lower().split()):
            relevant_files.append(url)

    contextual_prompt = f"""You are an expert on OpenBot. Based on the following README content, 
provide a detailed answer about {user_input}. 

Important instructions:
1. Look for ANY relevant information about the topic
2. Include information about components, requirements, or related concepts
3. If you find ANY information that might help, include it
4. ALWAYS include the source URL when providing information
5. Format source citations as 'Source: [URL]' at the end of your response
6. Only say you cannot find information if there is absolutely nothing relevant

Content:
{chunk}

Relevant README files: {', '.join(relevant_files) if relevant_files else 'Search all files'}

Question: {user_input}

Remember: Even partial or related information is valuable. Include it and cite the source."""

    try:
        response = model.start_chat(history=[]).send_message(contextual_prompt)
        is_valid, cleaned_response = validate_response(response.text)
        
        # If we found relevant files but got no valid response, try one more time
        if relevant_files and not is_valid:
            response = model.start_chat(history=[]).send_message(contextual_prompt)
            is_valid, cleaned_response = validate_response(response.text)
        
        return is_valid, cleaned_response
    except Exception as e:
        return False, f"Error generating response: {str(e)}"

# Load the summarized content
summarized_readme_contents = load_preprocessed_summaries()

# Combine all the summarized content into one string
combined_summary_content = "\n\n---\n\n".join([f"Summary from {url}:\n{summary}"
                                              for url, summary in summarized_readme_contents.items()])

# Initialize session state
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Styling
st.markdown("""
    <style>
        .main-container { max-width: 750px; margin: 0 auto; }
        .response-card {
            background-color: #f9f9f9;
            border: 1px solid #ddd;
            border-radius: 8px;
            padding: 15px;
            margin-top: 10px;
            color: #333;
        }
        .error-card {
            background-color: #ffe6e6;
            border: 1px solid #ff9999;
        }
        .reference-text { font-size: 12px; color: #555; }
        .source-link {
            color: #0366d6;
            text-decoration: none;
            margin-right: 10px;
        }
        .source-link:hover { text-decoration: underline; }
    </style>
    """, unsafe_allow_html=True)

st.title("🔍 OpenBot Chat")

# Debug checkboxes
if st.checkbox("Show Summarized README Content"):
    st.text_area("Combined Summarized README Content", combined_summary_content, height=200)

if st.checkbox("Show RTR Content"):
    rtr_content = next((content for url, content in summarized_readme_contents.items() 
                       if 'rtr' in url.lower()), None)
    st.write("RTR README content:", rtr_content)

# User input form
with st.form(key="user_input_form"):
    user_input = st.text_input(
        "Ask a question about OpenBot",
        placeholder="e.g., What is OpenBot?",
        key="user_input"
    )
    submit_button = st.form_submit_button("Ask")

# Process user input and generate response
if submit_button and user_input:
    if not combined_summary_content:
        st.error("No README content available for processing.")
        st.stop()

    # Save user input
    st.session_state.chat_history.append(("user", user_input))

    # Split content into chunks
    CHUNK_SIZE = 15000
    readme_chunks = [combined_summary_content[i:i + CHUNK_SIZE] 
                    for i in range(0, len(combined_summary_content), CHUNK_SIZE)]

    # Process all chunks
    valid_responses = []
    for chunk in readme_chunks:
        is_valid, response = generate_response(user_input, chunk, summarized_readme_contents)
        if is_valid and "cannot find information" not in response.lower():
            valid_responses.append(response)

    # Prepare final response
    if valid_responses:
        final_response = "\n\n".join(valid_responses)
    else:
        final_response = "I cannot find information about this topic in the README files."

    st.session_state.chat_history.append(("assistant", final_response))

# Display chat history
for role, message in st.session_state.chat_history:
    card_class = "response-card"
    if "error" in message.lower():
        card_class += " error-card"
    
    # Split message into content and sources for better formatting
    parts = message.split("Source:")
    content = parts[0].strip()
    sources = "Source:" + parts[1] if len(parts) > 1 else ""
        
    st.markdown(f"""
        <div class="{card_class}">
            <strong>{'You' if role == 'user' else 'Gemini-Pro'}:</strong>
            <p>{content}</p>
            {f'<p class="reference-text">{sources}</p>' if sources else ''}
        </div>
        """, unsafe_allow_html=True)
