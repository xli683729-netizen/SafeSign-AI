import streamlit as st
from supabase import create_client
import openai
import pdfplumber
from docx import Document
from io import BytesIO

# --- 1. 商业化配置 ---
st.set_page_config(page_title="SafeSign Pro", page_icon="⚖️", layout="wide")

st.markdown("""
    <style>
    .report-box { padding: 15px; border-radius: 8px; border: 1px solid #eee; background-color: #f9f9f9; color: #333; }
    .stChatInputContainer { padding-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

@st.cache_resource
def init_engine():
    supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
    ai_client = openai.OpenAI(
        api_key=st.secrets["DEEPSEEK_API_KEY"], 
        base_url="https://api.deepseek.com"
    )
    return supabase, ai_client

supabase, ai_client = init_engine()

# --- 2. 极速解析逻辑 (优化 PDF 读取速度) ---
def fast_extract(file):
    try:
        if file.type == "application/pdf":
            with pdfplumber.open(file) as pdf:
                # 仅取前 10 页进行快速审计，避免超长文件拖慢速度
                pages = pdf.pages[:10] 
                return "\n".join([p.extract_text() for p in pages if p.extract_text()])
        elif file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            return "\n".join([p.text for p in Document(file).paragraphs])
        return ""
    except Exception as e:
        return f"Error: {e}"

# --- 3. Word 生成器 ---
def make_docx(audit, tmpl):
    doc = Document()
    doc.add_heading('SafeSign Pro 审计方案', 0)
    doc.add_heading('风险审计', level=1); doc.add_paragraph(audit)
    doc.add_heading('标准范本', level=1); doc.add_paragraph(tmpl)
    bio = BytesIO()
    doc.save(bio)
    return bio.getvalue()

# --- 4. 界面布局 ---
with st.sidebar:
    st.title("🛡️ SafeSign Pro")
    email = st.text_input("登记邮箱解锁下载:")
    if email:
        try: supabase.table("users").upsert({"email": email}).execute()
        except: pass
    st.info("模式：中国法律专业版")

st.title("⚖️ 合同智能审计与范本生成")

# 强制显示对话框（即使还没上传文件，也可以先咨询）
if "messages" not in st.session_state:
    st.session_state.messages = []

# 显示聊天历史
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

uploaded_file = st.file_uploader("上传合同 (PDF/Word)", type=["pdf", "docx"])

if uploaded_file:
    # 检查是否已经分析过，避免重复分析
    if "audit_result" not in st.session_state:
        with st.spinner("正在极速扫描条款..."):
            content = fast_extract(uploaded_file)
            if len(content) > 10:
                # 提示词优化，要求 AI 简明扼要，加快生成速度
                p = f"你是中国律师，请极简审计此合同风险并提供留白范本: {content[:4000]}"
                res = ai_client.chat.completions.create(
                    model="deepseek-chat",
                    messages=[{"role": "user", "content": p}]
                ).choices[0].message.content
                st.session_state.audit_result = res
            else:
                st.error("文件内容无法识别")

    # 显示结果
    if "audit_result" in st.session_state:
        st.subheader("📋 审计与范本建议")
        st.markdown(f"<div class='report-box'>{st.session_state.audit_result}</div>", unsafe_allow_html=True)
        
        # 强制显示下载按钮
        st.markdown("---")
        word_data = make_docx(st.session_state.audit_result, "请参考上方范本内容")
        st.download_button(
            label="📥 下载 Word 专业版方案",
            data=word_data,
            file_name=f"SafeSign_Audit_{uploaded_file.name}.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )

# --- 对话框逻辑 (放在最底部，确保始终可见) ---
st.markdown("---")
if prompt := st.chat_input("针对合同内容，您可以进一步追问律师..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    with st.chat_message("assistant"):
        # 实时咨询逻辑
        context = st.session_state.audit_result if "audit_result" in st.session_state else "通用法律咨询"
        response = ai_client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "system", "content": f"基于此背景回答: {context}"},
                      {"role": "user", "content": prompt}]
        ).choices[0].message.content
        st.markdown(response)
        st.session_state.messages.append({"role": "assistant", "content": response})
