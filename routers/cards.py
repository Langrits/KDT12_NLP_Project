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
