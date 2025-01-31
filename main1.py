import json
import os
import re
import streamlit as st
import google.generativeai as gen_ai
from dotenv import load_dotenv

def generate_improved_prompt(content_chunk, user_question):
    return f"""You are an expert assistant for OpenBot. Answer as directly as possible. 
If the information exists in the content below, provide it in a clear, step-by-step format.
Only say you don't have enough information if the content truly doesn't contain any relevant details.

Content: {content_chunk}

Question: {user_question}

Important: If you find ANY relevant information, include it in your response."""

def clean_response(response):
    """Clean up the response while preserving valid information"""
    # Don't remove content if it contains actual information
    if any(indicator in response.lower() for indicator in ['step', 'you can', 'need to', 'require', 'follow']):
        # Only clean up introductory phrases
        cleanup_patterns = {
            r"^Based on .*?, ": "",
            r"^According to .*?, ": "",
            r"^The documentation shows that ": "",
            r"^I can tell you that ": "",
            r"^Let me explain ": "",
        }
        
        cleaned = response
        for pattern, replacement in cleanup_patterns.items():
            cleaned = re.sub(pattern, replacement, cleaned, flags=re.IGNORECASE)
        
        return cleaned.strip()
    
    # If no clear information indicators found, check for explicit "no information" statements
    if any(phrase in response.lower() for phrase in [
        "cannot be answered",
        "don't have enough information",
        "cannot provide",
        "no information available"
    ]):
        return "I apologize, but I don't have enough information about that specific topic in my current knowledge base."
    
    # If response exists but doesn't match above patterns, preserve it
    return response.strip()

def process_chunk_response(chunk, user_input):
    """Process a single chunk and return its cleaned response"""
    try:
        improved_prompt = generate_improved_prompt(chunk, user_input)
        response = model.start_chat(history=[]).send_message(improved_prompt)
        cleaned_response = clean_response(response.text)
        
        # Only return the response if it contains actual information
        if cleaned_response and not cleaned_response.startswith("I apologize"):
            return cleaned_response
        return None
    except Exception as e:
        st.error(f"Error processing chunk: {e}")
        return None

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

    # Combine valid responses or provide fallback
    if valid_responses:
        final_response = " ".join(valid_responses)
    else:
        final_response = "I apologize, but I don't have enough information about that specific topic in my current knowledge base."
    
    st.session_state.chat_history.append(("assistant", final_response))

# [Rest of the display code remains the same...]
