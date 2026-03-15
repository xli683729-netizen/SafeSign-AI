import streamlit as st
import openai
from PIL import Image
import pdfplumber
import easyocr
import numpy as np
from fpdf import FPDF
from docx import Document
import io

# 1. 基础配置
st.set_page_config(page_title="SafeSign AI Pro", layout="wide", page_icon="🛡️")

client = openai.OpenAI(
    api_key=st.secrets["DEEPSEEK_API_KEY"], 
    base_url="https://api.deepseek.com"
)

# 状态管理
if 'contract_text' not in st.session_state: st.session_state['contract_text'] = ""
if 'audit_results' not in st.session_state: st.session_state['audit_results'] = ""

# 2. 侧边栏
with st.sidebar:
    st.title("🛡️ SafeSign AI")
    mode = st.selectbox("Audit Protocol", ["General Commercial", "Influencer/Model", "Employment"])
    st.info("V7.0 All-In-One Pro")

# 3. 辅助功能：生成 PDF 导出
def export_pdf(text):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=10)
    safe_text = text.encode('latin-1', 'ignore').decode('latin-1')
    pdf.multi_cell(0, 8, txt=safe_text)
    return pdf.output(dest='S').encode('latin-1')

# 4. 主界面
st.title("🛡️ AI Professional Contract Suite")
st.markdown("---")

# 支持多种格式上传
uploaded_file = st.file_uploader("Upload Contract (Word, PDF, or Photo)", type=['png', 'jpg', 'jpeg', 'pdf', 'docx'])

if st.button("🚀 Run Full Audit"):
    if uploaded_file:
        with st.spinner("AI is analyzing your contract..."):
            try:
                text_content = ""
                # 情况 A：Word 文档
                if uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                    doc = Document(uploaded_file)
                    text_content = "\n".join([para.text for para in doc.paragraphs])
                
                # 情况 B：图片/拍照
                elif uploaded_file.type in ["image/png", "image/jpeg", "image/jpg"]:
                    img = Image.open(uploaded_file)
                    reader = easyocr.Reader(['en'])
                    results = reader.readtext(np.array(img))
                    text_content = " ".join([res[1] for res in results])
                
                # 情况 C：PDF
                elif uploaded_file.type == "application/pdf":
                    with pdfplumber.open(uploaded_file) as pdf:
                        text_content = "\n".join([p.extract_text() for p in pdf.pages if p.extract_text()])
                
                st.session_state['contract_text'] = text_content

                if text_content:
                    prompt = f"Audit this {mode} contract. 1. Risk Score. 2. Red Flags. 3. REVISED FULL CONTRACT. Text: {text_content}"
                    response = client.chat.completions.create(
                        model="deepseek-chat",
                        messages=[{"role": "user", "content": prompt}],
                        temperature=0.2
                    )
                    st.session_state['audit_results'] = response.choices[0].message.content
                    st.success("✅ Audit Complete!")
                    st.markdown(st.session_state['audit_results'])
                    
                    # 导出 PDF 按钮
                    pdf_data = export_pdf(st.session_state['audit_results'])
                    st.download_button("📥 Download Revised Contract (PDF)", pdf_data, "Revised_Contract.pdf", "application/pdf")
            except Exception as e:
                st.error(f"Error: {e}")
    else:
        st.warning("Please upload a document first.")

# 5. 底部对话框
st.markdown("---")
st.subheader("💬 AI Strategic Consultation")
query = st.text_input("Ask a follow-up question:")
if query and st.session_state['contract_text']:
    res = client.chat.completions.create(
        model="deepseek-chat",
        messages=[{"role": "user", "content": f"Context: {st.session_state['contract_text']}\nQuestion: {query}"}]
    )
    st.info(res.choices[0].message.content)
