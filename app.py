import streamlit as st
import openai
import pdfplumber
from docx import Document
from io import BytesIO
import time

# --- 1. 商业级页面配置 ---
st.set_page_config(page_title="SafeSign Pro", layout="wide", page_icon="⚖️")

# 注入 CSS：固化 UI 布局，确保左右分栏高度一致
st.markdown("""
    <style>
    .report-card { 
        padding: 20px; border-radius: 10px; border: 1px solid #e0e0e0; 
        background-color: #ffffff; height: 620px; overflow-y: auto; 
        font-size: 15px; line-height: 1.6;
    }
    .stChatInputContainer { padding-bottom: 20px; }
    .u-line { text-decoration: underline; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 核心状态初始化 ---
# 默认开启所有功能，取消会员锁定逻辑
if "audit_res" not in st.session_state: st.session_state.audit_res = "🚩 风险审计报告将在此显示..."
if "tmpl_res" not in st.session_state: st.session_state.tmpl_res = "📄 标准合同范本将在此生成..."

@st.cache_resource
def init_ai():
    # 请确保在 Streamlit 控制台或 secrets.toml 中配置了 API Key
    return openai.OpenAI(
        api_key=st.secrets["DEEPSEEK_API_KEY"], 
        base_url="https://api.deepseek.com"
    )

ai_client = init_ai()

# --- 3. 极速文档解析引擎 ---
def fast_extract(file):
    try:
        if file.type == "application/pdf":
            with pdfplumber.open(file) as pdf:
                # 仅解析核心条款（前15页），确保极速响应
                return "\n".join([p.extract_text() for p in pdf.pages[:15] if p.extract_text()])
        elif file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            return "\n".join([p.text for p in Document(file).paragraphs])
        return ""
    except Exception as e:
        return f"解析失败: {e}"

# --- 4. 侧边栏：品牌与工具栏 ---
with st.sidebar:
    st.title("🛡️ SafeSign Pro")
    st.caption("中国法律合同智能审计专家")
    st.markdown("---")
    st.success("✨ 当前状态：尊享全功能版")
    st.write("• 支持多格式合同审计")
    st.write("• 支持全行业范本起草")
    st.write("• 支持 Word 方案一键导出")
    st.markdown("---")
    st.info("💡 提示：本工具基于《中华人民共和国民法典》标准提供建议。")

# --- 5. 主界面：经典的左右 1:1 分栏 ---
st.title("⚖️ 企业级合同智能审计引擎")

col1, col2 = st.columns(2)
with col1:
    st.subheader("🚩 风险审计结果")
    st.markdown(f"<div class='report-card'>{st.session_state.audit_res}</div>", unsafe_allow_html=True)

with col2:
    st.subheader("📄 法律范本建议")
    st.markdown(f"<div class='report-card'>{st.session_state.tmpl_res}</div>", unsafe_allow_html=True)

# --- 6. 交互逻辑区 ---
st.markdown("---")
uploaded_file = st.file_uploader("📂 上传合同进行扫描 (PDF/Word)", type=["pdf", "docx"])

# 对话框逻辑：支持起草指令和追问
if chat_prompt := st.chat_input("输入指令（例如：‘起草一份标准劳动合同’）或针对审计结果追问..."):
    with st.spinner("AI 律师正在处理指令..."):
        # 场景 A: 指令起草
        if any(keyword in chat_prompt for keyword in ["写一份", "起草", "制作", "合同模板"]):
            p = f"你是一名资深中国律师。请直接起草一份符合法律规范的【{chat_prompt}】标准范本。要求：条款清晰，变量处用 [ ] 留白。直接输出范本内容。"
            res = ai_client.chat.completions.create(model="deepseek-chat", messages=[{"role": "user", "content": p}]).choices[0].message.content
            st.session_state.tmpl_res = res
            st.session_state.audit_res = f"✅ 已根据指令‘{chat_prompt}’生成范本。\n\n**建议提示**：在使用该范本前，请根据实际业务背景补充 [ ] 中的具体信息。"
        
        # 场景 B: 审计追问
        else:
            p = f"上下文背景: {st.session_state.audit_res}\n用户追问: {chat_prompt}\n请作为专业律师给出详细解答。"
            res = ai_client.chat.completions.create(model="deepseek-chat", messages=[{"role": "user", "content": p}]).choices[0].message.content
            st.session_state.audit_res = res
    st.rerun()

# 文件上传审计逻辑
if uploaded_file and st.session_state.audit_res.startswith("🚩"):
    with st.spinner("🔍 正在为您进行深度法律扫描..."):
        content = fast_extract(uploaded_file)
        # 强制标签化输出，确保内容精准落位
        p = f"你是中国资深律师。请审计以下合同内容并提供优化后的范本。格式要求：[AUDIT]在这里写详细审计建议[/AUDIT] [TMPL]在这里写标准合同范本[/TMPL]。内容：{content[:4000]}"
        full_res = ai_client.chat.completions.create(model="deepseek-chat", messages=[{"role": "user", "content": p}]).choices[0].message.content
        
        try:
            st.session_state.audit_res = full_res.split("[AUDIT]")[1].split("[/AUDIT]")[0].strip()
            st.session_state.tmpl_res = full_res.split("[TMPL]")[1].split("[/TMPL]")[0].strip()
        except:
            st.session_state.audit_res = "解析格式异常，请稍后重试。"
        st.rerun()

# --- 7. Word 导出功能 (全员开放) ---
if st.session_state.tmpl_res != "📄 标准范本将在此生成...":
    st.markdown("---")
    doc = Document()
    doc.add_heading('SafeSign Pro 法律服务报告', 0)
    doc.add_heading('一、合同风险审计建议', level=1); doc.add_paragraph(st.session_state.audit_res)
    doc.add_heading('二、标准合规合同范本', level=1); doc.add_paragraph(st.session_state.tmpl_res)
    bio = BytesIO()
    doc.save(bio)
    
    st.download_button(
        label="📥 下载 Word 专业版方案 (已免费开放)",
        data=bio.getvalue(),
        file_name="SafeSign_Legal_Report.docx",
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )
