"""
- 프롬프트 3종 (운세용 / 조언용 / 회고용)
- temperature 실험 (0.3 / 0.7 / 1.0)
- 실험 결과 CSV 저장
"""
 
import json
import random
import os
import csv
from datetime import datetime
from openai import OpenAI
from dotenv import load_dotenv
 
load_dotenv()
client = OpenAI(api_key=os.getenv("GITHUB_TOKEN"))
 
 
# ─────────────────────────────────────────
# 카드 불러오기 + 뽑기
# ─────────────────────────────────────────
 
def load_cards(path="cards.json"):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)["cards"]
 
 
def draw_cards(n=3):
    """카드 n장 뽑기. 각 카드는 50% 확률로 역방향 적용."""
    cards = load_cards()
    drawn = random.sample(cards, n)
    for card in drawn:
        card["is_reversed"] = random.random() < 0.5
        card["active_meaning"] = (
            card["meaning_reversed"] if card["is_reversed"] else card["meaning"]
        )
        card["direction"] = "역방향" if card["is_reversed"] else "정방향"
    return drawn
 
 
def format_card_info(cards):
    """카드 정보를 프롬프트용 텍스트로 변환."""
    lines = []
    positions = ["과거·원인", "현재·상황", "미래·조언"]
    for pos, card in zip(positions, cards):
        lines.append(
            f"  [{pos}] {card['name']} ({card['direction']})\n"
            f"    의미: {card['active_meaning']}\n"
            f"    키워드: {', '.join(card['keywords'])}"
        )
    return "\n".join(lines)
 
 
# ─────────────────────────────────────────
# 프롬프트 3종
# ─────────────────────────────────────────
 
def prompt_fortune(cards, condition, todo):
    """
    [1번] 운세용 프롬프트
    - 카드 + 컨디션 + 할 일 → 오늘의 운세 생성
    - 기획안 2단계 '오늘의 운세' 에 해당
    """
    card_text = format_card_info(cards)
    return f"""당신은 따뜻하고 직관적인 타로 카드 리더입니다.
오늘 뽑힌 카드를 바탕으로 사용자의 오늘 하루 운세를 알려주세요.
 
[카드 정보]
{card_text}
 
[사용자 정보]
- 오늘 컨디션: {condition}
- 오늘 할 일: {todo}
 
아래 형식으로 작성해 주세요:
 
🌟 오늘의 전체 운세
(카드 3장의 흐름을 연결해 오늘의 전반적인 흐름을 2~3문장으로)
 
⚡ 주의할 점
(오늘 조심해야 할 것 1가지를 1문장으로)
 
✨ 오늘의 키워드
(오늘을 대표하는 단어 3개, 쉼표로 구분)
 
말투는 친근하고 따뜻하게, 지나치게 신비롭지 않게 써주세요."""
 
 
def prompt_advice(cards, condition, todo):
    """
    [2번] 조언용 프롬프트
    - 카드 + 컨디션 + 할 일 → 구체적 하루 계획 제안
    - 기획안 5단계 '카드 기반 조언' 에 해당
    """
    card_text = format_card_info(cards)
    return f"""당신은 실용적인 조언을 해주는 타로 카드 상담사입니다.
오늘 뽑힌 카드와 사용자 상황을 바탕으로 구체적인 하루 행동 계획을 제안해 주세요.
 
[카드 정보]
{card_text}
 
[사용자 정보]
- 오늘 컨디션: {condition}
- 오늘 할 일: {todo}
 
아래 형식으로 작성해 주세요:
 
🌅 오전 (09:00~12:00)
• (카드 에너지를 반영한 구체적 행동 1가지)
 
☀️ 오후 (13:00~18:00)
• (카드 에너지를 반영한 구체적 행동 1가지)
 
🌙 저녁 (19:00~22:00)
• (카드 에너지를 반영한 구체적 행동 1가지)
 
💡 오늘의 한 마디
(하루를 관통하는 짧고 인상적인 한 문장)
 
행동은 실제로 할 수 있는 것으로, 추상적이지 않게 작성해 주세요."""
 
 
def prompt_review(cards, condition, todo):
    """
    [3번] 회고용 프롬프트
    - 카드 + 컨디션 + 할 일 → 저녁 회고 질문 생성
    - 기획안 저녁 회고 파트에 해당
    """
    card_text = format_card_info(cards)
    return f"""당신은 하루를 의미 있게 마무리하도록 돕는 타로 카드 가이드입니다.
오늘 뽑힌 카드를 바탕으로 저녁 회고를 위한 질문을 만들어 주세요.
 
[카드 정보]
{card_text}
 
[사용자 정보]
- 오늘 컨디션: {condition}
- 오늘 할 일: {todo}
 
아래 형식으로 작성해 주세요:
 
🌙 오늘 하루 돌아보기
 
Q1. (오늘 카드 메시지와 연결된 성찰 질문 1개)
 
Q2. (오늘 할 일과 연결된 구체적 회고 질문 1개)
 
Q3. (내일을 위한 준비 질문 1개)
 
🌟 오늘의 타로 메시지
(하루를 마무리하는 따뜻한 한 마디)
 
질문은 간결하고 답하기 쉬운 형태로 작성해 주세요."""
 
 
# ─────────────────────────────────────────
# API 호출 공통 함수
# ─────────────────────────────────────────
 
def call_api(prompt_text, temperature=0.7):
    """OpenAI API 호출. temperature 조절 가능."""
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "당신은 친근하고 따뜻한 타로 카드 상담사입니다."
                },
                {
                    "role": "user",
                    "content": prompt_text
                }
            ],
            temperature=temperature,
            max_tokens=800,
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"⚠️ 오류: {str(e)}"
 
 
def get_all_plans(cards, condition, todo, temperature=0.7):
    """프롬프트 3종을 모두 호출해 결과를 딕셔너리로 반환."""
    return {
        "fortune": call_api(prompt_fortune(cards, condition, todo), temperature),
        "advice":  call_api(prompt_advice(cards, condition, todo), temperature),
        "review":  call_api(prompt_review(cards, condition, todo), temperature),
    }
 
 
# ─────────────────────────────────────────
# temperature 실험 (A 역할 핵심 업무)
# ─────────────────────────────────────────
 
def run_temperature_experiment(condition="보통", todo="팀 프로젝트 마무리"):
    """
    동일한 카드 + 컨디션 + 할 일로
    temperature 0.3 / 0.7 / 1.0 결과를 비교해 CSV로 저장.
 
    기획안 2페이지 '실험 설계' 그대로 구현.
    """
    print("=" * 50)
    print("temperature 실험 시작")
    print(f"컨디션: {condition} | 할 일: {todo}")
    print("=" * 50)
 
    # 동일한 카드로 실험 (고정)
    cards = draw_cards(3)
    print("\n[고정 카드]")
    for c in cards:
        print(f"  - {c['name']} ({c['direction']})")
 
    temperatures = [0.3, 0.7, 1.0]
    results = []
 
    for temp in temperatures:
        print(f"\n⏳ temperature={temp} 실험 중...")
        # 운세용 프롬프트로만 비교 (대표 실험)
        prompt_text = prompt_fortune(cards, condition, todo)
        result = call_api(prompt_text, temperature=temp)
 
        results.append({
            "temperature": temp,
            "card_1": cards[0]["name"],
            "card_2": cards[1]["name"],
            "card_3": cards[2]["name"],
            "condition": condition,
            "todo": todo,
            "result": result,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        })
        print(f"✅ temperature={temp} 완료")
        print("-" * 40)
        print(result[:200] + "...")  # 앞부분만 미리보기
 
    # CSV 저장
    filename = f"experiment_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    with open(filename, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=results[0].keys())
        writer.writeheader()
        writer.writerows(results)
 
    print(f"\n✅ 실험 완료! 결과 저장됨: {filename}")
    print("\n[보고서용 요약]")
    print(f"{'temperature':<15} {'특성'}")
    print("-" * 40)
    print(f"{'0.3':<15} 일관성 높음, 창의성 낮음 — 비슷한 표현 반복")
    print(f"{'0.7':<15} 균형 — 적절한 다양성과 일관성")
    print(f"{'1.0':<15} 창의성 높음, 일관성 낮음 — 해석이 다양하지만 산발적")
    print(f"\n결과 파일 '{filename}'을 열어 직접 비교해 보세요.")
 
    return results, filename
 
 
# ─────────────────────────────────────────
# 직접 실행 시 실험 자동 수행
# ─────────────────────────────────────────
 
if __name__ == "__main__":
    import sys
 
    if len(sys.argv) > 1 and sys.argv[1] == "experiment":
        # python prompts.py experiment
        run_temperature_experiment(
            condition="보통",
            todo="팀 프로젝트 마무리"
        )
    else:
        # python prompts.py → 단일 테스트
        print("=== 프롬프트 3종 단일 테스트 ===")
        cards = draw_cards(3)
        print("\n[뽑힌 카드]")
        for c in cards:
            print(f"  - {c['name']} ({c['direction']})")
 
        condition = "보통"
        todo = "팀 프로젝트 발표 준비"
 
        print("\n[1] 운세용 프롬프트 미리보기:")
        print(prompt_fortune(cards, condition, todo)[:300] + "...\n")
 
        print("[2] 조언용 프롬프트 미리보기:")
        print(prompt_advice(cards, condition, todo)[:300] + "...\n")
 
        print("[3] 회고용 프롬프트 미리보기:")
        print(prompt_review(cards, condition, todo)[:300] + "...")
 
        print("\n API 호출 없이 프롬프트 구조만 확인했습니다.")
        print("실제 API 실험은: python prompts.py experiment")