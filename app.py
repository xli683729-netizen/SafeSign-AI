import streamlit as st
import openai
import pdfplumber
from docx import Document
from fpdf import FPDF

# 1. 强制初始化（防止并发卡顿）
st.set_page_config(page_title="SafeSign AI Pro", layout="wide")

# 2. 这里的 Key 必须和 Secrets 里一模一样
try:
    api_key = st.secrets["DEEPSEEK_API_KEY"]
    client = openai.OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
except Exception as e:
    st.error("🔑 API Key Missing! Please check Secrets.")
    st.stop()

# 3. 极简 UI 布局
st.title("🛡️ SafeSign AI Professional")
st.info("Commercial Grade - High Speed Active")

# 上传区
up_file = st.file_uploader("Upload Contract (PDF or Word)", type=['pdf', 'docx'])

if st.button("🚀 Run Full Audit", use_container_width=True):
    if up_file:
        with st.spinner("AI is analyzing..."):
            try:
                # 兼容性读取
                if up_file.name.endswith('.pdf'):
                    with pdfplumber.open(up_file) as pdf:
                        text = "\n".join([p.extract_text() for p in pdf.pages if p.extract_text()])
                else:
                    doc = Document(up_file)
                    text = "\n".join([p.text for p in doc.paragraphs])
                
                # 发送给 AI
                res = client.chat.completions.create(
                    model="deepseek-chat",
                    messages=[{"role": "user", "content": f"Audit this contract: {text[:4000]}"}]
                )
                st.success("✅ Audit Done!")
                st.write(res.choices[0].message.content)
            except Exception as e:
                st.error(f"Error: {e}")
    else:
        st.warning("Please upload a file.")
