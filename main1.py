import os
import streamlit as st
from dotenv import load_dotenv
from sqlalchemy import create_engine
import google.generativeai as gen_ai

# Load environment variables
load_dotenv()

# Function to get summaries from the database
def get_summaries_from_db():
    engine = create_engine(os.getenv("DATABASE_URL"))
    with engine.connect() as connection:
        result = connection.execute("SELECT * FROM readme_summaries")
        summaries = result.fetchall()
    return summaries

# Configure Streamlit page settings
st.set_page_config(page_title="OpenBot Chat", page_icon="🔍", layout="centered")

# Configure Gemini AI
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
gen_ai.configure(api_key=GOOGLE_API_KEY)
model = gen_ai.GenerativeModel('gemini-pro')

# Initialize session state for chat history
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

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

st.title("🔍 OpenBot Chat")

# User input area
with st.form(key="user_input_form"):
    user_input = st.text_input("Ask a question about OpenBot", placeholder="e.g., What is OpenBot?", key="user_input")
    submit_button = st.form_submit_button("Ask")

# Process user input
if submit_button and user_input:
    # Get the summarized content from the database
    summarized_readme_contents = get_summaries_from_db()
    
    if not summarized_readme_contents:
        st.error("Could not load summarized README contents from the database.")
        st.stop()

    # Save user input to chat history
    st.session_state.chat_history.append(("user", user_input))

    # Split the summarized content into chunks if necessary
    CHUNK_SIZE = 15000  # Adjust chunk size to fit within token limits
    readme_chunks = [content[1] for content in summarized_readme_contents]  # Assuming the second item in tuple is the summary content

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
