import streamlit as st
import openai
import pdfplumber
from docx import Document
from fpdf import FPDF

# 1. US Market Configuration
st.set_page_config(page_title="SafeSign AI - Professional Contract Audit", layout="wide", page_icon="🛡️")

try:
    client = openai.OpenAI(
        api_key=st.secrets["DEEPSEEK_API_KEY"], 
        base_url="https://api.deepseek.com"
    )
except:
    st.error("🔑 Connecting to Secure Cloud...")
    st.stop()

# Business Logic State
if 'usage_count' not in st.session_state: st.session_state['usage_count'] = 0
if 'is_subscribed' not in st.session_state: st.session_state['is_subscribed'] = False
if 'audit_res' not in st.session_state: st.session_state['audit_res'] = ""

# 2. Sidebar - Branding & Support (US Style)
with st.sidebar:
    st.title("🛡️ SafeSign AI")
    st.markdown("### Professional Legal Compliance")
    st.divider()
    
    if not st.session_state['is_subscribed']:
        st.warning("Current: Free Trial")
        st.caption("Limit: 1 Analysis. PDF Download Locked.")
    else:
        st.success("Status: PRO Member")
    
    st.divider()
    st.selectbox("Legal Jurisdiction", ["Federal/General Commercial"])
    
    st.divider()
    st.markdown("### 💬 Support & Inquiry")
    st.info("Need custom audit or help?")
    st.write("📧 Email: support@yourdomain.com") # 换成你的邮箱
    st.write("📱 WhatsApp: +1 XXX-XXX-XXXX") # 换成你的号

# 3. PDF Function
def export_as_pdf(text):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=10)
    safe_text = text.encode('latin-1', 'ignore').decode('latin-1')
    pdf.multi_cell(0, 8, txt=safe_text)
    return pdf.output(dest='S').encode('latin-1')

# 4. Main Interface
st.title("🛡️ SafeSign AI: Professional Contract Auditor")
st.caption("AI-powered risk detection for US commercial contracts.")

# 4.1 Pricing Table (US Style)
if not st.session_state['is_subscribed']:
    with st.expander("💎 Upgrade to Pro (Unlock All Features)", expanded=False):
        c1, c2 = st.columns(2)
        with c1:
            st.info("### Single Scan\n**$9.9 / doc**\n- Full Risk Report\n- Unlock PDF Export")
        with c2:
            st.success("### Monthly Pro\n**$49.0 / mo**\n- Unlimited Scans\n- Priority Support")
        
        # 支付链接按钮
        st.link_button("💳 Pay & Activate via Stripe/PayPal", "https://your-payment-link.com")
        st.caption("After payment, please enter your Activation Code below.")

st.divider()

# 4.2 Upload
st.markdown("#### Step 1: Upload Document")
uploaded_file = st.file_uploader("Drop Word (.docx) or PDF file", type=['pdf', 'docx'])

# 4.3 Execution
if uploaded_file:
    if st.session_state['usage_count'] >= 1 and not st.session_state['is_subscribed']:
        st.error("⚠️ Trial limit reached. Please upgrade to PRO to continue.")
    else:
        if st.button("🚀 EXECUTE AI AUDIT", use_container_width=True, type="primary"):
            with st.spinner("Analyzing legal risks..."):
                try:
                    content = ""
                    if uploaded_file.name.endswith('.pdf'):
                        with pdfplumber.open(uploaded_file) as pdf:
                            content = "\n".join([p.extract_text() for p in pdf.pages if p.extract_text()])
                    else:
                        doc = Document(uploaded_file)
                        content = "\n".join([p.text for p in doc.paragraphs])
                    
                    prompt = f"Act as a US commercial lawyer. Audit this contract: 1.Risk Score (0-100) 2.Top 3 Critical Red Flags 3.Revised Clauses. Text: {content[:6000]}"
                    response = client.chat.completions.create(
                        model="deepseek-chat",
                        messages=[{"role": "user", "content": prompt}]
                    )
                    st.session_state['audit_res'] = response.choices[0].message.content
                    st.session_state['usage_count'] += 1
                    st.rerun()
                except Exception as e:
                    st.error("Connection busy. Please try again.")

# 4.4 Results
if st.session_state['audit_res']:
    st.success("✅ Audit Report Ready")
    st.markdown(st.session_state['audit_res'])
    
    if st.session_state['is_subscribed']:
        pdf_data = export_as_pdf(st.session_state['audit_res'])
        st.download_button("📥 Download Revised Contract (PDF)", pdf_data, "Report.pdf", "application/pdf", use_container_width=True)
    else:
        st.warning("🔒 PDF Download is locked for trial users. Upgrade to PRO to unlock.")

# 5. Disclaimer (Essential for US Market)
st.divider()
st.caption("Disclaimer: SafeSign AI is an AI-powered tool and does not provide formal legal advice. Please consult with a licensed attorney for major legal decisions.")
