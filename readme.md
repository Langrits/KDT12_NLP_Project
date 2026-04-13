# 🔮 타로 하루 플래너

> "타로가 건네는 한 마디로 하루를 시작하고 마무리하다"

타로 카드 뽑기를 통해 오늘 하루를 계획하고 저녁에 회고하는
LLM + NLP 기반 하루 플래닝 서비스입니다.

---

## 👥 팀원 및 역할

| 이름 | 역할 | 담당 파일 |
|---|---|---|
| A(정유진) | 데이터 & 프롬프트 설계 | cards_original.json, cards_reversed.json, prompts.py |
| B(박원호) | LLM 파이프라인 | llm_handler.py |
| C(이현아) | NLP 모델 | nlp_handler.py |
| D(문종필 | UI & 발표 | ui |
---

## 🛠 기술 스택

| 구분 | 사용 기술 |
|---|---|
| LLM | OpenAI GPT-4o-mini (GitHub Models) / Gemini(gemini-3.1-flash-lite-preview) |
| NLP — 키워드 추출, 감성 분석 | MiniLM + KeyBERT + DistilBERT + Okt (형태소 분석) |
| UI | FastAPI, Nest.js, Railway, Vercel, Supabase |
| 언어 | Python 3.10+ |

---

## ⚙️ 설치 및 실행

### 1. 패키지 설치

```bash
pip install -r requirements.txt
```

### 2. GPU 버전 PyTorch (선택)

```bash
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu128
```

### 3. 환경변수 설정

프로젝트 루트에 아래 파일 생성 (Git에 올리지 않음)

```
# GITHUB_TOKEN.env
GITHUB_TOKEN=your_github_token_here

# GEMINI_API_KEY.env
GEMINI_API_KEY=your_gemini_api_key_here
```

### 4. 실행

**터미널 테스트 (OpenAI)**
```bash
python test_gpt_terminal.py
```

**터미널 테스트 (Gemini)**
```bash
python test_gemini_terminal.py
```

**Streamlit UI 실행**
```
(미완성)
```

---

## 📁 프로젝트 구조

```
KDT12_NLP_Project/
├── llm_handler.py            # LLM 호출 (OpenAI)
├── llm_handler_gemini.py     # LLM 호출 (Gemini)
├── nlp_handler.py            # NLP 모델
├── prompts.py                # 프롬프트 템플릿
├── terminal_test_gpt_terminal.py          # 터미널 테스트 (OpenAI)
├── terminal_test_gemini_terminal.py   # 터미널 테스트 (Gemini)
├── cards_original.json   # 메이저 아르카나 22장 (정방향)
├── cards_original.json   # 메이저 아르카나 22장 (역방향)
├── requirements.txt
└── .gitignore
```

---

## 🔮 서비스 흐름

### 아침 플래닝
```
카드 3장 선택 (정/역방향 랜덤)
      ↓
NLP 전처리 (KeyBERT + 감성분석)
      ↓
LLM 운세 생성 (과거-현재-미래 해석)
      ↓
컨디션 입력
      ↓
할 일 입력
      ↓
LLM 맞춤 조언 생성
      ↓
할 일 확정
```

### 저녁 회고
```
완료한 할 일 체크
      ↓
LLM 회고 생성 (카드 재해석 + 총평)
```

---

## 📊 NLP-LLM 파이프라인

```
카드 의미 텍스트
      ↓
[NLP 전처리]
키워드 추출 + 감성 분석
      ↓ 결과 주입
[LLM 생성]
운세 / 조언 / 회고
```

---

## ⚠️ 주의사항

- 각자 본인 API 키를 발급받아 사용하세요
- GPU 없으면 CPU로도 실행 가능합니다