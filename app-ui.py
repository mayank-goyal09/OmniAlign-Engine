import streamlit as st
import os
from src.extractor import extract_structured_data
from src.vector_engine import VectorEngine
from src.analyzer import GapAnalyzer

# Page Config 🚀
st.set_page_config(page_title="OmniMatch AI", layout="wide")
st.title("🤖 OmniMatch AI: Universal Semantic Engine")
st.markdown("---")

# Initialize Engine (using cache so it doesn't reload every time)
@st.cache_resource
def get_tools():
    return VectorEngine(), GapAnalyzer()

engine, analyzer = get_tools()

# Sidebar for Uploading 📂
with st.sidebar:
    st.header("Upload Documents")
    uploaded_files = st.file_uploader("Drop PDFs here", accept_multiple_files=True, type="pdf")
    
    if st.button("Process Documents"):
        for uploaded_file in uploaded_files:
            # Save temp file
            with open(uploaded_file.name, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            # Extract & Add to Vector Store
            with st.spinner(f"Reading {uploaded_file.name}..."):
                data = extract_structured_data(uploaded_file.name)
                data_dict = data.model_dump()  # Convert Pydantic model to dict
                engine.add_document(data_dict)
            st.success(f"Indexed: {data_dict['entity_name']}")

# Main Area for Matching 🔍
target_input = st.text_area("Enter your Target Requirements (Job Desc, Law, or Project Specs):")

if st.button("Run Semantic Match"):
    if target_input:
        with st.spinner("Finding the best match..."):
            results = engine.search(target_input, top_k=1)
            
            if results:
                best_match = results[0]
                st.subheader(f"🎯 Best Match Found: {best_match['entity_name']}")
                
                # Show Gap Analysis
                st.markdown("### 📊 Analysis Report")
                report_placeholder = st.empty()
                full_report = ""
                try:
                    # Stream the response chunk by chunk to prevent freezing and show immediate progress
                    report_stream = analyzer.generate_report_stream(target_input, best_match)
                    for chunk in report_stream:
                        full_report += chunk
                        report_placeholder.markdown(full_report)
                except Exception as e:
                    # Fallback if streaming fails
                    report = analyzer.generate_report(target_input, best_match)
                    report_placeholder.markdown(report)
            else:
                st.error("No documents found in the database. Please upload some first!")