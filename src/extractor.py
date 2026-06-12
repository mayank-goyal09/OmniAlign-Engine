import sys
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

import os
from typing import List, Optional
from pydantic import BaseModel, Field
from langchain_community.document_loaders import PyPDFLoader
from langchain_ollama import OllamaLLM
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

# 2. Initialize the "Brain" 🧠
llm = OllamaLLM(model="mistral") 
parser = PydanticOutputParser(pydantic_object=OmniSchema)

# 3. The Extraction Engine ⚙️
def extract_structured_data(file_path: str):
    # Load the PDF
    loader = PyPDFLoader(file_path)
    pages = loader.load_and_split()
    full_text = " ".join([page.page_content for page in pages])
    
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
    return parser.parse(response)

# --- QUICK TEST ---
if __name__ == "__main__":
    # Create a dummy test or point to a real PDF
    # result = extract_structured_data("my_resume.pdf")
    # print(result.json())
    print("✅ Extractor Script Ready!")