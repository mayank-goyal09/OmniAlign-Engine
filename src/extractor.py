import sys
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

import os
from typing import List, Optional
from pydantic import BaseModel, Field
from langchain_community.document_loaders import PyPDFLoader
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import PromptTemplate

# 1. Define the 'Universal' Schema 🏗️
# This works for Resumes, Legal Docs, or Medical Reports!
class OmniSchema(BaseModel):
    document_type: str = Field(description="The category of document (e.g., Resume, Contract, Research)")
    entity_name: str = Field(description="The primary subject (e.g., Candidate Name, Company Name)")
    key_features: List[str] = Field(description="Top 5-10 skills, clauses, or technical specs found")
    experience_level: Optional[str] = Field(description="Seniority level or document complexity")
    summary: str = Field(description="A 3-sentence professional executive summary")

from dotenv import load_dotenv
load_dotenv()

import hashlib
import json
from langchain_openai import ChatOpenAI

# 2. Initialize the "Brain" 🧠
# Using Groq's llama-3.3-70b-versatile model for sub-second high-intelligence processing
llm = ChatOpenAI(
    base_url="https://api.groq.com/openai/v1",
    api_key=os.environ.get("GROQ_API_KEY"),
    model="llama-3.3-70b-versatile",
    temperature=0
)
parser = PydanticOutputParser(pydantic_object=OmniSchema)

CACHE_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "extraction_cache.json")

def get_file_hash(file_path: str) -> str:
    hasher = hashlib.md5()
    with open(file_path, 'rb') as f:
        buf = f.read()
        hasher.update(buf)
    return hasher.hexdigest()

def load_cache() -> dict:
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_cache(cache: dict):
    os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
    try:
        with open(CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(cache, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"⚠️ Warning: Could not save cache: {e}")

# 3. The Extraction Engine ⚙️
def extract_structured_data(file_path: str):
    try:
        file_hash = get_file_hash(file_path)
        cache = load_cache()
        if file_hash in cache:
            print(f"⚡ Cache hit for {os.path.basename(file_path)}!")
            return OmniSchema(**cache[file_hash])
    except Exception as e:
        print(f"⚠️ Warning: Cache check failed: {e}")
        file_hash = None
        cache = {}

    # Load the document based on type
    _, ext = os.path.splitext(file_path.lower())
    if ext == ".pdf":
        loader = PyPDFLoader(file_path)
        pages = loader.load_and_split()
        full_text = " ".join([page.page_content for page in pages])
    elif ext == ".docx":
        import docx
        doc = docx.Document(file_path)
        full_text = "\n".join([p.text for p in doc.paragraphs])
    elif ext in [".txt", ".md", ".json"]:
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            full_text = f.read()
    else:
        raise ValueError(f"Unsupported file format: {ext}")
    
    # Create the Prompt (The Instructions)
    prompt = PromptTemplate(
        template="You are a Master Data Analyst.\n{format_instructions}\nExtract data from this text:\n{text}",
        input_variables=["text"],
        partial_variables={"format_instructions": parser.get_format_instructions()},
    )

    # Combine & Run
    _input = prompt.format(text=full_text[:4000]) # Limit text to fit LLM window
    response = llm.invoke(_input)
    
    # Clean and Parse
    response_content = response.content if hasattr(response, "content") else str(response)
    parsed = parser.parse(response_content)
    
    # Save to cache
    if file_hash:
        try:
            cache[file_hash] = parsed.model_dump()
            save_cache(cache)
        except Exception as e:
            print(f"⚠️ Warning: Could not write cache entry: {e}")
            
    return parsed

# --- QUICK TEST ---
if __name__ == "__main__":
    # Create a dummy test or point to a real PDF
    # result = extract_structured_data("my_resume.pdf")
    # print(result.json())
    print("✅ Extractor Script Ready!")