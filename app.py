import streamlit as st
from supabase import create_client
import openai
import pdfplumber
from docx import Document
from io import BytesIO

# --- 1. 配置与样式 (保持 1:1 对比布局) ---
st.set_page_config(page_title="SafeSign Pro", page_icon="⚖️", layout="wide")

st.markdown("""
    <style>
    .report-card { 
        padding: 20px; border-radius: 10px; border: 1px solid #e0e0e0; 
        background-color: #ffffff; height: 650px; overflow-y: auto; 
    }
    .stChatInputContainer { padding-bottom: 30px; }
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

# --- 2. 文档解析引擎 ---
def extract_content(file):
    try:
        if file.type == "application/pdf":
            with pdfplumber.open(file) as pdf:
                return "\n".join([p.extract_text() for p in pdf.pages[:15] if p.extract_text()])
        elif file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            return "\n".join([p.text for p in Document(file).paragraphs])
        return ""
    except Exception as e:
        return f"解析失败: {e}"

# --- 3. Word 导出引擎 (支持纯范本导出) ---
def export_docx(audit, template):
    doc = Document()
    doc.add_heading('SafeSign Pro 法律服务文档', 0)
    if audit:
        doc.add_heading('一、法律风险审计报告', level=1)
        doc.add_paragraph(audit)
    doc.add_heading('二、标准合同范本(留白版)', level=1)
    doc.add_paragraph(template)
    bio = BytesIO()
    doc.save(bio)
    return bio.getvalue()

# --- 4. 侧边栏 ---
with st.sidebar:
    st.title("🛡️ SafeSign Pro")
    st.caption("中国通用法律助手")
    email = st.text_input("登记邮箱（解锁下载）:", placeholder="example@mail.com")
    if email:
        try: supabase.table("users").upsert({"email": email}).execute()
        except: pass
    st.markdown("---")
    st.info("模式：审计 + 创作双引擎")

# --- 5. 主界面逻辑 ---
st.title("⚖️ SafeSign Pro：企业级法律智能引擎")

if "audit_part" not in st.session_state: st.session_state.audit_part = "等待上传合同或输入指令..."
if "tmpl_part" not in st.session_state: st.session_state.tmpl_part = "等待生成范本..."
if "chat_history" not in st.session_state: st.session_state.chat_history = []

uploaded_file = st.file_uploader("上传待审核合同 (PDF/Word)", type=["pdf", "docx"])

# A. 文件上传触发审计
if uploaded_file:
    if "last_file" not in st.session_state or st.session_state.last_file != uploaded_file.name:
        with st.spinner("正在进行深度法律审计..."):
            text = extract_content(uploaded_file)
            prompt = f"你是一名资深中国律师。请先对以下合同进行风险审计，然后提供一份变量留白的标准范本。要求使用 [AUDIT]审计内容[/AUDIT] 和 [TMPL]范本内容[/TMPL] 格式返回。内容：{text[:4000]}"
            res = ai_client.chat.completions.create(model="deepseek-chat", messages=[{"role": "user", "content": prompt}]).choices[0].message.content
            
            # 简单解析
            if "[AUDIT]" in res:
                st.session_state.audit_part = res.split("[AUDIT]")[1].split("[/AUDIT]")[0].strip()
                st.session_state.tmpl_part = res.split("[TMPL]")[1].split("[/TMPL]")[0].strip()
            st.session_state.last_file = uploaded_file.name

# B. 对话框输入触发创作（如“写一份租房合同”）
st.markdown("---")
if chat_prompt := st.chat_input("输入‘写一份XXX合同’或针对审计结果追问..."):
    st.session_state.chat_history.append({"role": "user", "content": chat_prompt})
    
    with st.spinner("AI 律师正在处理您的请求..."):
        # 判断是否是创作请求
        if "写一份" in chat_prompt or "起草" in chat_prompt or "生成" in chat_prompt:
            create_prompt = f"你是一名资深中国律师。请直接起草一份完整的、符合中国法律的【{chat_prompt}】标准范本。要求所有变量（如姓名、金额、日期）用 [ ] 留白。直接输出合同内容。"
            new_tmpl = ai_client.chat.completions.create(model="deepseek-chat", messages=[{"role": "user", "content": create_prompt}]).choices[0].message.content
            st.session_state.tmpl_part = new_tmpl
            st.session_state.audit_part = f"已根据您的指令‘{chat_prompt}’生成了全新的标准合同范本，请查看右侧。"
        else:
            # 普通追问
            ans = ai_client.chat.completions.create(
                model="deepseek-chat", 
                messages=[{"role": "system", "content": f"背景:{st.session_state.audit_part}"}, {"role": "user", "content": chat_prompt}]
            ).choices[0].message.content
            st.session_state.chat_history.append({"role": "assistant", "content": ans})

# --- 6. 核心展示区：左右 1:1 对比 ---
col1, col2 = st.columns(2)
with col1:
    st.subheader("🚩 风险审计 / 指令状态")
    st.markdown(f"<div class='report-card'>{st.session_state.audit_part}</div>", unsafe_allow_html=True)

with col2:
    st.subheader("📄 标准范本建议")
    st.markdown(f"<div class='report-card'>{st.session_state.tmpl_part}</div>", unsafe_allow_html=True)

# 下载按钮
st.markdown("---")
if st.session_state.tmpl_part != "等待生成范本...":
    doc_bytes = export_docx(st.session_state.audit_part, st.session_state.tmpl_part)
    st.download_button(
        label="📥 下载 Word 方案（含最新生成的合同）",
        data=doc_bytes,
        file_name="SafeSign_Legal_Service.docx",
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )

# 历史对话显示
for msg in st.session_state.chat_history:
    with st.chat_message(msg["role"]): st.markdown(msg["content"])
