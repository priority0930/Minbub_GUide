"""
feature_extraction.py
======================

AI/인간 글쓰기 비교 연구(docs/research_design.md §7)에서 사용하는 **30개 핵심 feature**를
추출하는 모듈이다. 다섯 범주(A 문장 구조, B 어휘 다양성, C 품사 비율, D 반복성·규칙성,
E 감성·정보량)로 구성되며, 각 feature는 `FEATURE_DEFINITIONS`에 정의·계산식·의미·
길이 민감도·정규화 여부가 함께 기록되어 있다 (연구설계 §19 "Feature Engineering 원칙").

지원 언어
---------
- English (``language="en"``): NLTK(``punkt``, ``averaged_perceptron_tagger``)로
  문장 분리·토큰화·품사 태깅을 하고, VADER로 감성 점수를 낸다.
- Korean (``language="ko"``): `kiwipiepy`가 설치되어 있으면 형태소 분석 기반으로
  품사 비율을 계산한다. **주의**: 이번 세션이 실행된 샌드박스에서는 시스템 setuptools의
  구버전 문제로 `kiwipiepy_model` 휠 빌드가 실패해 설치할 수 없었다 (Google Colab이나
  일반 PC에서는 `pip install kiwipiepy`로 정상 설치된다 — 연구설계 §7 C 참고). 이
  모듈의 한국어 경로는 코드 리뷰는 마쳤으나 **이 세션에서 직접 실행 검증은 하지 못했다**는
  점을 투명하게 밝혀둔다. kiwipiepy가 없으면 명확한 오류 메시지와 함께 대안(Okt 등)을
  안내한다.

이 모듈은 어떤 특정 실행 환경에도 종속되지 않도록 설계했다 — `nltk.download(...)`가
필요한 리소스는 최초 1회만 받고, 이미 있으면 다시 받지 않는다.
"""

from __future__ import annotations

import math
import os
import re
from collections import Counter
from typing import Any, Optional

# ---------------------------------------------------------------------------
# 0. Feature 정의 메타데이터 (연구설계 §19의 요구사항: 정의/계산식/이유/길이민감도/정규화)
# ---------------------------------------------------------------------------
# 이 리스트는 노트북 SECTION 8에서 "30개 feature 설명표"를 출력하는 데 그대로 쓰인다.
# 각 rationale은 "이 변수가 AI/인간 비교에서 왜 의미가 있을 수 있는가"에 대한 가설이며,
# 실제로 의미가 있는지는 분석 결과가 결정한다 (연구설계 §0 원칙).

FEATURE_DEFINITIONS: list[dict[str, Any]] = [
    # --- A. 문장 구조 ---------------------------------------------------
    dict(id=1, name="sentence_count", category="A_sentence_structure",
         definition="텍스트 내 문장의 총 개수",
         formula="len(sentences)",
         rationale="글의 전체 길이를 나타내는 통제 변수. 다른 feature를 해석할 때 분모로도 쓰인다.",
         length_sensitive=True, normalization="길이 통제 변수로 사용, 비율 계산의 분모"),
    dict(id=2, name="avg_sentence_length", category="A_sentence_structure",
         definition="문장 하나의 평균 단어 수",
         formula="word_count / sentence_count",
         rationale="AI는 문장 길이를 균일하게 맞추는 경향(H1)이 있을 수 있다는 가설의 기준값.",
         length_sensitive=False, normalization="이미 단어수/문장수 비율이라 추가 정규화 불필요"),
    dict(id=3, name="sentence_length_std", category="A_sentence_structure",
         definition="문장별 단어 수의 표준편차",
         formula="std([len(s) for s in sentences])",
         rationale="H1, H7(burstiness) 검증의 핵심 변수 — 값이 작을수록 문장 길이가 균일함.",
         length_sensitive=True, normalization="문장 수가 매우 적으면 불안정하므로 sentence_count와 함께 해석"),
    dict(id=4, name="sentence_length_cv", category="A_sentence_structure",
         definition="문장 길이의 변동계수 (표준편차 / 평균)",
         formula="sentence_length_std / avg_sentence_length",
         rationale="평균 문장 길이 자체가 다른 두 텍스트를 공정하게 비교하기 위한 길이-보정 변동성 지표.",
         length_sensitive=False, normalization="이미 정규화된 지표 (std를 mean으로 나눔)"),
    dict(id=5, name="max_sentence_length", category="A_sentence_structure",
         definition="가장 긴 문장의 단어 수",
         formula="max([len(s) for s in sentences])",
         rationale="극단값 존재 여부 — 인간 글에 유독 긴 만연체 문장이 섞여 있는지 확인.",
         length_sensitive=True, normalization="정규화하지 않고 std/cv와 함께 해석"),
    dict(id=6, name="min_sentence_length", category="A_sentence_structure",
         definition="가장 짧은 문장의 단어 수",
         formula="min([len(s) for s in sentences])",
         rationale="짧은 강조 문장의 사용 여부 — 수사적 리듬의 단서.",
         length_sensitive=True, normalization="정규화하지 않고 std/cv와 함께 해석"),
    dict(id=7, name="comma_rate", category="A_sentence_structure",
         definition="문장당 평균 쉼표 개수",
         formula="comma_count / sentence_count",
         rationale="절 구조의 복잡도, 종속절 삽입 빈도를 간접적으로 나타낸다.",
         length_sensitive=False, normalization="문장 수로 나눈 비율이라 이미 정규화됨"),
    dict(id=8, name="punctuation_rate", category="A_sentence_structure",
         definition="단어 100개당 구두점(.,!?;:—) 개수",
         formula="punct_count / word_count * 100",
         rationale="구두점 사용 밀도 — 문장 리듬 및 형식성의 지표.",
         length_sensitive=False, normalization="100단어 기준 비율로 이미 정규화됨"),

    # --- B. 어휘 다양성 ---------------------------------------------------
    dict(id=9, name="word_count", category="B_lexical_diversity",
         definition="총 단어(토큰) 수",
         formula="len(word_tokens)",
         rationale="길이 통제 변수. 다른 feature의 분모로도 사용된다.",
         length_sensitive=True, normalization="정규화하지 않음 — 길이 자체를 나타내는 통제 변수"),
    dict(id=10, name="unique_word_count", category="B_lexical_diversity",
         definition="고유(중복 제거) 단어 수",
         formula="len(set(word_tokens))",
         rationale="어휘 사용 폭의 원값. TTR 등 정규화 지표의 재료.",
         length_sensitive=True, normalization="단독으로는 길이에 민감 — TTR/MATTR과 함께 해석"),
    dict(id=11, name="type_token_ratio", category="B_lexical_diversity",
         definition="Type-Token Ratio: 고유 단어 수 / 전체 단어 수",
         formula="unique_word_count / word_count",
         rationale="어휘 다양성의 고전적 지표(H4 검증). 텍스트가 길어질수록 값이 작아지는 한계가 있다.",
         length_sensitive=True, normalization="텍스트 길이가 크게 다르면 비교 시 root_ttr/MATTR을 함께 봐야 함"),
    dict(id=12, name="root_ttr", category="B_lexical_diversity",
         definition="Guiraud's R (Root TTR): 고유 단어 수 / sqrt(전체 단어 수)",
         formula="unique_word_count / sqrt(word_count)",
         rationale="TTR보다 텍스트 길이에 덜 민감한 어휘 다양성 지표.",
         length_sensitive=False, normalization="제곱근 보정으로 이미 길이 영향을 줄임"),
    dict(id=13, name="mattr", category="B_lexical_diversity",
         definition="Moving-Average TTR (window=50 단어)",
         formula="윈도우를 1단어씩 옮기며 각 윈도우의 TTR을 구한 뒤 평균",
         rationale="길이에 가장 안정적인 어휘 다양성 지표. 텍스트가 window보다 짧으면 전체 텍스트로 1회 계산.",
         length_sensitive=False, normalization="이동평균 자체가 길이 보정 역할을 함"),
    dict(id=14, name="avg_word_length", category="B_lexical_diversity",
         definition="단어의 평균 글자(문자) 수",
         formula="mean([len(w) for w in word_tokens])",
         rationale="어휘 수준(난이도)의 간접 지표 — 추상적/전문적 어휘 사용 경향과 관련될 수 있다.",
         length_sensitive=False, normalization="이미 평균값이라 정규화 불필요"),
    dict(id=15, name="lexical_repetition_rate", category="B_lexical_diversity",
         definition="3회 이상 등장한 단어(heavy repeater)가 전체 단어 토큰에서 차지하는 비율",
         formula="sum(freq for w,freq in counts.items() if freq>=3) / word_count",
         rationale="같은 단어를 과도하게 반복 사용하는 경향(어휘 절약)을 포착 — TTR과 달리 '토큰 관점'.",
         length_sensitive=False, normalization="비율이라 이미 정규화됨"),

    # --- C. 품사 사용 비율 --------------------------------------------------
    dict(id=16, name="noun_ratio", category="C_pos_ratio",
         definition="명사 토큰 수 / 전체 토큰 수",
         formula="noun_count / total_tokens",
         rationale="정보 밀도가 높은 글일수록 명사 비율이 높은 경향이 있다는 가설(H5).",
         length_sensitive=False, normalization="비율이라 이미 정규화됨"),
    dict(id=17, name="verb_ratio", category="C_pos_ratio",
         definition="동사 토큰 수 / 전체 토큰 수",
         formula="verb_count / total_tokens",
         rationale="서술·서사 중심 글일수록 동사 비율이 높을 수 있다.",
         length_sensitive=False, normalization="비율이라 이미 정규화됨"),
    dict(id=18, name="adjective_ratio", category="C_pos_ratio",
         definition="형용사 토큰 수 / 전체 토큰 수",
         formula="adj_count / total_tokens",
         rationale="수식·평가적 표현의 빈도 — AI가 형용사를 과다 사용한다는 통념(H5)의 검증 대상.",
         length_sensitive=False, normalization="비율이라 이미 정규화됨"),
    dict(id=19, name="adverb_ratio", category="C_pos_ratio",
         definition="부사 토큰 수 / 전체 토큰 수",
         formula="adv_count / total_tokens",
         rationale="정도·양태 부사 사용 경향 — 문체의 격식성과 관련될 수 있다.",
         length_sensitive=False, normalization="비율이라 이미 정규화됨"),
    dict(id=20, name="pronoun_ratio", category="C_pos_ratio",
         definition="대명사 토큰 수 / 전체 토큰 수",
         formula="pronoun_count / total_tokens",
         rationale="1인칭/개인적 서술 정도의 간접 지표.",
         length_sensitive=False, normalization="비율이라 이미 정규화됨"),
    dict(id=21, name="particle_ratio", category="C_pos_ratio",
         definition="(한국어) 조사 비율 / (영어) 전치사·한정사 등 기능어 비율",
         formula="particle_or_function_word_count / total_tokens",
         rationale="문법적 기능어 사용 밀도 — 언어별로 조사(한국어)와 전치사·관사(영어)로 조작적 정의를 달리한다.",
         length_sensitive=False, normalization="비율이라 이미 정규화됨"),
    dict(id=22, name="conjunction_ratio", category="C_pos_ratio",
         definition="접속사/연결어 토큰 수 / 전체 토큰 수",
         formula="conjunction_count / total_tokens",
         rationale="문장·절 연결 빈도 — H2(접속 표현 반복)와 밀접히 관련된 기초 변수.",
         length_sensitive=False, normalization="비율이라 이미 정규화됨"),

    # --- D. 반복성·규칙성 ---------------------------------------------------
    dict(id=23, name="repeated_word_rate", category="D_repetition_regularity",
         definition="2회 이상 등장한 단어 타입의 비율 (타입 관점의 재사용도)",
         formula="len([w for w,c in counts.items() if c>=2]) / unique_word_count",
         rationale="B15(토큰 관점의 heavy repetition)와 달리, '얼마나 많은 서로 다른 단어가 재사용되는가'를 본다.",
         length_sensitive=True, normalization="unique_word_count로 나눠 어느 정도 보정됨"),
    dict(id=24, name="repeated_bigram_rate", category="D_repetition_regularity",
         definition="2회 이상 등장한 bigram이 전체 bigram에서 차지하는 비율",
         formula="sum(c for bg,c in bigram_counts.items() if c>=2) / total_bigrams",
         rationale="구(phrase) 수준의 반복 — 정형화된 표현을 반복 사용하는 경향(H3)과 관련.",
         length_sensitive=False, normalization="비율이라 이미 정규화됨"),
    dict(id=25, name="repeated_trigram_rate", category="D_repetition_regularity",
         definition="2회 이상 등장한 trigram이 전체 trigram에서 차지하는 비율",
         formula="sum(c for tg,c in trigram_counts.items() if c>=2) / total_trigrams",
         rationale="bigram보다 더 긴 정형구 반복 — 상투적 표현 사용 경향의 강한 증거.",
         length_sensitive=False, normalization="비율이라 이미 정규화됨"),
    dict(id=26, name="sentence_start_repetition", category="D_repetition_regularity",
         definition="문장 시작 단어가 반복되는 정도",
         formula="1 - (문장 시작 단어의 고유 개수 / 문장 수)",
         rationale="AI가 비슷한 문장 시작 패턴(예: '이것은', 'This')을 반복한다는 관찰(H6)의 검증 변수.",
         length_sensitive=True, normalization="문장 수로 나눠 비율화했으나 문장 수가 적으면 불안정"),
    dict(id=27, name="conjunction_repetition_rate", category="D_repetition_regularity",
         definition="가장 많이 쓰인 접속 표현이 전체 접속 표현 중 차지하는 비율",
         formula="max(conjunction_word_counts.values()) / sum(conjunction_word_counts.values())  (접속 표현이 없으면 0)",
         rationale="H2 — 특정 접속어(예: '그리고', 'however')에 편중되는 경향을 직접 측정.",
         length_sensitive=False, normalization="비율이라 이미 정규화됨"),
    dict(id=28, name="three_item_enumeration_rate", category="D_repetition_regularity",
         definition="'A, B, and C' / 'A, B, 그리고 C' 형태의 3항 병렬 나열이 문장 10개당 등장하는 횟수",
         formula="(3항 나열 패턴 매치 수 / sentence_count) * 10",
         rationale="실험적 feature(H3) — 'AI가 3개씩 항목을 나열하는 습관이 있다'는 세간의 관찰을 정량적으로 검증하기 위해 도입.",
         length_sensitive=False, normalization="문장 10개당 비율로 정규화. 정규식 기반 휴리스틱이므로 완벽한 병렬구조 탐지는 아님(한계로 명시)"),

    # --- E. 감성·정보량 ------------------------------------------------------
    dict(id=29, name="sentiment_score", category="E_sentiment_information",
         definition="어휘 기반 감성 극성 점수 (-1=매우 부정 ~ +1=매우 긍정)",
         formula="영어: VADER compound score / 한국어: 자체 긍부정 어휘사전 기반 점수",
         rationale="정서적 어휘 사용 정도 — 문체의 '감정적 색채'를 정량화.",
         length_sensitive=False, normalization="-1~1로 이미 정규화된 척도"),
    dict(id=30, name="lexical_entropy", category="E_sentiment_information",
         definition="단어 사용 분포의 Shannon entropy (정규화: log2(word_count)로 나눔)",
         formula="H = -sum(p_i * log2(p_i)) for word types; normalized_H = H / log2(word_count)",
         rationale="어휘 선택의 예측가능성/불확실성 — 값이 낮을수록 특정 단어에 예측 가능하게 쏠려 있음을 뜻한다.",
         length_sensitive=False, normalization="log2(word_count)로 나눠 0~1 범위로 정규화"),
]

FEATURE_NAMES: list[str] = [f["name"] for f in FEATURE_DEFINITIONS]
assert len(FEATURE_NAMES) == 30, f"feature 개수는 30개여야 하는데 {len(FEATURE_NAMES)}개입니다."


# ---------------------------------------------------------------------------
# 1. 언어별 리소스 준비
# ---------------------------------------------------------------------------

_NLTK_READY = False


def ensure_nltk_resources() -> None:
    """영어 분석에 필요한 NLTK 리소스(punkt, POS tagger, VADER)를 준비한다.

    이미 다운로드되어 있으면 아무것도 하지 않는다. 이 함수가 실행되는 환경에 따라
    ``NLTK_ALLOW_PROXIED_URLOPEN`` 환경변수가 필요할 수 있다(사내/샌드박스 proxy 환경 한정,
    일반 PC나 Google Colab에서는 필요하지 않다).
    """
    global _NLTK_READY
    if _NLTK_READY:
        return
    os.environ.setdefault("NLTK_ALLOW_PROXIED_URLOPEN", "1")
    import nltk

    resources = {
        "tokenizers/punkt": "punkt",
        "tokenizers/punkt_tab": "punkt_tab",
        "taggers/averaged_perceptron_tagger": "averaged_perceptron_tagger",
        "taggers/averaged_perceptron_tagger_eng": "averaged_perceptron_tagger_eng",
        "sentiment/vader_lexicon": "vader_lexicon",
    }
    for path, pkg in resources.items():
        try:
            nltk.data.find(path)
        except LookupError:
            nltk.download(pkg, quiet=True)
    _NLTK_READY = True


_KIWI_INSTANCE = None


def _get_kiwi():
    """한국어 형태소 분석기(kiwipiepy)를 준비한다. 없으면 안내 메시지와 함께 예외를 낸다."""
    global _KIWI_INSTANCE
    if _KIWI_INSTANCE is not None:
        return _KIWI_INSTANCE
    try:
        from kiwipiepy import Kiwi
    except ImportError as e:
        raise ImportError(
            "한국어 형태소 분석을 위해 kiwipiepy가 필요합니다. "
            "`pip install kiwipiepy`로 설치하세요 (Google Colab/일반 PC에서는 보통 문제없이 "
            "설치됩니다). 대안으로 KoNLPy의 Okt를 쓰려면 이 함수를 직접 교체하세요."
        ) from e
    _KIWI_INSTANCE = Kiwi()
    return _KIWI_INSTANCE


# ---------------------------------------------------------------------------
# 2. 전처리: 문장 분리 / 토큰화 / 품사 태깅
# ---------------------------------------------------------------------------

_EN_SUBORDINATING_CONJ = {
    "because", "although", "though", "since", "while", "if", "unless",
    "whereas", "when", "after", "before", "as", "until", "so", "however",
    "therefore", "moreover", "furthermore", "nevertheless", "thus", "hence",
}
_KO_CONJ_WORDS = {
    "그리고", "그러나", "하지만", "그런데", "따라서", "그래서", "또한", "즉",
    "왜냐하면", "그러므로", "그럼에도", "한편", "반면",
}


def _normalize_language(language: str) -> str:
    language = (language or "en").lower()
    return "ko" if language.startswith("ko") else "en"


def split_sentences(text: str, language: str = "en") -> list[str]:
    """텍스트를 문장 단위로 분리한다."""
    language = _normalize_language(language)
    text = text.strip()
    if not text:
        return []
    if language == "en":
        ensure_nltk_resources()
        from nltk.tokenize import sent_tokenize
        return [s.strip() for s in sent_tokenize(text) if s.strip()]
    else:
        try:
            kiwi = _get_kiwi()
            return [s.text.strip() for s in kiwi.split_into_sents(text) if s.text.strip()]
        except ImportError:
            # kiwipiepy가 없는 환경을 위한 정규식 폴백 (정확도는 떨어짐 — 한계로 명시)
            parts = re.split(r"(?<=[.!?다\n])\s+", text)
            return [p.strip() for p in parts if p.strip()]


def tokenize_words(text: str, language: str = "en") -> list[str]:
    """단어(형태소) 토큰 리스트를 반환한다 (구두점 제외, 소문자화하지 않음 — 필요 시 호출부에서 처리)."""
    language = _normalize_language(language)
    if language == "en":
        ensure_nltk_resources()
        from nltk.tokenize import word_tokenize
        tokens = word_tokenize(text)
        return [t for t in tokens if re.search(r"[A-Za-z0-9]", t)]
    else:
        try:
            kiwi = _get_kiwi()
            return [tok.form for tok in kiwi.tokenize(text)]
        except ImportError:
            return re.findall(r"[가-힣A-Za-z0-9]+", text)


def pos_tag_tokens(text: str, language: str = "en") -> list[tuple[str, str]]:
    """(단어, 품사태그) 리스트를 반환한다."""
    language = _normalize_language(language)
    if language == "en":
        ensure_nltk_resources()
        from nltk.tokenize import word_tokenize
        from nltk import pos_tag
        tokens = word_tokenize(text)
        return pos_tag(tokens)
    else:
        kiwi = _get_kiwi()  # ImportError 시 그대로 전파 (한국어는 정확한 POS가 필수적이라 폴백을 두지 않음)
        return [(tok.form, tok.tag) for tok in kiwi.tokenize(text)]


# ---------------------------------------------------------------------------
# 3. 품사 그룹 매핑
# ---------------------------------------------------------------------------

_EN_POS_GROUPS = {
    "noun": {"NN", "NNS", "NNP", "NNPS"},
    "verb": {"VB", "VBD", "VBG", "VBN", "VBP", "VBZ"},
    "adjective": {"JJ", "JJR", "JJS"},
    "adverb": {"RB", "RBR", "RBS"},
    "pronoun": {"PRP", "PRP$", "WP", "WP$"},
    # 영어에는 조사가 없으므로 전치사(IN)+한정사(DT)를 "기능어(particle 대응)"로 조작적 정의한다.
    "particle": {"IN", "DT", "RP"},
    "conjunction": {"CC"},
}

# kiwipiepy 품사 태그 체계 (세종 태그셋 축약형 접두어 기준)
_KO_POS_PREFIX_GROUPS = {
    "noun": ("NNG", "NNP", "NNB"),
    "verb": ("VV", "VX"),
    "adjective": ("VA",),
    "adverb": ("MAG", "MAJ"),
    "pronoun": ("NP",),
    "particle": ("JKS", "JKC", "JKG", "JKO", "JKB", "JKV", "JKQ", "JX", "JC"),
    "conjunction": ("MAJ",),  # 접속부사. 어미 결합 접속(EC 중 일부)은 근사치로 취급 (한계로 명시)
}


def pos_group_ratios(tagged: list[tuple[str, str]], language: str) -> dict[str, float]:
    """품사 태깅 결과에서 noun/verb/adjective/adverb/pronoun/particle/conjunction 비율을 계산한다."""
    language = _normalize_language(language)
    total = len(tagged) if tagged else 1
    counts = {g: 0 for g in ["noun", "verb", "adjective", "adverb", "pronoun", "particle", "conjunction"]}

    if language == "en":
        for _, tag in tagged:
            for group, tagset in _EN_POS_GROUPS.items():
                if tag in tagset:
                    counts[group] += 1
        # 영어는 종속접속사가 IN(전치사)과 태그를 공유하므로 어휘 목록으로 보정한다.
        extra_subordinating = sum(1 for w, tag in tagged if w.lower() in _EN_SUBORDINATING_CONJ)
        counts["conjunction"] += extra_subordinating
    else:
        for _, tag in tagged:
            for group, prefixes in _KO_POS_PREFIX_GROUPS.items():
                if tag.startswith(prefixes):
                    counts[group] += 1

    return {f"{g}_ratio": counts[g] / total for g in counts}


# ---------------------------------------------------------------------------
# 4. 개별 feature 계산 헬퍼
# ---------------------------------------------------------------------------

def _mattr(word_tokens: list[str], window: int = 50) -> float:
    """Moving-Average Type-Token Ratio. 토큰 수가 window보다 적으면 전체 텍스트로 1회 TTR을 구한다."""
    n = len(word_tokens)
    if n == 0:
        return 0.0
    if n <= window:
        return len(set(word_tokens)) / n
    ratios = []
    for i in range(n - window + 1):
        win = word_tokens[i:i + window]
        ratios.append(len(set(win)) / window)
    return sum(ratios) / len(ratios)


def _shannon_entropy(word_tokens: list[str]) -> tuple[float, float]:
    """(raw entropy, length-normalized entropy)를 반환한다."""
    n = len(word_tokens)
    if n <= 1:
        return 0.0, 0.0
    counts = Counter(word_tokens)
    probs = [c / n for c in counts.values()]
    raw_h = -sum(p * math.log2(p) for p in probs)
    denom = math.log2(n) if n > 1 else 1.0
    normalized_h = raw_h / denom if denom > 0 else 0.0
    return raw_h, normalized_h


def _ngram_repetition_rate(word_tokens: list[str], n: int) -> float:
    if len(word_tokens) < n:
        return 0.0
    ngrams = [tuple(word_tokens[i:i + n]) for i in range(len(word_tokens) - n + 1)]
    counts = Counter(ngrams)
    total = len(ngrams)
    repeated = sum(c for c in counts.values() if c >= 2)
    return repeated / total if total else 0.0


_THREE_ITEM_ENUM_PATTERN_EN = re.compile(
    r"\b\w+(?:\s+\w+){0,3},\s*\w+(?:\s+\w+){0,3},?\s+and\s+\w+(?:\s+\w+){0,3}\b",
    re.IGNORECASE,
)
_THREE_ITEM_ENUM_PATTERN_KO = re.compile(
    r"[가-힣A-Za-z0-9]+,\s*[가-힣A-Za-z0-9]+,?\s*(그리고|및)\s*[가-힣A-Za-z0-9]+"
)


def _three_item_enumeration_count(sentences: list[str], language: str) -> int:
    pattern = _THREE_ITEM_ENUM_PATTERN_EN if _normalize_language(language) == "en" else _THREE_ITEM_ENUM_PATTERN_KO
    return sum(len(pattern.findall(s)) for s in sentences)


def _sentiment_score(text: str, language: str) -> float:
    language = _normalize_language(language)
    if language == "en":
        ensure_nltk_resources()
        from nltk.sentiment import SentimentIntensityAnalyzer
        sia = SentimentIntensityAnalyzer()
        return sia.polarity_scores(text)["compound"]
    else:
        # 한국어 감성사전은 별도 다운로드가 필요한 대형 리소스가 많아, 학부 연구 범위에서
        # 다루기 쉬운 소규모 내장 극성사전으로 근사한다 (정확도의 한계를 명시).
        positive = {"희망", "행복", "성장", "발전", "사랑", "평화", "자유", "협력", "감사", "아름답"}
        negative = {"절망", "슬픔", "파괴", "전쟁", "고통", "죽음", "불행", "억압", "위기", "폭력"}
        tokens = re.findall(r"[가-힣]+", text)
        pos = sum(1 for t in tokens if any(p in t for p in positive))
        neg = sum(1 for t in tokens if any(nge in t for nge in negative))
        denom = pos + neg
        return 0.0 if denom == 0 else (pos - neg) / denom


# ---------------------------------------------------------------------------
# 5. 메인 함수: extract_features
# ---------------------------------------------------------------------------

def extract_features(text: str, language: str = "en") -> dict[str, float]:
    """텍스트 하나에서 30개 feature를 모두 계산해 dict로 반환한다.

    Parameters
    ----------
    text : str
        분석할 원문(사람 excerpt_text 또는 AI generated_text).
    language : str
        "en" 또는 "ko". 그 외 값은 "en"으로 취급한다.

    Returns
    -------
    dict[str, float]
        FEATURE_NAMES에 정의된 30개 key + 참고용 char_count.
    """
    language = _normalize_language(language)
    text = (text or "").strip()

    if not text:
        # 빈 텍스트(예: 저작권으로 excerpt_text가 비어있는 Human 샘플)는 전부 NaN으로 반환한다.
        # 노트북 SECTION 11(결측치 검사)에서 이 샘플들은 feature 분석 대상에서 제외해야 한다.
        return {name: float("nan") for name in FEATURE_NAMES} | {"char_count": 0}

    sentences = split_sentences(text, language)
    if not sentences:
        sentences = [text]

    tagged = pos_tag_tokens(text, language)
    word_tokens_raw = [w for w, _ in tagged]
    word_tokens = [w.lower() for w in word_tokens_raw if re.search(r"[가-힣A-Za-z0-9]", w)]

    sentence_word_lengths = [len(tokenize_words(s, language)) or 1 for s in sentences]

    # --- A. 문장 구조 ---
    sentence_count = len(sentences)
    avg_sentence_length = sum(sentence_word_lengths) / sentence_count
    if sentence_count > 1:
        mean_len = avg_sentence_length
        variance = sum((x - mean_len) ** 2 for x in sentence_word_lengths) / (sentence_count - 1)
        sentence_length_std = math.sqrt(variance)
    else:
        sentence_length_std = 0.0
    sentence_length_cv = sentence_length_std / avg_sentence_length if avg_sentence_length else 0.0
    max_sentence_length = max(sentence_word_lengths)
    min_sentence_length = min(sentence_word_lengths)
    comma_count = text.count(",") + text.count("、")
    comma_rate = comma_count / sentence_count
    punct_count = len(re.findall(r"[.!?;:,—\-·。！？；：]", text))
    word_count = len(word_tokens)
    punctuation_rate = (punct_count / word_count * 100) if word_count else 0.0

    # --- B. 어휘 다양성 ---
    unique_word_count = len(set(word_tokens))
    type_token_ratio = unique_word_count / word_count if word_count else 0.0
    root_ttr = unique_word_count / math.sqrt(word_count) if word_count else 0.0
    mattr = _mattr(word_tokens, window=50)
    avg_word_length = sum(len(w) for w in word_tokens) / word_count if word_count else 0.0
    counts = Counter(word_tokens)
    lexical_repetition_rate = (
        sum(c for c in counts.values() if c >= 3) / word_count if word_count else 0.0
    )

    # --- C. 품사 비율 ---
    pos_ratios = pos_group_ratios(tagged, language)

    # --- D. 반복성·규칙성 ---
    repeated_word_rate = (
        len([w for w, c in counts.items() if c >= 2]) / unique_word_count if unique_word_count else 0.0
    )
    repeated_bigram_rate = _ngram_repetition_rate(word_tokens, 2)
    repeated_trigram_rate = _ngram_repetition_rate(word_tokens, 3)

    sentence_starts = [tokenize_words(s, language)[0].lower() for s in sentences if tokenize_words(s, language)]
    unique_starts = len(set(sentence_starts))
    sentence_start_repetition = 1 - (unique_starts / sentence_count) if sentence_count else 0.0

    conj_words_in_text = [w.lower() for w in word_tokens if (
        w.lower() in _EN_SUBORDINATING_CONJ or w in _KO_CONJ_WORDS
    )]
    conj_counter = Counter(conj_words_in_text)
    conjunction_repetition_rate = (
        max(conj_counter.values()) / sum(conj_counter.values()) if conj_counter else 0.0
    )

    three_item_count = _three_item_enumeration_count(sentences, language)
    three_item_enumeration_rate = (three_item_count / sentence_count) * 10 if sentence_count else 0.0

    # --- E. 감성·정보량 ---
    sentiment_score = _sentiment_score(text, language)
    _, lexical_entropy = _shannon_entropy(word_tokens)

    features = {
        "sentence_count": sentence_count,
        "avg_sentence_length": avg_sentence_length,
        "sentence_length_std": sentence_length_std,
        "sentence_length_cv": sentence_length_cv,
        "max_sentence_length": max_sentence_length,
        "min_sentence_length": min_sentence_length,
        "comma_rate": comma_rate,
        "punctuation_rate": punctuation_rate,
        "word_count": word_count,
        "unique_word_count": unique_word_count,
        "type_token_ratio": type_token_ratio,
        "root_ttr": root_ttr,
        "mattr": mattr,
        "avg_word_length": avg_word_length,
        "lexical_repetition_rate": lexical_repetition_rate,
        "noun_ratio": pos_ratios["noun_ratio"],
        "verb_ratio": pos_ratios["verb_ratio"],
        "adjective_ratio": pos_ratios["adjective_ratio"],
        "adverb_ratio": pos_ratios["adverb_ratio"],
        "pronoun_ratio": pos_ratios["pronoun_ratio"],
        "particle_ratio": pos_ratios["particle_ratio"],
        "conjunction_ratio": pos_ratios["conjunction_ratio"],
        "repeated_word_rate": repeated_word_rate,
        "repeated_bigram_rate": repeated_bigram_rate,
        "repeated_trigram_rate": repeated_trigram_rate,
        "sentence_start_repetition": sentence_start_repetition,
        "conjunction_repetition_rate": conjunction_repetition_rate,
        "three_item_enumeration_rate": three_item_enumeration_rate,
        "sentiment_score": sentiment_score,
        "lexical_entropy": lexical_entropy,
    }
    # 순서를 FEATURE_NAMES와 맞추고, 참고용 char_count를 덧붙인다.
    ordered = {name: features[name] for name in FEATURE_NAMES}
    ordered["char_count"] = len(text)
    return ordered


if __name__ == "__main__":
    demo_text = (
        "Science does not simply describe and explain nature; it is part of the interplay "
        "between nature and ourselves. Once we accept the limits of our instruments and our "
        "senses, we begin to see the world not as it is, but as we are able to know it. This "
        "recognition, uncomfortable as it may be, is also liberating, and it reminds us, "
        "again and again, that humility is the beginning of understanding."
    )
    result = extract_features(demo_text, language="en")
    for k, v in result.items():
        print(f"{k:32s} {v}")
