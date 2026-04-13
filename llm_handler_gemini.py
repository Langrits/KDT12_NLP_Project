"""
llm_handler_gemini.py
Gemini 버전 LLM 핸들러
기존 llm_handler.py 건드리지 않음
"""

from openai import OpenAI
from dotenv import load_dotenv
import os
from prompts import (
    SPREAD_POSITIONS,
    FORTUNE_SYSTEM,  FORTUNE_USER,
    ADVICE_SYSTEM,   ADVICE_USER,
    RETROSPECTIVE_SYSTEM, RETROSPECTIVE_USER
)

load_dotenv("GEMINI_API_KEY.env")

client = OpenAI(
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
    api_key=os.getenv("GEMINI_API_KEY")
)

MODEL = "gemini-3.1-flash-lite-preview"


def _call_llm(system_prompt, user_prompt, temperature=0.7):
    completion = client.chat.completions.create(
        model=MODEL,
        temperature=temperature,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_prompt}
        ]
    )
    return completion.choices[0].message.content


def _cards_to_text(cards):
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