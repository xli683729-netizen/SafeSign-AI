import streamlit as st
import openai
import pdfplumber
from docx import Document
from fpdf import FPDF
from datetime import datetime

# 1. US Enterprise Config
st.set_page_config(page_title="SafeSign AI Pro", layout="wide", page_icon="🛡️")

# 连接 AI
try:
    client = openai.OpenAI(api_key=st.secrets["DEEPSEEK_API_KEY"], base_url="https://api.deepseek.com")
except:
    st.error("🔑 Secure System Initializing...")
    st.stop()

# --- 商业逻辑状态 (后续对接数据库) ---
if 'user_email' not in st.session_state: st.session_state['user_email'] = ""
if 'is_pro' not in st.session_state: st.session_state['is_pro'] = False
if 'audit_res' not in st.session_state: st.session_state['audit_res'] = ""

# 2. 侧边栏：登录与订阅管理
with st.sidebar:
    st.title("🛡️ SafeSign AI")
    st.divider()
    
    # 邮箱登录入口
    st.subheader("Member Login")
    email_input = st.text_input("Enter your Email to sync subscription:", value=st.session_state['user_email'])
    if email_input:
        st.session_state['user_email'] = email_input
        # 此处将来对接数据库：check_subscription(email_input)
        # 暂时用一个简单逻辑：如果是老板您的邮箱，自动解锁
        if "@admin.com" in email_input: 
            st.session_state['is_pro'] = True
            st.success("Admin Access Granted")

    st.divider()
    if st.session_state['is_pro']:
        st.success(f"PRO Member: {st.session_state['user_email']}")
    else:
        st.warning("Status: Standard (Limited)")
    
    st.divider()
    st.markdown("### 📞 Support & Consulting")
    st.link_button("📅 Book Legal Call", "https://calendly.com/your-link")
    st.write("✉️ support@safesignai.com")

# 3. PDF Generator
def export_pdf(text):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=10)
    safe_text = text.encode('latin-1', 'ignore').decode('latin-1')
    pdf.multi_cell(0, 8, txt=safe_text)
    return pdf.output(dest='S').encode('latin-1')

# 4. Main App
st.title("🛡️ Professional Legal Auditor")
st.caption("AI-Powered Compliance for US Entrepreneurs")

# 4.1 自动化的定价区
if not st.session_state['is_pro']:
    with st.container(border=True):
        st.markdown("### 💎 Unlock Full Access")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Monthly Subscription**")
            st.markdown("### $49 / month")
            st.write("- Unlimited Audits\n- PDF Downloads\n- Priority Support")
            st.link_button("Subscribe Monthly", "https://buy.stripe.com/test_subscription_link")
        with col2:
            st.markdown("**Single Audit**")
            st.markdown("### $9.9 / doc")
            st.write("- One Deep Scan\n- Single PDF Export\n- No Monthly Commitment")
            st.link_button("Pay per Use", "https://buy.stripe.com/test_single_link")

st.divider()

# 4.2 Audit Logic
uploaded_file = st.file_uploader("Upload Your Contract (Word or PDF)", type=['pdf', 'docx'])

if uploaded_file:
    # 如果没有登录或没有订阅，只给看报告，不能下载
    if st.button("🚀 RUN LEGAL AUDIT", use_container_width=True, type="primary"):
        with st.spinner("AI Law Engine Scanning..."):
            try:
                # 解析代码 (同前)
                if uploaded_file.name.endswith('.pdf'):
                    with pdfplumber.open(uploaded_file) as pdf:
                        text = "\n".join([p.extract_text() for p in pdf.pages if p.extract_text()])
                else:
                    doc = Document(uploaded_file)
                    text = "\n".join([p.text for p in doc.paragraphs])
                
                res = client.chat.completions.create(
                    model="deepseek-chat",
                    messages=[{"role": "user", "content": f"US Lawyer Audit: {text[:6000]}"}]
                )
                st.session_state['audit_res'] = res.choices[0].message.content
                st.rerun()
            except Exception as e:
                st.error("System Busy.")

# 4.3 Result Display
if st.session_state['audit_res']:
    st.success("✅ Audit Report Ready")
    st.markdown(st.session_state['audit_res'])
    
    # 商业锁：只有付费用户能下载
    if st.session_state['is_pro']:
        pdf_data = export_pdf(st.session_state['audit_res'])
        st.download_button("📥 Download PDF Report", pdf_data, "Report.pdf", "application/pdf", use_container_width=True)
    else:
        st.warning("🔒 PDF Download is reserved for PRO members. Please subscribe above to unlock.")

st.divider()
st.caption("Privacy: Your files are processed securely and never stored on our servers.")
