import streamlit as st
from supabase import create_client
import openai
import pdfplumber
from docx import Document
from io import BytesIO
from fpdf import FPDF

# --- 1. 商业化视觉与核心配置 ---
st.set_page_config(
    page_title="SafeSign Pro | Enterprise Legal Auditor",
    page_icon="⚖️",
    layout="wide"
)

# 强制统一 UI 风格：深邃、专业
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; background-color: #1A1C23; color: white; }
    .report-box { padding: 20px; border-radius: 10px; border: 1px solid #dee2e6; background-color: white; }
    </style>
    """, unsafe_content_type=True)

@st.cache_resource
def init_engine():
    supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
    ai_client = openai.OpenAI(
        api_key=st.secrets["DEEPSEEK_API_KEY"], 
        base_url="https://api.deepseek.com"
    )
    return supabase, ai_client

supabase, ai_client = init_engine()

# --- 2. 全格式解析引擎 ---
def extract_text(file):
    try:
        if file.type == "application/pdf":
            with pdfplumber.open(file) as pdf:
                return "\n".join([page.extract_text() for page in pdf.pages if page.extract_text()])
        elif file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            return "\n".join([p.text for p in Document(file).paragraphs])
        else:
            return "SUPPORTED_FORMAT_REQUIRED"
    except:
        return ""

# --- 3. 核心功能：双重逻辑生成 (审计 + 范本) ---
def get_ai_legal_services(content):
    # 任务 1：深度审计
    audit_prompt = f"As a corporate lawyer, perform a rigorous risk audit on this contract. Highlight high-risk clauses, missing protections, and unfavorable terms. Contract: {content[:6000]}"
    
    # 任务 2：生成标准范本（变量留白）
    template_prompt = f"Based on the intent of the following text, draft a Professional Standard Agreement Template. IMPORTANT: Leave variables like [PARTY NAME], [EFFECTIVE DATE], [COMPENSATION AMOUNT], and [GOVERNING STATE] blank for the user to fill. Use structured legal formatting. Source: {content[:4000]}"
    
    try:
        # 并行或串行调用 AI
        audit_res = ai_client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": audit_prompt}]
        ).choices[0].message.content

        template_res = ai_client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": template_prompt}]
        ).choices[0].message.content
        
        return audit_res, template_res
    except Exception as e:
        return f"Error: {e}", ""

# --- 4. 界面与流程设计 ---
with st.sidebar:
    st.image("https://img.icons8.com/ios-filled/100/000000/law.png", width=80)
    st.title("SafeSign Pro")
    st.caption("Enterprise-Grade Contract Intelligence")
    st.markdown("---")
    email = st.text_input("Client ID / Email:", placeholder="Enter for PRO access")
    if email:
        supabase.table("users").upsert({"email": email, "expire_date": "2030-01-01"}).execute()
        st.success("AUTHENTICATED")

st.title("⚖️ Contract Audit & Template Generation")
st.markdown("### Professional analysis for any commercial agreement.")

uploaded_file = st.file_uploader("Upload Document (PDF, DOCX)", type=["pdf", "docx"])

if uploaded_file:
    with st.spinner("Analyzing legal structure..."):
        text_content = extract_text(uploaded_file)
        
        if len(text_content) > 10:
            audit_report, legal_template = get_ai_legal_services(text_content)
            
            # 布局：左边审计报告，右边范本建议
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("🚩 Risk Audit Report")
                st.markdown(f"<div class='report-box'>{audit_report}</div>", unsafe_content_type=True)
                
            with col2:
                st.subheader("📄 Standardized Template")
                st.info("Variables are left as [BLANK] for your customization.")
                st.markdown(f"<div class='report-box'>{legal_template}</div>", unsafe_content_type=True)

            st.markdown("---")
            
            # 一键导出功能
            if email:
                # 这里可以扩展为两个下载按钮，一个下报告，一个下范本
                st.download_button("📥 Export Comprehensive PDF Bundle", data=audit_report + "\n\n" + legal_template, file_name="SafeSign_Pro_Full_Package.txt")
        else:
            st.error("Text detection failed. Please upload a clear digital document.")

st.markdown("---")
st.caption("© 2026 SafeSign Intelligence. Strictly Confidential.")
