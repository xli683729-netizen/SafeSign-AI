import streamlit as st
import openai
from PIL import Image
import pdfplumber
import easyocr
import numpy as np
from fpdf import FPDF
import io

# 1. 基础配置
st.set_page_config(page_title="SafeSign AI Pro", layout="wide", page_icon="🛡️")

# 2. 连接 DeepSeek 大脑
client = openai.OpenAI(
    api_key=st.secrets["DEEPSEEK_API_KEY"], 
    base_url="https://api.deepseek.com"
)

# 状态管理：确保对话框能记住合同
if 'contract_text' not in st.session_state: st.session_state['contract_text'] = ""
if 'audit_results' not in st.session_state: st.session_state['audit_results'] = ""

# 3. 侧边栏：专业模式切换
with st.sidebar:
    st.title("🛡️ SafeSign AI")
    st.subheader("Global Compliance")
    mode = st.selectbox("Audit Protocol", ["General Commercial", "Influencer/Model", "Employment"])
    st.divider()
    st.info("V6.8 Enterprise Active")

# 4. 辅助功能：生成 PDF
def export_pdf(text):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=10)
    # 过滤掉 PDF 不支持的特殊字符
    safe_text = text.encode('latin-1', 'ignore').decode('latin-1')
    pdf.multi_cell(0, 8, txt=safe_text)
    return pdf.output(dest='S').encode('latin-1')

# 5. 主界面
st.title("🛡️ AI Professional Contract Suite")
st.markdown("---")

# 功能 1：文件上传/拍照识别
uploaded_file = st.file_uploader("Upload PDF or Take a Photo", type=['png', 'jpg', 'jpeg', 'pdf'])

if st.button("🚀 Run Full Audit"):
    if uploaded_file:
        with st.spinner("AI is scanning and auditing..."):
            try:
                # OCR 逻辑（保留拍照功能）
                if uploaded_file.type in ["image/png", "image/jpeg", "image/jpg"]:
                    img = Image.open(uploaded_file)
                    reader = easyocr.Reader(['en'])
                    results = reader.readtext(np.array(img))
                    st.session_state['contract_text'] = " ".join([res[1] for res in results])
                else:
                    with pdfplumber.open(uploaded_file) as pdf:
                        st.session_state['contract_text'] = "\n".join([p.extract_text() for p in pdf.pages if p.extract_text()])
                
                if st.session_state['contract_text']:
                    # AI 核心分析
                    prompt = f"Audit this {mode} contract. Provide: 1. Risk Score. 2. Red Flags. 3. A REVISED FULL CONTRACT. Text: {st.session_state['contract_text']}"
                    response = client.chat.completions.create(
                        model="deepseek-chat",
                        messages=[{"role": "user", "content": prompt}],
                        temperature=0.2
                    )
                    st.session_state['audit_results'] = response.choices[0].message.content
                    st.success("✅ Audit Complete!")
                    st.markdown(st.session_state['audit_results'])
                    
                    # 功能 2：一键导出 PDF
                    pdf_data = export_pdf(st.session_state['audit_results'])
                    st.download_button(
                        label="📥 Download Revised Contract (PDF)",
                        data=pdf_data,
                        file_name="SafeSign_Audit_Report.pdf",
                        mime="application/pdf"
                    )
            except Exception as e:
                st.error(f"Error: {e}")
    else:
        st.warning("Please upload a document first.")

# 功能 3：底部 AI 咨询对话框
st.markdown("---")
st.subheader("💬 AI Strategic Consultation")
query = st.text_input("Ask a follow-up question (e.g., 'What is missing here?'):")

if query:
    if st.session_state['contract_text']:
        with st.spinner("Consulting AI..."):
            res = client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": f"Contract: {st.session_state['contract_text']}\nQuestion: {query}"}]
            )
            st.chat_message("assistant").write(res.choices[0].message.content)
    else:
        st.info("Please run the audit first to give AI context.")
