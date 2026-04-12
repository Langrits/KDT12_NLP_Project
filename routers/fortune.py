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
    summary, body = "", ""
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
