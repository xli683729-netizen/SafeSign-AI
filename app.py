cimport streamlit as st
import openai
import pdfplumber
from docx import Document
from fpdf import FPDF

# 1. 基础配置
st.set_page_config(page_title="SafeSign AI Pro", layout="wide", page_icon="🛡️")

client = openai.OpenAI(
    api_key=st.secrets["DEEPSEEK_API_KEY"], 
    base_url="https://api.deepseek.com"
)

# 状态管理
if 'raw_text' not in st.session_state: st.session_state['raw_text'] = ""

# 2. 侧边栏
with st.sidebar:
    st.title("🛡️ SafeSign AI")
    mode = st.selectbox("Protocol", ["General Commercial", "Influencer/Model", "Employment"])
    st.success("High-Speed Engine Active")

# 3. 辅助功能：导出 PDF
def export_pdf(text):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=10)
    safe_text = text.encode('latin-1', 'ignore').decode('latin-1')
    pdf.multi_cell(0, 8, txt=safe_text)
    return pdf.output(dest='S').encode('latin-1')

# 4. 主界面
st.title("🛡️ AI Contract Audit Suite")
st.markdown("---")

# 极速入口：支持 Word/PDF 上传 或 直接粘贴
tab1, tab2 = st.tabs(["📄 Upload Document", "✍️ Paste Contract Text"])

text_content = ""

with tab1:
    up_file = st.file_uploader("Upload Word (.docx) or PDF", type=['pdf', 'docx'])
    if up_file:
        if up_file.type == "application/pdf":
            with pdfplumber.open(up_file) as pdf:
                text_content = "\n".join([p.extract_text() for p in pdf.pages if p.extract_text()])
        else:
            doc = Document(up_file)
            text_content = "\n".join([p.text for p in doc.paragraphs])

with tab2:
    pasted_text = st.text_area("Paste text here (or use phone camera to 'copy text' and paste):", height=200)
    if pasted_text:
        text_content = pasted_text

if st.button("🚀 Start Audit", use_container_width=True):
    if text_content:
        st.session_state['raw_text'] = text_content
        with st.spinner("Analyzing..."):
            try:
                prompt = f"Audit this {mode} contract: 1.Risk Score 2.Red Flags 3.REVISED FULL CONTRACT. Text: {text_content}"
                res = client.chat.completions.create(
                    model="deepseek-chat",
                    messages=[{"role": "user", "content": prompt}]
                )
                audit_res = res.choices[0].message.content
                st.success("✅ Complete")
                st.markdown(audit_res)
                
                # 导出 PDF
                pdf_data = export_pdf(audit_res)
                st.download_button("📥 Download Corrected PDF", pdf_data, "Revised.pdf", "application/pdf")
            except Exception as e:
                st.error(f"Error: {e}")

# 5. 底部对话
st.divider()
query = st.text_input("💬 Follow-up question:")
if query and st.session_state['raw_text']:
    res = client.chat.completions.create(
        model="deepseek-chat",
        messages=[{"role": "user", "content": f"Context: {st.session_state['raw_text']}\nQ: {query}"}]
    )
    st.info(res.choices[0].message.content)ontent)
