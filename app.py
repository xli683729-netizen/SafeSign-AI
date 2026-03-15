import streamlit as st
from supabase import create_client
import openai
import pdfplumber
from docx import Document
from io import BytesIO
from fpdf import FPDF

# --- 1. 商业化配置 (修正报错) ---
st.set_page_config(
    page_title="SafeSign Pro | Global Contract Auditor",
    page_icon="⚖️",
    layout="wide"
)

# 修复后的样式注入
st.markdown("""
    <style>
    .report-box { 
        padding: 20px; 
        border-radius: 10px; 
        border: 1px solid #dee2e6; 
        background-color: #ffffff;
        color: #1A1C23;
    }
    </style>
    """, unsafe_allow_html=True) # 这里修正了之前的参数错误

@st.cache_resource
def init_engine():
    supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
    ai_client = openai.OpenAI(
        api_key=st.secrets["DEEPSEEK_API_KEY"], 
        base_url="https://api.deepseek.com"
    )
    return supabase, ai_client

supabase, ai_client = init_engine()

# --- 2. 格式解析 ---
def extract_text(file):
    try:
        if file.type == "application/pdf":
            with pdfplumber.open(file) as pdf:
                return "\n".join([page.extract_text() for page in pdf.pages if page.extract_text()])
        elif file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            doc = Document(file)
            return "\n".join([p.text for p in doc.paragraphs])
        return ""
    except:
        return ""

# --- 3. AI 逻辑：审计报告 + 留白范本 ---
def run_legal_engine(content):
    # 逻辑 1：严谨审计
    audit_p = f"Professional legal audit of this contract. Identify risks and missing clauses: {content[:5000]}"
    # 逻辑 2：生成留白范本 (名字、日期、金额全部空出来)
    template_p = f"Draft a professional standard template based on this contract. Leave variables like [NAME], [DATE], [COMPENSATION] blank for user input: {content[:3000]}"
    
    try:
        audit_res = ai_client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": audit_p}]
        ).choices[0].message.content

        template_res = ai_client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": template_p}]
        ).choices[0].message.content
        return audit_res, template_res
    except Exception as e:
        return f"AI Error: {e}", ""

# --- 4. 界面布局 ---
with st.sidebar:
    st.title("🛡️ SafeSign Pro")
    st.caption("Professional Grade Auditor")
    email = st.text_input("Client Identification (Email):")
    if email:
        try:
            supabase.table("users").upsert({"email": email, "expire_date": "2030-01-01"}).execute()
            st.success("AUTHENTICATED")
        except:
            st.warning("Database sync offline, but Pro features enabled.")

st.title("⚖️ SafeSign Pro: Enterprise Legal Intelligence")
st.markdown("##### Strategic Audit & Standardized Template Generation")

uploaded_file = st.file_uploader("Upload Agreement (PDF or Word)", type=["pdf", "docx"])

if uploaded_file:
    with st.spinner("Executing legal analysis..."):
        raw_text = extract_text(uploaded_file)
        if len(raw_text) > 20:
            report, template = run_legal_engine(raw_text)
            
            # 双栏展示
            c1, c2 = st.columns(2)
            with c1:
                st.subheader("🚩 Risk Audit Report")
                st.markdown(f"<div class='report-box'>{report}</div>", unsafe_allow_html=True)
            with c2:
                st.subheader("📄 Standard Template (Variables Blank)")
                st.markdown(f"<div class='report-box'>{template}</div>", unsafe_allow_html=True)
                
            st.markdown("---")
            if email:
                st.download_button("📥 Export Full Documentation", data=f"AUDIT:\n{report}\n\nTEMPLATE:\n{template}", file_name="SafeSign_Pro_Pack.txt")
        else:
            st.error("Document is unreadable. Please upload a digital text-based file.")

st.markdown("---")
st.caption("© 2026 SafeSign Intelligence. Confidential & Professional.")
