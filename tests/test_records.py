# tests/test_records.py
from unittest.mock import MagicMock, patch

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
    mock_sb.table.return_value.select.return_value.gte.return_value.lt.return_value.order.return_value.execute.return_value.data = [
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
