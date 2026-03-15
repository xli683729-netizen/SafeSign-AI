import streamlit as st
from supabase import create_client
import openai
import pdfplumber
from docx import Document
from io import BytesIO

# --- 1. 商业视觉与核心配置 (稳定版) ---
st.set_page_config(
    page_title="SafeSign Pro | 法律合同智能审计",
    page_icon="⚖️",
    layout="wide"
)

# 修正样式的 HTML 注入
st.markdown("""
    <style>
    .report-box { 
        padding: 20px; border-radius: 8px; border: 1px solid #e6e9ef; 
        background-color: #ffffff; color: #2c3e50; line-height: 1.6;
    }
    .stButton>button { background-color: #1f2937; color: white; border-radius: 5px; }
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

# --- 2. 增强型文档解析 (解决 PDF 读取问题) ---
def extract_text(file):
    text = ""
    try:
        if file.type == "application/pdf":
            with pdfplumber.open(file) as pdf:
                # 增强：逐页提取，并过滤掉空行
                pages_text = [p.extract_text() for p in pdf.pages if p.extract_text()]
                text = "\n".join(pages_text)
        elif file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            doc = Document(file)
            text = "\n".join([p.text for p in doc.paragraphs])
        return text
    except Exception as e:
        return f"解析出错: {e}"

# --- 3. Word (.docx) 生成引擎 ---
def create_word_docx(report_content, template_content):
    doc = Document()
    doc.add_heading('SafeSign Pro 法律合规报告', 0)
    
    doc.add_heading('第一部分：合同风险审计报告', level=1)
    doc.add_paragraph(report_content)
    
    doc.add_page_break()
    
    doc.add_heading('第二部分：标准化合同范本（留白变量版）', level=1)
    doc.add_paragraph("注：[ ] 中内容请根据实际业务填写。")
    doc.add_paragraph(template_content)
    
    bio = BytesIO()
    doc.save(bio)
    return bio.getvalue()

# --- 4. 中国法律审计逻辑 ---
def run_chinese_legal_engine(content):
    # 任务 1：基于中国法律的深度审计
    audit_p = f"""
    你是一名中国执业律师，请依据《中华人民共和国民法典》对以下合同进行风险审计。
    请指出：
    1. 显失公平的条款（如过高的违约金、单方解除权）。
    2. 缺失的法定条款（如管辖法院、不可抗力、送达地址）。
    3. 潜在法律漏洞。
    合同内容: {content[:5000]}
    """
    # 任务 2：生成对应的标准留白范本
    template_p = f"""
    请根据上述合同的业务意图，重新起草一份标准的中国商事合同范本。
    要求：
    1. 结构严谨，包含完整的声明与保证、违约责任、争议解决条款。
    2. 将所有变量（如甲方名称、身份证号、金额、日期）用 [ ] 留白。
    3. 语言专业、地道，符合中国法律书写规范。
    原合同意图参考: {content[:3000]}
    """
    try:
        audit_res = ai_client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "system", "content": "你是一位精通中国民法典的资深法务专家。"},
                      {"role": "user", "content": audit_p}]
        ).choices[0].message.content

        template_res = ai_client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": template_p}]
        ).choices[0].message.content
        return audit_res, template_res
    except Exception as e:
        return f"AI 服务异常: {e}", ""

# --- 5. 交互界面 ---
with st.sidebar:
    st.title("🛡️ SafeSign Pro")
    st.caption("中国通用法律合同审计插件")
    st.markdown("---")
    email = st.text_input("会员中心 (输入邮箱登记):", placeholder="yourname@example.com")
    if True:
        try:
            supabase.table("users").upsert({"email": email, "expire_date": "2030-01-01"}).execute()
            st.success("✅ 授权成功：专业版已激活")
        except:
            st.info("单机预览模式已开启")

st.title("⚖️ SafeSign Pro：企业级合同智能审计引擎")
st.info("支持 PDF 与 Word 格式。系统将自动识别风险并为您生成标准的法律模版。")

uploaded_file = st.file_uploader("上传待审核合同", type=["pdf", "docx"])

if uploaded_file:
    with st.spinner("⚖️ 法律引擎正在扫描条款..."):
        full_text = extract_text(uploaded_file)
        
        if len(full_text) > 20:
            report, template = run_chinese_legal_engine(full_text)
            
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("🚩 风险审计报告")
                st.markdown(f"<div class='report-box'>{report}</div>", unsafe_allow_html=True)
            with col2:
                st.subheader("📄 标准合同范本 (留白版)")
                st.markdown(f"<div class='report-box'>{template}</div>", unsafe_allow_html=True)
                
            st.markdown("---")
            if email:
                # 生成 Word 文件供下载
                word_file = create_word_docx(report, template)
                st.download_button(
                    label="📥 下载专业版 Word 文档 (含报告与范本)",
                    data=word_file,
                    file_name=f"SafeSign_Pro_审计方案_{uploaded_file.name}.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                )
        else:
            st.error("未能识别合同文字，请确保 PDF 是电子版而非模糊的照片。")

st.markdown("---")
st.caption("© 2026 SafeSign 中国区法律科技中心 | 本结果由 AI 生成，仅供参考，不构成法律意见。")
