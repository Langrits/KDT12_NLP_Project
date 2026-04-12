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
