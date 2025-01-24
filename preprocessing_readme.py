import os
import json
import requests
import google.generativeai as gen_ai
from dotenv import load_dotenv
import streamlit as st
from datetime import datetime

# Load environment variables
load_dotenv()

# Configure Google AI
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    st.error("Please set your GOOGLE_API_KEY in .env file")
    raise Exception("Missing GOOGLE_API_KEY")

gen_ai.configure(api_key=GOOGLE_API_KEY)
model = gen_ai.GenerativeModel('gemini-pro')

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

def fetch_and_summarize(progress_bar=None):
    summaries = {}
    total_urls = len(README_URLS)
    
    for idx, (display_url, raw_url) in enumerate(README_URLS.items()):
        try:
            # Update progress
            if progress_bar:
                progress_bar.progress((idx + 1) / total_urls, f"Processing {idx + 1}/{total_urls}")
            
            # Fetch README content
            response = requests.get(raw_url)
            if response.status_code == 200:
                content = response.text
                
                # More specific summary prompt
                summary_prompt = f"""
                Create a detailed, searchable summary of this README. Include:
                1. ALL technical information verbatim (commands, URLs, paths, versions)
                2. ALL setup instructions and requirements exactly as written
                3. ALL features and capabilities
                4. ALL functionality descriptions
                5. ALL configuration options
                Do not paraphrase technical details. Keep exact wording for critical information.

                README content:
                {content}

                Please ensure the summary retains exact links, commands, and technical details.
                """
                
                summary_response = model.start_chat(history=[]).send_message(summary_prompt)
                
                # Store both the summary and original content
                summaries[display_url] = {
                    "summary": summary_response.text,
                    "content": content,
                    "last_updated": datetime.now().isoformat(),
                    "path": raw_url
                }
                print(f"✓ Processed: {display_url}")
                if st:
                    st.write(f"✓ Processed: {display_url}")
            else:
                print(f"✗ Failed to fetch: {display_url}")
                if st:
                    st.error(f"Failed to fetch: {display_url}")
                
        except Exception as e:
            print(f"✗ Error processing {display_url}: {e}")
            if st:
                st.error(f"Error processing {display_url}: {e}")
            continue
    
    # Save to JSON file
    output_path = 'readme_summaries.json'
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(summaries, f, ensure_ascii=False, indent=2)
    
    print(f"\n✓ Saved summaries to {output_path}")
    if st:
        st.success(f"Saved summaries to {output_path}")
    
    return summaries

if __name__ == "__main__":
    fetch_and_summarize()
