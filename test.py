from LMM.mini_project.KDT12_NLP_Project.llm_handler import generate_fortune, generate_advice, generate_retrospective

# 임시 테스트 데이터 (나중에 C한테 받을 nlp_result 형식)
test_cards = [
    {"name_kr": "달", "reversed": True},
    {"name_kr": "태양", "reversed": False},
    {"name_kr": "탑", "reversed": False},
]

test_nlp = {
    "keywords": ["혼란", "활력", "변화"],
    "sentiment_label": "neutral",
    "sentiment_score": 0.5
}

# 운세 생성 테스트
print("=== 운세 ===")
print(generate_fortune(test_cards, test_nlp))

# 조언 생성 테스트
print("\n=== 조언 ===")
print(generate_advice(test_cards, "오후에 팀 발표, 저녁에 운동", "보통", test_nlp))