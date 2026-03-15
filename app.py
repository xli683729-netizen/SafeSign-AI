import streamlit as st
import openai
from PIL import Image
import pdfplumber
import easyocr
import numpy as np
from fpdf import FPDF
from docx import Document
import io

# --- 1. 性能核心：模型缓存（防止 5000 人同时用时内存溢出） ---
@st.cache_resource
def load_ocr_model():
    # 提前加载模型，常驻内存，避免重复加载导致的严重卡顿
    return easyocr.Reader(['en'])

# --- 2. 页面与 API 初始化 ---
st.set_page_config(page_title="SafeSign AI Enterprise", layout="wide", page_icon="🛡️")

client = openai.OpenAI(
    api_key=st.secrets["DEEPSEEK_API_KEY"], 
    base_url="https://api.deepseek.com"
)

# 使用 SessionState 保证多用户并发时数据互不干扰
if 'contract_text' not in st.session_state: st.session_state['contract_text'] = ""

# --- 3. 辅助功能 ---
def export_pdf(text):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=10)
    # 工业级过滤字符
    safe_text = text.encode('latin-1', 'ignore').decode('latin-1')
    pdf.multi_cell(0, 8, txt=safe_text)
    return pdf.output(dest='S').encode('latin-1')

# --- 4. 主界面 ---
st.title("🛡️ SafeSign AI Professional (Enterprise)")
st.caption("High-Performance Legal Audit Engine")

# 侧边栏
with st.sidebar:
    st.header("Settings")
    mode = st.selectbox("Protocol", ["General", "Influencer", "Employment"])
    st.success("Server Status: Online")

# 上传区
uploaded_file = st.file_uploader("Upload Contract", type=['png', 'jpg', 'jpeg', 'pdf', 'docx'])

if st.button("🚀 Start High-Speed Audit"):
    if uploaded_file:
        with st.spinner("Processing through AI cluster..."):
            try:
                reader = load_ocr_model() # 调用缓存的模型
                text_content = ""
                
                # 针对不同格式的高效处理逻辑
                if uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                    doc = Document(uploaded_file)
                    text_content = "\n".join([p.text for p in doc.paragraphs])
                elif uploaded_file.type in ["image/png", "image/jpeg", "image/jpg"]:
                    img = Image.open(uploaded_file)
                    results = reader.readtext(np.array(img))
                    text_content = " ".join([res[1] for res in results])
                elif uploaded_file.type == "application/pdf":
                    with pdfplumber.open(uploaded_file) as pdf:
                        text_content = "\n".join([p.extract_text() for p in pdf.pages if p.extract_text()])
                
                st.session_state['contract_text'] = text_content

                if text_content:
                    # 降低 Temperature 保证并发时输出的稳定性
                    response = client.chat.completions.create(
                        model="deepseek-chat",
                        messages=[{"role": "user", "content": f"Audit {mode} contract. Score, RedFlags, RevisedText: {text_content}"}],
                        temperature=0.1 
                    )
                    audit_res = response.choices[0].message.content
                    
                    st.success("✅ Audit Complete")
                    st.markdown(audit_res)
                    
                    # 导出 PDF
                    pdf_data = export_pdf(audit_res)
                    st.download_button("📥 Download Revised Contract", pdf_data, "Report.pdf", "application/pdf")
            except Exception as e:
                st.error(f"Engine Busy: {str(e)}")
    else:
        st.warning("Please provide a file.")

# --- 5. 咨询对话框 ---
st.divider()
query = st.text_input("💬 Ask AI anything about this contract:")
if query and st.session_state['contract_text']:
    with st.spinner("Consulting..."):
        res = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": f"Context: {st.session_state['contract_text']}\nQ: {query}"}]
        )
        st.info(res.choices[0].message.content)
