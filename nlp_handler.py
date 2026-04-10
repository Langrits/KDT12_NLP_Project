"""
nlp_handler.py
C 담당 — KeyBERT 키워드 추출 + 감성 분석 파이프라인
B한테 넘길 nlp_result 딕셔너리 생성
"""

import json
import os
from keybert import KeyBERT
from transformers import pipeline
from sentence_transformers import SentenceTransformer

# ─────────────────────────────────────────────
# 모델 초기화 (파일 import 시 한 번만 로드)
# ─────────────────────────────────────────────

# KeyBERT — 한국어 포함 다국어 모델
from sentence_transformers import SentenceTransformer
st_model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
kw_model = KeyBERT(model=st_model)

# 감성 분석 — snunlp/KR-ELECTRA (한국어 특화)
sentiment_pipeline = pipeline(
    "text-classification",
    model="lxyuan/distilbert-base-multilingual-cased-sentiments-student",
    top_k=None  # 전체 레이블 점수 반환
)


# ─────────────────────────────────────────────
# 1. 키워드 추출
# ─────────────────────────────────────────────

from konlpy.tag import Okt
okt = Okt()

def extract_keywords(text: str, top_n: int = 5) -> list[str]:
    # 형태소 분석으로 명사만 추출
    nouns = okt.nouns(text)
    # 한 글자 단어 제거
    nouns = [n for n in nouns if len(n) > 1]
    noun_text = " ".join(nouns)
    
    if not noun_text.strip():
        return nouns[:top_n]
    
    results = kw_model.extract_keywords(
        noun_text,
        keyphrase_ngram_range=(1, 1),  # 명사만 쓰니까 1단어로
        stop_words=None,
        top_n=top_n,
        use_mmr=True,
        diversity=0.5,
        candidates=None
    )
    return [kw for kw, score in results]


# ─────────────────────────────────────────────
# 2. 감성 분석
# ─────────────────────────────────────────────

def analyze_sentiment(text: str) -> dict:
    """
    텍스트의 긍정/부정 감성 점수 반환
    
    Args:
        text: 분석할 텍스트
    
    Returns:
        {
            "sentiment_score": float (0~1, 1에 가까울수록 긍정),
            "sentiment_label": str ("positive" or "negative")
        }
    """
    results = sentiment_pipeline(text)[0]  # 리스트 안의 첫 번째 결과
    
    # 레이블별 점수 추출
    scores = {item["label"]: item["score"] for item in results}
    
    # 모델 레이블: "positive" / "negative" (또는 "LABEL_0" / "LABEL_1")
    # snunlp 모델 기준으로 positive 점수 사용
    if "positive" in scores:
        pos_score = scores["positive"]
    elif "LABEL_1" in scores:
        pos_score = scores["LABEL_1"]
    else:
        # fallback: 가장 높은 점수 레이블이 positive인지 판단
        top = max(results, key=lambda x: x["score"])
        pos_score = top["score"] if "pos" in top["label"].lower() else 1 - top["score"]
    
    label = "positive" if pos_score >= 0.5 else "negative"
    
    return {
        "sentiment_score": round(pos_score, 4),
        "sentiment_label": label
    }


# ─────────────────────────────────────────────
# 3. 전처리 함수 — B한테 넘길 nlp_result 생성
# ─────────────────────────────────────────────

def preprocess_card(card: dict) -> dict:
    """
    카드 데이터를 받아 NLP 전처리 후 B에게 넘길 딕셔너리 반환
    
    Args:
        card: cards.json 또는 cards_reversed.json의 카드 딕셔너리
              {"id": 0, "name": "바보", "meaning": "...", "keywords": [...], ...}
    
    Returns:
        B와 합의한 형식:
        {
            "keywords": [...],
            "sentiment_score": float,
            "sentiment_label": str
        }
    """
    meaning_text = card.get("meaning", "")
    
    keywords = extract_keywords(meaning_text, top_n=5)
    sentiment = analyze_sentiment(meaning_text)
    
    return {
        "keywords": keywords,
        "sentiment_score": sentiment["sentiment_score"],
        "sentiment_label": sentiment["sentiment_label"]
    }


# ─────────────────────────────────────────────
# 4. 후처리 함수 — LLM 운세 텍스트 재분석
# ─────────────────────────────────────────────

def postprocess_fortune(fortune_text: str) -> dict:
    """
    LLM이 생성한 운세 텍스트를 다시 NLP로 분석
    → 원본 카드 키워드와 비교용 데이터 생성 목적
    
    Args:
        fortune_text: LLM이 생성한 운세 문자열
    
    Returns:
        {
            "keywords": [...],
            "sentiment_score": float,
            "sentiment_label": str
        }
    """
    keywords = extract_keywords(fortune_text, top_n=5)
    sentiment = analyze_sentiment(fortune_text)
    
    return {
        "keywords": keywords,
        "sentiment_score": sentiment["sentiment_score"],
        "sentiment_label": sentiment["sentiment_label"]
    }


# ─────────────────────────────────────────────
# 5. 비교 분석 함수 — 보고서용
# ─────────────────────────────────────────────

def compare_keywords(original_keywords: list, llm_keywords: list) -> dict:
    original_set = set(original_keywords)
    llm_set = set(llm_keywords)

    # 완전 일치
    exact_matched = original_set & llm_set

    # 부분 일치 (원본 키워드가 LLM 키워드에 포함되거나 반대)
    partial_matched = set()
    for orig in original_set:
        for llm in llm_set:
            if orig in llm or llm in orig:
                partial_matched.add(orig)

    all_matched = exact_matched | partial_matched
    match_rate = len(all_matched) / len(original_set) if original_set else 0.0

    return {
        "exact_match_count":   len(exact_matched),
        "partial_match_count": len(partial_matched),
        "match_rate":          round(match_rate, 4),
        "exact_matched":       list(exact_matched),
        "partial_matched":     list(partial_matched)
    }


def compare_card_directions(card_normal: dict, card_reversed: dict) -> dict:
    """
    동일 카드의 정방향 vs 역방향 감성 점수 차이 분석
    보고서 '정/역방향 감성 점수 변화' 표 생성용
    
    Args:
        card_normal: 정방향 카드 딕셔너리
        card_reversed: 역방향 카드 딕셔너리
    
    Returns:
        비교 결과 딕셔너리
    """
    normal_result = preprocess_card(card_normal)
    reversed_result = preprocess_card(card_reversed)
    
    score_diff = round(
        normal_result["sentiment_score"] - reversed_result["sentiment_score"], 4
    )
    
    return {
        "card_name": card_normal["name"],
        "normal": {
            "keywords": normal_result["keywords"],
            "sentiment_score": normal_result["sentiment_score"],
            "sentiment_label": normal_result["sentiment_label"]
        },
        "reversed": {
            "keywords": reversed_result["keywords"],
            "sentiment_score": reversed_result["sentiment_score"],
            "sentiment_label": reversed_result["sentiment_label"]
        },
        "score_diff": score_diff  # 양수면 정방향이 더 긍정적
    }


# ─────────────────────────────────────────────
# 6. JSON 로드 유틸 (선택적으로 사용)
# ─────────────────────────────────────────────

def load_cards(json_path: str) -> list[dict]:
    """cards.json 또는 cards_reversed.json 로드"""
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    # 키 이름이 "cards" 또는 "cards_reversed"
    return data.get("cards") or data.get("cards_reversed", [])
