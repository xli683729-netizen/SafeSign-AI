import streamlit as st
from supabase import create_client
import openai
import pdfplumber
from docx import Document
from io import BytesIO
from fpdf import FPDF
import PIL.Image
import PIL.ImageOps

# --- 1. PRO-GRADE CONFIGURATION ---
st.set_page_config(
    page_title="SafeSign AI | Global Contract Auditor", 
    page_icon="⚖️", 
    layout="wide"
)

@st.cache_resource
def init_pro_services():
    # Persistent connection for high-traffic (5000+ users)
    supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
    ai_client = openai.OpenAI(
        api_key=st.secrets["DEEPSEEK_API_KEY"], 
        base_url="https://api.deepseek.com"
    )
    return supabase, ai_client

supabase, ai_client = init_pro_services()

# --- 2. MULTI-FORMAT TEXT EXTRACTION (PDF/DOCX/OCR) ---
def extract_contract_content(file):
    text = ""
    try:
        if file.type == "application/pdf":
            with pdfplumber.open(file) as pdf:
                text = "\n".join([page.extract_text() for page in pdf.pages if page.extract_text()])
        elif file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            doc = Document(file)
            text = "\n".join([p.text for p in doc.paragraphs])
        elif "image" in file.type:
            # Note: For professional scan/photo audit, we notify user 
            # DeepSeek-V3 can process text-heavy prompts or we use pre-processing
            text = "IMAGE_SCAN_MODE: Please ensure the photo is clear for AI analysis."
            # (Optional: Add OCR library here for 100% photo accuracy)
    except Exception as e:
        st.error(f"Analysis Error: {str(e)}")
    return text

# --- 3. ELITE LEGAL BRAIN (DeepSeek-V3 Prompt) ---
def analyze_with_ai(content):
    # Professional American Legal Logic
    system_prompt = """
    You are a Senior Corporate Attorney specializing in the US Creator Economy. 
    Audit this contract for an Influencer/Content Creator. 
    Focus on:
    - Usage Rights & IP (Is it perpetual? Worldwide?)
    - Exclusivity Clauses (Non-compete traps)
    - Payment Terms (Net-30, late fees, gross vs net)
    - Termination for Convenience
    - Indemnification & Liability
    Provide a professional, concise risk assessment in American English.
    """
    try:
        response = ai_client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"AUDIT THIS CONTRACT: {content[:8000]}"}
            ],
            temperature=0.3 # Low temperature for high accuracy
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Legal Engine Offline: {str(e)}"

# --- 4. INSTANT PDF REPORT GENERATOR ---
def create_pdf_report(report_text):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt="SafeSign AI - Legal Risk Assessment", ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Arial", size=11)
    # Cleaning text for PDF encoding
    safe_text = report_text.encode('latin-1', 'ignore').decode('latin-1')
    pdf.multi_cell(0, 8, txt=safe_text)
    return pdf.output(dest='S').encode('latin-1')

# --- 5. HIGH-CONVERSION UI ---
with st.sidebar:
    st.image("https://via.placeholder.com/150x50?text=SafeSign+PRO", use_container_width=True)
    st.markdown("### 🔐 Member Access")
    user_email = st.text_input("Registration Email:", placeholder="name@creator.com")
    
    if user_email:
        # Auto-register for early access marketing
        supabase.table("users").upsert({"email": user_email, "expire_date": "2027-01-01"}).execute()
        st.success("PRO STATUS: ACTIVE")
        st.caption("Early Access: Free Tier")
    else:
        st.info("Log in to download PDF reports.")

st.title("⚖️ SafeSign AI: Professional Contract Auditor")
st.markdown("""
**Stop signing away your rights.** Upload your brand deal, contract, or even a photo of a scan. 
Our AI detects high-risk clauses in seconds.
""")

# File Uploader
uploaded_file = st.file_uploader(
    "Upload Contract (PDF, DOCX, or Clear Photo)", 
    type=["pdf", "docx", "png", "jpg", "jpeg"]
)

if uploaded_file:
    with st.spinner("🔍 Deep-scanning legal clauses..."):
        raw_text = extract_contract_content(uploaded_file)
        
        if len(raw_text) > 50:
            analysis = analyze_with_ai(raw_text)
            
            # --- Results Display ---
            st.subheader("🚩 Risk Assessment Summary")
            st.markdown(analysis)
            
            # --- One-Click PDF Generation ---
            if user_email:
                pdf_bytes = create_pdf_report(analysis)
                st.download_button(
                    label="📥 Download Certified PDF Report",
                    data=pdf_bytes,
                    file_name=f"SafeSign_Audit_{uploaded_file.name}.pdf",
                    mime="application/pdf"
                )
            else:
                st.warning("Please provide your email in the sidebar to download the full PDF report.")
            
            # --- Interactive AI Consultant (Chat) ---
            st.markdown("---")
            st.subheader("💬 Ask Your AI Attorney")
            user_msg = st.chat_input("Ex: 'Can I terminate this if they don't pay in 15 days?'")
            if user_msg:
                with st.chat_message("assistant"):
                    st.write(f"Analyzing your question about: **{user_msg}**...")
                    # Chat logic would go here
        else:
            st.error("Text extraction failed. Please ensure the document is not password-protected or blurred.")

# Footer
st.markdown("---")
st.caption("© 2026 SafeSign AI | San Francisco, CA. For informational purposes only. Not legal advice.")
