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
    Validate the response for contradictions and empty content
    Returns: (bool, str) - (is_valid, cleaned_response)
    """
    if not response_text or response_text.isspace():
        return False, "No valid response generated."
    
    # Check for contradictory statements
    contradictions = [
        ("provided" in response_text.lower() and "not provided" in response_text.lower()),
        ("contains" in response_text.lower() and "does not contain" in response_text.lower()),
        ("found" in response_text.lower() and "not found" in response_text.lower())
    ]
    
    if any(contradictions):
        return False, "Response contained contradictions. Please try rephrasing your question."
    
    return True, response_text

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

# Debug checkbox
if st.checkbox("Show Summarized README Content"):
    st.text_area("Combined Summarized README Content", combined_summary_content, height=200)

# User input form
with st.form(key="user_input_form"):
    user_input = st.text_input(
        "Ask a question about OpenBot",
        placeholder="e.g., What is OpenBot?",
        key="user_input"
    )
    submit_button = st.form_submit_button("Ask")

def generate_response(user_input, chunk):
    """Generate and validate response for a single chunk"""
    contextual_prompt = f"""Based on the following summarized README content chunk, please answer the question.
If the information is not present in the provided content, respond with:
"I apologize, but I cannot find specific information about [topic] in the README files. If you're interested in this topic, you may want to check the project's discussion forums or issue tracker for more details."

Replace [topic] with the specific topic from the question.

If you find relevant information, include specific citations to the README files:

{chunk}

Question: {user_input}"""

    try:
        response = model.start_chat(history=[]).send_message(contextual_prompt)
        is_valid, cleaned_response = validate_response(response.text)
        return is_valid, cleaned_response
    except Exception as e:
        return False, f"Error generating response: {str(e)}"

    try:
        response = model.start_chat(history=[]).send_message(contextual_prompt)
        is_valid, cleaned_response = validate_response(response.text)
        return is_valid, cleaned_response
    except Exception as e:
        return False, f"Error generating response: {str(e)}"

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
        is_valid, response = generate_response(user_input, chunk)
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
        
    st.markdown(f"""
        <div class="{card_class}">
            <strong>{'You' if role == 'user' else 'Gemini-Pro'}:</strong>
            <p>{message}</p>
        </div>
        """, unsafe_allow_html=True)
