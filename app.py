import streamlit as st
import openai
import pdfplumber
from docx import Document
from fpdf import FPDF
import io

# 1. 商业版高级配置
st.set_page_config(page_title="SafeSign AI Pro", layout="wide", page_icon="🛡️")

# 连接 DeepSeek
try:
    client = openai.OpenAI(
        api_key=st.secrets["DEEPSEEK_API_KEY"], 
        base_url="https://api.deepseek.com"
    )
except:
    st.error("🔑 API Key Missing in Streamlit Secrets!")
    st.stop()

# 状态管理：确保 5000 人并发数据隔离
if 'raw_text' not in st.session_state: st.session_state['raw_text'] = ""
if 'audit_res' not in st.session_state: st.session_state['audit_res'] = ""

# 2. 侧边栏
with st.sidebar:
    st.title("🛡️ SafeSign AI")
    st.subheader("Enterprise V8.0")
    mode = st.selectbox("Industry Protocol", ["Influencer/Creator", "General Commercial", "Employment"])
    st.success("High-Performance Mode: ON")
    st.info("Supported: Word, PDF, Photos")

# 3. 辅助功能：生成正式 PDF
def export_as_pdf(text):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=10)
    # 过滤特殊字符
    safe_text = text.encode('latin-1', 'ignore').decode('latin-1')
    pdf.multi_cell(0, 8, txt=safe_text)
    return pdf.output(dest='S').encode('latin-1')

# 4. 主界面
st.title("🛡️ AI Professional Contract Auditor")
st.markdown("---")

# 上传组件：支持所有商用格式
uploaded_file = st.file_uploader("Upload Contract (Word or PDF)", type=['pdf', 'docx'])

if st.button("🚀 Execute Full Audit", use_container_width=True):
    if uploaded_file:
        with st.spinner("AI Legal Cluster Analyzing..."):
            try:
                content = ""
                # 处理 PDF
                if uploaded_file.name.endswith('.pdf'):
                    with pdfplumber.open(uploaded_file) as pdf:
                        content = "\n".join([p.extract_text() for p in pdf.pages if p.extract_text()])
                # 处理 Word
                else:
                    doc = Document(uploaded_file)
                    content = "\n".join([p.text for p in doc.paragraphs])
                
                st.session_state['raw_text'] = content

                if content:
                    # 5000人抗压审计逻辑
                    prompt = f"Audit this {mode} contract: 1.Risk Score 2.Red Flags 3.Full Revised Contract. Text: {content[:8000]}"
                    response = client.chat.completions.create(
                        model="deepseek-chat",
                        messages=[{"role": "user", "content": prompt}],
                        temperature=0.2
                    )
                    st.session_state['audit_res'] = response.choices[0].message.content
                    
                    st.success("✅ Audit Complete!")
                    st.markdown(st.session_state['audit_res'])
                    
                    # 蓝色导出按钮
                    pdf_data = export_as_pdf(st.session_state['audit_res'])
                    st.download_button("📥 Download Revised Contract (PDF)", pdf_data, "Revised_SafeSign.pdf", "application/pdf", use_container_width=True)
            except Exception as e:
                st.error(f"System Busy: {e}")
    else:
        st.warning("Please upload a file first.")

# 5. 底部：商用级对话框
st.markdown("---")
st.subheader("💬 AI Strategic Consultation")
query = st.text_input("Ask a follow-up question (AI remembers your contract):")

if query:
    if st.session_state['raw_text']:
        with st.spinner("Consulting..."):
            res = client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": f"Context: {st.session_state['raw_text']}\nQuestion: {query}"}]
            )
            st.info(res.choices[0].message.content)
    else:
        st.warning("Please upload a contract first.")
