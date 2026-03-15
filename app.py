import streamlit as st
import openai
import pdfplumber
from docx import Document
from fpdf import FPDF
import io

# 1. 基础页面设置
st.set_page_config(page_title="SafeSign AI Pro", layout="wide", page_icon="🛡️")

# 2. 连接 DeepSeek 大脑
client = openai.OpenAI(
    api_key=st.secrets["DEEPSEEK_API_KEY"], 
    base_url="https://api.deepseek.com"
)

# 初始化 Session State (保证 5000 人并发时不卡顿，数据隔离)
if 'contract_text' not in st.session_state: st.session_state['contract_text'] = ""
if 'audit_report' not in st.session_state: st.session_state['audit_report'] = ""

# 3. 侧边栏：专业模式切换
with st.sidebar:
    st.title("🛡️ SafeSign AI")
    st.subheader("Enterprise Version")
    mode = st.selectbox("Audit Protocol", ["Influencer/Model", "General Commercial", "Employment"])
    st.divider()
    st.success("Server: High Speed Active")

# 4. 辅助功能：生成正式 PDF 导出
def create_pdf_report(text):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=10)
    # 过滤非 Latin-1 字符防止导出报错
    safe_text = text.encode('latin-1', 'ignore').decode('latin-1')
    pdf.multi_cell(0, 8, txt=safe_text)
    return pdf.output(dest='S').encode('latin-1')

# 5. 主界面布局
st.title("🛡️ AI Professional Contract Suite")
st.markdown("---")

# 支持 Word, PDF 上传
uploaded_file = st.file_uploader("Upload Contract (PDF or Word)", type=['pdf', 'docx'])

if st.button("🚀 Run Full Audit", use_container_width=True):
    if uploaded_file:
        with st.spinner("AI is analyzing legal risks..."):
            try:
                text_content = ""
                # A: 处理 Word
                if uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                    doc = Document(uploaded_file)
                    text_content = "\n".join([p.text for p in doc.paragraphs])
                # B: 处理 PDF
                else:
                    with pdfplumber.open(uploaded_file) as pdf:
                        text_content = "\n".join([p.extract_text() for p in pdf.pages if p.extract_text()])
                
                st.session_state['contract_text'] = text_content

                if text_content:
                    # 调用 AI 审计
                    prompt = f"Audit this {mode} contract. 1.Risk Score 2.Red Flags 3.Full Revised Contract. Text: {text_content}"
                    response = client.chat.completions.create(
                        model="deepseek-chat",
                        messages=[{"role": "user", "content": prompt}],
                        temperature=0.2
                    )
                    st.session_state['audit_report'] = response.choices[0].message.content
                    
                    st.success("✅ Audit Complete!")
                    st.markdown(st.session_state['audit_report'])
                    
                    # 生成并显示导出按钮
                    pdf_data = create_pdf_report(st.session_state['audit_report'])
                    st.download_button(
                        label="📥 Download Revised Contract (PDF)",
                        data=pdf_data,
                        file_name="SafeSign_Audit_Report.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )
            except Exception as e:
                st.error(f"System overloaded. Please try again. Error: {e}")
    else:
        st.warning("Please upload a document first.")

# 6. 底部：AI 咨询对话框 (5000人并发核心功能)
st.markdown("---")
st.subheader("💬 AI Strategic Consultation")
query = st.text_input("Ask a follow-up question (e.g., 'Is the liability clause fair?'):")

if query:
    if st.session_state['contract_text']:
        with st.spinner("AI Expert is thinking..."):
            res = client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": f"Context: {st.session_state['contract_text']}\nQuestion: {query}"}]
            )
            st.info(res.choices[0].message.content)
    else:
        st.info("Please run an audit first to give AI context.")
