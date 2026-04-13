# 타로 데이플래너 구현 플랜

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** FastAPI 백엔드 + Next.js 모바일 프론트엔드로 타로 데이플래너 앱을 완성하고 Railway/Vercel에 배포 가능한 상태로 만든다.

**Architecture:** FastAPI(Railway)가 카드 추첨·NLP 분석·LLM 호출·Supabase 저장을 담당하고, Next.js(Vercel)가 6개 모바일 화면을 제공한다. 하루치 상태는 Zustand로 관리하고, 날짜별 기록은 Supabase PostgreSQL에 영구 저장된다.

**Tech Stack:** Python 3.11, FastAPI 0.115, uvicorn, supabase-py 2.x, pytest + httpx · Next.js 16 (App Router), TypeScript, Tailwind v4, Zustand, @supabase/supabase-js, shadcn/ui (radix-ui)

---

## 파일 맵

### 백엔드 (신규 생성)
```
KDT12_NLP_Project/
├── main.py                    ← FastAPI 앱, CORS, 라우터 등록, 정적 파일 마운트
├── db.py                      ← Supabase 클라이언트 싱글턴
├── routers/
│   ├── __init__.py
│   ├── cards.py               ← POST /cards/draw
│   ├── fortune.py             ← POST /fortune
│   ├── advice.py              ← POST /advice
│   ├── retrospective.py       ← POST /retrospective
│   └── records.py             ← POST /records, GET /records, GET /records/{date}
├── tests/
│   ├── __init__.py
│   ├── conftest.py            ← TestClient fixture, NLP/LLM mock patch
│   ├── test_cards.py
│   ├── test_fortune.py
│   ├── test_advice.py
│   ├── test_retrospective.py
│   └── test_records.py
├── requirements.txt           ← 기존 파일에 추가
└── Procfile                   ← Railway 배포용
```

### 프론트엔드 (신규/수정)
```
frontend/src/
├── app/
│   ├── globals.css            ← 수정: 다크 퍼플 테마 변수 추가
│   ├── layout.tsx             ← 수정: 모바일 뷰포트, 폰트
│   ├── page.tsx               ← 수정: 홈 화면
│   ├── draw/page.tsx          ← 카드 뽑기
│   ├── fortune/page.tsx       ← 운세 결과
│   ├── plan/page.tsx          ← 할 일 & 조언
│   ├── retrospective/page.tsx ← 회고
│   └── history/page.tsx       ← 기록
├── components/
│   ├── BottomNav.tsx          ← 하단 네비게이션 바
│   ├── TarotCard.tsx          ← 카드 컴포넌트 (앞/뒤면, 뒤집기 애니메이션)
│   ├── SentimentBadge.tsx     ← positive/negative/neutral 배지
│   └── LoadingSpinner.tsx     ← LLM 대기 중 스피너
├── lib/
│   ├── api.ts                 ← FastAPI 호출 함수 모음
│   └── supabase.ts            ← Supabase anon 클라이언트 (기록 조회용)
└── store/
    └── useDailyStore.ts       ← Zustand 데이터 스토어
```

---

## Phase 1 — FastAPI 백엔드

---

### Task 1: 백엔드 의존성 + FastAPI 앱 부트스트랩

**Files:**
- Modify: `requirements.txt`
- Create: `main.py`
- Create: `db.py`

- [ ] **Step 1: requirements.txt 업데이트**

```
# requirements.txt

# LLM
openai

# Env var
python-dotenv

# NLP
keybert==0.9.0
sentence-transformers==2.7.0
transformers==4.57.6
konlpy

# Web
fastapi==0.115.12
uvicorn[standard]==0.34.0
python-multipart==0.0.20

# DB
supabase==2.15.2

# Test
pytest==8.3.5
httpx==0.28.1
pytest-mock==3.14.0
```

- [ ] **Step 2: 패키지 설치 확인**

```bash
pip install -r requirements.txt
```

Expected: 오류 없이 설치 완료.

- [ ] **Step 3: `db.py` 작성**

```python
# db.py
import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv("GITHUB_TOKEN.env")

_url = os.getenv("SUPABASE_URL", "")
_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

# URL이 없으면 None — 테스트에서 mock으로 교체됨
supabase: Client | None = create_client(_url, _key) if _url and _key else None
```

- [ ] **Step 4: `main.py` 작성**

```python
# main.py
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from routers import cards, fortune, advice, retrospective, records

app = FastAPI(title="타로 데이플래너 API")

_raw = os.getenv("ALLOWED_ORIGINS", "")
ALLOWED_ORIGINS = _raw.split(",") if _raw else ["*"]
_credentials = "*" not in ALLOWED_ORIGINS

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=_credentials,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

app.mount("/card_img", StaticFiles(directory="card_img"), name="card_img")

app.include_router(cards.router, prefix="/cards", tags=["cards"])
app.include_router(fortune.router, tags=["fortune"])
app.include_router(advice.router, tags=["advice"])
app.include_router(retrospective.router, tags=["retrospective"])
app.include_router(records.router, prefix="/records", tags=["records"])


@app.get("/health")
def health():
    return {"status": "ok"}
```

- [ ] **Step 5: `routers/__init__.py` 생성**

```python
# routers/__init__.py
```

- [ ] **Step 6: 서버 기동 확인**

```bash
uvicorn main:app --reload
```

브라우저에서 `http://localhost:8000/health` → `{"status":"ok"}` 확인.

- [ ] **Step 7: 커밋**

```bash
git add main.py db.py routers/__init__.py requirements.txt
git commit -m "feat: FastAPI 앱 부트스트랩, CORS, Supabase 클라이언트"
```

---

### Task 2: 카드 추첨 엔드포인트 (`POST /cards/draw`)

**Files:**
- Create: `routers/cards.py`
- Create: `tests/conftest.py`
- Create: `tests/__init__.py`
- Create: `tests/test_cards.py`

- [ ] **Step 1: `tests/conftest.py` 작성**

```python
# tests/conftest.py
import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch


@pytest.fixture
def client():
    """NLP 모델 로드 없이 TestClient 반환."""
    # nlp_handler 모듈이 임포트될 때 무거운 모델 로드를 막는다
    with patch("nlp_handler.kw_model"), \
         patch("nlp_handler.sentiment_pipeline"), \
         patch("nlp_handler.okt"), \
         patch("db.supabase", new=MagicMock()):
        from main import app
        yield TestClient(app)
```

- [ ] **Step 2: `tests/__init__.py` 생성**

```python
# tests/__init__.py
```

- [ ] **Step 3: 실패하는 테스트 작성**

```python
# tests/test_cards.py
def test_draw_returns_three_cards(client):
    resp = client.post("/cards/draw")
    assert resp.status_code == 200
    data = resp.json()
    assert "cards" in data
    assert len(data["cards"]) == 3


def test_draw_card_has_required_fields(client):
    resp = client.post("/cards/draw")
    card = resp.json()["cards"][0]
    for field in ("id", "name", "reversed", "direction", "meaning", "image_url"):
        assert field in card, f"Missing field: {field}"


def test_draw_card_direction_matches_reversed(client):
    resp = client.post("/cards/draw")
    for card in resp.json()["cards"]:
        if card["reversed"]:
            assert card["direction"] == "역방향"
        else:
            assert card["direction"] == "정방향"
```

- [ ] **Step 4: 테스트 실패 확인**

```bash
pytest tests/test_cards.py -v
```

Expected: FAIL — `routers/cards.py` 없음.

- [ ] **Step 5: `routers/cards.py` 구현**

```python
# routers/cards.py
import json
import random
from pathlib import Path
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()

BASE = Path(__file__).parent.parent
_original = json.loads((BASE / "cards_original.json").read_text(encoding="utf-8"))["cards"]
_reversed = json.loads((BASE / "cards_reversed.json").read_text(encoding="utf-8"))["cards_reversed"]
_reversed_map = {c["id"]: c for c in _reversed}


class DrawnCard(BaseModel):
    id: int
    name: str
    english: str
    reversed: bool
    direction: str        # "정방향" | "역방향"
    meaning: str
    keywords: list[str]
    energy: str
    image_url: str


class DrawResponse(BaseModel):
    cards: list[DrawnCard]


@router.post("/draw", response_model=DrawResponse)
def draw_cards():
    positions = random.sample(_original, 3)
    result = []
    for card in positions:
        is_reversed = random.random() < 0.3   # 30% 역방향
        base = _reversed_map[card["id"]] if is_reversed else card
        img_name = f"{card['id']}. {card['name']} 카드.jpg"
        result.append(DrawnCard(
            id=card["id"],
            name=card["name"],
            english=card["english"],
            reversed=is_reversed,
            direction="역방향" if is_reversed else "정방향",
            meaning=base.get("meaning", card["meaning"]),
            keywords=base.get("keywords", card["keywords"]),
            energy=card.get("energy", ""),
            image_url=f"/card_img/{img_name}",
        ))
    return DrawResponse(cards=result)
```

- [ ] **Step 6: 테스트 통과 확인**

```bash
pytest tests/test_cards.py -v
```

Expected: 3 tests PASSED.

- [ ] **Step 7: 커밋**

```bash
git add routers/cards.py tests/__init__.py tests/conftest.py tests/test_cards.py
git commit -m "feat: POST /cards/draw — 카드 3장 추첨"
```

---

### Task 3: 운세 생성 엔드포인트 (`POST /fortune`)

**Files:**
- Create: `routers/fortune.py`
- Create: `tests/test_fortune.py`

- [ ] **Step 1: 실패하는 테스트 작성**

```python
# tests/test_fortune.py
from unittest.mock import patch


SAMPLE_CARDS = [
    {"id": 0, "name": "바보", "reversed": False, "direction": "정방향",
     "meaning": "새로운 시작", "keywords": ["자유", "모험"], "energy": "활기참"},
    {"id": 1, "name": "마법사", "reversed": False, "direction": "정방향",
     "meaning": "능력 발휘", "keywords": ["의지", "집중"], "energy": "집중"},
    {"id": 2, "name": "여교황", "reversed": False, "direction": "정방향",
     "meaning": "내면의 지혜", "keywords": ["직관", "신비"], "energy": "차분함"},
]


def test_fortune_returns_summary_and_text(client):
    with patch("routers.fortune.generate_fortune", return_value="한 줄 요약: 새 출발\n\n오늘의 운세:\n좋은 하루"), \
         patch("routers.fortune.preprocess_card", return_value={"keywords": ["자유"], "sentiment_score": 0.8, "sentiment_label": "positive"}):
        resp = client.post("/fortune", json={"cards": SAMPLE_CARDS})
    assert resp.status_code == 200
    data = resp.json()
    assert "summary" in data
    assert "fortune" in data
    assert "nlp_result" in data


def test_fortune_requires_three_cards(client):
    resp = client.post("/fortune", json={"cards": SAMPLE_CARDS[:2]})
    assert resp.status_code == 422
```

- [ ] **Step 2: 테스트 실패 확인**

```bash
pytest tests/test_fortune.py -v
```

Expected: FAIL.

- [ ] **Step 3: `routers/fortune.py` 구현**

```python
# routers/fortune.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from nlp_handler import preprocess_card
from llm_handler import generate_fortune

router = APIRouter()


class CardInput(BaseModel):
    id: int
    name: str
    reversed: bool
    direction: str
    meaning: str
    keywords: list[str]
    energy: str


class FortuneRequest(BaseModel):
    cards: list[CardInput]


class NlpResult(BaseModel):
    keywords: list[str]
    sentiment_score: float
    sentiment_label: str


class FortuneResponse(BaseModel):
    summary: str
    fortune: str
    nlp_result: NlpResult


def _parse_llm(text: str) -> tuple[str, str]:
    """LLM 응답에서 한 줄 요약과 본문을 분리한다."""
    summary, body = "", text
    for line in text.splitlines():
        if line.startswith("한 줄 요약:"):
            summary = line.replace("한 줄 요약:", "").strip()
        elif line.startswith("오늘의 운세:"):
            body = text[text.find("오늘의 운세:") + len("오늘의 운세:"):].strip()
    return summary, body


@router.post("/fortune", response_model=FortuneResponse)
def fortune(req: FortuneRequest):
    if len(req.cards) != 3:
        raise HTTPException(422, "카드 3장이 필요합니다")
    combined = " ".join(c.meaning for c in req.cards)
    # 합쳐진 의미 텍스트로 NLP 분석
    nlp = preprocess_card({"meaning": combined})
    cards_dict = [c.model_dump() for c in req.cards]
    raw = generate_fortune(cards_dict, nlp)
    summary, body = _parse_llm(raw)
    return FortuneResponse(summary=summary, fortune=body, nlp_result=NlpResult(**nlp))
```

- [ ] **Step 4: 테스트 통과 확인**

```bash
pytest tests/test_fortune.py -v
```

Expected: 2 tests PASSED.

- [ ] **Step 5: 커밋**

```bash
git add routers/fortune.py tests/test_fortune.py
git commit -m "feat: POST /fortune — NLP 분석 + LLM 운세 생성"
```

---

### Task 4: 조언 생성 엔드포인트 (`POST /advice`)

**Files:**
- Create: `routers/advice.py`
- Create: `tests/test_advice.py`

- [ ] **Step 1: 실패하는 테스트 작성**

```python
# tests/test_advice.py
from unittest.mock import patch

SAMPLE_CARDS = [
    {"id": 0, "name": "바보", "reversed": False, "direction": "정방향",
     "meaning": "새로운 시작", "keywords": ["자유"], "energy": "활기참"},
    {"id": 1, "name": "마법사", "reversed": False, "direction": "정방향",
     "meaning": "능력 발휘", "keywords": ["의지"], "energy": "집중"},
    {"id": 2, "name": "여교황", "reversed": False, "direction": "정방향",
     "meaning": "내면의 지혜", "keywords": ["직관"], "energy": "차분함"},
]
SAMPLE_NLP = {"keywords": ["자유"], "sentiment_score": 0.8, "sentiment_label": "positive"}


def test_advice_returns_summary_and_text(client):
    with patch("routers.advice.generate_advice", return_value="한 줄 요약: 흐름을 따라\n\n오늘의 조언:\n잘 할 수 있어요"):
        resp = client.post("/advice", json={
            "cards": SAMPLE_CARDS,
            "condition": "좋음",
            "tasks": ["보고서 작성", "운동 30분"],
            "nlp_result": SAMPLE_NLP,
        })
    assert resp.status_code == 200
    data = resp.json()
    assert "summary" in data
    assert "advice" in data


def test_advice_requires_condition(client):
    resp = client.post("/advice", json={
        "cards": SAMPLE_CARDS,
        "tasks": ["보고서 작성"],
        "nlp_result": SAMPLE_NLP,
    })
    assert resp.status_code == 422
```

- [ ] **Step 2: 테스트 실패 확인**

```bash
pytest tests/test_advice.py -v
```

Expected: FAIL.

- [ ] **Step 3: `routers/advice.py` 구현**

```python
# routers/advice.py
from fastapi import APIRouter
from pydantic import BaseModel
from llm_handler import generate_advice

router = APIRouter()


class CardInput(BaseModel):
    id: int
    name: str
    reversed: bool
    direction: str
    meaning: str
    keywords: list[str]
    energy: str


class NlpResult(BaseModel):
    keywords: list[str]
    sentiment_score: float
    sentiment_label: str


class AdviceRequest(BaseModel):
    cards: list[CardInput]
    condition: str           # '최고'|'좋음'|'보통'|'나쁨'
    tasks: list[str]
    nlp_result: NlpResult


class AdviceResponse(BaseModel):
    summary: str
    advice: str


def _parse_llm(text: str) -> tuple[str, str]:
    summary, body = "", text
    for line in text.splitlines():
        if line.startswith("한 줄 요약:"):
            summary = line.replace("한 줄 요약:", "").strip()
        elif line.startswith("오늘의 조언:"):
            body = text[text.find("오늘의 조언:") + len("오늘의 조언:"):].strip()
    return summary, body


@router.post("/advice", response_model=AdviceResponse)
def advice(req: AdviceRequest):
    cards_dict = [c.model_dump() for c in req.cards]
    raw = generate_advice(
        cards=cards_dict,
        tasks="\n".join(req.tasks),
        condition=req.condition,
        nlp_result=req.nlp_result.model_dump(),
    )
    summary, body = _parse_llm(raw)
    return AdviceResponse(summary=summary, advice=body)
```

- [ ] **Step 4: 테스트 통과 확인**

```bash
pytest tests/test_advice.py -v
```

Expected: 2 tests PASSED.

- [ ] **Step 5: 커밋**

```bash
git add routers/advice.py tests/test_advice.py
git commit -m "feat: POST /advice — 조건 + 할 일 기반 LLM 조언 생성"
```

---

### Task 5: 회고 생성 엔드포인트 (`POST /retrospective`)

**Files:**
- Create: `routers/retrospective.py`
- Create: `tests/test_retrospective.py`

- [ ] **Step 1: 실패하는 테스트 작성**

```python
# tests/test_retrospective.py
from unittest.mock import patch

SAMPLE_CARDS = [
    {"id": 0, "name": "바보", "reversed": False, "direction": "정방향",
     "meaning": "새로운 시작", "keywords": ["자유"], "energy": "활기참"},
    {"id": 1, "name": "마법사", "reversed": False, "direction": "정방향",
     "meaning": "능력 발휘", "keywords": ["의지"], "energy": "집중"},
    {"id": 2, "name": "여교황", "reversed": False, "direction": "정방향",
     "meaning": "내면의 지혜", "keywords": ["직관"], "energy": "차분함"},
]
SAMPLE_NLP = {"keywords": ["자유"], "sentiment_score": 0.8, "sentiment_label": "positive"}


def test_retrospective_returns_summary_and_text(client):
    with patch("routers.retrospective.generate_retrospective",
               return_value="한 줄 요약: 빛을 향한 하루\n\n오늘의 회고:\n잘 마무리했어요"):
        resp = client.post("/retrospective", json={
            "cards": SAMPLE_CARDS,
            "completed_tasks": ["보고서 작성"],
            "incomplete_tasks": ["운동 30분"],
            "nlp_result": SAMPLE_NLP,
        })
    assert resp.status_code == 200
    data = resp.json()
    assert "summary" in data
    assert "retrospective" in data
```

- [ ] **Step 2: 테스트 실패 확인**

```bash
pytest tests/test_retrospective.py -v
```

Expected: FAIL.

- [ ] **Step 3: `routers/retrospective.py` 구현**

```python
# routers/retrospective.py
from fastapi import APIRouter
from pydantic import BaseModel
from llm_handler import generate_retrospective

router = APIRouter()


class CardInput(BaseModel):
    id: int
    name: str
    reversed: bool
    direction: str
    meaning: str
    keywords: list[str]
    energy: str


class NlpResult(BaseModel):
    keywords: list[str]
    sentiment_score: float
    sentiment_label: str


class RetrospectiveRequest(BaseModel):
    cards: list[CardInput]
    completed_tasks: list[str]
    incomplete_tasks: list[str]
    nlp_result: NlpResult


class RetrospectiveResponse(BaseModel):
    summary: str
    retrospective: str


def _parse_llm(text: str) -> tuple[str, str]:
    summary, body = "", text
    for line in text.splitlines():
        if line.startswith("한 줄 요약:"):
            summary = line.replace("한 줄 요약:", "").strip()
        elif line.startswith("오늘의 회고:"):
            body = text[text.find("오늘의 회고:") + len("오늘의 회고:"):].strip()
    return summary, body


@router.post("/retrospective", response_model=RetrospectiveResponse)
def retrospective(req: RetrospectiveRequest):
    cards_dict = [c.model_dump() for c in req.cards]
    raw = generate_retrospective(
        cards=cards_dict,
        completed_tasks=req.completed_tasks,
        incomplete_tasks=req.incomplete_tasks,
        nlp_result=req.nlp_result.model_dump(),
    )
    summary, body = _parse_llm(raw)
    return RetrospectiveResponse(summary=summary, retrospective=body)
```

- [ ] **Step 4: 테스트 통과 확인**

```bash
pytest tests/test_retrospective.py -v
```

Expected: 1 test PASSED.

- [ ] **Step 5: 커밋**

```bash
git add routers/retrospective.py tests/test_retrospective.py
git commit -m "feat: POST /retrospective — 완료/미완료 기반 LLM 회고 생성"
```

---

### Task 6: Supabase DB 스키마 + 기록 엔드포인트

**Files:**
- Create: `routers/records.py`
- Create: `tests/test_records.py`

- [ ] **Step 1: Supabase 마이그레이션 적용**

Supabase MCP 또는 Supabase 대시보드 SQL 에디터에서 실행:

```sql
CREATE TABLE IF NOT EXISTS daily_records (
  id                uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
  date              date        NOT NULL UNIQUE,
  cards             jsonb       NOT NULL,
  nlp_result        jsonb,
  fortune           text,
  summary           text,
  condition         text,
  tasks             text[],
  advice            text,
  advice_summary    text,
  completed_tasks   text[],
  incomplete_tasks  text[],
  retrospective     text,
  retro_summary     text,
  created_at        timestamptz DEFAULT now()
);

-- 읽기는 anon key로 허용 (프론트엔드 직접 조회)
ALTER TABLE daily_records ENABLE ROW LEVEL SECURITY;
CREATE POLICY "anon_read" ON daily_records FOR SELECT USING (true);
CREATE POLICY "service_write" ON daily_records FOR ALL USING (true);
```

- [ ] **Step 2: 실패하는 테스트 작성**

```python
# tests/test_records.py
from unittest.mock import MagicMock, patch
import datetime

SAMPLE_RECORD = {
    "date": "2026-04-12",
    "cards": [
        {"id": 0, "name": "바보", "reversed": False, "direction": "정방향"},
    ],
    "nlp_result": {"keywords": ["자유"], "sentiment_score": 0.8, "sentiment_label": "positive"},
    "fortune": "좋은 하루",
    "summary": "새 출발",
    "condition": "좋음",
    "tasks": ["보고서 작성"],
    "advice": "흐름을 따라가세요",
    "advice_summary": "흐름을 따라",
    "completed_tasks": ["보고서 작성"],
    "incomplete_tasks": [],
    "retrospective": "잘 마무리했어요",
    "retro_summary": "빛을 향한 하루",
}


def test_save_record_returns_date(client):
    mock_sb = MagicMock()
    mock_sb.table.return_value.upsert.return_value.execute.return_value.data = [
        {"id": "uuid-123", "date": "2026-04-12"}
    ]
    with patch("routers.records.supabase", mock_sb):
        resp = client.post("/records", json=SAMPLE_RECORD)
    assert resp.status_code == 200
    assert resp.json()["date"] == "2026-04-12"


def test_get_records_by_month(client):
    mock_sb = MagicMock()
    mock_sb.table.return_value.select.return_value.gte.return_value.lte.return_value.order.return_value.execute.return_value.data = [
        {"date": "2026-04-12", "summary": "새 출발", "cards": [], "nlp_result": {"sentiment_label": "positive"}}
    ]
    with patch("routers.records.supabase", mock_sb):
        resp = client.get("/records?year=2026&month=4")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_get_record_by_date(client):
    mock_sb = MagicMock()
    mock_sb.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value.data = SAMPLE_RECORD
    with patch("routers.records.supabase", mock_sb):
        resp = client.get("/records/2026-04-12")
    assert resp.status_code == 200
    assert resp.json()["date"] == "2026-04-12"
```

- [ ] **Step 3: 테스트 실패 확인**

```bash
pytest tests/test_records.py -v
```

Expected: FAIL.

- [ ] **Step 4: `routers/records.py` 구현**

```python
# routers/records.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from db import supabase
import datetime

router = APIRouter()


class RecordIn(BaseModel):
    date: str
    cards: list
    nlp_result: dict | None = None
    fortune: str | None = None
    summary: str | None = None
    condition: str | None = None
    tasks: list[str] | None = None
    advice: str | None = None
    advice_summary: str | None = None
    completed_tasks: list[str] | None = None
    incomplete_tasks: list[str] | None = None
    retrospective: str | None = None
    retro_summary: str | None = None


@router.post("", response_model=dict)
def save_record(record: RecordIn):
    data = record.model_dump()
    result = supabase.table("daily_records").upsert(data, on_conflict="date").execute()
    row = result.data[0]
    return {"id": row.get("id"), "date": row.get("date")}


@router.get("", response_model=list)
def get_records(year: int, month: int):
    start = f"{year:04d}-{month:02d}-01"
    # 월 마지막 날 계산
    if month == 12:
        end = f"{year + 1:04d}-01-01"
    else:
        end = f"{year:04d}-{month + 1:02d}-01"
    result = (
        supabase.table("daily_records")
        .select("date,summary,cards,nlp_result,retro_summary")
        .gte("date", start)
        .lte("date", end)
        .order("date", desc=True)
        .execute()
    )
    return result.data


@router.get("/{date}", response_model=dict)
def get_record(date: str):
    try:
        result = (
            supabase.table("daily_records")
            .select("*")
            .eq("date", date)
            .single()
            .execute()
        )
    except Exception:
        raise HTTPException(404, f"{date} 기록 없음")
    if not result.data:
        raise HTTPException(404, f"{date} 기록 없음")
    return result.data
```

- [ ] **Step 5: 테스트 통과 확인**

```bash
pytest tests/test_records.py -v
```

Expected: 3 tests PASSED.

- [ ] **Step 6: 전체 테스트 통과 확인**

```bash
pytest tests/ -v
```

Expected: 전체 PASSED.

- [ ] **Step 7: 커밋**

```bash
git add routers/records.py tests/test_records.py
git commit -m "feat: /records CRUD — Supabase 날짜별 기록 저장/조회"
```

---

## Phase 2 — 프론트엔드

---

### Task 7: 테마 + 레이아웃 + BottomNav

**Files:**
- Modify: `frontend/src/app/globals.css`
- Modify: `frontend/src/app/layout.tsx`
- Create: `frontend/src/components/BottomNav.tsx`

- [ ] **Step 1: `globals.css` 테마 변수 추가**

기존 파일 끝에 추가:

```css
/* 타로 다크 퍼플 테마 */
:root {
  --tarot-bg: #0f0520;
  --tarot-surface: #1a0b33;
  --tarot-card: #2a1550;
  --tarot-border: #3d2070;
  --tarot-accent: #8b5cf6;
  --tarot-accent-hover: #7c3aed;
  --tarot-gold: #f59e0b;
  --tarot-text: #f3f0ff;
  --tarot-muted: #a78bca;
  --tarot-positive: #10b981;
  --tarot-negative: #ef4444;
  --tarot-neutral: #6b7280;
}

body {
  background-color: var(--tarot-bg);
  color: var(--tarot-text);
}
```

- [ ] **Step 2: `layout.tsx` 모바일 래퍼로 교체**

```tsx
// frontend/src/app/layout.tsx
import type { Metadata } from "next";
import { Geist } from "next/font/google";
import "./globals.css";
import BottomNav from "@/components/BottomNav";

const geist = Geist({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "타로 데이플래너",
  description: "타로카드로 하루를 계획하고 회고하세요",
  viewport: "width=device-width, initial-scale=1, maximum-scale=1",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ko">
      <body className={geist.className}>
        <div className="mx-auto max-w-[390px] min-h-screen relative flex flex-col"
             style={{ background: "var(--tarot-bg)" }}>
          <main className="flex-1 overflow-y-auto pb-20">
            {children}
          </main>
          <BottomNav />
        </div>
      </body>
    </html>
  );
}
```

- [ ] **Step 3: `BottomNav.tsx` 작성**

```tsx
// frontend/src/components/BottomNav.tsx
"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Home, LayoutList, Moon, BookOpen } from "lucide-react";

const NAV = [
  { href: "/",             icon: Home,        label: "홈" },
  { href: "/plan",         icon: LayoutList,  label: "계획" },
  { href: "/retrospective",icon: Moon,        label: "회고" },
  { href: "/history",      icon: BookOpen,    label: "기록" },
];

export default function BottomNav() {
  const path = usePathname();
  return (
    <nav className="fixed bottom-0 left-1/2 -translate-x-1/2 w-full max-w-[390px]
                    flex justify-around items-center h-16 px-4 border-t"
         style={{ background: "var(--tarot-surface)", borderColor: "var(--tarot-border)" }}>
      {NAV.map(({ href, icon: Icon, label }) => {
        const active = path === href;
        return (
          <Link key={href} href={href}
                className="flex flex-col items-center gap-0.5 text-xs"
                style={{ color: active ? "var(--tarot-accent)" : "var(--tarot-muted)" }}>
            <Icon size={22} />
            <span>{label}</span>
          </Link>
        );
      })}
    </nav>
  );
}
```

- [ ] **Step 4: 개발 서버 실행 확인**

```bash
cd frontend && npm run dev
```

`http://localhost:3000` 에서 다크 퍼플 배경과 하단 네비게이션 확인.

- [ ] **Step 5: 커밋**

```bash
git add frontend/src/app/globals.css frontend/src/app/layout.tsx frontend/src/components/BottomNav.tsx
git commit -m "feat: 다크 퍼플 테마, 모바일 레이아웃, BottomNav"
```

---

### Task 8: API 클라이언트 + Zustand 스토어

**Files:**
- Create: `frontend/src/lib/api.ts`
- Create: `frontend/src/lib/supabase.ts`
- Create: `frontend/src/store/useDailyStore.ts`

- [ ] **Step 1: 패키지 설치**

```bash
cd frontend
npm install zustand @supabase/supabase-js
```

- [ ] **Step 2: `lib/api.ts` 작성**

```typescript
// frontend/src/lib/api.ts

const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export type DrawnCard = {
  id: number; name: string; english: string;
  reversed: boolean; direction: string;
  meaning: string; keywords: string[]; energy: string; image_url: string;
};

export type NlpResult = {
  keywords: string[]; sentiment_score: number; sentiment_label: string;
};

export async function drawCards(): Promise<{ cards: DrawnCard[] }> {
  const res = await fetch(`${BASE}/cards/draw`, { method: "POST" });
  if (!res.ok) throw new Error("카드 추첨 실패");
  return res.json();
}

export async function fetchFortune(cards: DrawnCard[]) {
  const res = await fetch(`${BASE}/fortune`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ cards }),
  });
  if (!res.ok) throw new Error("운세 생성 실패");
  return res.json() as Promise<{ summary: string; fortune: string; nlp_result: NlpResult }>;
}

export async function fetchAdvice(
  cards: DrawnCard[], condition: string, tasks: string[], nlp_result: NlpResult
) {
  const res = await fetch(`${BASE}/advice`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ cards, condition, tasks, nlp_result }),
  });
  if (!res.ok) throw new Error("조언 생성 실패");
  return res.json() as Promise<{ summary: string; advice: string }>;
}

export async function fetchRetrospective(
  cards: DrawnCard[], completed_tasks: string[], incomplete_tasks: string[], nlp_result: NlpResult
) {
  const res = await fetch(`${BASE}/retrospective`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ cards, completed_tasks, incomplete_tasks, nlp_result }),
  });
  if (!res.ok) throw new Error("회고 생성 실패");
  return res.json() as Promise<{ summary: string; retrospective: string }>;
}

export async function saveRecord(record: Record<string, unknown>) {
  const res = await fetch(`${BASE}/records`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(record),
  });
  if (!res.ok) throw new Error("기록 저장 실패");
  return res.json();
}

export async function getRecords(year: number, month: number) {
  const res = await fetch(`${BASE}/records?year=${year}&month=${month}`);
  if (!res.ok) throw new Error("기록 조회 실패");
  return res.json();
}

export async function getRecordByDate(date: string) {
  const res = await fetch(`${BASE}/records/${date}`);
  if (res.status === 404) return null;
  if (!res.ok) throw new Error("기록 조회 실패");
  return res.json();
}
```

- [ ] **Step 3: `lib/supabase.ts` 작성**

```typescript
// frontend/src/lib/supabase.ts
import { createClient } from "@supabase/supabase-js";

export const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
);
```

- [ ] **Step 4: `store/useDailyStore.ts` 작성**

```typescript
// frontend/src/store/useDailyStore.ts
import { create } from "zustand";
import type { DrawnCard, NlpResult } from "@/lib/api";

export type Condition = "최고" | "좋음" | "보통" | "나쁨";

interface DailyStore {
  date: string;
  cards: DrawnCard[];
  nlpResult: NlpResult | null;
  fortune: string;
  summary: string;
  condition: Condition | null;
  tasks: string[];
  advice: string;
  adviceSummary: string;
  completedTasks: string[];
  incompleteTasks: string[];
  retrospective: string;
  retroSummary: string;

  setCards: (cards: DrawnCard[]) => void;
  setFortune: (summary: string, fortune: string, nlp: NlpResult) => void;
  setCondition: (c: Condition) => void;
  setTasks: (tasks: string[]) => void;
  setAdvice: (summary: string, advice: string) => void;
  setRetrospective: (summary: string, retro: string, done: string[], notDone: string[]) => void;
  reset: () => void;
}

const today = () => new Date().toISOString().slice(0, 10);

export const useDailyStore = create<DailyStore>((set) => ({
  date: today(),
  cards: [],
  nlpResult: null,
  fortune: "",
  summary: "",
  condition: null,
  tasks: [],
  advice: "",
  adviceSummary: "",
  completedTasks: [],
  incompleteTasks: [],
  retrospective: "",
  retroSummary: "",

  setCards: (cards) => set({ cards }),
  setFortune: (summary, fortune, nlpResult) => set({ summary, fortune, nlpResult }),
  setCondition: (condition) => set({ condition }),
  setTasks: (tasks) => set({ tasks }),
  setAdvice: (adviceSummary, advice) => set({ adviceSummary, advice }),
  setRetrospective: (retroSummary, retrospective, completedTasks, incompleteTasks) =>
    set({ retroSummary, retrospective, completedTasks, incompleteTasks }),
  reset: () => set({ date: today(), cards: [], nlpResult: null, fortune: "", summary: "",
                     condition: null, tasks: [], advice: "", adviceSummary: "",
                     completedTasks: [], incompleteTasks: [], retrospective: "", retroSummary: "" }),
}));
```

- [ ] **Step 5: `.env.local` 생성**

```bash
# frontend/.env.local
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_SUPABASE_URL=https://xxxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJxxx
```

`.gitignore`에 `.env.local` 추가 (없으면):
```bash
echo ".env.local" >> frontend/.gitignore
```

- [ ] **Step 6: 커밋**

```bash
git add frontend/src/lib/ frontend/src/store/ frontend/.gitignore
git commit -m "feat: API 클라이언트, Supabase 클라이언트, Zustand 스토어"
```

---

### Task 9: 홈 화면 (`/`)

**Files:**
- Modify: `frontend/src/app/page.tsx`
- Create: `frontend/src/components/LoadingSpinner.tsx`

- [ ] **Step 1: `LoadingSpinner.tsx` 작성**

```tsx
// frontend/src/components/LoadingSpinner.tsx
export default function LoadingSpinner({ message = "로딩 중..." }: { message?: string }) {
  return (
    <div className="flex flex-col items-center justify-center gap-3 py-12">
      <div className="w-10 h-10 rounded-full border-4 border-t-transparent animate-spin"
           style={{ borderColor: "var(--tarot-accent)", borderTopColor: "transparent" }} />
      <p className="text-sm" style={{ color: "var(--tarot-muted)" }}>{message}</p>
    </div>
  );
}
```

- [ ] **Step 2: 홈 화면 `page.tsx` 구현**

```tsx
// frontend/src/app/page.tsx
"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useDailyStore } from "@/store/useDailyStore";
import { getRecordByDate } from "@/lib/api";
import LoadingSpinner from "@/components/LoadingSpinner";

const today = () => new Date().toISOString().slice(0, 10);

function formatDate(iso: string) {
  const d = new Date(iso);
  return `${d.getFullYear()}년 ${d.getMonth() + 1}월 ${d.getDate()}일 ${["일","월","화","수","목","금","토"][d.getDay()]}요일`;
}

export default function HomePage() {
  const router = useRouter();
  const { cards, fortune } = useDailyStore();
  const [checking, setChecking] = useState(true);

  useEffect(() => {
    getRecordByDate(today()).then((rec) => {
      if (rec?.fortune) {
        // 이미 오늘 기록이 있으면 운세 결과 화면으로
        router.replace("/fortune");
      }
      setChecking(false);
    }).catch(() => setChecking(false));
  }, [router]);

  if (checking) return <LoadingSpinner message="오늘의 기록 확인 중..." />;

  return (
    <div className="flex flex-col items-center px-6 pt-8 gap-6 min-h-screen"
         style={{ background: "var(--tarot-bg)" }}>
      {/* 헤더 */}
      <div className="w-full flex justify-between items-center">
        <p className="text-sm" style={{ color: "var(--tarot-muted)" }}>{formatDate(today())}</p>
      </div>

      {/* 타로볼 */}
      <div className="relative flex items-center justify-center w-48 h-48 my-4">
        <div className="w-40 h-40 rounded-full"
             style={{ background: "radial-gradient(circle at 35% 35%, #6d28d9, #1a0b33)" }} />
        <div className="absolute top-4 left-8 w-3 h-3 rounded-full"
             style={{ background: "#c4b5fd", opacity: 0.6 }} />
      </div>

      {/* 타이틀 */}
      <div className="text-center">
        <h1 className="text-2xl font-bold mb-2" style={{ color: "var(--tarot-text)" }}>
          타로 데이플래너
        </h1>
        <p className="text-sm" style={{ color: "var(--tarot-muted)" }}>
          타로카드로 오늘 하루를 계획하고 회고하세요
        </p>
      </div>

      {/* CTA 버튼 */}
      {cards.length > 0 ? (
        <button onClick={() => router.push("/fortune")}
                className="w-full py-4 rounded-full text-white font-semibold"
                style={{ background: "var(--tarot-surface)", border: "1px solid var(--tarot-border)" }}>
          오늘의 운세 보기
        </button>
      ) : null}

      <button onClick={() => router.push("/draw")}
              className="w-full py-4 rounded-full text-white font-bold text-lg"
              style={{ background: "var(--tarot-accent)" }}>
        ✦ 오늘의 카드 뽑기
      </button>

      <p className="text-xs text-center" style={{ color: "var(--tarot-muted)" }}>
        매일 아침 3장의 카드로 과거 현재 미래를 읽어보세요
      </p>
    </div>
  );
}
```

- [ ] **Step 3: 화면 확인**

`http://localhost:3000` — 다크 퍼플 홈 화면, 타로볼, 카드 뽑기 버튼 확인.

- [ ] **Step 4: 커밋**

```bash
git add frontend/src/app/page.tsx frontend/src/components/LoadingSpinner.tsx
git commit -m "feat: 홈 화면 — 타로볼, 카드 뽑기 진입"
```

---

### Task 10: 카드 뽑기 화면 (`/draw`)

**Files:**
- Create: `frontend/src/app/draw/page.tsx`
- Create: `frontend/src/components/TarotCard.tsx`

- [ ] **Step 1: `TarotCard.tsx` 작성**

```tsx
// frontend/src/components/TarotCard.tsx
"use client";
import Image from "next/image";

interface TarotCardProps {
  card?: { name: string; image_url: string; direction: string };
  position: "과거" | "현재" | "미래";
  selected?: boolean;
  faceDown?: boolean;
  onClick?: () => void;
}

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export default function TarotCard({ card, position, selected, faceDown, onClick }: TarotCardProps) {
  return (
    <div onClick={onClick}
         className="flex flex-col items-center gap-2 cursor-pointer"
         style={{ opacity: onClick ? 1 : 0.9 }}>
      <div className="w-24 h-36 rounded-xl overflow-hidden border-2 transition-all"
           style={{
             borderColor: selected ? "var(--tarot-gold)" : "var(--tarot-border)",
             background: "var(--tarot-card)",
             boxShadow: selected ? "0 0 16px var(--tarot-gold)" : undefined,
           }}>
        {!faceDown && card ? (
          <Image
            src={`${API}${encodeURI(card.image_url)}`}
            alt={card.name}
            width={96} height={144}
            className="w-full h-full object-cover"
            unoptimized
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center"
               style={{ background: "var(--tarot-card)" }}>
            <span className="text-3xl">✦</span>
          </div>
        )}
      </div>
      <span className="text-xs font-medium"
            style={{ color: selected ? "var(--tarot-gold)" : "var(--tarot-muted)" }}>
        {position}
      </span>
    </div>
  );
}
```

- [ ] **Step 2: `draw/page.tsx` 작성**

```tsx
// frontend/src/app/draw/page.tsx
"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { useDailyStore } from "@/store/useDailyStore";
import { drawCards, fetchFortune, type DrawnCard } from "@/lib/api";
import TarotCard from "@/components/TarotCard";
import LoadingSpinner from "@/components/LoadingSpinner";

const POSITIONS = ["과거", "현재", "미래"] as const;

export default function DrawPage() {
  const router = useRouter();
  const { setCards, setFortune } = useDailyStore();
  const [deck, setDeck] = useState<DrawnCard[]>([]);
  const [selected, setSelected] = useState<number | null>(null);
  const [loading, setLoading] = useState(false);
  const [step, setStep] = useState<"idle" | "picking" | "confirming">("idle");

  async function handleShuffle() {
    setLoading(true);
    try {
      const { cards } = await drawCards();
      setDeck(cards);
      setStep("picking");
      setSelected(null);
    } finally {
      setLoading(false);
    }
  }

  async function handleConfirm() {
    if (deck.length === 0) return;
    setLoading(true);
    setCards(deck);
    try {
      const result = await fetchFortune(deck);
      setFortune(result.summary, result.fortune, result.nlp_result);
      router.push("/fortune");
    } finally {
      setLoading(false);
    }
  }

  if (loading) return <LoadingSpinner message={step === "confirming" ? "운세를 읽는 중..." : "카드를 섞는 중..."} />;

  return (
    <div className="flex flex-col px-6 pt-6 gap-6">
      {/* 헤더 */}
      <div className="flex items-center gap-3">
        <button onClick={() => router.back()} className="text-lg" style={{ color: "var(--tarot-muted)" }}>‹</button>
        <h2 className="text-lg font-bold">오늘의 카드 뽑기</h2>
      </div>

      {/* 스텝 표시 */}
      <p className="text-xs text-center" style={{ color: "var(--tarot-muted)" }}>
        STEP 1/3 · {deck.length === 0 ? "카드를 섞어주세요" : "카드를 선택하세요"}
      </p>

      <p className="text-sm text-center" style={{ color: "var(--tarot-text)" }}>
        마음을 가라앉히고 3장의 카드를<br />직관에 따라 선택하세요
      </p>

      {/* 카드 3장 */}
      <div className="flex justify-center gap-4 my-4">
        {POSITIONS.map((pos, i) => (
          <TarotCard
            key={pos}
            position={pos}
            card={deck[i]}
            selected={selected === i}
            faceDown={deck.length === 0}
            onClick={deck.length > 0 ? () => setSelected(i) : undefined}
          />
        ))}
      </div>

      {/* 버튼 */}
      <button onClick={handleShuffle}
              className="w-full py-3 rounded-full font-semibold border"
              style={{ borderColor: "var(--tarot-border)", color: "var(--tarot-text)", background: "transparent" }}>
        ✦ 카드 섞기
      </button>

      <button onClick={() => { setStep("confirming"); handleConfirm(); }}
              disabled={deck.length === 0}
              className="w-full py-4 rounded-full font-bold text-white disabled:opacity-40"
              style={{ background: "var(--tarot-accent)" }}>
        이 카드로 오늘을 시작할게요
      </button>

      <p className="text-xs text-center" style={{ color: "var(--tarot-muted)" }}>
        카드를 탭하여 선택하세요
      </p>
    </div>
  );
}
```

- [ ] **Step 3: 동작 확인**

백엔드 실행 후 `http://localhost:3000/draw` → 카드 섞기 버튼 클릭 → 카드 3장 표시 확인.

- [ ] **Step 4: 커밋**

```bash
git add frontend/src/app/draw/ frontend/src/components/TarotCard.tsx
git commit -m "feat: 카드 뽑기 화면 — 셔플, 3장 선택, 운세 생성 이동"
```

---

### Task 11: 운세 결과 화면 (`/fortune`)

**Files:**
- Create: `frontend/src/app/fortune/page.tsx`
- Create: `frontend/src/components/SentimentBadge.tsx`

- [ ] **Step 1: `SentimentBadge.tsx` 작성**

```tsx
// frontend/src/components/SentimentBadge.tsx
const CONFIG = {
  positive: { label: "✦ positive", bg: "#10b98133", color: "#10b981" },
  negative: { label: "✦ negative", bg: "#ef444433", color: "#ef4444" },
  neutral:  { label: "✦ neutral",  bg: "#6b728033", color: "#9ca3af" },
};

export default function SentimentBadge({ label }: { label: string }) {
  const cfg = CONFIG[label as keyof typeof CONFIG] ?? CONFIG.neutral;
  return (
    <span className="px-3 py-1 rounded-full text-xs font-semibold"
          style={{ background: cfg.bg, color: cfg.color }}>
      {cfg.label}
    </span>
  );
}
```

- [ ] **Step 2: `fortune/page.tsx` 구현**

```tsx
// frontend/src/app/fortune/page.tsx
"use client";
import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useDailyStore } from "@/store/useDailyStore";
import TarotCard from "@/components/TarotCard";
import SentimentBadge from "@/components/SentimentBadge";

const POSITIONS = ["과거", "현재", "미래"] as const;

export default function FortunePage() {
  const router = useRouter();
  const { cards, fortune, summary, nlpResult } = useDailyStore();

  useEffect(() => {
    if (cards.length === 0) router.replace("/");
  }, [cards, router]);

  if (cards.length === 0) return null;

  return (
    <div className="flex flex-col px-6 pt-6 gap-5">
      <div className="flex items-center gap-3">
        <button onClick={() => router.back()} style={{ color: "var(--tarot-muted)" }}>‹</button>
        <h2 className="text-lg font-bold">오늘의 운세</h2>
      </div>

      <p className="text-xs text-center" style={{ color: "var(--tarot-muted)" }}>
        {new Date().toLocaleDateString("ko-KR", { year:"numeric", month:"long", day:"numeric", weekday:"long" })}
      </p>

      {/* 카드 3장 */}
      <div className="flex justify-center gap-3">
        {cards.map((card, i) => (
          <TarotCard key={i} card={card} position={POSITIONS[i]} selected />
        ))}
      </div>

      {/* 감성 배지 */}
      <div className="flex items-center gap-2">
        <span className="text-xs" style={{ color: "var(--tarot-muted)" }}>오늘의 에너지</span>
        {nlpResult && <SentimentBadge label={nlpResult.sentiment_label} />}
      </div>

      {/* 한 줄 요약 */}
      <div className="rounded-xl p-4" style={{ background: "var(--tarot-card)", border: "1px solid var(--tarot-gold)" }}>
        <p className="text-sm font-bold" style={{ color: "var(--tarot-gold)" }}>{summary}</p>
      </div>

      {/* 운세 본문 */}
      <div>
        <p className="text-xs font-semibold mb-2" style={{ color: "var(--tarot-muted)" }}>오늘의 운세</p>
        <p className="text-sm leading-7" style={{ color: "var(--tarot-text)" }}>{fortune}</p>
      </div>

      {/* 다음 단계 */}
      <button onClick={() => router.push("/plan")}
              className="w-full py-4 rounded-full font-bold text-white mt-2"
              style={{ background: "var(--tarot-accent)" }}>
        오늘의 할 일 계획하기 →
      </button>
    </div>
  );
}
```

- [ ] **Step 3: 커밋**

```bash
git add frontend/src/app/fortune/ frontend/src/components/SentimentBadge.tsx
git commit -m "feat: 운세 결과 화면 — 카드, 감성 배지, 운세 텍스트"
```

---

### Task 12: 할 일 & 조언 화면 (`/plan`)

**Files:**
- Create: `frontend/src/app/plan/page.tsx`

- [ ] **Step 1: `plan/page.tsx` 구현**

```tsx
// frontend/src/app/plan/page.tsx
"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useDailyStore, type Condition } from "@/store/useDailyStore";
import { fetchAdvice } from "@/lib/api";
import LoadingSpinner from "@/components/LoadingSpinner";

const CONDITIONS: Condition[] = ["최고", "좋음", "보통", "나쁨"];

export default function PlanPage() {
  const router = useRouter();
  const { cards, nlpResult, condition, tasks, advice, adviceSummary,
          setCondition, setTasks, setAdvice } = useDailyStore();

  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (cards.length === 0) router.replace("/");
  }, [cards, router]);

  function addTask() {
    const t = input.trim();
    if (!t) return;
    setTasks([...tasks, t]);
    setInput("");
  }

  function removeTask(i: number) {
    setTasks(tasks.filter((_, idx) => idx !== i));
  }

  async function handleAdvice() {
    if (!condition || !nlpResult) return;
    setLoading(true);
    try {
      const result = await fetchAdvice(cards, condition, tasks, nlpResult);
      setAdvice(result.summary, result.advice);
    } finally {
      setLoading(false);
    }
  }

  if (cards.length === 0) return null;

  return (
    <div className="flex flex-col px-6 pt-6 gap-5">
      <div className="flex items-center gap-3">
        <button onClick={() => router.back()} style={{ color: "var(--tarot-muted)" }}>‹</button>
        <h2 className="text-lg font-bold">오늘의 할 일 & 조언</h2>
      </div>

      {/* 컨디션 */}
      <div>
        <p className="text-xs mb-2" style={{ color: "var(--tarot-muted)" }}>오늘 컨디션</p>
        <div className="flex gap-2">
          {CONDITIONS.map((c) => (
            <button key={c} onClick={() => setCondition(c)}
                    className="px-4 py-2 rounded-full text-sm font-medium transition-all"
                    style={{
                      background: condition === c ? "var(--tarot-accent)" : "var(--tarot-card)",
                      color: condition === c ? "white" : "var(--tarot-muted)",
                      border: `1px solid ${condition === c ? "var(--tarot-accent)" : "var(--tarot-border)"}`,
                    }}>
              {c}
            </button>
          ))}
        </div>
      </div>

      {/* 할 일 입력 */}
      <div>
        <p className="text-xs mb-2" style={{ color: "var(--tarot-muted)" }}>오늘 할 일</p>
        <div className="flex gap-2 mb-3">
          <input value={input} onChange={(e) => setInput(e.target.value)}
                 onKeyDown={(e) => e.key === "Enter" && addTask()}
                 placeholder="할 일 추가..."
                 className="flex-1 rounded-xl px-4 py-3 text-sm outline-none"
                 style={{ background: "var(--tarot-card)", color: "var(--tarot-text)",
                          border: "1px solid var(--tarot-border)" }} />
          <button onClick={addTask} className="px-4 py-3 rounded-xl text-sm font-bold"
                  style={{ background: "var(--tarot-accent)", color: "white" }}>+</button>
        </div>
        <ul className="flex flex-col gap-2">
          {tasks.map((t, i) => (
            <li key={i} className="flex items-center justify-between px-4 py-3 rounded-xl text-sm"
                style={{ background: "var(--tarot-card)" }}>
              <span style={{ color: "var(--tarot-text)" }}>· {t}</span>
              <button onClick={() => removeTask(i)} style={{ color: "var(--tarot-muted)" }}>✕</button>
            </li>
          ))}
        </ul>
      </div>

      {/* 조언 버튼 */}
      <button onClick={handleAdvice}
              disabled={!condition || loading}
              className="w-full py-4 rounded-full font-bold text-white disabled:opacity-40"
              style={{ background: "var(--tarot-accent)" }}>
        {loading ? "조언 생성 중..." : "✦ 카드 기반 조언 받기"}
      </button>

      {/* 조언 결과 */}
      {advice && (
        <div className="flex flex-col gap-3">
          <div className="rounded-xl p-4"
               style={{ background: "var(--tarot-card)", border: "1px solid var(--tarot-gold)" }}>
            <p className="text-sm font-bold" style={{ color: "var(--tarot-gold)" }}>{adviceSummary}</p>
          </div>
          <div>
            <p className="text-xs font-semibold mb-2" style={{ color: "var(--tarot-muted)" }}>오늘의 조언</p>
            <p className="text-sm leading-7" style={{ color: "var(--tarot-text)" }}>{advice}</p>
          </div>
        </div>
      )}
    </div>
  );
}
```

- [ ] **Step 2: 커밋**

```bash
git add frontend/src/app/plan/
git commit -m "feat: 할 일 & 조언 화면 — 컨디션 선택, 투두, LLM 조언"
```

---

### Task 13: 회고 화면 (`/retrospective`)

**Files:**
- Create: `frontend/src/app/retrospective/page.tsx`

- [ ] **Step 1: `retrospective/page.tsx` 구현**

```tsx
// frontend/src/app/retrospective/page.tsx
"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useDailyStore } from "@/store/useDailyStore";
import { fetchRetrospective, saveRecord } from "@/lib/api";

export default function RetrospectivePage() {
  const router = useRouter();
  const store = useDailyStore();
  const { cards, nlpResult, tasks, setRetrospective } = store;

  const [checked, setChecked] = useState<boolean[]>([]);
  const [loading, setLoading] = useState(false);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    if (cards.length === 0) router.replace("/");
    else setChecked(tasks.map(() => false));
  }, [cards, tasks, router]);

  function toggle(i: number) {
    setChecked((prev) => prev.map((v, idx) => idx === i ? !v : v));
  }

  async function handleRetro() {
    if (!nlpResult) return;
    const done = tasks.filter((_, i) => checked[i]);
    const notDone = tasks.filter((_, i) => !checked[i]);
    setLoading(true);
    try {
      const result = await fetchRetrospective(cards, done, notDone, nlpResult);
      setRetrospective(result.summary, result.retrospective, done, notDone);

      // Supabase 저장
      const s = useDailyStore.getState();
      await saveRecord({
        date: s.date, cards: s.cards.map(c => ({ id: c.id, name: c.name, reversed: c.reversed, direction: c.direction })),
        nlp_result: s.nlpResult, fortune: s.fortune, summary: s.summary,
        condition: s.condition, tasks: s.tasks, advice: s.advice, advice_summary: s.adviceSummary,
        completed_tasks: done, incomplete_tasks: notDone,
        retrospective: result.retrospective, retro_summary: result.summary,
      });
      setSaved(true);
    } finally {
      setLoading(false);
    }
  }

  if (cards.length === 0) return null;

  const { retrospective, retroSummary } = store;

  return (
    <div className="flex flex-col px-6 pt-6 gap-5">
      <div className="flex items-center gap-3">
        <button onClick={() => router.back()} style={{ color: "var(--tarot-muted)" }}>‹</button>
        <h2 className="text-lg font-bold">오늘의 회고</h2>
      </div>

      <p className="text-sm text-center" style={{ color: "var(--tarot-muted)" }}>
        하루를 마무리하며 돌아보는 시간
      </p>

      {/* 할 일 체크 */}
      <div>
        <div className="flex gap-2 mb-3">
          {["완료(체크)", "별(현재)", "미완(이동)"].map((t, i) => (
            <button key={i} className="px-3 py-1 rounded-full text-xs"
                    style={{ background: i === 1 ? "var(--tarot-surface)" : "transparent",
                             color: "var(--tarot-muted)", border: "1px solid var(--tarot-border)" }}>
              {t}
            </button>
          ))}
        </div>

        <p className="text-xs mb-3" style={{ color: "var(--tarot-muted)" }}>오늘 할 일 체크</p>
        <ul className="flex flex-col gap-2">
          {tasks.map((t, i) => (
            <li key={i} onClick={() => toggle(i)}
                className="flex items-center gap-3 px-4 py-3 rounded-xl cursor-pointer"
                style={{ background: "var(--tarot-card)" }}>
              <div className="w-5 h-5 rounded-full border-2 flex items-center justify-center"
                   style={{ borderColor: checked[i] ? "var(--tarot-accent)" : "var(--tarot-border)",
                            background: checked[i] ? "var(--tarot-accent)" : "transparent" }}>
                {checked[i] && <span className="text-white text-xs">✓</span>}
              </div>
              <span className="text-sm" style={{ color: checked[i] ? "var(--tarot-muted)" : "var(--tarot-text)",
                                                  textDecoration: checked[i] ? "line-through" : "none" }}>
                {t}
              </span>
            </li>
          ))}
        </ul>
      </div>

      <button onClick={handleRetro}
              disabled={loading || saved}
              className="w-full py-4 rounded-full font-bold text-white disabled:opacity-40"
              style={{ background: "var(--tarot-accent)" }}>
        {loading ? "회고 생성 중..." : saved ? "저장 완료 ✓" : "✦ AI 회고 생성하기"}
      </button>

      {retroSummary && (
        <div className="flex flex-col gap-3">
          <div className="rounded-xl p-4"
               style={{ background: "var(--tarot-card)", border: "1px solid var(--tarot-gold)" }}>
            <p className="text-sm font-bold" style={{ color: "var(--tarot-gold)" }}>{retroSummary}</p>
          </div>
          <div>
            <p className="text-xs font-semibold mb-2" style={{ color: "var(--tarot-muted)" }}>오늘의 회고</p>
            <p className="text-sm leading-7" style={{ color: "var(--tarot-text)" }}>{retrospective}</p>
          </div>
        </div>
      )}
    </div>
  );
}
```

- [ ] **Step 2: 커밋**

```bash
git add frontend/src/app/retrospective/
git commit -m "feat: 회고 화면 — 체크리스트, AI 회고, Supabase 저장"
```

---

### Task 14: 기록 화면 (`/history`)

**Files:**
- Create: `frontend/src/app/history/page.tsx`

- [ ] **Step 1: `history/page.tsx` 구현**

```tsx
// frontend/src/app/history/page.tsx
"use client";
import { useEffect, useState } from "react";
import { getRecords } from "@/lib/api";
import SentimentBadge from "@/components/SentimentBadge";
import LoadingSpinner from "@/components/LoadingSpinner";

type DailyRecord = {
  date: string; summary: string; retro_summary: string;
  cards: { name: string }[];
  nlp_result: { sentiment_label: string };
};

const FILTERS = ["전체", "운세", "계획", "회고"] as const;

export default function HistoryPage() {
  const now = new Date();
  const [year, setYear] = useState(now.getFullYear());
  const [month, setMonth] = useState(now.getMonth() + 1);
  const [records, setRecords] = useState<DailyRecord[]>([]);
  const [loading, setLoading] = useState(false);
  const [filter, setFilter] = useState<(typeof FILTERS)[number]>("전체");

  useEffect(() => {
    setLoading(true);
    getRecords(year, month).then(setRecords).finally(() => setLoading(false));
  }, [year, month]);

  function prevMonth() {
    if (month === 1) { setYear(y => y - 1); setMonth(12); }
    else setMonth(m => m - 1);
  }
  function nextMonth() {
    if (month === 12) { setYear(y => y + 1); setMonth(1); }
    else setMonth(m => m + 1);
  }

  const positive = records.filter(r => r.nlp_result?.sentiment_label === "positive").length;
  const rate = records.length > 0 ? Math.round((positive / records.length) * 100) : 0;

  return (
    <div className="flex flex-col px-6 pt-6 gap-5">
      <h2 className="text-lg font-bold">나의 타로 기록</h2>

      {/* 월 선택 */}
      <div className="flex items-center justify-center gap-4">
        <button onClick={prevMonth} style={{ color: "var(--tarot-muted)" }}>‹</button>
        <span className="font-semibold">{year}년 {month}월</span>
        <button onClick={nextMonth} style={{ color: "var(--tarot-muted)" }}>›</button>
      </div>

      {/* 필터 탭 */}
      <div className="flex gap-2">
        {FILTERS.map((f) => (
          <button key={f} onClick={() => setFilter(f)}
                  className="px-3 py-1 rounded-full text-xs font-medium"
                  style={{
                    background: filter === f ? "var(--tarot-accent)" : "var(--tarot-card)",
                    color: filter === f ? "white" : "var(--tarot-muted)",
                  }}>
            {f}
          </button>
        ))}
      </div>

      {loading ? <LoadingSpinner /> : (
        <>
          {/* 기록 목록 */}
          <ul className="flex flex-col gap-3">
            {records.map((rec) => (
              <li key={rec.date} className="rounded-xl p-4"
                  style={{ background: "var(--tarot-card)" }}>
                <div className="flex justify-between items-start mb-2">
                  <span className="text-xs" style={{ color: "var(--tarot-muted)" }}>
                    {new Date(rec.date).toLocaleDateString("ko-KR", { month:"long", day:"numeric", weekday:"short" })}
                  </span>
                  {rec.nlp_result && <SentimentBadge label={rec.nlp_result.sentiment_label} />}
                </div>
                <p className="text-xs mb-1" style={{ color: "var(--tarot-muted)" }}>
                  {rec.cards?.map(c => c.name).join(" · ")}
                </p>
                <p className="text-sm font-semibold" style={{ color: "var(--tarot-text)" }}>
                  {rec.summary}
                </p>
                {rec.retro_summary && (
                  <p className="text-xs mt-1" style={{ color: "var(--tarot-muted)" }}>회고: {rec.retro_summary}</p>
                )}
              </li>
            ))}
          </ul>

          {/* 월간 통계 */}
          {records.length > 0 && (
            <div className="rounded-xl p-4 flex justify-around"
                 style={{ background: "var(--tarot-card)" }}>
              <div className="text-center">
                <p className="text-2xl font-bold" style={{ color: "var(--tarot-accent)" }}>{records.length}</p>
                <p className="text-xs" style={{ color: "var(--tarot-muted)" }}>기록일</p>
              </div>
              <div className="text-center">
                <p className="text-2xl font-bold" style={{ color: "var(--tarot-gold)" }}>{rate}%</p>
                <p className="text-xs" style={{ color: "var(--tarot-muted)" }}>긍정 에너지</p>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
```

- [ ] **Step 2: 커밋**

```bash
git add frontend/src/app/history/
git commit -m "feat: 기록 화면 — 월별 히스토리, 감성 통계"
```

---

## Phase 3 — 배포

---

### Task 15: Railway 배포 설정

**Files:**
- Create: `Procfile`
- Create: `.env.example`

- [ ] **Step 1: `Procfile` 생성**

```
web: uvicorn main:app --host 0.0.0.0 --port $PORT
```

- [ ] **Step 2: `.env.example` 생성** (Railway 환경변수 참조용)

```
# Railway 환경변수 (실제 값은 Railway 대시보드에 입력)
GITHUB_TOKEN=ghp_xxxx
SUPABASE_URL=https://xxxx.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJxxx
ALLOWED_ORIGINS=https://your-app.vercel.app
```

- [ ] **Step 3: Railway 배포**

1. Railway 대시보드에서 새 프로젝트 생성 → GitHub 레포 연결
2. Root directory를 `11.NLP/mini-project/KDT12_NLP_Project` 으로 설정
3. 환경변수 4개 입력 (`.env.example` 참조)
4. 배포 후 `https://your-app.railway.app/health` → `{"status":"ok"}` 확인

- [ ] **Step 4: 커밋**

```bash
git add Procfile .env.example
git commit -m "feat: Railway 배포 설정 (Procfile, env.example)"
```

---

### Task 16: Vercel 배포 설정

**Files:**
- Create: `frontend/.env.production` (로컬 참조용, git에 포함 안 됨)

- [ ] **Step 1: Vercel 배포**

```bash
cd frontend
npx vercel
```

또는 Vercel 대시보드 → Import Project → GitHub 레포
- Root directory: `11.NLP/mini-project/KDT12_NLP_Project/frontend`
- Framework preset: Next.js (자동 감지)

- [ ] **Step 2: Vercel 환경변수 설정**

Vercel 대시보드 → Settings → Environment Variables:

| 변수명 | 값 |
|--------|-----|
| `NEXT_PUBLIC_API_URL` | Railway 서버 URL (예: `https://tarot-api.railway.app`) |
| `NEXT_PUBLIC_SUPABASE_URL` | Supabase 프로젝트 URL |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Supabase anon key |

- [ ] **Step 3: Railway `ALLOWED_ORIGINS` 업데이트**

Railway 환경변수에서 `ALLOWED_ORIGINS`를 Vercel 배포 URL로 업데이트:
```
ALLOWED_ORIGINS=https://your-app.vercel.app
```

- [ ] **Step 4: 배포 확인**

Vercel 도메인 접속 → 홈 화면 → 카드 뽑기 → 운세 → 할 일 & 조언 → 회고 → 기록 전 흐름 확인.

- [ ] **Step 5: 최종 커밋**

```bash
git add .
git commit -m "chore: Vercel 배포 완료, 전체 플로우 검증"
```

---

## 전체 테스트 실행 명령

```bash
# 백엔드 전체 테스트
cd KDT12_NLP_Project
pytest tests/ -v

# 프론트엔드 린트
cd frontend
npm run lint
```
