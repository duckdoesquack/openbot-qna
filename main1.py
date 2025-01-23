import os
import streamlit as st
from dotenv import load_dotenv
import requests
import google.generativeai as gen_ai
import sqlite3
from datetime import datetime, timedelta
from contextlib import contextmanager
import threading

# Load environment variables
load_dotenv()

# Thread-local storage for database connections
thread_local = threading.local()

# Database setup and connection management
@contextmanager
def get_db_connection():
    """Thread-safe database connection context manager"""
    if not hasattr(thread_local, "connection"):
        thread_local.connection = sqlite3.connect('openbot_summaries.db', check_same_thread=False)
    try:
        yield thread_local.connection
    except Exception as e:
        thread_local.connection.rollback()
        raise e

def init_db():
    """Initialize the database schema"""
    with get_db_connection() as conn:
        c = conn.cursor()
        # Check if table exists
        c.execute('''SELECT count(name) FROM sqlite_master 
                    WHERE type='table' AND name='readme_summaries' ''')
        if c.fetchone()[0] == 0:
            c.execute('''
                CREATE TABLE readme_summaries (
                    url TEXT PRIMARY KEY,
                    summary TEXT,
                    last_updated TIMESTAMP
                )
            ''')
            conn.commit()
            return True  # Table was created
        return False    # Table already existed

def update_summary_in_db(url, summary):
    """Update a single summary in the database"""
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute('''
            INSERT OR REPLACE INTO readme_summaries (url, summary, last_updated)
            VALUES (?, ?, ?)
        ''', (url, summary, datetime.now().isoformat()))
        conn.commit()

def get_summaries_from_db():
    """Retrieve all summaries from the database"""
    init_db()  # Ensure table exists
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute('SELECT url, summary FROM readme_summaries')
        return c.fetchall()

def is_update_needed():
    """Check if the database needs updating"""
    init_db()  # Ensure table exists
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute('SELECT COUNT(*) FROM readme_summaries')
        count = c.fetchone()[0]
        
        if count == 0:
            return True
            
        c.execute('SELECT MAX(last_updated) FROM readme_summaries')
        result = c.fetchone()[0]
        
        if result is None:
            return True
        
        try:
            last_update = datetime.fromisoformat(result)
        except (ValueError, TypeError):
            return True
            
        return datetime.now() - last_update > timedelta(days=1)

# README URLs dictionary (your existing README_URLS dictionary here)
README_URLS = {
    # Your existing URLs here
}

# README processing functions
def fetch_and_summarize_readmes():
    """Process all READMEs and store summaries"""
    try:
        init_db()  # Ensure database exists
        
        GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
        gen_ai.configure(api_key=GOOGLE_API_KEY)
        model = gen_ai.GenerativeModel('gemini-pro')
        
        for display_url, raw_url in README_URLS.items():
            try:
                response = requests.get(raw_url)
                if response.status_code == 200:
                    content = response.text
                    summary_prompt = f"Summarize the following README content briefly:\n\n{content}"
                    summary_response = model.start_chat(history=[]).send_message(summary_prompt)
                    summary = summary_response.text
                    update_summary_in_db(display_url, summary)
            except Exception as e:
                st.error(f"Error processing {display_url}: {str(e)}")
    except Exception as e:
        st.error(f"Error during README processing: {str(e)}")

# Streamlit cache for summaries
@st.cache_data(ttl=3600)  # Cache for 1 hour
def get_cached_summaries():
    """Get cached summaries with thread-safe database access"""
    try:
        summaries = get_summaries_from_db()
        if not summaries:
            return ""
        return "\n\n---\n\n".join([f"Summary from {url}:\n{summary}" 
                                  for url, summary in summaries])
    except Exception as e:
        st.error(f"Error retrieving cached summaries: {str(e)}")
        return ""

# Streamlit app setup
st.set_page_config(
    page_title="OpenBot Chat",
    page_icon="🔍",
    layout="centered",
)

# Initialize database on startup
init_db()

# Initialize Gemini model
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    st.error("GOOGLE_API_KEY not found in environment variables")
    st.stop()

gen_ai.configure(api_key=GOOGLE_API_KEY)
model = gen_ai.GenerativeModel('gemini-pro')

# Initialize session state
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Styling
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
    </style>
    """, unsafe_allow_html=True)

st.title("🔍 OpenBot Chat")

# Check for updates and process if needed
try:
    if is_update_needed():
        st.info("Updating README summaries... This may take a few minutes.")
        fetch_and_summarize_readmes()
except Exception as e:
    st.error(f"Error checking for updates: {str(e)}")

# Get summaries
combined_summary_content = get_cached_summaries()

# Debug information
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

# Process user input
if submit_button and user_input:
    if not combined_summary_content:
        st.warning("No summaries available. Processing READMEs...")
        fetch_and_summarize_readmes()
        combined_summary_content = get_cached_summaries()
        if not combined_summary_content:
            st.error("Could not process READMEs. Please try again later.")
            st.stop()

    st.session_state.chat_history.append(("user", user_input))

    # Process in chunks
    CHUNK_SIZE = 15000
    readme_chunks = [combined_summary_content[i:i + CHUNK_SIZE] 
                    for i in range(0, len(combined_summary_content), CHUNK_SIZE)]

    responses = []
    for chunk in readme_chunks:
        try:
            contextual_prompt = f"""Based on the following summarized README content chunk, please provide a detailed answer to the question. If the information comes from a specific README, include that source in your response:

{chunk}

Question: {user_input}

Please provide a comprehensive answer and cite which README file(s) the information comes from."""
            response = model.start_chat(history=[]).send_message(contextual_prompt)
            responses.append(response.text)
        except Exception as e:
            st.error(f"Error generating response: {str(e)}")
            continue

    if responses:
        final_response = "\n\n---\n\n".join(responses)
        st.session_state.chat_history.append(("assistant", final_response))
    else:
        st.error("Failed to generate any responses. Please try again.")

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
