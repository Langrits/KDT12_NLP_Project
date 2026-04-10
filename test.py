"""
test.py
전체 파이프라인 테스트
nlp_handler → llm_handler 순서로 실행
"""

import json
from nlp_handler import (
    preprocess_card,
    postprocess_fortune,
    compare_keywords,
    load_cards
)
from llm_handler import (
    generate_fortune,
    generate_advice,
    generate_retrospective
)

# ── 1. 카드 데이터 로드 ──
cards_normal   = load_cards("cards_original.json")
cards_reversed = load_cards("cards_reversed.json")

# ── 2. 카드 3장 선택 (테스트용 고정) ──
selected = [
    {**cards_normal[18],   "reversed": False},   # 달 (정방향)
    {**cards_normal[19],   "reversed": False},   # 태양 (정방향)
    {**cards_reversed[16], "reversed": True},    # 탑 (역방향)
]

# ── 3. NLP 전처리 ──
# 카드 3장 의미 텍스트 합쳐서 분석
combined_meaning = " ".join([c["meaning"] for c in selected])

from nlp_handler import extract_keywords, analyze_sentiment
keywords  = extract_keywords(combined_meaning, top_n=5)
sentiment = analyze_sentiment(combined_meaning)

nlp_result = {
    "keywords":        keywords,
    "sentiment_score": sentiment["sentiment_score"],
    "sentiment_label": sentiment["sentiment_label"]
}

print("=" * 40)
print("📌 NLP 전처리 결과")
print(f"키워드: {nlp_result['keywords']}")
print(f"감성:   {nlp_result['sentiment_label']} ({nlp_result['sentiment_score']})")

# ── 4. 운세 생성 ──
print("\n" + "=" * 40)
print("🔮 오늘의 운세")
fortune = generate_fortune(selected, nlp_result)
print(fortune)

# ── 5. 조언 생성 ──
print("\n" + "=" * 40)
print("💬 오늘의 조언")
advice = generate_advice(
    cards=selected,
    tasks="오후에 팀 발표, 저녁에 운동",
    condition="보통",
    nlp_result=nlp_result
)
print(advice)

# ── 6. 회고 생성 ──
print("\n" + "=" * 40)
print("📝 오늘의 회고")
retrospective = generate_retrospective(
    cards=selected,
    completed_tasks=["팀 발표"],
    incomplete_tasks=["저녁 운동"],
    nlp_result=nlp_result
)
print(retrospective)

# ── 7. LLM 운세 텍스트 후처리 ──
print("\n" + "=" * 40)
print("📊 LLM 운세 후처리 결과")
post_result = postprocess_fortune(fortune)
print(f"LLM 키워드: {post_result['keywords']}")
print(f"LLM 감성:   {post_result['sentiment_label']} ({post_result['sentiment_score']})")

# ── 8. 키워드 비교 ──
print("\n" + "=" * 40)
print("🔍 카드 원본 키워드 vs LLM 키워드 비교")
original_keywords = [kw for c in selected for kw in c.get("keywords", [])]
comparison = compare_keywords(original_keywords, post_result["keywords"])
print(f"일치 키워드: {comparison['matched_keywords']}")
print(f"일치율:      {comparison['match_rate'] * 100:.1f}%")