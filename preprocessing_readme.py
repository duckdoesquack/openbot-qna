import os
import json
import time
import requests
import google.generativeai as gen_ai

gen_ai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
model = gen_ai.GenerativeModel('gemini-pro')

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

def process_readmes():
    summaries = []
    for i, (name, url) in enumerate(README_URLS.items()):
        if i > 0 and i % 5 == 0:
            time.sleep(60)
        try:
            content = requests.get(url).text
            summary = model.start_chat(history=[]).send_message(
                f"Summarize this README:\n\n{content}",
                generation_config={"temperature": 0.3, "max_output_tokens": 500}
            ).text
            summaries.append([name, summary])
        except Exception as e:
            print(f"Error processing {name}: {e}")
    
    data = {
        "last_updated": time.time(),
        "summaries": summaries
    }
    
    with open('readme_summaries.json', 'w') as f:
        json.dump(data, f)

if __name__ == "__main__":
    process_readmes()
