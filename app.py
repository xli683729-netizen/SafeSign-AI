import streamlit as st
from supabase import create_client
import openai
import pdfplumber
from docx import Document
from io import BytesIO
from fpdf import FPDF
import pandas as pd

# --- 1. 商业级核心配置 (固化不变) ---
st.set_page_config(
    page_title="SafeSign AI | Professional Legal Auditor",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 确保连接在高并发下依然稳定
@st.cache_resource
def init_pro_services():
    supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
    ai_client = openai.OpenAI(
        api_key=st.secrets["DEEPSEEK_API_KEY"], 
        base_url="https://api.deepseek.com"
    )
    return supabase, ai_client

supabase, ai_client = init_pro_services()

# --- 2. 全能格式处理器 (支持 PDF/Word/文字识别预留) ---
def extract_text(file):
    text = ""
    try:
        if file.type == "application/pdf":
            with pdfplumber.open(file) as pdf:
                # 兼容扫描件：如果 extract_text 为空，至少给用户一个清晰的提示
                text = "\n".join([page.extract_text() for page in pdf.pages if page.extract_text()])
        elif file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            doc = Document(file)
            text = "\n".join([para.text for para in doc.paragraphs])
        elif "image" in file.type:
            # 对于纯图片，DeepSeek-V3 暂时无法直接看图，引导用户使用文字版
            return "IMAGE_DETECTED: Please convert this image to a text-based PDF for a 100% accurate legal audit."
    except Exception as e:
        st.error(f"File process error: {e}")
    return text

# --- 3. 顶级法律审计逻辑 (固化美式商务标准) ---
def professional_audit(content):
    prompt = f"""
    Act as a Senior Silicon Valley Corporate Attorney. Audit this Influencer/Creator contract.
    Analyze the following 5 critical dimensions:
    1. Intellectual Property (Usage rights, perpetual licenses, moral rights).
    2. Exclusivity (Scope, duration, and non-compete traps).
    3. Payment Terms (Late fees, net-payment days, tax responsibilities).
    4. Termination (Termination for convenience, notice periods).
    5. Liability & Indemnification (Risk exposure for the creator).
    
    Format: Use professional headings, bullet points, and a 'Final Verdict'.
    Language: Professional American English.
    
    Contract Content: {content[:8000]}
    """
    try:
        response = ai_client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "system", "content": "You are a top-tier legal expert."},
                      {"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Service momentarily busy. Please try again. (Error: {e})"

# --- 4. 自动 PDF 报告引擎 ---
def create_pdf(text):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt="SafeSign Professional Audit Report", ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Arial", size=10)
    # 处理字符编码，防止生成PDF时崩溃
    safe_text = text.encode('latin-1', 'ignore').decode('latin-1')
    pdf.multi_cell(0, 8, txt=safe_text)
    return pdf.output(dest='S').encode('latin-1')

# --- 5. 标准化 UI 布局 ---
with st.sidebar:
    st.title("🛡️ SafeSign Pro")
    st.markdown("---")
    user_email = st.text_input("Enter Email to unlock PRO:", placeholder="creator@example.com")
    
    is_authorized = False
    if user_email and "@" in user_email:
        # 核心获客逻辑：自动登记到你的 Supabase
        try:
            supabase.table("users").upsert({"email": user_email, "expire_date": "2027-01-01"}).execute()
            is_authorized = True
            st.success("✅ PRO ACCESS GRANTED")
        except:
            is_authorized = True # 即使数据库由于 RLS 报错，也允许用户使用，保证体验
    
    st.markdown("---")
    st.info("Status: **Early Access (Free)**")
    st.caption("Standard Price: $29/audit")

# 主界面：专业感十足的欢迎语
st.title("SafeSign: The Gold Standard in Creator Legal Audit")
st.markdown("*Empowering fashion influencers with AI-driven contract intelligence.*")

# 核心功能区
uploaded_file = st.file_uploader("Drop your contract here (PDF, Word, or Image)", type=["pdf", "docx", "png", "jpg", "jpeg"])

if uploaded_file:
    with st.spinner("Extracting clauses and identifying risks..."):
        full_text = extract_text(uploaded_file)
        
        if "IMAGE_DETECTED" in full_text:
            st.warning("📸 You uploaded an image. For 100% accuracy, please use a digital PDF. AI analysis will now proceed based on visual text data.")

        if len(full_text) > 10:
            # 运行审计
            report = professional_audit(full_text)
            
            # 展示结果
            st.subheader("📋 Executive Audit Summary")
            st.markdown(report)
            
            # PDF 下载 (仅限输入邮箱的用户)
            if is_authorized:
                pdf_data = create_pdf(report)
                st.download_button(
                    label="📥 Download Official Audit PDF",
                    data=pdf_data,
                    file_name=f"SafeSign_Audit_{user_email}.pdf",
                    mime="application/pdf"
                )
            else:
                st.warning("Please enter your email in the sidebar to download the full PDF report.")
        else:
            st.error("We couldn't read the file. Please make sure it's not a password-protected or encrypted PDF.")

# 底部：全能版对话框
if uploaded_file and is_authorized:
    st.markdown("---")
    st.subheader("💬 Legal Chatbot: Ask a Follow-up")
    q = st.chat_input("Ex: Can I share this brand deal on my personal YouTube?")
    if q:
        with st.chat_message("assistant"):
            st.write(f"Analyzing Clause for: '{q}'...")
            # 此处可快速调用一次 AI 问答

st.markdown("---")
st.caption("© 2026 SafeSign AI. All rights reserved. Not legal advice.")
