import streamlit as st
from supabase import create_client
import openai
import pdfplumber
from docx import Document
from fpdf import FPDF
from datetime import datetime

# 1. 数据库与 AI 初始化
@st.cache_resource
def init_db():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

supabase = init_db()
client = openai.OpenAI(api_key=st.secrets["DEEPSEEK_API_KEY"], base_url="https://api.deepseek.com")

# 检查会员函数：不仅查邮箱，还查是否到期
def check_member(email):
    if not email: return False
    res = supabase.table("users").select("*").eq("email", email).execute()
    if res.data:
        expire_date_str = res.data[0]['expire_date']
        # 对比当前时间
        expire_date = datetime.fromisoformat(expire_date_str.replace('Z', '+00:00'))
        if expire_date > datetime.now(expire_date.tzinfo):
            return True
    return False

# 2. 侧边栏：登录界面
with st.sidebar:
    st.title("🛡️ SafeSign Pro")
    user_email = st.text_input("Member Login (Email):")
    is_pro = check_member(user_email)
    
    if is_pro:
        st.success(f"Verified: {user_email}")
    elif user_email:
        st.error("No active subscription.")

# 3. 主界面逻辑（略，同前：如果是 is_pro 则开启下载按钮）
# ... (此处放之前的解析和审计代码)
if st.button("🚀 RUN LEGAL AUDIT"):
    # ... 解析逻辑 ...
    st.write("Audit Report Result...")
    
    if is_pro:
        st.download_button("📥 Download PDF Report", data=b"pdf_content", file_name="Report.pdf")
    else:
        st.warning("🔒 Subscription required to download PDF.")
