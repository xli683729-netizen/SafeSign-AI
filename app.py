import streamlit as st
import openai
from PIL import Image
import pdfplumber
import easyocr
import numpy as np

# 1. 页面基础配置
st.set_page_config(page_title="SafeSign AI Pro", layout="wide", page_icon="🛡️")

# 2. 连接 DeepSeek 大脑
client = openai.OpenAI(
    api_key=st.secrets["DEEPSEEK_API_KEY"], 
    base_url="https://api.deepseek.com"
)

# 3. 侧边栏
with st.sidebar:
    st.title("🛡️ SafeSign AI")
    st.subheader("Global Compliance Suite")
    mode = st.selectbox("Audit Protocol", ["General Commercial", "Influencer/Model", "Employment"])
    st.divider()
    st.caption("© 2026 SafeSign AI. v6.0 Pro")

# 4. 主界面
st.title("AI Contract Audit Dashboard")
st.warning("ATTENTION: This is an AI-powered analytical tool for informational purposes only.")

# 5. 上传区：支持拍照和PDF
uploaded_file = st.file_uploader("Upload Document (PDF or Camera Scan)", type=['png', 'jpg', 'jpeg', 'pdf'])

if st.button("🚀 Run AI Risk Audit"):
    if uploaded_file:
        with st.spinner("Decoding document & Analyzing legal risks..."):
            try:
                extracted_text = ""
                # A部分：图片识别 (针对手机拍照)
                if uploaded_file.type in ["image/png", "image/jpeg", "image/jpg"]:
                    image = Image.open(uploaded_file)
                    reader = easyocr.Reader(['en']) # 识别英文
                    # 将图片转为数组并识别
                    results = reader.readtext(np.array(image))
                    extracted_text = " ".join([res[1] for res in results])
                
                # B部分：PDF提取
                elif uploaded_file.type == "application/pdf":
                    with pdfplumber.open(uploaded_file) as pdf:
                        extracted_text = "\n".join([page.extract_text() for page in pdf.pages if page.extract_text()])

                # C部分：AI 法律审计
                if not extracted_text.strip():
                    st.error("Error: Could not extract text. Please ensure the photo is clear.")
                else:
                    prompt = f"Audit this {mode} contract and list: 1. Risk Score 2. Red Flags 3. Suggested Revisions. Text: {extracted_text}"
                    response = client.chat.completions.create(
                        model="deepseek-chat",
                        messages=[{"role": "system", "content": "You are a professional legal auditor."},
                                 {"role": "user", "content": prompt}],
                        temperature=0.2
                    )
                    st.success("✅ Audit Complete")
                    st.markdown(response.choices[0].message.content)
            except Exception as e:
                st.error(f"System Error: {str(e)}")
    else:
        st.info("Please upload a file or take a photo first.")
