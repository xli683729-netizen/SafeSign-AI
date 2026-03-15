import streamlit as st
from supabase import create_client
import openai
from datetime import datetime
import pytz

# --- 1. 初始化 ---
@st.cache_resource
def init_connections():
    supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
    client = openai.OpenAI(
        api_key=st.secrets["DEEPSEEK_API_KEY"], 
        base_url="https://api.deepseek.com"
    )
    return supabase, client

supabase, client = init_connections()

# --- 2. 核心：登记邮箱并自动授权 ---
def register_and_authorize(email):
    if not email or "@" not in email:
        return False, "Please enter a valid email."
    
    try:
        # 检查是否已经是老用户
        response = supabase.table("users").select("*").eq("email", email).execute()
        
        if not response.data:
            # 新用户：自动往数据库存入，并给一年有效期
            expire_date = "2027-03-15T00:00:00+00:00"
            supabase.table("users").insert({
                "email": email, 
                "expire_date": expire_date
            }).execute()
            return True, "Welcome! Early Access Granted."
        else:
            return True, "Welcome back, Pro Member."
            
    except Exception as e:
        # 如果数据库报错（比如重复），只要邮箱对了也让他用，不影响用户体验
        return True, "Access Granted."

# --- 3. 界面设计 ---
st.set_page_config(page_title="SafeSign AI | Professional Legal Audit", layout="wide")

# 侧边栏：品牌展示
with st.sidebar:
    st.markdown("### 🛡️ SafeSign Pro")
    st.markdown("---")
    email_input = st.text_input("Enter your email to unlock PRO:", placeholder="creator@example.com")
    
    authorized = False
    if email_input:
        authorized, msg = register_and_authorize(email_input)
        if authorized:
            st.success("✅ PRO STATUS: ACTIVE")
            st.caption("Early Access: $0.00 (Standard: $29.00)")
        else:
            st.warning(msg)
    else:
        st.info("Unlock PDF reports and deep analysis by entering your email.")

# 主界面
st.title("⚖️ SafeSign AI: Creator Legal Audit")
st.markdown("#### *The smartest way for fashion influencers to sign contracts.*")

# 推广横幅
if not authorized:
    st.warning("🎁 **Limited Time Offer:** All Pro features are currently FREE for our first 500 creators!")

# --- 4. 业务逻辑 ---
uploaded_file = st.file_uploader("Upload your Brand Contract (PDF or Word)", type=["pdf", "docx"])

if uploaded_file:
    with st.spinner("AI is analyzing legal risks and hidden traps..."):
        # 这里放置您的 DeepSeek 处理逻辑
        # text = extract_text(uploaded_file)
        # result = call_deepseek(text)
        st.subheader("📝 Audit Summary")
        st.error("🚩 **High Risk:** The brand owns your image rights PERMANENTLY. (Clause 4.2)")
        st.warning("⚠️ **Warning:** No clear payment deadline mentioned.")
        
        st.markdown("---")
        
        # --- 权限控制 ---
        if authorized:
            st.success("Full Report Generated Successfully.")
            # 真实情况下这里会生成 PDF 字节流
            st.download_button(
                label="📥 Download Detailed Audit Report (PDF)",
                data="Your PDF Data Here",
                file_name="SafeSign_Professional_Report.pdf",
                mime="application/pdf"
            )
        else:
            st.button("📥 Download Detailed Report (Email Required)", disabled=True)
            st.info("Please enter your email in the sidebar to unlock the PDF download.")

# 页脚
st.markdown("---")
st.caption("© 2026 SafeSign AI. Helping fashion creators protect their business.")
