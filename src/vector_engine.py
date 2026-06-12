import sys
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

import faiss
import numpy as np
import warnings
warnings.filterwarnings("ignore")
import logging
logging.getLogger("transformers.modeling_utils").setLevel(logging.ERROR)

from sentence_transformers import SentenceTransformer

# 1. Load the "Translator" 🤖
# This model turns English sentences into lists of numbers (Vectors)
model = SentenceTransformer('all-MiniLM-L6-v2') 

class VectorEngine:
    def __init__(self, dimension: int = 384):
        # 384 is the standard size for the MiniLM model
        self.index = faiss.IndexFlatL2(dimension)
        self.metadata = [] # To keep track of which vector belongs to which doc

    def add_document(self, doc_json: dict):
        # We combine the summary and features into one "searchable" string
        text_to_embed = f"{doc_json['summary']} Keywords: {', '.join(doc_json['key_features'])}"
        
        # Convert text to Vector 🧬
        vector = model.encode([text_to_embed])
        
        # Add to FAISS index
        self.index.add(np.array(vector).astype('float32'))
        self.metadata.append(doc_json)
        print(f"✅ Added {doc_json['entity_name']} to the Vector Map!")

    def search(self, query_text: str, top_k: int = 2):
        # Convert the user's query into a vector
        query_vector = model.encode([query_text])
        
        # Find the 'k' closest documents
        distances, indices = self.index.search(np.array(query_vector).astype('float32'), top_k)
        
        results = []
        for i in indices[0]:
            if i != -1: # -1 means no match found
                results.append(self.metadata[i])
        return results

# --- QUICK TEST ---
if __name__ == "__main__":
    engine = VectorEngine()
    # Dummy data for testing
    test_doc = {
        "entity_name": "Mayank Goyal",
        "summary": "Data Science student focused on AI and Automation.",
        "key_features": ["Python", "LLMs", "FAISS"]
    }
    engine.add_document(test_doc)
    
    matches = engine.search("Looking for an AI automation expert")
    print(f"Top Match: {matches[0]['entity_name']}")