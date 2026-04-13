# 타로 데이플래너 앱 — 설계 명세서

**날짜**: 2026-04-12  
**상태**: 승인됨

---

## 1. 개요

타로 카드를 활용한 모바일 데이플래너 앱. 매일 아침 카드 3장을 뽑아 운세를 확인하고, 오늘의 할 일과 조언을 받으며, 저녁에 하루를 회고한다. 날짜별 기록은 Supabase에 영구 저장된다.

---

## 2. 전체 아키텍처

```
[사용자 브라우저]
      ↕ HTTPS
[Next.js — Vercel]          ← 6개 화면 (모바일 뷰)
      ↕ REST API (JSON)
[FastAPI — Railway]         ← NLP 분석 + LLM 운세/조언/회고 생성
      ↕ Supabase Client
[Supabase PostgreSQL]       ← 날짜별 기록 영구 저장
```

| 서비스 | 역할 | 배포 플랫폼 |
|--------|------|-------------|
| Next.js (TypeScript, Tailwind) | UI, 라우팅, 상태관리 | Vercel (무료) |
| FastAPI (Python) | 카드 추첨, NLP, LLM 호출, DB 저장 | Railway |
| Supabase PostgreSQL | 날짜별 기록 저장/조회 | Supabase (무료) |

---

## 3. FastAPI 백엔드

### 3-1. 프로젝트 구조

```
KDT12_NLP_Project/
├── main.py                  ← FastAPI 앱 진입점, CORS 설정
├── routers/
│   ├── cards.py             ← /cards/draw
│   ├── fortune.py           ← /fortune
│   ├── advice.py            ← /advice
│   ├── retrospective.py     ← /retrospective
│   └── records.py           ← /records (저장/조회)
├── nlp_handler.py           ← 기존 KeyBERT + 감성 분석
├── llm_handler.py           ← 기존 GPT-4o-mini 호출
├── prompts.py               ← 기존 프롬프트 정의
├── cards_original.json
├── cards_reversed.json
├── card_img/
└── requirements.txt
```

### 3-2. API 엔드포인트

| Method | Path | 요청 Body | 응답 |
|--------|------|-----------|------|
| `POST` | `/cards/draw` | `{}` | `{cards: [{id, name, reversed, direction, meaning}]}` |
| `POST` | `/fortune` | `{cards}` | `{summary, fortune, nlp_result}` |
| `POST` | `/advice` | `{cards, condition, tasks, nlp_result}` | `{summary, advice}` |
| `POST` | `/retrospective` | `{cards, completed_tasks, incomplete_tasks, nlp_result}` | `{summary, retrospective}` |
| `POST` | `/records` | 하루 전체 데이터 (아래 스키마 참조) | `{id, date}` |
| `GET` | `/records?year=&month=` | — | `[{date, cards, summary, sentiment_label, ...}]` |
| `GET` | `/records/{date}` | — | 특정 날짜 전체 기록 (`date` 형식: `YYYY-MM-DD`) |

### 3-3. CORS 미들웨어 설정

`main.py`에 아래와 같이 설정한다. 개발 중에는 `*`, 프로덕션에서는 Vercel 도메인만 허용한다.

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

app = FastAPI()

_raw = os.getenv("ALLOWED_ORIGINS", "")
ALLOWED_ORIGINS = _raw.split(",") if _raw else ["*"]

# 주의: allow_origins=["*"] 일 때 allow_credentials=True 는 Starlette 오류를 유발한다.
# 개발 환경(origins=["*"])에서는 credentials=False, 프로덕션(특정 도메인)에서는 True.
_credentials = "*" not in ALLOWED_ORIGINS

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=_credentials,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
```

**환경변수 설정 예시:**

| 환경 | `ALLOWED_ORIGINS` 값 | `allow_credentials` 결과 |
|------|----------------------|--------------------------|
| 로컬 개발 | (미설정) | `["*"]` → `False` |
| 프로덕션 | `https://tarot.vercel.app` | `["https://tarot.vercel.app"]` → `True` |

---

## 4. Supabase DB 스키마

```sql
CREATE TABLE daily_records (
  id                uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
  date              date        NOT NULL UNIQUE,
  cards             jsonb       NOT NULL,
  -- cards 형식: [{id, name, reversed, direction}]
  nlp_result        jsonb,
  -- nlp_result 형식: {keywords: string[], sentiment_score: float, sentiment_label: string}
  fortune           text,
  summary           text,           -- 운세 한 줄 요약
  condition         text,           -- '최고' | '좋음' | '보통' | '나쁨'
  tasks             text[],         -- 오늘 할 일 목록
  advice            text,
  advice_summary    text,           -- 조언 한 줄 요약
  completed_tasks   text[],
  incomplete_tasks  text[],
  retrospective     text,
  retro_summary     text,           -- 회고 한 줄 요약
  created_at        timestamptz DEFAULT now()
);
```

---

## 5. Next.js 프론트엔드

### 5-1. 화면 구조 (App Router)

| Route | 화면 | 설명 |
|-------|------|------|
| `/` | 홈 | 날짜 표시, 오늘의 운세 보기 / 카드 뽑기 진입 |
| `/draw` | 카드 뽑기 | 3장 카드 선택 (과거/현재/미래), 셔플 |
| `/fortune` | 운세 결과 | 카드 + 감성 배지 + 운세 텍스트, 할 일 계획으로 이동 |
| `/plan` | 할 일 & 조언 | 컨디션 선택, 할 일 입력, 조언 생성 |
| `/retrospective` | 회고 | 완료/미완료 체크, AI 회고 생성 |
| `/history` | 나의 타로 기록 | 월별 히스토리, 필터(전체/운세/계획/회고), 통계 |

### 5-2. 상태관리 (Zustand)

하루치 세션 데이터를 화면 간 공유한다. 앱 재시작 시 오늘 날짜 기록이 Supabase에 있으면 불러온다.

```typescript
interface DailyStore {
  date: string;                    // 'YYYY-MM-DD'
  cards: Card[];                   // 뽑은 카드 3장
  nlpResult: NlpResult | null;
  fortune: string;
  summary: string;
  condition: Condition | null;     // '최고'|'좋음'|'보통'|'나쁨'
  tasks: string[];
  advice: string;
  completedTasks: string[];
  incompleteTasks: string[];
  retrospective: string;
}
```

### 5-3. 카드 이미지 서빙

`card_img/` 폴더의 이미지는 FastAPI에서 정적 파일로 서빙한다.

```python
from fastapi.staticfiles import StaticFiles
app.mount("/card_img", StaticFiles(directory="card_img"), name="card_img")
```

프론트엔드에서 카드 이미지 URL: `{NEXT_PUBLIC_API_URL}/card_img/{카드번호}.%20{카드이름}%20카드.jpg`  
(파일명에 공백이 포함되므로 URL 인코딩 필요. 실제로는 FastAPI가 `/cards/draw` 응답에 `image_url` 필드를 포함해 프론트에 전달한다.)

---

## 6. 환경변수

### Railway (FastAPI 서버)

| 변수명 | 설명 | 예시 |
|--------|------|------|
| `GITHUB_TOKEN` | GitHub Models API 키 (GPT-4o-mini) | `ghp_xxxx` |
| `SUPABASE_URL` | Supabase 프로젝트 URL | `https://xxxx.supabase.co` |
| `SUPABASE_SERVICE_ROLE_KEY` | Supabase service role 키 (DB 쓰기용) | `eyJxxx` |
| `ALLOWED_ORIGINS` | CORS 허용 오리진 (쉼표 구분) | `https://tarot.vercel.app` |

### Vercel (Next.js 프론트엔드)

| 변수명 | 설명 | 예시 |
|--------|------|------|
| `NEXT_PUBLIC_API_URL` | FastAPI 서버 URL | `https://tarot-api.railway.app` |
| `NEXT_PUBLIC_SUPABASE_URL` | Supabase 프로젝트 URL | `https://xxxx.supabase.co` |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Supabase anon 키 (읽기용) | `eyJxxx` |

> **보안 참고**: Supabase 쓰기(INSERT/UPDATE)는 FastAPI 서버에서 `SERVICE_ROLE_KEY`로 수행한다. 프론트엔드에 노출되는 `ANON_KEY`는 읽기 전용 RLS 정책과 함께 사용한다.

---

## 7. 데이터 흐름 요약

```
1. 홈 화면 진입
   └─ GET /records/{오늘날짜} → 오늘 기록 있으면 결과 화면으로 이동

2. 카드 뽑기
   └─ POST /cards/draw → 카드 3장 반환 → Zustand 저장

3. 운세 생성
   └─ POST /fortune (cards) → NLP 분석 → LLM → {summary, fortune, nlp_result}

4. 할 일 & 조언
   └─ POST /advice (cards, condition, tasks, nlp_result) → {summary, advice}

5. 회고
   └─ POST /retrospective (cards, completed/incomplete, nlp_result) → {summary, retrospective}
   └─ POST /records → Supabase 저장

6. 기록 조회
   └─ GET /records?year=&month= → 월별 목록
```

---

## 8. 범위 외 (이번 구현에 포함하지 않음)

- 사용자 인증 / 로그인
- 푸시 알림
- 카드 의미 상세 설명 팝업
- 다국어 지원
