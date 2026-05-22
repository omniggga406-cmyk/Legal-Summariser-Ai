import os
import sys

# Crucial Windows/OneDrive Path Fix: Force Python to register the project directory
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.append(CURRENT_DIR)

import streamlit as st
from src.parser import parse_legal_document_generator
from src.agents import process_unified_legal_analysis

if sys.platform.startswith("win"):
    sys.stdout.reconfigure(encoding='utf-8')

st.set_page_config(page_title="NyayaSummary AI", page_icon="⚖️", layout="wide")

st.markdown("""
    <style>
    .main-title { font-size:42px !important; font-weight: 700; color: #1E3A8A; text-align: center; margin-bottom: 5px; }
    .subtitle { font-size:18px !important; text-align: center; color: #555555; margin-bottom: 30px; }
    .stat-card { background-color: #F3F4F6 !important; padding: 20px; border-radius: 10px; border-left: 5px solid #1E3A8A; margin-bottom: 15px; }
    .stat-card h4 { color: #1E3A8A !important; margin: 0 !important; font-weight: 600 !important; }
    .stat-card p { color: #1F2937 !important; font-weight: bold !important; margin: 5px 0 0 0 !important; }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-title">⚖️ NyayaSummary AI</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Multi-Agent Legal Summarization Engine for Indian Jurisprudence</div>', unsafe_allow_html=True)

st.sidebar.header("📁 Document Workspace")
uploaded_file = st.sidebar.file_uploader("Upload Indian Legal PDF", type=["pdf"])

if uploaded_file is not None:
    temp_path = os.path.join(".", "temp_process.pdf")
    file_bytes = uploaded_file.getvalue()
    
    with open(temp_path, "wb") as f:
        f.write(file_bytes)
        
    st.sidebar.success("Document Ingested Successfully!")
    
    if st.sidebar.button("⚡ Run AI Analysis", use_container_width=True):
        try:
            progress_msg = st.empty()
            progress_bar = st.empty()
            parsed_text = ""
            
            progress_msg.info("⏳ Parsing document layout structures...")
            progress_bar.progress(0.0)
            
            for progress, text_data in parse_legal_document_generator(temp_path):
                progress_bar.progress(progress)
                if text_data is not None:
                    parsed_text = text_data
            
            progress_msg.empty()
            progress_bar.empty()
            
            if not parsed_text.strip():
                st.error("❌ The uploaded document appears to contain empty text layers. Please check your file.")
                st.stop()
            
            with st.spinner("Processing architectural legal parameter extraction..."):
                # CACHE REMOVED: Directly forces a fresh API run with your new key every single time
                state = {
                    "raw_text": parsed_text, "doc_type": "", "indian_statutes": [], "final_summary": ""
                }
                output = process_unified_legal_analysis(state)

            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f'<div class="stat-card"><h4>Detected Document Profile</h4><p style="font-size:22px;">{output["doc_type"]}</p></div>', unsafe_allow_html=True)
            with col2:
                laws_list = ", ".join(output['indian_statutes']) if output['indian_statutes'] else "General Indian Law"
                st.markdown(f'<div class="stat-card"><h4>Laws & Statutes Used</h4><p style="font-size:16px;">{laws_list}</p></div>', unsafe_allow_html=True)
            
            st.markdown("---")
            
            st.markdown("### 📊 Expert Analytical Briefing Note")
            st.markdown(output["final_summary"])
            
            if os.path.exists(temp_path):
                os.remove(temp_path)
                    
        except Exception as e:
            st.error(f"System execution bottleneck encountered: {str(e)}")
else:
    st.info("👈 Please drop an Indian court case record, contract document, judgment, or FIR PDF file into the upload zone to start analysis.")
