# app.py
# Gemini API + PDF 기반 AI 챗봇
# PDF에서 텍스트를 추출해 Gemini에게 컨텍스트로 전달하고, 멀티턴 대화를 지원합니다.

import glob
import os

import google.generativeai as genai
import pdfplumber
import streamlit as st
from dotenv import load_dotenv

# 로컬 개발: .env 파일에서 환경변수 로드 (파일 없으면 무시)
load_dotenv()

# ── 페이지 기본 설정 ────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AI 비서 챗봇",
    page_icon="🤖",
    layout="centered",
    initial_sidebar_state="expanded",
)

# ── CSS: 채팅 입력창을 항상 하단에 고정 ────────────────────────────────────
st.markdown("""
<style>
/* 어시스턴트 말풍선 배경색 */
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) {
    background-color: #f0f4ff;
    border-radius: 12px;
    padding: 4px 8px;
}
</style>
""", unsafe_allow_html=True)


# ── 1. API 키 로드 ──────────────────────────────────────────────────────────
# 우선순위: .env 환경변수 → Streamlit Cloud Secrets
# 로컬:  .env 파일에 GEMINI_API_KEY=your-key 입력 (위 load_dotenv()가 읽어줌)
# 배포:  Streamlit Cloud 앱 설정 → Secrets 탭에 GEMINI_API_KEY = "your-key" 입력
api_key = os.environ.get("GEMINI_API_KEY") or st.secrets.get("GEMINI_API_KEY", "")

if not api_key:
    st.error("⚠️ GEMINI_API_KEY가 설정되지 않았습니다.")
    st.info("`.env` 파일에 `GEMINI_API_KEY=발급받은키` 를 추가하세요. (.env.example 참고)")
    st.stop()

genai.configure(api_key=api_key)


# ── 2. PDF 텍스트 추출 ──────────────────────────────────────────────────────
# @st.cache_resource : 앱이 실행되는 동안 한 번만 추출하고 재사용 (속도 최적화)
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
                # 각 페이지 텍스트를 이어 붙임 (추출 실패 페이지는 빈 문자열)
                pages = "\n".join(page.extract_text() or "" for page in pdf.pages)
            full_text += f"\n\n===== 📄 문서: {name} =====\n{pages}"
        except Exception as e:
            full_text += f"\n\n===== 📄 문서: {name} (읽기 실패: {e}) =====\n"

    return full_text.strip(), names


doc_text, doc_names = load_pdf_context()


# ── 3. Gemini 모델 초기화 ───────────────────────────────────────────────────
# system_instruction: 모델의 역할과 참고 문서를 설정하는 시스템 프롬프트
# PDF 전문을 컨텍스트로 넣어 문서 기반 답변을 유도합니다.
SYSTEM_PROMPT = f"""당신은 AI 도구 사용법을 친절하게 안내하는 AI 비서입니다.

[역할]
- 아래 제공된 문서를 근거로 사용자 질문에 한국어로 답변합니다.
- 문서에 없는 내용은 "제공된 문서에는 해당 내용이 없습니다"라고 솔직하게 말합니다.
- 답변은 간결하고 이해하기 쉽게 작성합니다. 필요 시 번호 목록을 활용하세요.

[참고 문서]
{doc_text if doc_text else "문서를 찾을 수 없습니다. docs/ 폴더에 PDF 파일을 넣어주세요."}
"""


@st.cache_resource
def get_model():
    """Gemini 모델 객체를 캐싱하여 재사용합니다."""
    return genai.GenerativeModel(
        model_name="gemini-1.5-flash",   # 무료 티어 지원
        system_instruction=SYSTEM_PROMPT,
    )


model = get_model()


# ── 4. 세션 상태 초기화 ─────────────────────────────────────────────────────
# st.session_state: 브라우저 탭이 유지되는 동안 값을 보존하는 저장소
if "chat" not in st.session_state:
    st.session_state.chat = model.start_chat(history=[])   # Gemini 대화 세션
if "messages" not in st.session_state:
    st.session_state.messages = []   # UI에 표시할 메시지 목록


# ── 5. 사이드바 ─────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("📚 참고 문서")
    if doc_names:
        for name in doc_names:
            st.success(f"✅ {name}")
    else:
        st.warning("docs/ 폴더에 PDF가 없습니다.")

    st.divider()

    # 대화 초기화 버튼
    if st.button("🔄 대화 초기화", use_container_width=True):
        st.session_state.chat = model.start_chat(history=[])
        st.session_state.messages = []
        st.rerun()

    st.divider()
    st.caption("**모델:** gemini-1.5-flash")
    st.caption("**배포:** Streamlit Cloud")
    st.caption("**API:** Google Gemini (무료 티어)")


# ── 6. 메인 채팅 UI ─────────────────────────────────────────────────────────
st.title("🤖 AI 비서 챗봇")
st.caption("ChatGPT · Claude Code 사용법을 질문하세요. 문서를 기반으로 답변합니다.")

# 첫 방문 시 안내 메시지
if not st.session_state.messages:
    with st.chat_message("assistant"):
        st.write(
            "안녕하세요! 👋\n\n"
            "저는 AI 도구 사용법을 안내하는 AI 비서입니다.\n"
            "ChatGPT나 Claude Code 사용 방법, 프롬프트 작성법 등을 질문해보세요!"
        )

# 이전 대화 기록 표시
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# 채팅 입력창 (엔터 또는 전송 버튼으로 제출)
if prompt := st.chat_input("질문을 입력하세요..."):

    # 사용자 메시지 표시 및 저장
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    # Gemini API 호출 및 응답 표시
    with st.chat_message("assistant"):
        with st.spinner("답변을 생성하고 있습니다..."):
            try:
                response = st.session_state.chat.send_message(prompt)
                answer = response.text
            except Exception as e:
                answer = f"⚠️ 오류가 발생했습니다: {e}\n\nAPI 키를 확인하거나 잠시 후 다시 시도하세요."

        st.write(answer)

    # 어시스턴트 응답 저장
    st.session_state.messages.append({"role": "assistant", "content": answer})
