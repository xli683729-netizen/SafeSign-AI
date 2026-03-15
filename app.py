import streamlit as st
import openai
from PIL import Image
import pdfplumber
import easyocr
import numpy as np
from fpdf import FPDF
from docx import Document
import io

# --- 1. 商用级内存优化：缓存 OCR 模型 ---
# 这样服务器启动时只加载一次模型，5000人共享，不会重复吃内存
@st.cache_resource
def get_ocr_reader():
    return easyocr.Reader(['en'])

# --- 2. 初始化配置 ---
st.set_page_config(
    page_title="SafeSign AI Pro - Enterprise",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 链接 DeepSeek
client = openai.OpenAI(
    api_key=st.secrets["DEEPSEEK_API_KEY"], 
    base_url="https://api.deepseek.com"
)

# 使用 SessionState 隔离不同用户的对话内容
if 'raw_text' not in st.session_state: st.session_state['raw_text'] = ""

# --- 3. 核心功能函数 ---
def generate_pdf(text):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=10)
    # 工业级过滤字符，防止导出时因特殊符号报错
    safe_text = text.encode('latin-1', 'ignore').decode('latin-1')
    pdf.multi_cell(0, 8, txt=safe_text)
    return pdf.output(dest='S').encode('latin-1')

# --- 4. UI 界面 ---
st.title("🛡️ SafeSign AI Professional")
st.subheader("Enterprise-Grade Contract Audit Engine")

with st.sidebar:
    st.header("Settings")
    mode = st.selectbox("Industry Protocol", ["General Commercial", "Influencer/Creator", "Employment"])
    st.markdown("---")
    st.success("✅ System Secure")
    st.info("Support: support@safesign.ai")

# 全格式支持上传
uploaded_file = st.file_uploader("Upload Contract (PDF, Word, or Photo)", type=['png', 'jpg', 'jpeg', 'pdf', 'docx'])

if st.button("🚀 Execute Global Audit", use_container_width=True):
    if uploaded_file:
        with st.spinner("AI Cluster is analyzing..."):
            try:
                content = ""
                # Word 处理
                if uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                    doc = Document(uploaded_file)
                    content = "\n".join([p.text for p in doc.paragraphs])
                # 图片/拍照处理
                elif uploaded_file.type in ["image/png", "image/jpeg", "image/jpg"]:
                    reader = get_ocr_reader()
                    img = Image.open(uploaded_file)
                    results = reader.readtext(np.array(img))
                    content = " ".join([res[1] for res in results])
                # PDF 处理
                else:
                    with pdfplumber.open(uploaded_file) as pdf:
                        content = "\n".join([p.extract_text() for p in pdf.pages if p.extract_text()])

                st.session_state['raw_text'] = content

                if content:
                    # 5000人并发时，DeepSeek API 调用需要严谨
                    response = client.chat.completions.create(
                        model="deepseek-chat",
                        messages=[{
                            "role": "system",
                            "content": f"You are an expert legal auditor for {mode}."
                        }, {
                            "role": "user",
                            "content": f"Audit this contract: Score (0-100), Red Flags, and a full REVISED version. Text: {content}"
                        }],
                        temperature=0.1 # 极低随机性，商用更严谨
                    )
                    audit_output = response.choices[0].message.content
                    st.write(audit_output)
                    
                    # 导出按钮
                    pdf_bytes = generate_pdf(audit_output)
                    st.download_button(
                        "📥 Export Corrected Contract (PDF)",
                        pdf_bytes,
                        "Revised_SafeSign_Contract.pdf",
                        "application/pdf",
                        use_container_width=True
                    )
            except Exception as e:
                st.error(f"System Busy: Please try again in a moment. ({str(e)})")
    else:
        st.warning("Please upload a file to begin.")

# --- 5. 底部对话咨询 ---
st.divider()
st.subheader("💬 Strategic Follow-up")
user_q = st.text_input("Ask a follow-up question regarding the audit:")
if user_q and st.session_state['raw_text']:
    with st.spinner("Consulting..."):
        res = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": f"Context: {st.session_state['raw_text']}\nQuestion: {user_q}"}]
        )
        st.info(res.choices[0].message.content)
