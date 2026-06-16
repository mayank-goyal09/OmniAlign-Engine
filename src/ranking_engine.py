import sys
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

import os
import json
import warnings
import numpy as np
import faiss
from typing import List

from pydantic import BaseModel, Field
from langchain_community.document_loaders import PyPDFLoader
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv
load_dotenv()

import logging
logging.getLogger("transformers.modeling_utils").setLevel(logging.ERROR)
warnings.filterwarnings("ignore")

# Define parser schema for ranking output
class RankingResult(BaseModel):
    alignment_score: int = Field(description="Integer score from 0 to 100 based on attribute alignment and skill transferability.")
    logic: str = Field(description="1-sentence explanation of why this entity is a high/low match.")

class EntityEvaluation(BaseModel):
    entity_id: str = Field(description="The exact entity_id of the entity being evaluated.")
    alignment_score: int = Field(description="Integer score from 0 to 100 based on attribute alignment and skill transferability.")
    logic: str = Field(description="1-sentence explanation of why this entity is a high/low match.")

class BatchRankingResult(BaseModel):
    evaluations: List[EntityEvaluation] = Field(description="List of evaluations for all the entities provided.")

class SemanticRankingEngine:
    def __init__(self, dimension: int = 384):
        # 1. Initialize the Vector Store (FAISS)
        self.index = faiss.IndexFlatL2(dimension)
        # 2. Initialize the Embedder
        self.embedder = SentenceTransformer('all-MiniLM-L6-v2')
        # 3. Initialize the Evaluator Brain (llama-3.3-70b-versatile via Groq)
        self.llm = ChatOpenAI(
            base_url="https://api.groq.com/openai/v1",
            api_key=os.environ.get("GROQ_API_KEY"),
            model="llama-3.3-70b-versatile",
            temperature=0
        )
        self.metadata = []
        self.parser = PydanticOutputParser(pydantic_object=RankingResult)
        self.batch_parser = PydanticOutputParser(pydantic_object=BatchRankingResult)
        
    def process_batch(self, directory_path: str, batch_size: int = 10):
        """Batch processing layer to stream documents from a directory to conserve RAM"""
        if not os.path.exists(directory_path):
            print(f"Directory {directory_path} not found.")
            return

        files = [os.path.join(directory_path, f) for f in os.listdir(directory_path) if f.lower().endswith(".pdf")]
        
        print(f"Found {len(files)} files to process in {directory_path}...")
        
        # Process in batches of 'batch_size'
        for i in range(0, len(files), batch_size):
            batch_files = files[i:i+batch_size]
            print(f"Processing batch {i//batch_size + 1} ({len(batch_files)} files)...")
            
            for file_path in batch_files:
                try:
                    # using PyPDFLoader to load document
                    loader = PyPDFLoader(file_path)
                    pages = loader.load_and_split()
                    
                    if not pages:
                        continue
                        
                    # We just join the first few pages to avoid massive embeddings
                    full_text = " ".join([page.page_content for page in pages[:3]])
                    
                    # Vector Indexing: Convert text to Vector
                    vector = self.embedder.encode([full_text])
                    
                    # Store in FAISS
                    self.index.add(np.array(vector).astype('float32'))
                    self.metadata.append({
                        "entity_id": os.path.basename(file_path),
                        "content": full_text
                    })
                    print(f"✅ Indexed {os.path.basename(file_path)}")
                except Exception as e:
                    print(f"❌ Failed to process {os.path.basename(file_path)}: {e}")

    def rank_entities(self, benchmark_reqs: str, top_n: int = 10) -> str:
        """Two-Stage Ranking Logic"""
        if len(self.metadata) == 0:
            return json.dumps({"error": "No entities indexed yet. Call process_batch first."})

        # --- Stage 1 (Retrieval): Use FAISS ---
        print("\n🔍 Stage 1: Retrieving top matches from vector database...")
        benchmark_vector = self.embedder.encode([benchmark_reqs])
        k = min(top_n, len(self.metadata))
        
        distances, indices = self.index.search(np.array(benchmark_vector).astype('float32'), k)
        
        top_entities = []
        for i in indices[0]:
            if i != -1:
                top_entities.append(self.metadata[i])
        
        if not top_entities:
            return json.dumps([])

        # --- Stage 2 (Groq Batch Evaluation): Pass to Llama 3.3 for evaluation ---
        print(f"🧠 Stage 2: Passing {len(top_entities)} entities to Llama 3.3 for batch evaluation...")
        
        # Format the candidates info
        candidates_str = ""
        for entity in top_entities:
            candidates_str += f"\n---\nEntity ID: {entity['entity_id']}\nProfile snippet:\n{entity['content'][:2000]}\n"

        batch_prompt = PromptTemplate(
            template="""You are an expert Alignment Evaluator.
Evaluate how well the following Entities' attributes map to the Benchmark Requirements.
Look for 'Skill Transferability' and 'Attribute Alignment' (e.g., strong problem-solving in one sector transferring well to another).

BENCHMARK REQUIREMENTS:
{benchmark}

ENTITIES TO EVALUATE:
{entities_content}

{format_instructions}
""",
            input_variables=["benchmark", "entities_content"],
            partial_variables={"format_instructions": self.batch_parser.get_format_instructions()},
        )

        leaderboard = []
        try:
            _input = batch_prompt.format(benchmark=benchmark_reqs, entities_content=candidates_str)
            response = self.llm.invoke(_input)
            response_content = response.content if hasattr(response, "content") else str(response)
            
            parsed_res = self.batch_parser.parse(response_content)
            for eval_entry in parsed_res.evaluations:
                leaderboard.append({
                    "entity_id": eval_entry.entity_id,
                    "alignment_score": eval_entry.alignment_score,
                    "logic": eval_entry.logic
                })
        except Exception as batch_error:
            print(f"⚠️ Batch evaluation failed: {batch_error}. Falling back to sequential evaluation...")
            # Fallback logic: individual sequential evaluation using Groq
            single_prompt = PromptTemplate(
                template="""You are an expert Alignment Evaluator.
Evaluate how well the Entity's attributes map to the Benchmark Requirements.
Look for 'Skill Transferability' and 'Attribute Alignment'.

BENCHMARK REQUIREMENTS:
{benchmark}

ENTITY PROFILE (Sample Context):
{entity_content}

{format_instructions}
""",
                input_variables=["benchmark", "entity_content"],
                partial_variables={"format_instructions": self.parser.get_format_instructions()},
            )
            for entity in top_entities:
                try:
                    content_snippet = entity['content'][:3000]
                    _input = single_prompt.format(benchmark=benchmark_reqs, entity_content=content_snippet)
                    
                    response = self.llm.invoke(_input)
                    response_content = response.content if hasattr(response, "content") else str(response)
                    parsed_res = self.parser.parse(response_content)
                    
                    leaderboard.append({
                        "entity_id": entity["entity_id"],
                        "alignment_score": parsed_res.alignment_score,
                        "logic": parsed_res.logic
                    })
                except Exception as single_error:
                    print(f"⚠️ Could not evaluate {entity['entity_id']} individually: {single_error}")

        # Sort by alignment score descending
        leaderboard.sort(key=lambda x: x["alignment_score"], reverse=True)
        
        # Final formatting
        final_results = []
        for rank, entry in enumerate(leaderboard, start=1):
            final_results.append({
                "rank": rank,
                "entity_id": entry["entity_id"],
                "alignment_score": entry["alignment_score"],
                "logic": entry["logic"]
            })
            
        return json.dumps(final_results, indent=4)

if __name__ == "__main__":
    engine = SemanticRankingEngine()
    
    # Simple test data (User should have some dummy pdfs in a directory)
    test_dir = "../data" # Assuming a data folder might exist
    
    print("Welcome to Semantic Comparison & Ranking Engine Demo!")
    
    # We won't auto-run it on a directory unless it exists
    if os.path.exists("test_docs"):
        engine.process_batch("test_docs")
        
        benchmark = "Looking for someone with deep expertise in optimizing highly distributed machine learning pipelines, specifically focusing on fault tolerance and low latency."
        result_json = engine.rank_entities(benchmark)
        
        print("\n🏆 --- LEADERBOARD --- 🏆")
        print(result_json)
    else:
        print("Note: To run a full test, create a 'test_docs' directory and add some PDFs.")
