import streamlit as st
import os
import re
from src.extractor import extract_structured_data
from src.vector_engine import VectorEngine
from src.analyzer import GapAnalyzer

# Page Config 🚀
st.set_page_config(page_title="OmniMatch AI", layout="wide", initial_sidebar_state="collapsed")

# Initialize Engine (using cache so it doesn't reload every time)
@st.cache_resource
def get_tools():
    return VectorEngine(), GapAnalyzer()

engine, analyzer = get_tools()

# Styling
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap');

/* Shifting aurora background animation */
@keyframes aurora {
    0% { background-position: 0% 50%; }
    50% { background-position: 100% 50%; }
    100% { background-position: 0% 50%; }
}

body, [data-testid="stAppViewContainer"], .main {
    background: linear-gradient(-45deg, #0e0a1f, #160e35, #080512, #211548) !important;
    background-size: 400% 400% !important;
    animation: aurora 20s ease infinite !important;
    font-family: 'Outfit', sans-serif !important;
    color: #e0e0fc !important;
}

/* Hide Streamlit headers and footers */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

/* Custom Glassmorphism Card style */
.glass-card {
    background: rgba(22, 17, 43, 0.65) !important;
    backdrop-filter: blur(12px) !important;
    -webkit-backdrop-filter: blur(12px) !important;
    border: 1px solid rgba(111, 76, 255, 0.25) !important;
    border-radius: 18px !important;
    padding: 24px !important;
    margin-bottom: 20px !important;
    box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.4) !important;
    transition: all 0.3s ease !important;
}

.glass-card:hover {
    border-color: rgba(111, 76, 255, 0.45) !important;
    box-shadow: 0 8px 32px 0 rgba(111, 76, 255, 0.2) !important;
    transform: translateY(-2px) !important;
}

/* Stat Cards for System Overview Dashboard */
.stat-card {
    background: rgba(22, 17, 43, 0.5) !important;
    backdrop-filter: blur(8px) !important;
    -webkit-backdrop-filter: blur(8px) !important;
    border: 1px solid rgba(111, 76, 255, 0.2) !important;
    border-radius: 14px !important;
    padding: 16px !important;
    text-align: center !important;
    transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1) !important;
    box-shadow: 0 4px 24px rgba(0, 0, 0, 0.3) !important;
}

.stat-card:hover {
    border-color: rgba(111, 76, 255, 0.45) !important;
    background: rgba(111, 76, 255, 0.08) !important;
    transform: translateY(-4px) !important;
    box-shadow: 0 10px 30px rgba(111, 76, 255, 0.25) !important;
}

.stat-val {
    font-size: 24px !important;
    font-weight: 700 !important;
    color: #ffffff !important;
    margin-bottom: 4px !important;
    text-shadow: 0 0 10px rgba(255,255,255,0.1);
}

.stat-label {
    font-size: 11px !important;
    color: #a5a2e6 !important;
    text-transform: uppercase !important;
    letter-spacing: 1.5px !important;
    font-weight: 500 !important;
}

/* Prompt Box Styling (rounded rectangular) */
div[data-testid="stTextArea"] {
    background: transparent !important;
}
div[data-testid="stTextArea"] textarea {
    background: rgba(15, 11, 33, 0.75) !important;
    color: #f0f0ff !important;
    border: 2px solid rgba(111, 76, 255, 0.35) !important;
    border-radius: 20px !important;
    padding: 18px 24px !important;
    font-size: 16px !important;
    line-height: 1.6 !important;
    font-family: 'Outfit', sans-serif !important;
    box-shadow: inset 0 2px 4px rgba(0,0,0,0.5) !important;
    transition: all 0.3s ease !important;
}

div[data-testid="stTextArea"] textarea:focus {
    border-color: #9d7cff !important;
    box-shadow: 0 0 15px rgba(111, 76, 255, 0.5) !important;
    background: rgba(18, 13, 38, 0.85) !important;
}

/* Buttons */
div.stButton > button {
    background: linear-gradient(135deg, #6f4cff 0%, #a855f7 100%) !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 30px !important;
    padding: 12px 36px !important;
    font-weight: 600 !important;
    font-size: 16px !important;
    letter-spacing: 0.5px !important;
    box-shadow: 0 4px 15px rgba(111, 76, 255, 0.3) !important;
    transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1) !important;
    margin: 0 auto !important;
    display: block !important;
}

div.stButton > button:hover {
    background: linear-gradient(135deg, #8162ff 0%, #b866ff 100%) !important;
    box-shadow: 0 6px 20px rgba(111, 76, 255, 0.5), 0 0 12px rgba(168, 85, 247, 0.3) !important;
    transform: translateY(-1px) !important;
}

div.stButton > button:active {
    transform: translateY(1px) !important;
}

/* Glass Expander Styling */
div[data-testid="stExpander"] {
    background: rgba(22, 17, 43, 0.4) !important;
    backdrop-filter: blur(8px) !important;
    border: 1px solid rgba(111, 76, 255, 0.18) !important;
    border-radius: 14px !important;
    margin-bottom: 24px !important;
}

/* Headings with expansion animation */
@keyframes tracking-in-expand {
  0% {
    letter-spacing: -0.2em;
    opacity: 0;
  }
  40% {
    opacity: 0.6;
  }
  100% {
    opacity: 1;
  }
}

h1 {
    background: linear-gradient(90deg, #b89eff, #ffffff 60%, #a5f3fc) !important;
    -webkit-background-clip: text !important;
    -webkit-text-fill-color: transparent !important;
    font-weight: 800 !important;
    letter-spacing: -1.5px !important;
    text-align: center;
    animation: tracking-in-expand 1s cubic-bezier(0.215, 0.610, 0.355, 1.000) both !important;
}

h2, h3 {
    color: #cbbaff !important;
    font-weight: 600 !important;
}

/* Scrollbar customization */
::-webkit-scrollbar {
    width: 8px;
    height: 8px;
}
::-webkit-scrollbar-track {
    background: rgba(12, 8, 23, 0.5);
}
::-webkit-scrollbar-thumb {
    background: rgba(111, 76, 255, 0.3);
    border-radius: 4px;
}
::-webkit-scrollbar-thumb:hover {
    background: rgba(111, 76, 255, 0.5);
}
</style>
""", unsafe_allow_html=True)

# Helper function to parse LLM report
def parse_report(report_text):
    if not report_text:
        return None, "", "", ""
        
    score_match = re.search(r"(?:MATCH SCORE|Score|Alignment Score)[^\d]*(\d+)", report_text, re.IGNORECASE)
    score = int(score_match.group(1)) if score_match else None
    
    strengths_match = re.search(r"(?:STRENGTHS|Strengths|Alignment Points):\s*(.*?)(?=(?:GAPS|Gaps|Missing|ACTION PLAN|Action Plan|$))", report_text, re.DOTALL | re.IGNORECASE)
    strengths = strengths_match.group(1).strip() if strengths_match else ""
    
    gaps_match = re.search(r"(?:GAPS|Gaps|Weakness|Missing):\s*(.*?)(?=(?:ACTION PLAN|Action Plan|Strengths|$))", report_text, re.DOTALL | re.IGNORECASE)
    gaps = gaps_match.group(1).strip() if gaps_match else ""
    
    action_match = re.search(r"(?:ACTION PLAN|Action Plan|Bridge|Recommendations):\s*(.*?)(?=$)", report_text, re.DOTALL | re.IGNORECASE)
    action_plan = action_match.group(1).strip() if action_match else ""
    
    return score, strengths, gaps, action_plan

def render_as_html_list(text):
    if not text:
        return "<em>None specified</em>"
    lines = text.split("\n")
    html = "<ul style='margin: 0; padding-left: 20px; list-style-type: square;'>"
    has_items = False
    for line in lines:
        line = line.strip()
        if not line:
            continue
        # Remove list markers like - or * or numbers
        cleaned = re.sub(r"^[-*\s\d\.\)]+", "", line).strip()
        if cleaned:
            html += f"<li style='margin-bottom: 8px; color: #e0e0fc;'>{cleaned}</li>"
            has_items = True
    html += "</ul>"
    if not has_items:
        return text.replace("\n", "<br>")
    return html

# App Header
st.markdown("<h1>🤖 OmniMatch AI</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #a5a2e6; font-size: 18px; margin-top: -10px; margin-bottom: 30px;'>Universal Semantic Engine & Deep Gap Analyzer</p>", unsafe_allow_html=True)

# System Stats row (Overview Dashboard)
num_docs = len(engine.metadata)
stat_col1, stat_col2, stat_col3, stat_col4 = st.columns(4)

with stat_col1:
    st.markdown(f"""
    <div class="stat-card">
        <div class="stat-val" style="color: #10b981;">🟢 Active</div>
        <div class="stat-label">System Engine</div>
    </div>
    """, unsafe_allow_html=True)
with stat_col2:
    st.markdown(f"""
    <div class="stat-card">
        <div class="stat-val" style="color: #a855f7;">{num_docs}</div>
        <div class="stat-label">Indexed Files</div>
    </div>
    """, unsafe_allow_html=True)
with stat_col3:
    st.markdown(f"""
    <div class="stat-card">
        <div class="stat-val" style="color: #3b82f6;">MiniLM-L6</div>
        <div class="stat-label">Vector Embedder</div>
    </div>
    """, unsafe_allow_html=True)
with stat_col4:
    st.markdown(f"""
    <div class="stat-card">
        <div class="stat-val" style="color: #f59e0b;">Llama-3.3</div>
        <div class="stat-label">LLM Critic</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<div style='height: 25px;'></div>", unsafe_allow_html=True)

# Expander for Knowledge Base
num_docs = len(engine.metadata)
db_title = f"📁 Knowledge Base & Document Hub ({num_docs} Documents Indexed)"
with st.expander(db_title, expanded=(num_docs == 0)):
    # Grid: File upload on left, current list on right
    up_col, list_col = st.columns([1, 1])
    
    with up_col:
        st.markdown("<h4 style='margin-top:0; color: #a855f7;'>Upload New Documents</h4>", unsafe_allow_html=True)
        uploaded_files = st.file_uploader(
            "Drag and drop documents here (PDF, DOCX, TXT)",
            accept_multiple_files=True,
            type=["pdf", "docx", "txt"],
            label_visibility="collapsed"
        )
        
        if st.button("🚀 Process & Index"):
            if not uploaded_files:
                st.warning("Please select files to upload.")
            else:
                import tempfile
                success_count = 0
                for uploaded_file in uploaded_files:
                    suffix = os.path.splitext(uploaded_file.name)[1]
                    # Create temp file in system temp directory
                    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
                    temp_path = temp_file.name
                    
                    try:
                        temp_file.write(uploaded_file.getbuffer())
                        temp_file.close() # Close file handle so parser can open it on Windows
                        
                        with st.spinner(f"Indexing {uploaded_file.name}..."):
                            data = extract_structured_data(temp_path)
                            data_dict = data.model_dump()
                            engine.add_document(data_dict)
                            success_count += 1
                        st.success(f"Indexed: {data_dict['entity_name']}")
                    except Exception as e:
                        st.error(f"Error processing {uploaded_file.name}: {e}")
                    finally:
                        try:
                            if os.path.exists(temp_path):
                                os.remove(temp_path)
                        except Exception as cleanup_error:
                            print(f"Error cleaning up temp file: {cleanup_error}")
                if success_count > 0:
                    st.success(f"Successfully indexed {success_count} document(s)!")
                    st.rerun()

    with list_col:
        st.markdown("<h4 style='margin-top:0; color: #a855f7;'>Currently Indexed Documents</h4>", unsafe_allow_html=True)
        if num_docs == 0:
            st.info("No documents in database. Upload some documents to start.")
        else:
            # Custom styled list container
            st.markdown("<div style='max-height: 250px; overflow-y: auto; padding-right: 5px;'>", unsafe_allow_html=True)
            for doc in engine.metadata:
                d_col1, d_col2 = st.columns([5, 1])
                with d_col1:
                    st.markdown(f"""
                    <div style='background: rgba(255,255,255,0.05); padding: 8px 12px; border-radius: 8px; margin-bottom: 6px; border: 1px solid rgba(111,76,255,0.1);'>
                        <strong style='color: #cbbaff;'>{doc['entity_name']}</strong><br/>
                        <span style='font-size: 12px; color: #a5a2e6;'>Type: {doc.get('document_type', 'N/A')} | Level: {doc.get('experience_level', 'N/A')}</span>
                    </div>
                    """, unsafe_allow_html=True)
                with d_col2:
                    st.markdown("<div style='padding-top: 10px;'>", unsafe_allow_html=True)
                    if st.button("🗑️", key=f"del_{doc['entity_name']}", help="Remove from database"):
                        engine.remove_document(doc['entity_name'])
                        st.success(f"Removed {doc['entity_name']}!")
                        st.rerun()
                    st.markdown("</div>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

# Main Query Area
st.markdown("<h3 style='text-align: center; color: #ffffff;'>🎯 Run Semantic Alignment</h3>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #a5a2e6; margin-top: -10px; margin-bottom: 20px;'>Define the target requirements to match against your knowledge base</p>", unsafe_allow_html=True)

# Center columns for query box
q_col1, q_col2, q_col3 = st.columns([1, 6, 1])
with q_col2:
    # Set default target input or use empty
    target_input = st.text_area(
        label="Input requirements details",
        placeholder="E.g., We need a Senior Data Scientist with 5+ years of experience in Python, FAISS vector search, and Large Language Model deployments...",
        height=140,
        label_visibility="collapsed"
    )
    
    st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)
    
    # Matching Action
    run_match = st.button("✨ Run Semantic Alignment")

if run_match:
    if not target_input.strip():
        st.warning("Please enter some target requirements to search.")
    elif num_docs == 0:
        st.error("Your database is empty. Please upload some documents first!")
    else:
        # Save to session state to show results persist
        st.session_state.target_query = target_input
        
        with st.spinner("🔍 Querying Vector Map..."):
            results = engine.search(target_input, top_k=1)
            
        if results:
            best_match = results[0]
            st.session_state.best_match = best_match
            
            # Streaming the report
            report_container = st.empty()
            full_report = ""
            
            with st.spinner("🧠 Analyzing Gaps & Skill Transferability..."):
                try:
                    report_stream = analyzer.generate_report_stream(target_input, best_match)
                    for chunk in report_stream:
                        full_report += chunk
                        # Render streaming markdown inside a nice glowing container
                        report_container.markdown(f"""
                        <div class="glass-card">
                            <h3 style='color: #a855f7; margin-top: 0;'>📝 Generating Gap Analysis Report...</h3>
                            <div style='color: #e0e0fc;'>
                                {full_report}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                except Exception as e:
                    # Fallback if stream fails
                    full_report = analyzer.generate_report(target_input, best_match)
                    
            st.session_state.report = full_report
            st.rerun()
        else:
            st.error("No matches found in the vector database.")

# Display results if present in session state
if "best_match" in st.session_state and st.session_state.best_match and "report" in st.session_state and st.session_state.report:
    best_match = st.session_state.best_match
    report_text = st.session_state.report
    
    st.markdown("---")
    st.markdown("<h2 style='text-align: center; color: #a855f7; margin-bottom: 25px;'>📊 Alignment & Gap Report Dashboard</h2>", unsafe_allow_html=True)
    
    # 1. Best Match Overview Card
    st.markdown(f"""
    <div class="glass-card" style="border-top: 3px solid #a855f7 !important;">
        <h3 style="margin-top: 0; color: #a855f7; font-size: 22px;">🎯 Top Aligned Entity: {best_match['entity_name']}</h3>
        <div style="display: flex; gap: 30px; margin-bottom: 12px; flex-wrap: wrap;">
            <div><strong style="color:#cbbaff;">Type:</strong> {best_match.get('document_type', 'N/A')}</div>
            <div><strong style="color:#cbbaff;">Experience Level:</strong> {best_match.get('experience_level', 'N/A')}</div>
        </div>
        <p style="margin-bottom: 12px; line-height: 1.6; color: #e0e0fc;"><strong style="color:#cbbaff;">Executive Summary:</strong> {best_match.get('summary', 'No summary available.')}</p>
        <div>
            <strong style="color:#cbbaff;">Key Identified Attributes:</strong><br/>
            {" ".join([f"<span style='display:inline-block; background:rgba(111,76,255,0.15); border: 1px solid rgba(111,76,255,0.3); border-radius:12px; padding:3px 10px; margin:4px 4px 4px 0; font-size:13px; color:#e0e0fc;'>{feat}</span>" for feat in best_match.get('key_features', [])])}
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Parse report to render structured components
    score, strengths, gaps, action_plan = parse_report(report_text)
    
    # If parsing failed or sections empty, render raw markdown report in a glass card
    if not (strengths or gaps or action_plan):
        st.markdown(f"""
        <div class="glass-card">
            <h3 style="color: #a855f7; margin-top: 0;">📋 Detailed Gap Analysis</h3>
            <div style="color: #e0e0fc; line-height: 1.6;">
                {report_text}
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        # Match Score metric
        if score is not None:
            # Color based on score range
            score_color = "#10b981" if score >= 80 else ("#f59e0b" if score >= 50 else "#ef4444")
            st.markdown(f"""
            <div style="text-align: center; margin-bottom: 30px; background: rgba(22,17,43,0.5); padding: 15px; border-radius: 16px; border: 1px solid rgba(111,76,255,0.15); display: inline-block; width: 100%;">
                <span style="font-size: 18px; color: #a5a2e6; text-transform: uppercase; letter-spacing: 1.5px;">Match Alignment Score</span>
                <div style="font-size: 72px; font-weight: 800; color: {score_color}; text-shadow: 0 0 20px {score_color}44; margin: 5px 0;">
                    {score}%
                </div>
            </div>
            """, unsafe_allow_html=True)
            
        # Display Strengths and Gaps in columns
        s_col, g_col = st.columns(2)
        
        with s_col:
            st.markdown(f"""
            <div class="glass-card" style="border-left: 5px solid #10b981 !important; height: 100%;">
                <h4 style="color: #10b981; margin-top:0; font-size:18px; display: flex; align-items: center; gap: 8px;">
                    🟢 Strengths & Alignment
                </h4>
                <div style="margin-top: 12px;">
                    {render_as_html_list(strengths)}
                </div>
            </div>
            """, unsafe_allow_html=True)
            
        with g_col:
            st.markdown(f"""
            <div class="glass-card" style="border-left: 5px solid #f59e0b !important; height: 100%;">
                <h4 style="color: #f59e0b; margin-top:0; font-size:18px; display: flex; align-items: center; gap: 8px;">
                    🟡 Identified Gaps
                </h4>
                <div style="margin-top: 12px;">
                    {render_as_html_list(gaps)}
                </div>
            </div>
            """, unsafe_allow_html=True)
            
        # Display Action Plan
        st.markdown(f"""
        <div class="glass-card" style="border-left: 5px solid #3b82f6 !important;">
            <h4 style="color: #3b82f6; margin-top:0; font-size:18px; display: flex; align-items: center; gap: 8px;">
                🔵 Recommendation & Action Plan
            </h4>
            <div style="margin-top: 12px;">
                {render_as_html_list(action_plan)}
            </div>
        </div>
        """, unsafe_allow_html=True)
        
    # Option to reset/clear dashboard
    if st.button("🗑️ Clear Analysis Report"):
        st.session_state.best_match = None
        st.session_state.report = None
        st.rerun()