import streamlit as st
from supabase import create_client
import openai
import pdfplumber
from docx import Document
from io import BytesIO

# --- 1. 商业化配置 ---
st.set_page_config(page_title="SafeSign Pro", page_icon="⚖️", layout="wide")

# 注入 CSS 确保双栏高度一致，视觉专业
st.markdown("""
    <style>
    .report-card { 
        padding: 20px; border-radius: 10px; border: 1px solid #e0e0e0; 
        background-color: #ffffff; height: 600px; overflow-y: auto; 
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

# --- 2. 增强解析逻辑 ---
def extract_content(file):
    try:
        if file.type == "application/pdf":
            with pdfplumber.open(file) as pdf:
                # 仅解析前15页，确保响应速度在1分钟内
                return "\n".join([p.extract_text() for p in pdf.pages[:15] if p.extract_text()])
        elif file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            return "\n".join([p.text for p in Document(file).paragraphs])
        return ""
    except Exception as e:
        return f"解析失败: {e}"

# --- 3. Word 导出引擎 ---
def export_docx(audit, template):
    doc = Document()
    doc.add_heading('SafeSign Pro 合同审计方案', 0)
    doc.add_heading('一、法律风险审计报告', level=1); doc.add_paragraph(audit)
    doc.add_heading('二、标准合同范本(留白版)', level=1); doc.add_paragraph(template)
    bio = BytesIO()
    doc.save(bio)
    return bio.getvalue()

# --- 4. 侧边栏：会员中心 ---
with st.sidebar:
    st.title("🛡️ SafeSign Pro")
    st.caption("中国通用法律合同审计插件")
    email = st.text_input("登记邮箱（解锁下载）:", placeholder="example@mail.com")
    if email:
        try: supabase.table("users").upsert({"email": email}).execute()
        except: pass
    st.markdown("---")
    st.info("当前环境：中国民法典标准")

# --- 5. 主界面布局 ---
st.title("⚖️ 企业级合同智能审计引擎")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

uploaded_file = st.file_uploader("上传待审核合同 (PDF/Word)", type=["pdf", "docx"])

if uploaded_file:
    if "final_report" not in st.session_state:
        with st.spinner("正在依照中国法律深度扫描条款..."):
            text = extract_content(uploaded_file)
            if len(text) > 10:
                # 提示词要求 AI 严格按两部分输出
                prompt = f"你是一名资深中国律师。请先对以下合同进行风险审计，然后提供一份变量留白的标准范本。要求专业、地道、严谨。合同内容：{text[:4500]}"
                full_res = ai_client.chat.completions.create(
                    model="deepseek-chat",
                    messages=[{"role": "user", "content": prompt}]
                ).choices[0].message.content
                
                # 简单拆分结果（实际商用建议 AI 分两次返回或用分隔符）
                parts = full_res.split("范本")
                st.session_state.audit_part = parts[0]
                st.session_state.tmpl_part = "范本" + parts[1] if len(parts) > 1 else "请咨询律师获取详细范本"
                st.session_state.final_report = full_res

    # --- 核心：左右对称布局 ---
    if "final_report" in st.session_state:
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("🚩 风险审计报告")
            st.markdown(f"<div class='report-card'>{st.session_state.audit_part}</div>", unsafe_allow_html=True)
        
        with col2:
            st.subheader("📄 标准范本建议")
            st.markdown(f"<div class='report-card'>{st.session_state.tmpl_part}</div>", unsafe_allow_html=True)
        
        # 下载区域
        st.markdown("---")
        doc_bytes = export_docx(st.session_state.audit_part, st.session_state.tmpl_part)
        st.download_button(
            label="📥 下载专业版 Word 方案（含审计+范本）",
            data=doc_bytes,
            file_name=f"SafeSign审计方案_{uploaded_file.name}.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )

# --- 6. 底部固定对话框 ---
st.markdown("### 💬 法律顾问咨询")
for msg in st.session_state.chat_history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if chat_prompt := st.chat_input("您可以针对审计结果进一步追问..."):
    st.session_state.chat_history.append({"role": "user", "content": chat_prompt})
    with st.chat_message("user"):
        st.markdown(chat_prompt)
    
    with st.chat_message("assistant"):
        context = st.session_state.get("final_report", "通用法律咨询")
        ans = ai_client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "system", "content": f"基于此合同背景回答: {context}"},
                      {"role": "user", "content": chat_prompt}]
        ).choices[0].message.content
        st.markdown(ans)
        st.session_state.chat_history.append({"role": "assistant", "content": ans})
