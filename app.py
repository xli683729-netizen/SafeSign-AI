import streamlit as st
import openai
from PIL import Image
import pdfplumber
import easyocr
import numpy as np
from fpdf import FPDF

# --- 1. 基础配置 ---
st.set_page_config(page_title="SafeSign AI Pro", layout="wide", page_icon="🛡️")

# --- 2. 连接 DeepSeek 大脑 ---
client = openai.OpenAI(
    api_key=st.secrets["DEEPSEEK_API_KEY"], 
    base_url="https://api.deepseek.com"
)

# --- 3. 侧边栏 ---
with st.sidebar:
    st.title("🛡️ SafeSign AI")
    st.subheader("Global Compliance Suite")
    mode = st.selectbox("Audit Protocol", ["General Commercial", "Influencer/Model", "Employment"])
    st.divider()
    st.info("Status: Pro Version Active")
    st.caption("© 2026 SafeSign AI. v6.5")

# --- 4. 辅助功能：生成 PDF ---
def create_pdf(text):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    # 处理编码问题，确保特殊字符不报错
    clean_text = text.encode('latin-1', 'ignore').decode('latin-1')
    pdf.multi_cell(0, 10, txt=clean_text)
    return pdf.output(dest='S').encode('latin-1')

# --- 5. 主界面 ---
st.title("🛡️ AI Contract Audit & Generator")
st.markdown("---")

uploaded_file = st.file_uploader("Upload Document (PDF or Camera Scan)", type=['png', 'jpg', 'jpeg', 'pdf'])

if 'contract_text' not in st.session_state: st.session_state['contract_text'] = ""
if 'revised_contract' not in st.session_state: st.session_state['revised_contract'] = ""

if st.button("🚀 Run AI Risk Audit"):
    if uploaded_file:
        with st.spinner("Decoding & Analyzing..."):
            try:
                # OCR 识别逻辑
                if uploaded_file.type in ["image/png", "image/jpeg", "image/jpg"]:
                    image = Image.open(uploaded_file)
                    reader = easyocr.Reader(['en'])
                    results = reader.readtext(np.array(image))
                    text_content = " ".join([res[1] for res in results])
                else:
                    with pdfplumber.open(uploaded_file) as pdf:
                        text_content = "\n".join([page.extract_text() for page in pdf.pages if page.extract_text()])
                
                st.session_state['contract_text'] = text_content

                # 让 AI 给出风险分析 + 一个修正后的版本
                prompt = f"Audit this {mode} contract. 1. List Risk Score and Red Flags. 2. Provide a 'REVISED FULL CONTRACT' that is fair and legal. Text: {text_content}"
                
                response = client.chat.completions.create(
                    model="deepseek-chat",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.2
                )
                
                full_res = response.choices[0].message.content
                st.session_state['revised_contract'] = full_res # 暂存修正后的合同
                
                st.success("✅ Audit Complete")
                st.markdown(full_res)
                
                # --- 新增：PDF 导出按钮 ---
                pdf_data = create_pdf(full_res)
                st.download_button(
                    label="📥 Download Revised Contract (PDF)",
                    data=pdf_data,
                    file_name="SafeSign_Revised_Contract.pdf",
                    mime="application/pdf"
                )
                
            except Exception as e:
                st.error(f"System Error: {str(e)}")
    else:
        st.warning("Please upload a file first!")

# --- 6. 底部 AI 战略咨询 ---
st.markdown("---")
st.subheader("💬 AI Strategic Consultation")
user_query = st.text_input("Ask a follow-up question:")
if user_query and st.session_state['contract_text']:
    res = client.chat.completions.create(
        model="deepseek-chat",
        messages=[{"role": "user", "content": f"Context: {st.session_state['contract_text']}\nQuestion: {user_query}"}]
    )
    st.chat_message("assistant").write(res.choices[0].message.content)
