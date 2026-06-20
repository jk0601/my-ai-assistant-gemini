# 🤖 AI 비서 챗봇 (Gemini 버전)

PDF 문서를 기반으로 질문에 답변하는 AI 챗봇입니다.  
Google Gemini API를 사용하며, Streamlit으로 웹앱을 만들고 무료로 배포합니다.

---

## 주요 기능

- **PDF 문서 기반 답변** — `docs/` 폴더의 PDF를 자동으로 읽어 AI 컨텍스트로 활용
- **멀티턴 대화** — 이전 대화 맥락을 기억하며 연속 질문 가능
- **대화 초기화** — 사이드바의 버튼으로 새 대화 시작
- **무료 배포** — Streamlit Community Cloud에서 무료 호스팅

---

## 폴더 구조

```
my-ai-assistant-gemini/
├── app.py                          # 메인 앱 (전체 코드)
├── requirements.txt                # 필요한 패키지 목록
├── .gitignore                      # API 키 등 민감 파일 제외
├── .streamlit/
│   └── secrets.toml.example       # API 키 설정 예시 파일
└── docs/
    ├── ChatGPT_사용가이드.pdf
    └── 클로드코드_사용가이드.pdf
```

---

## 로컬에서 실행하기

### 1단계: Gemini API 키 발급

1. [Google AI Studio](https://aistudio.google.com/app/apikey) 접속
2. **Create API Key** 클릭
3. 발급된 키 복사

### 2단계: API 키 설정

`.streamlit/` 폴더 안에 `secrets.toml` 파일을 새로 만들고 아래 내용 입력:

```toml
GEMINI_API_KEY = "여기에_발급받은_키_붙여넣기"
```

> ⚠️ `secrets.toml`은 `.gitignore`에 등록되어 있어 GitHub에 올라가지 않습니다.

### 3단계: 패키지 설치 및 실행

```bash
# 패키지 설치
pip install -r requirements.txt

# 앱 실행
streamlit run app.py
```

브라우저에서 `http://localhost:8501` 자동 열림

---

## GitHub에 올리기

```bash
git init
git add .
git commit -m "init: Gemini PDF 챗봇"
git remote add origin https://github.com/사용자명/my-ai-assistant-gemini.git
git push -u origin main
```

> `.gitignore` 덕분에 `secrets.toml`(API 키)은 자동으로 제외됩니다.

---

## Streamlit Cloud에 배포하기

### 1단계: 배포 연결

1. [share.streamlit.io](https://share.streamlit.io) 접속
2. **New app** 클릭
3. GitHub 저장소 선택 → Main file path: `app.py` → **Deploy**

### 2단계: API 키 등록 (중요!)

배포 후 앱 대시보드에서:

1. 앱 우측 메뉴(⋮) → **Settings**
2. **Secrets** 탭 클릭
3. 아래 내용 붙여넣기:

```toml
GEMINI_API_KEY = "여기에_실제_키_입력"
```

4. **Save** 클릭 → 앱 자동 재시작

---

## PDF 추가 방법

1. `docs/` 폴더에 PDF 파일 복사
2. GitHub에 커밋·푸시
3. Streamlit Cloud가 자동으로 최신 버전 반영

```bash
git add docs/새로운파일.pdf
git commit -m "docs: 새 PDF 추가"
git push
```

---

## 동작 원리

```
[PDF 파일] → pdfplumber로 텍스트 추출
     ↓
[Gemini system prompt] 에 PDF 전문 삽입
     ↓
사용자 질문 → Gemini API → 문서 기반 답변
```

Gemini 1.5 Flash 모델은 **100만 토큰** 컨텍스트를 지원하므로,  
수십 페이지 분량의 PDF도 통째로 전달할 수 있습니다.

---

## 트러블슈팅

| 증상 | 해결 방법 |
|------|-----------|
| `GEMINI_API_KEY가 설정되지 않았습니다` | `.streamlit/secrets.toml` 파일 생성 및 키 입력 |
| `404 Not Found` (API 오류) | API 키 오타 확인, [AI Studio](https://aistudio.google.com)에서 키 재발급 |
| PDF 텍스트가 깨짐 | 스캔 PDF(이미지 PDF)는 텍스트 추출 불가, 디지털 PDF 사용 권장 |
| 로컬에서 실행 안 됨 | `pip install -r requirements.txt` 재실행 |
| Streamlit Cloud 배포 후 오류 | 앱 Settings → Secrets에 API 키 등록 확인 |
