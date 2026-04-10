# llm_handler.py

from openai import OpenAI
from dotenv import load_dotenv
import os
from prompts import (
    SPREAD_POSITIONS,
    FORTUNE_SYSTEM,  FORTUNE_USER,
    ADVICE_SYSTEM,   ADVICE_USER,
    RETROSPECTIVE_SYSTEM, RETROSPECTIVE_USER
)

load_dotenv("GITHUB_TOKEN.env")

client = OpenAI(
    base_url="https://models.inference.ai.azure.com",
    api_key=os.getenv("GITHUB_TOKEN")
)


def _call_llm(system_prompt, user_prompt, temperature=0.7):
    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=temperature,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_prompt}
        ]
    )
    return completion.choices[0].message.content


def _cards_to_text(cards):
    """카드 리스트 → 과거-현재-미래 위치 포함 텍스트"""
    lines = []
    for i, card in enumerate(cards):
        position = SPREAD_POSITIONS[i]
        direction = "역방향" if card.get("reversed") else "정방향"
        lines.append(
            f"- {position['name']} 자리 ({position['desc']}): "
            f"{card['name']} ({direction})"
        )
    return "\n".join(lines)


def generate_fortune(cards, nlp_result, temperature=0.7):
    system_prompt = FORTUNE_SYSTEM
    user_prompt = FORTUNE_USER.format(
        cards_text=_cards_to_text(cards),
        keywords=", ".join(nlp_result.get("keywords", [])),
        sentiment_label=nlp_result.get("sentiment_label", ""),
        sentiment_score=nlp_result.get("sentiment_score", "")
    )
    return _call_llm(system_prompt, user_prompt, temperature)


def generate_advice(cards, tasks, condition, nlp_result, temperature=0.7):
    system_prompt = ADVICE_SYSTEM
    user_prompt = ADVICE_USER.format(
        cards_text=_cards_to_text(cards),
        condition=condition,
        tasks=tasks,
        keywords=", ".join(nlp_result.get("keywords", [])),
        sentiment_label=nlp_result.get("sentiment_label", "")
    )
    return _call_llm(system_prompt, user_prompt, temperature)


def generate_retrospective(cards, completed_tasks, incomplete_tasks, nlp_result, temperature=0.7):
    system_prompt = RETROSPECTIVE_SYSTEM
    user_prompt = RETROSPECTIVE_USER.format(
        cards_text=_cards_to_text(cards),
        completed_tasks=completed_tasks if completed_tasks else ["없음"],
        incomplete_tasks=incomplete_tasks if incomplete_tasks else ["없음"],
        keywords=", ".join(nlp_result.get("keywords", []))
    )
    return _call_llm(system_prompt, user_prompt, temperature)