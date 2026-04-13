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
    assert data["summary"] == "흐름을 따라"
    assert data["advice"] == "잘 할 수 있어요"


def test_advice_requires_condition(client):
    resp = client.post("/advice", json={
        "cards": SAMPLE_CARDS,
        "tasks": ["보고서 작성"],
        "nlp_result": SAMPLE_NLP,
    })
    assert resp.status_code == 422
