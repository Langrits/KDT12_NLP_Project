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
    """LLM 응답에서 한 줄 요약과 오늘의 회고 본문을 분리한다."""
    summary, body = "", ""
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
