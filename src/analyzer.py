import sys
import os
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

from dotenv import load_dotenv
load_dotenv()

from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate

# Initialize our Critic 🧠
# Using Groq's llama-3.3-70b-versatile model for sub-second high-intelligence processing
llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    temperature=0,
    groq_api_key=os.environ.get("GROQ_API_KEY")
)

class GapAnalyzer:
    def __init__(self):
        self.template = """
        You are a Senior Industry Consultant. 
        Compare the 'Candidate/Document' against the 'Target Requirements'.
        
        TARGET REQUIREMENTS:
        {target}
        
        CANDIDATE/DOCUMENT DATA:
        {candidate}
        
        Provide a professional report with:
        1. MATCH SCORE: (0-100)
        2. STRENGTHS: (Top 3 alignment points)
        3. GAPS: (What is missing or weak?)
        4. ACTION PLAN: (How to bridge the gap?)
        
        Format as a clean bulleted list.
        """
        self.prompt = PromptTemplate(template=self.template, input_variables=["target", "candidate"])

    def generate_report(self, target_text, candidate_json):
        # We convert the JSON back to a string for the LLM to read
        candidate_str = f"Name: {candidate_json['entity_name']}\nSkills: {', '.join(candidate_json['key_features'])}\nSummary: {candidate_json['summary']}"
        
        _input = self.prompt.format(target=target_text, candidate=candidate_str)
        response = llm.invoke(_input)
        return response.content if hasattr(response, "content") else str(response)

    def generate_report_stream(self, target_text, candidate_json):
        # Convert the JSON back to a string for the LLM to read
        candidate_str = f"Name: {candidate_json['entity_name']}\nSkills: {', '.join(candidate_json['key_features'])}\nSummary: {candidate_json['summary']}"
        
        _input = self.prompt.format(target=target_text, candidate=candidate_str)
        for chunk in llm.stream(_input):
            yield chunk.content if hasattr(chunk, "content") else str(chunk)

# --- QUICK TEST ---
if __name__ == "__main__":
    analyzer = GapAnalyzer()
    
    # Example: A Job Description
    job_desc = "We need a Senior Data Scientist with 5 years of experience in AWS, Docker, and Python."
    
    # Example: Our extracted data from Step 1
    my_data = {
        "entity_name": "Mayank",
        "key_features": ["Python", "Machine Learning", "FAISS"],
        "summary": "AI enthusiast with 2 years experience in building LLM projects."
    }
    
    report = analyzer.generate_report(job_desc, my_data)
    print("🚀 --- GAP ANALYSIS REPORT --- 🚀")
    print(report)