# app.py
# Gemini API + PDF 기반 AI 챗봇
# PDF에서 텍스트를 추출해 Gemini에게 컨텍스트로 전달하고, 멀티턴 대화를 지원합니다.

import glob
import logging
import os

import pdfplumber
import streamlit as st
from dotenv import load_dotenv
from google import genai
from google.genai import types

# pdfminer이 한국어 폰트 파싱 시 출력하는 FontBBox 경고 억제 (기능에 영향 없음)
logging.getLogger("pdfminer").setLevel(logging.ERROR)

# 로컬 개발: .env 파일에서 환경변수 로드 (파일 없으면 무시)
load_dotenv()

# ── 페이지 기본 설정 ────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AI 비서 챗봇",
    page_icon="🤖",
    layout="centered",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) {
    background-color: #f0f4ff;
    border-radius: 12px;
    padding: 4px 8px;
}
</style>
""", unsafe_allow_html=True)


# ── 1. API 키 로드 ──────────────────────────────────────────────────────────
# 우선순위: .env 환경변수 → Streamlit Cloud Secrets
# 로컬:  .env 파일에 GEMINI_API_KEY=your-key 입력
# 배포:  Streamlit Cloud 앱 설정 → Secrets 탭에 GEMINI_API_KEY = "your-key" 입력
api_key = os.environ.get("GEMINI_API_KEY") or st.secrets.get("GEMINI_API_KEY", "")

if not api_key:
    st.error("⚠️ GEMINI_API_KEY가 설정되지 않았습니다.")
    st.info("`.env` 파일에 `GEMINI_API_KEY=발급받은키` 를 추가하세요. (.env.example 참고)")
    st.stop()


# ── 2. PDF 텍스트 추출 ──────────────────────────────────────────────────────
@st.cache_resource
def load_pdf_context() -> tuple[str, list[str]]:
    """
    docs/ 폴더의 PDF 파일을 모두 읽어 하나의 텍스트로 합칩니다.
    반환값: (전체_텍스트, 파일명_목록)
    """
    pdf_paths = sorted(glob.glob(os.path.join("docs", "*.pdf")))
    if not pdf_paths:
        return "", []

    full_text = ""
    names = []
    for path in pdf_paths:
        name = os.path.basename(path)
        names.append(name)
        try:
            with pdfplumber.open(path) as pdf:
                pages = "\n".join(page.extract_text() or "" for page in pdf.pages)
            full_text += f"\n\n===== 📄 문서: {name} =====\n{pages}"
        except Exception as e:
            full_text += f"\n\n===== 📄 문서: {name} (읽기 실패: {e}) =====\n"

    return full_text.strip(), names


doc_text, doc_names = load_pdf_context()


# ── 3. Gemini 클라이언트 초기화 (google-genai SDK) ─────────────────────────
SYSTEM_PROMPT = f"""당신은 AI 도구 사용법을 친절하게 안내하는 AI 비서입니다.

[역할]
- 아래 제공된 문서를 근거로 사용자 질문에 한국어로 답변합니다.
- 문서에 없는 내용은 "제공된 문서에는 해당 내용이 없습니다"라고 솔직하게 말합니다.
- 답변은 간결하고 이해하기 쉽게 작성합니다. 필요 시 번호 목록을 활용하세요.

[참고 문서]
{doc_text if doc_text else "문서를 찾을 수 없습니다. docs/ 폴더에 PDF 파일을 넣어주세요."}
"""


@st.cache_resource
def get_client(key: str) -> genai.Client:
    """Gemini 클라이언트를 캐싱하여 재사용합니다."""
    return genai.Client(api_key=key)


client = get_client(api_key)


# ── 4. 세션 상태 초기화 ─────────────────────────────────────────────────────
def new_chat():
    """새 대화 세션을 만듭니다."""
    st.session_state.chat = client.chats.create(
        model="gemini-2.5-flash",
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
        ),
    )
    st.session_state.messages = []


if "chat" not in st.session_state:
    new_chat()


# ── 5. 사이드바 ─────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("📚 참고 문서")
    if doc_names:
        for name in doc_names:
            st.success(f"✅ {name}")
    else:
        st.warning("docs/ 폴더에 PDF가 없습니다.")

    st.divider()

    if st.button("🔄 대화 초기화", use_container_width=True):
        new_chat()
        st.rerun()

    st.divider()
    st.caption("**모델:** gemini-2.5-flash")
    st.caption("**배포:** Streamlit Cloud")
    st.caption("**API:** Google Gemini (무료 티어)")


# ── 6. 메인 채팅 UI ─────────────────────────────────────────────────────────
st.title("🤖 AI 비서 챗봇")
st.caption("ChatGPT · Claude Code 사용법을 질문하세요. 문서를 기반으로 답변합니다.")

if not st.session_state.messages:
    with st.chat_message("assistant"):
        st.write(
            "안녕하세요! 👋\n\n"
            "저는 AI 도구 사용법을 안내하는 AI 비서입니다.\n"
            "ChatGPT나 Claude Code 사용 방법, 프롬프트 작성법 등을 질문해보세요!"
        )

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

if prompt := st.chat_input("질문을 입력하세요..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    with st.chat_message("assistant"):
        with st.spinner("답변을 생성하고 있습니다..."):
            try:
                response = st.session_state.chat.send_message(prompt)
                answer = response.text
            except Exception as e:
                answer = f"⚠️ 오류가 발생했습니다: {e}\n\nAPI 키를 확인하거나 잠시 후 다시 시도하세요."
        st.write(answer)

    st.session_state.messages.append({"role": "assistant", "content": answer})
