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
