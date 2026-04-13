# terminal_test.py

import random
from nlp_handler import extract_keywords, analyze_sentiment, load_cards
from llm_handler import generate_fortune, generate_advice, generate_retrospective

# ─────────────────────────────────────────────
# 유틸 함수
# ─────────────────────────────────────────────

TEMPERATURE = 0.7

def print_divider(title=""):
    if title:
        print(f"\n{'=' * 40}")
        print(f"  {title}")
        print('=' * 40)
    else:
        print('=' * 40)

def input_valid(prompt, valid_range, count=1, allow_duplicate=False):
    """
    유효한 번호 입력받기
    - count: 입력받을 개수
    - valid_range: 유효한 번호 범위 (list)
    """
    while True:
        try:
            raw = input(prompt).strip()
            nums = list(map(int, raw.split()))

            if len(nums) != count:
                print(f"  ⚠ {count}개를 입력해주세요. 다시 입력하세요.")
                continue

            if not allow_duplicate and len(nums) != len(set(nums)):
                print("  ⚠ 중복된 번호가 있습니다. 다시 입력하세요.")
                continue

            if not all(n in valid_range for n in nums):
                print(f"  ⚠ {min(valid_range)}~{max(valid_range)} 사이 번호를 입력하세요.")
                continue

            return nums

        except ValueError:
            print("  ⚠ 숫자만 입력하세요. (예: 1 5 13)")


def input_tasks():
    """할 일 입력 — 쉼표 구분"""
    while True:
        raw = input("입력: ").strip()
        tasks = [t.strip() for t in raw.split(",") if t.strip()]
        if not tasks:
            print("  ⚠ 최소 1개 이상 입력하세요.")
            continue
        return tasks


# ─────────────────────────────────────────────
# 메인
# ─────────────────────────────────────────────

def main():
    print_divider("🔮 타로 하루 플래너 — 터미널 테스트")

    # ── 카드 데이터 로드 ──
    cards_normal   = load_cards("cards_original.json")
    cards_reversed = load_cards("cards_reversed.json")

    # 22장 합치고 정/역방향 랜덤 적용
    all_cards = []
    for i in range(22):
        is_reversed = random.choice([True, False])
        card = {
            **cards_normal[i],          # name은 정방향 기준으로 통일
            "reversed": is_reversed,
            "meaning": cards_reversed[i]["meaning"] if is_reversed else cards_normal[i]["meaning"],
            "keywords": cards_reversed[i]["keywords"] if is_reversed else cards_normal[i]["keywords"],
            "energy": cards_reversed[i]["energy"] if is_reversed else cards_normal[i]["energy"],
        }
        all_cards.append(card)

    # 섞기
    random.shuffle(all_cards)

    # ── 1단계: 카드 선택 ──
    print(f"1 ~ 22 중 번호 3개를 선택하세요.\n")

    selected_nums = input_valid(
        "번호를 3개 입력하세요 (예: 1 5 13): ",
        valid_range=list(range(1, 23)),
        count=3
    )
    selected = [all_cards[n - 1] for n in selected_nums]

    print("\n선택한 카드:")
    for card in selected:
        direction = "역방향" if card["reversed"] else "정방향"
        print(f"  - {card['name']} ({direction})")

    # ── NLP 전처리 ──
    combined_meaning = " ".join([c["meaning"] for c in selected])
    keywords  = extract_keywords(combined_meaning, top_n=5)
    sentiment = analyze_sentiment(combined_meaning)

    nlp_result = {
        "keywords":        keywords,
        "sentiment_score": sentiment["sentiment_score"],
        "sentiment_label": sentiment["sentiment_label"]
    }

    print(f"\n📌 카드 키워드: {', '.join(nlp_result['keywords'])}")
    print(f"📌 오늘의 에너지: {nlp_result['sentiment_label']} ({nlp_result['sentiment_score']})")

    # ── 2단계: 운세 출력 ──
    print_divider("2단계 | 오늘의 운세")
    print("🔮 운세를 뽑는 중...\n")
    fortune = generate_fortune(selected, nlp_result, temperature = TEMPERATURE)
    print(fortune)

    # ── 3단계: 컨디션 입력 ──
    print_divider("3단계 | 오늘의 컨디션")
    print("오늘 컨디션을 선택하세요.")
    print("  1. 😴 피곤함   2. 😐 보통   3. ⚡ 에너지 넘침\n")

    condition_map = {1: "피곤함", 2: "보통", 3: "에너지 넘침"}
    condition_num = input_valid("입력: ", valid_range=[1, 2, 3], count=1)[0]
    condition = condition_map[condition_num]
    print(f"  → {condition} 선택됨")

    # ── 4단계: 할 일 입력 ──
    print_divider("4단계 | 오늘 할 일")
    print("오늘 할 일을 입력하세요. (쉼표로 구분)")
    print("예: 팀발표, 운동, 독서\n")
    tasks = input_tasks()

    print("\n📋 입력된 할 일:")
    for i, task in enumerate(tasks):
        print(f"  {i+1}. {task}")

    # ── 5단계: 조언 출력 ──
    print_divider("5단계 | 오늘의 조언")
    print("💬 조언을 생성하는 중...\n")
    advice = generate_advice(
        cards=selected,
        tasks=", ".join(tasks),
        condition=condition,
        nlp_result=nlp_result,
        temperature = TEMPERATURE
    )
    print(advice)

    # ── 6단계: 할 일 목록 정리 ──
    print_divider("6단계 | 하루 마무리")
    print("📋 오늘의 할 일 목록\n")
    for i, task in enumerate(tasks):
        print(f"  {i+1}. {task}")

    # ── 7단계: 완료 항목 입력 ──
    print("\n완료한 항목 번호를 입력하세요.")
    print("예: 1 3  (없으면 0 입력)\n")

    while True:
        raw = input("입력: ").strip()
        try:
            if raw == "0":
                completed_nums = []
                break
            completed_nums = list(map(int, raw.split()))
            valid = list(range(1, len(tasks) + 1))
            if all(n in valid for n in completed_nums):
                break
            print(f"  ⚠ 1~{len(tasks)} 사이 번호를 입력하세요.")
        except ValueError:
            print("  ⚠ 숫자만 입력하세요.")

    completed   = [tasks[n - 1] for n in completed_nums]
    incomplete  = [t for t in tasks if t not in completed]

    print()
    for task in tasks:
        status = "✅" if task in completed else "❌"
        print(f"  {status} {task}")

    # ── 8단계: 회고 출력 ──
    print_divider("8단계 | 오늘의 회고")
    print("📝 회고를 생성하는 중...\n")
    retrospective = generate_retrospective(
        cards=selected,
        completed_tasks=completed if completed else ["없음"],
        incomplete_tasks=incomplete if incomplete else ["없음"],
        nlp_result=nlp_result,
        temperature = TEMPERATURE
    )
    print(retrospective)

    print_divider("🔮 오늘 하루도 수고했어요!")


if __name__ == "__main__":
    main()