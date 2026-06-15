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

import os
import json

DB_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "vector_db.json")

class VectorEngine:
    def __init__(self, dimension: int = 384):
        # 384 is the standard size for the MiniLM model
        self.index = faiss.IndexFlatL2(dimension)
        self.metadata = [] # To keep track of which vector belongs to which doc
        self.load_from_disk()

    def add_document(self, doc_json: dict):
        # Check if already exists, if so remove first to avoid duplicates
        self.remove_document(doc_json['entity_name'], save=False)

        # We combine the summary and features into one "searchable" string
        text_to_embed = f"{doc_json['summary']} Keywords: {', '.join(doc_json['key_features'])}"
        
        # Convert text to Vector 🧬
        vector = model.encode([text_to_embed])[0]
        
        # Add to FAISS index
        self.index.add(np.array([vector]).astype('float32'))
        
        # Save vector as list in metadata for serialization
        doc_json_copy = doc_json.copy()
        doc_json_copy['vector'] = vector.tolist()
        self.metadata.append(doc_json_copy)
        self.save_to_disk()
        print(f"✅ Added {doc_json['entity_name']} to the Vector Map!")

    def remove_document(self, entity_name: str, save: bool = True):
        initial_len = len(self.metadata)
        self.metadata = [doc for doc in self.metadata if doc['entity_name'] != entity_name]
        if len(self.metadata) < initial_len:
            self.rebuild_index()
            if save:
                self.save_to_disk()
            print(f"❌ Removed {entity_name} from the Vector Map!")
            return True
        return False

    def rebuild_index(self):
        self.index.reset()
        if self.metadata:
            vectors = np.array([doc['vector'] for doc in self.metadata]).astype('float32')
            self.index.add(vectors)

    def save_to_disk(self):
        os.makedirs(os.path.dirname(DB_FILE), exist_ok=True)
        try:
            with open(DB_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.metadata, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"⚠️ Warning: Could not save vector database: {e}")

    def load_from_disk(self):
        if os.path.exists(DB_FILE):
            try:
                with open(DB_FILE, 'r', encoding='utf-8') as f:
                    self.metadata = json.load(f)
                self.rebuild_index()
                print(f"⚡ Loaded {len(self.metadata)} documents from database!")
            except Exception as e:
                print(f"⚠️ Warning: Could not load vector database: {e}")

    def search(self, query_text: str, top_k: int = 2):
        if not self.metadata:
            return []
        # Convert the user's query into a vector
        query_vector = model.encode([query_text])
        
        # Find the 'k' closest documents
        k = min(top_k, len(self.metadata))
        distances, indices = self.index.search(np.array(query_vector).astype('float32'), k)
        
        results = []
        for i in indices[0]:
            if i != -1 and i < len(self.metadata): # -1 means no match found
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