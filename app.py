# --- THE MASTER CONTROLLER --- ⚙️
import sys
import os

# Fix Windows console encoding for emoji/unicode output
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

from src.extractor import extract_structured_data
from src.vector_engine import VectorEngine
from src.analyzer import GapAnalyzer

# Initialize our Engine
engine = VectorEngine()
analyzer = GapAnalyzer()

def run_project(new_job_desc: str, pdf_files: list):
    # 1. Read & Extract all PDFs
    for pdf in pdf_files:
        data = extract_structured_data(pdf)
        # Convert Pydantic model to dict so downstream code can use dict-style access
        data_dict = data.model_dump()
        engine.add_document(data_dict)
    
    # 2. Search for the Best Match
    best_matches = engine.search(new_job_desc, top_k=1)
    
    if best_matches:
        top_match = best_matches[0]
        print(f"✅ Found the best match: {top_match['entity_name']}")
        
        # 3. Generate the Report
        report = analyzer.generate_report(new_job_desc, top_match)
        print("\n📈 --- FINAL REPORT --- 📈")
        print(report)
    else:
        print("❌ No matches found!")

if __name__ == "__main__":
    print("🚀 Starting OmniMatch...")
    run_project(
        new_job_desc="Senior Data Scientist with experience in AI and Machine Learning", 
        pdf_files=[r"data\MayankGoyal_Resume.pdf"]
    )