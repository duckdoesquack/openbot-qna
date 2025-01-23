import os
import streamlit as st
import requests
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
from transformers import pipeline

@st.cache_data
def fetch_and_cache_readmes(readme_urls):
    readme_contents = {}
    for url in readme_urls:
        raw_url = url.replace('github.com', 'raw.githubusercontent.com').replace('/blob/', '/')
        try:
            response = requests.get(raw_url)
            if response.status_code == 200:
                readme_contents[url] = response.text
        except Exception as e:
            st.error(f"Error fetching {url}: {e}")
    return readme_contents

def create_semantic_search_index(readme_contents):
    model = SentenceTransformer('all-MiniLM-L6-v2')
    texts = list(readme_contents.values())
    urls = list(readme_contents.keys())
    
    embeddings = model.encode(texts)
    dimension = embeddings.shape[1]
    
    index = faiss.IndexFlatL2(dimension)
    index.add(embeddings)
    
    return index, texts, urls, model

def semantic_search(query, index, texts, urls, model, top_k=3):
    query_embedding = model.encode([query])
    distances, indices = index.search(query_embedding, top_k)
    
    results = []
    for i in indices[0]:
        results.append({
            'text': texts[i],
            'url': urls[i]
        })
    
    return results

def generate_response(query, contexts):
    context_text = " ".join([ctx['text'] for ctx in contexts])
    sources = [ctx['url'] for ctx in contexts]
    
    # Use a smaller, faster model
    generator = pipeline('text-generation', model='distilgpt2')
    prompt = f"Context: {context_text}\n\nQuestion: {query}\n\nAnswer:"
    response = generator(prompt, max_length=250, num_return_sequences=1)[0]['generated_text']
    
    # Extract clean response
    cleaned_response = response.split("Answer:")[-1].strip()
    
    return cleaned_response, sources

def main():
    st.title("🤖 OpenBot README Assistant")
    
    # GitHub README URLs
    README_URLS = [
        "https://github.com/isl-org/OpenBot/blob/master/README.md",
        "https://github.com/isl-org/OpenBot/blob/master/android/README.md",
        # Add more README URLs as needed
    ]
    
    # Fetch and cache READMEs
    readme_contents = fetch_and_cache_readmes(README_URLS)
    
    # Create semantic search index
    index, texts, urls, model = create_semantic_search_index(readme_contents)
    
    # User query
    query = st.text_input("Ask about OpenBot")
    
    if query:
        # Semantic search
        contexts = semantic_search(query, index, texts, urls, model)
        
        # Generate response
        response, sources = generate_response(query, contexts)
        
        # Display response with source links
        st.markdown(response)
        
        st.markdown("### Sources:")
        for source in sources:
            st.markdown(f"- [{source}]({source})")

if __name__ == "__main__":
    main()
