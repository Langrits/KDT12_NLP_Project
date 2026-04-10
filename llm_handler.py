# llm/llm_handler.py

from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv("GITHUB_TOKEN.env")

client = OpenAI(
    base_url="https://models.inference.ai.azure.com",
    api_key=os.getenv("GITHUB_TOKEN")
)

def _call_llm(system_prompt, user_prompt, temperature=0.7):
    """공통 LLM 호출 함수 — 내부에서만 사용"""
    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=temperature,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_prompt}
        ]
    )
    return completion.choices[0].message.content


def generate_fortune(cards, nlp_result, temperature=0.7):
    """1단계: 카드 기반 오늘의 운세 생성"""
    system_prompt = "당신은 타로 리더입니다. 카드의 상징성을 바탕으로 오늘의 운세를 해석해주세요. 행동을 규정하지 말고 참고할 관점을 제시해주세요."
    
    user_prompt = f"""
뽑힌 카드:
{chr(10).join([f"- {c['name_kr']} ({'역방향' if c['reversed'] else '정방향'})" for c in cards])}

카드 키워드: {nlp_result.get('keywords', [])}
에너지 점수: {nlp_result.get('sentiment_label', '')}

오늘의 운세를 3~4문장으로 해석해주세요.
"""
    return _call_llm(system_prompt, user_prompt, temperature)


def generate_advice(cards, tasks, condition, nlp_result, temperature=0.7):
    """2단계: 할 일에 대한 카드 기반 조언 생성"""
    system_prompt = "당신은 타로 리더입니다. 사용자의 오늘 할 일에 대해 카드의 에너지를 바탕으로 조언해주세요."

    user_prompt = f"""
오늘 뽑은 카드:
{chr(10).join([f"- {c['name_kr']} ({'역방향' if c['reversed'] else '정방향'})" for c in cards])}

오늘 컨디션: {condition}
오늘 할 일: {tasks}
카드 키워드: {nlp_result.get('keywords', [])}

각 할 일에 대해 카드 관점에서 짧게 조언해주세요.
"""
    return _call_llm(system_prompt, user_prompt, temperature)


def generate_retrospective(cards, completed_tasks, incomplete_tasks, nlp_result, temperature=0.7):
    """3단계: 저녁 회고 생성"""
    system_prompt = "당신은 타로 리더입니다. 아침에 뽑은 카드를 회고의 렌즈로 재해석하여 오늘 하루를 총평해주세요."

    user_prompt = f"""
오늘 아침 뽑은 카드:
{chr(10).join([f"- {c['name_kr']} ({'역방향' if c['reversed'] else '정방향'})" for c in cards])}

완료한 일: {completed_tasks}
완료 못한 일: {incomplete_tasks}
카드 키워드: {nlp_result.get('keywords', [])}

오늘 하루를 카드의 관점에서 재해석해서 총평해주세요.
잘한 점과 내일을 위한 한마디도 포함해주세요.
"""
    return _call_llm(system_prompt, user_prompt, temperature)