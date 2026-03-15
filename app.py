import streamlit as st
from supabase import create_client
import openai
import pdfplumber
from docx import Document
from fpdf import FPDF
from datetime import datetime
import pytz

# --- 1. 初始化数据库与 AI ---
# 确保你在 Streamlit Cloud 的 Secrets 里填好了 SUPABASE_URL, SUPABASE_KEY 和 DEEPSEEK_API_KEY
@st.cache_resource
def init_connections():
    supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
    client = openai.OpenAI(
        api_key=st.secrets["DEEPSEEK_API_KEY"], 
        base_url="https://api.deepseek.com"
    )
    return supabase, client

supabase, client = init_connections()

# --- 2. 核心功能：检查会员权限 ---
def check_membership(email):
    if not email:
        return False, "Please enter your email."
    
    try:
        # 去 Supabase 的 users 表里搜这个邮箱
        response = supabase.table("users").select("*").eq("email", email).execute()
        
        if not response.data:
            return False, "Not a PRO member yet."
        
        # 拿到到期时间并处理时区
        expire_str = response.data[0]['expire_date']
        expire_date = datetime.fromisoformat(expire_str.replace('Z', '+00:00'))
        now = datetime.now(pytz.utc)
        
        if expire_date > now:
            return True, f"PRO Active until {expire_date.strftime('%Y-%m-%d')}"
        else:
            return False, "Subscription expired."
            
    except Exception as e:
        return False, f"Connection error: {str(e)}"

# --- 3. 网页界面布局 ---
st.set_page_config(page_title="SafeSign AI Pro", layout="wide")

# 侧边栏：登录与支付
with st.sidebar:
    st.title("🛡️ SafeSign Member")
    email_input = st.text_input("Member Email (Login):", placeholder="your@email.com")
    
    is_pro, message = check_membership(email_input)
    
    if is_pro:
        st.success(message)
    elif email_input:
        st.warning(message)
        # 这里的链接替换成你 PayPal 审核通过后的按钮链接
        st.link_button("💎 Upgrade to PRO ($29/mo)", "https://www.paypal.com/your_link")

# 主界面
st.title("⚖️ SafeSign AI: Legal Audit for Creators")
st.info("Upload your contract. Let AI detect risks in seconds.")

uploaded_file = st.file_uploader("Upload Contract (PDF or Word)", type=["pdf", "docx"])

if uploaded_file:
    # 模拟审计过程
    with st.spinner("Analyzing legal risks..."):
        # (这里保留您之前的 pdfplumber/docx 解析逻辑)
        content = "Sample contract text extracted..." 
        
    st.subheader("📝 Audit Report")
    st.write("1. High Risk: Intellectual Property clause is vague.")
    st.write("2. Warning: Termination notice period is too short.")

    # --- 关键逻辑：PRO 权限控制 ---
    if is_pro:
        # 只有 PRO 才能看到这个按钮
        st.download_button(
            label="📥 Download Full PDF Audit Report",
            data="Sample PDF content", # 这里换成真实的 PDF 生成逻辑
            file_name="SafeSign_Audit_Report.pdf",
            mime="application/pdf"
        )
    else:
        # 非 PRO 看到提示
        st.button("📥 Download PDF Report (Locked)", disabled=True)
        st.error("Standard users can only view results online. Please log in with a PRO email to download the PDF.")
