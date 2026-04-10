"""
llm_handler.py
B 담당 — LLM 호출 함수 모음
"""

from openai import OpenAI
from dotenv import load_dotenv
import os
from prompts import (
    FORTUNE_SYSTEM, FORTUNE_USER,
    ADVICE_SYSTEM, ADVICE_USER,
    RETROSPECTIVE_SYSTEM, RETROSPECTIVE_USER
)

load_dotenv("GITHUB_TOKEN.env")

client = OpenAI(
    base_url="https://models.inference.ai.azure.com",
    api_key=os.getenv("GITHUB_TOKEN")
)


def _call_llm(system_prompt, user_prompt, temperature=0.7):
    """공통 LLM 호출 함수"""
    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=temperature,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_prompt}
        ]
    )
    return completion.choices[0].message.content


from prompts import (
    FORTUNE_SYSTEM, FORTUNE_USER,
    ADVICE_SYSTEM, ADVICE_USER,
    RETROSPECTIVE_SYSTEM, RETROSPECTIVE_USER
)

def generate_fortune(cards, nlp_result, temperature=0.7):
    cards_text = "\n".join([
        f"- {c['name']} ({'역방향' if c.get('reversed') else '정방향'})"
        for c in cards
    ])
    system_prompt = FORTUNE_SYSTEM
    user_prompt = FORTUNE_USER.format(
        cards_text=cards_text,
        keywords=', '.join(nlp_result.get('keywords', [])),
        sentiment_label=nlp_result.get('sentiment_label', ''),
        sentiment_score=nlp_result.get('sentiment_score', '')
    )
    return _call_llm(system_prompt, user_prompt, temperature)


def generate_advice(cards, tasks, condition, nlp_result, temperature=0.7):
    cards_text = "\n".join([
        f"- {c['name']} ({'역방향' if c.get('reversed') else '정방향'})"
        for c in cards
    ])
    system_prompt = ADVICE_SYSTEM
    user_prompt = ADVICE_USER.format(
        cards_text=cards_text,
        condition=condition,
        tasks=tasks,
        keywords=', '.join(nlp_result.get('keywords', [])),
        sentiment_label=nlp_result.get('sentiment_label', '')
    )
    return _call_llm(system_prompt, user_prompt, temperature)


def generate_retrospective(cards, completed_tasks, incomplete_tasks, nlp_result, temperature=0.7):
    cards_text = "\n".join([
        f"- {c['name']} ({'역방향' if c.get('reversed') else '정방향'})"
        for c in cards
    ])
    system_prompt = RETROSPECTIVE_SYSTEM
    user_prompt = RETROSPECTIVE_USER.format(
        cards_text=cards_text,
        completed_tasks=completed_tasks,
        incomplete_tasks=incomplete_tasks,
        keywords=', '.join(nlp_result.get('keywords', [])),
    )
    return _call_llm(system_prompt, user_prompt, temperature)