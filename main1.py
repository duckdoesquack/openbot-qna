import streamlit as st
import google.generativeai as gen_ai
import requests
from typing import Dict, List, Tuple

# Initialize Gemini
gen_ai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
model = gen_ai.GenerativeModel('gemini-pro')

# Store README data in session state instead of SQLite
@st.cache_data(ttl=3600)  # Cache for 1 hour
def fetch_and_summarize_readmes() -> List[Tuple[str, str]]:
    README_URLS = {
    "Main README": "https://raw.githubusercontent.com/isl-org/OpenBot/master/README.md",
    "Android README": "https://raw.githubusercontent.com/isl-org/OpenBot/master/android/README.md",
    "Android Controller": "https://raw.githubusercontent.com/isl-org/OpenBot/master/android/controller/README.md",
    "Android Robot": "https://raw.githubusercontent.com/isl-org/OpenBot/master/android/robot/README.md",
    "Google Services": "https://raw.githubusercontent.com/isl-org/OpenBot/master/android/robot/src/main/java/org/openbot/googleServices/README.md",
    "Contribution Guide": "https://raw.githubusercontent.com/isl-org/OpenBot/master/android/robot/ContributionGuide.md",
    "Body": "https://raw.githubusercontent.com/ob-f/OpenBot/master/body/README.md",
    "Block Body": "https://raw.githubusercontent.com/ob-f/OpenBot/master/body/diy/cad/block_body/README.md",
    "Glue Body": "https://raw.githubusercontent.com/ob-f/OpenBot/master/body/diy/cad/glue_body/README.md",
    "Regular Body": "https://raw.githubusercontent.com/ob-f/OpenBot/master/body/diy/cad/regular_body/README.md",
    "Slim Body": "https://raw.githubusercontent.com/ob-f/OpenBot/master/body/diy/cad/slim_body/README.md",
    "PCB": "https://raw.githubusercontent.com/ob-f/OpenBot/master/body/diy/pcb/README.md",
    "DIY": "https://raw.githubusercontent.com/ob-f/OpenBot/master/body/diy/README.md",
    "Lite": "https://raw.githubusercontent.com/ob-f/OpenBot/master/body/lite/README.md",
    "MTV PCB": "https://raw.githubusercontent.com/ob-f/OpenBot/master/body/mtv/pcb/README.md",
    "MTV": "https://raw.githubusercontent.com/ob-f/OpenBot/master/body/mtv/README.md",
    "RC Truck": "https://raw.githubusercontent.com/ob-f/OpenBot/master/body/rc_truck/README.md",
    "RTR": "https://raw.githubusercontent.com/ob-f/OpenBot/master/body/rtr/README.md",
    "Launch Image": "https://raw.githubusercontent.com/ob-f/OpenBot/master/controller/flutter/ios/Runner/Assets.xcassets/LaunchImage.imageset/README.md",
    "Flutter": "https://raw.githubusercontent.com/ob-f/OpenBot/master/controller/flutter/README.md",
    "Firmware": "https://raw.githubusercontent.com/ob-f/OpenBot/master/firmware/README.md",
    "Authentication": "https://raw.githubusercontent.com/ob-f/OpenBot/master/ios/OpenBot/OpenBot/Authentication/README.md",
    "iOS": "https://raw.githubusercontent.com/ob-f/OpenBot/master/ios/OpenBot/README.md",
    "Blockly": "https://raw.githubusercontent.com/ob-f/OpenBot/master/open-code/src/components/blockly/README.md",
    "Services": "https://raw.githubusercontent.com/ob-f/OpenBot/master/open-code/src/services/README.md",
    "Open Code": "https://raw.githubusercontent.com/ob-f/OpenBot/master/open-code/README.md",
    "Policy Frontend": "https://raw.githubusercontent.com/ob-f/OpenBot/master/policy/frontend/README.md",
    "Policy": "https://raw.githubusercontent.com/ob-f/OpenBot/master/policy/README.md",
    "Python": "https://raw.githubusercontent.com/ob-f/OpenBot/master/python/README.md"
}
    
    summaries = []
    for i, (name, url) in enumerate(README_URLS.items()):
        if i > 0 and i % 5 == 0:  # Add delay every 5 requests
            time.sleep(60)  # Wait 60 seconds
        try:
            content = requests.get(url).text
            summary = model.start_chat(history=[]).send_message(
                f"Summarize this README:\n\n{content}",
                generation_config={"temperature": 0.3, "max_output_tokens": 500}
            ).text
            summaries.append((name, summary))
        except Exception as e:
            st.error(f"Error processing {name}: {str(e)}")
    return summaries

# UI Setup
st.set_page_config(page_title="OpenBot Chat", page_icon="🔍", layout="centered")

st.markdown("""
<style>
    .response-card {
        background-color: #f9f9f9;
        border: 1px solid #ddd;
        border-radius: 8px;
        padding: 15px;
        margin: 10px 0;
    }
    .user-message { background-color: #e3f2fd; }
    .bot-message { background-color: #f5f5f5; }
    .source-citation {
        font-size: 0.85em;
        color: #666;
        border-top: 1px solid #eee;
        margin-top: 10px;
        padding-top: 5px;
    }
</style>
""", unsafe_allow_html=True)

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Initialize or get README summaries
if "readme_data" not in st.session_state:
    with st.spinner("Loading OpenBot documentation..."):
        st.session_state.readme_data = fetch_and_summarize_readmes()

st.title("🔍 OpenBot Chat")

with st.form("chat_form"):
    user_input = st.text_input("Ask about OpenBot", placeholder="e.g., What is OpenBot?")
    submit = st.form_submit_button("Ask")

if submit and user_input:
    st.session_state.chat_history.append(("user", user_input))
    
    prompt = f"""Based on these OpenBot documentation summaries, answer the question. 
Include [SourceName] tags to indicate which README files contributed to your answer.

Documentation:
{' '.join([f'[{name}]: {summary}' for name, summary in st.session_state.readme_data])}

Question: {user_input}"""

    try:
        response = model.start_chat(history=[]).send_message(
            prompt,
            generation_config={"temperature": 0.3, "max_output_tokens": 1000}
        ).text
        st.session_state.chat_history.append(("assistant", response))
    except Exception as e:
        st.error(f"Error generating response: {str(e)}")

# Display chat history
for role, message in st.session_state.chat_history:
    css_class = "user-message" if role == "user" else "bot-message"
    speaker = "You" if role == "user" else "Assistant"
    
    if role == "assistant":
        message_parts = message.split("[Source")
        main_message = message_parts[0]
        sources = " [Source".join(message_parts[1:]) if len(message_parts) > 1 else ""
        
        st.markdown(f"""
            <div class="response-card {css_class}">
                <strong>{speaker}:</strong>
                <p>{main_message}</p>
                <div class="source-citation">{sources}</div>
            </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
            <div class="response-card {css_class}">
                <strong>{speaker}:</strong>
                <p>{message}</p>
            </div>
        """, unsafe_allow_html=True)
