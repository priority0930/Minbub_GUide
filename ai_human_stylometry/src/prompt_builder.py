"""
build_ai_prompt() — Human 샘플의 metadata만으로 AI 생성용 프롬프트를 만드는 모듈.

설계 원칙 (docs/research_design.md §6, §13 참고):
    1. 이 함수는 Human 샘플의 excerpt_text/원문을 절대 인자로 받지 않는다.
       (함수 시그니처 자체에 원문 관련 필드가 없다 — 구조적으로 "원문을 보여주고
       비슷하게 써라"라는 실수를 막기 위함이다.)
    2. genre, domain, topic, purpose, audience, style, target length 등
       "글쓰기 조건"만 프롬프트에 담는다.
    3. "아래 인간 글과 비슷하게 작성하라", "○○ 작가처럼 써라", "문체를 모방하라" 같은
       표현은 절대 사용하지 않는다.
    4. 같은 입력(row)에 대해서는 항상 같은 프롬프트가 나오도록(재현 가능성) 결정론적으로
       작성한다. 무작위 요소를 넣지 않는다.

사용 예:
    >>> row = {
    ...     "pair_id": "P001",
    ...     "genre": "explanatory",
    ...     "domain": "history",
    ...     "topic": "late_joseon_reform",
    ...     "purpose": "information",
    ...     "audience": "general_students",
    ...     "style": "objective",
    ...     "original_language": "ko",
    ...     "excerpt_char_count": 600,
    ... }
    >>> build_ai_prompt(row)["prompt_text"]
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Mapping, Optional


# ---------------------------------------------------------------------------
# 1. genre/purpose/style/audience 코드 -> 자연어 설명 매핑
#    (연구 설계 §4 에서 정의한 통제 어휘를 그대로 사용한다)
# ---------------------------------------------------------------------------

GENRE_DESCRIPTIONS_KO: dict[str, str] = {
    "essay": "에세이",
    "history": "역사 서술",
    "philosophy": "철학적 논고",
    "science_essay": "과학 교양 에세이",
    "speech": "연설문",
    "literature": "문학적 산문",
    "social_criticism": "사회 비평",
    "autobiography": "자서전적 회고",
    "explanatory": "설명문",
    "argumentative": "논설문",
    "literary_prose": "문학적 산문",
}

PURPOSE_DESCRIPTIONS_KO: dict[str, str] = {
    "explanation": "정보를 명확하게 설명하는 것",
    "persuasion": "독자를 설득하는 것",
    "criticism": "대상을 비판적으로 검토하는 것",
    "analysis": "현상을 분석하는 것",
    "reflection": "주제에 대해 성찰하는 것",
    "narration": "사건이나 경험을 서술하는 것",
    "information": "정보를 전달하는 것",
    "problem_raising": "문제를 제기하는 것",
}

STYLE_DESCRIPTIONS_KO: dict[str, str] = {
    "objective": "객관적이고 담담한",
    "academic": "학술적인",
    "lyrical": "서정적인",
    "emotional": "감정이 실린",
    "critical": "비판적인",
    "reflective": "성찰적인",
    "formal": "격식 있는",
    "explanatory": "설명적인",
    "narrative": "서사적인",
}

AUDIENCE_DESCRIPTIONS_KO: dict[str, str] = {
    "general_public": "일반 대중",
    "students": "학생",
    "specialists": "전문가",
    "academic": "학술 독자",
    "unknown": "특정되지 않은 독자",
}

# 영어 프롬프트가 필요한 경우(예: original_language == "en")를 위한 매핑
GENRE_DESCRIPTIONS_EN: dict[str, str] = {
    "essay": "essay",
    "history": "historical writing",
    "philosophy": "philosophical essay",
    "science_essay": "popular-science essay",
    "speech": "speech",
    "literature": "literary prose",
    "social_criticism": "social criticism",
    "autobiography": "autobiographical reflection",
    "explanatory": "explanatory piece",
    "argumentative": "argumentative essay",
    "literary_prose": "literary prose",
}

PURPOSE_DESCRIPTIONS_EN: dict[str, str] = {
    "explanation": "clearly explain the subject",
    "persuasion": "persuade the reader",
    "criticism": "critically examine the subject",
    "analysis": "analyze a phenomenon",
    "reflection": "reflect on the topic",
    "narration": "narrate an event or experience",
    "information": "convey information",
    "problem_raising": "raise a problem for the reader to consider",
}

STYLE_DESCRIPTIONS_EN: dict[str, str] = {
    "objective": "an objective, even-toned",
    "academic": "an academic",
    "lyrical": "a lyrical",
    "emotional": "an emotionally engaged",
    "critical": "a critical",
    "reflective": "a reflective",
    "formal": "a formal",
    "explanatory": "an explanatory",
    "narrative": "a narrative",
}

AUDIENCE_DESCRIPTIONS_EN: dict[str, str] = {
    "general_public": "the general public",
    "students": "students",
    "specialists": "specialists",
    "academic": "an academic readership",
    "unknown": "a general, unspecified readership",
}

# 금칙 표현 목록: 프롬프트 문자열에 아래 패턴이 들어가면 build_ai_prompt는
# AssertionError를 낸다 (실수로 human 원문 참조 표현이 섞이는 것을 막는 안전장치).
_FORBIDDEN_SUBSTRINGS_KO = ["비슷하게 작성", "처럼 써", "문체를 모방", "아래 글", "아래 인간 글"]
_FORBIDDEN_SUBSTRINGS_EN = ["similar to the human", "in the style of", "mimic the style", "the text below"]


@dataclass
class AIPromptSpec:
    """build_ai_prompt()의 반환값을 담는 구조체."""

    pair_id: str
    prompt_id: str
    language: str
    prompt_text: str
    target_char_count: Optional[int]
    target_word_count: Optional[int]
    metadata_used: dict[str, Any]


def _make_prompt_id(pair_id: str, prompt_text: str) -> str:
    """pair_id + 프롬프트 내용의 해시로 결정론적 prompt_id를 만든다."""
    digest = hashlib.sha1(prompt_text.encode("utf-8")).hexdigest()[:8]
    return f"PR-{pair_id}-{digest}"


def _target_length_from_row(row: Mapping[str, Any], language: str) -> tuple[Optional[int], Optional[int]]:
    """Human 샘플의 실제 길이(글자 수/단어 수)를 목표 길이로 역산한다.

    - 한국어(ko): excerpt_char_count 기준, 값이 없으면 기본 600자
    - 영어(en) 등: excerpt_word_count 기준, 값이 없으면 기본 220 words
    """
    char_count = row.get("excerpt_char_count")
    word_count = row.get("excerpt_word_count")

    if language == "ko":
        target_char = int(char_count) if char_count else 600
        return target_char, None
    else:
        target_word = int(word_count) if word_count else 220
        return None, target_word


def build_ai_prompt(row: Mapping[str, Any]) -> dict[str, Any]:
    """Human 샘플 1건의 metadata로부터 AI 생성용 프롬프트를 만든다.

    Parameters
    ----------
    row : Mapping[str, Any]
        Human JSONL의 한 레코드(dict). 다음 키만 사용한다:
        pair_id, genre, domain, topic, purpose, audience, style,
        original_language, excerpt_char_count, excerpt_word_count.
        (author/title/excerpt_text 등 원문 관련 필드는 사용하지 않으며,
        설령 딕셔너리에 들어있어도 이 함수는 참조하지 않는다.)

    Returns
    -------
    dict
        {
          "pair_id": ..., "prompt_id": ..., "language": "ko"|"en",
          "prompt_text": "...", "target_char_count": int|None,
          "target_word_count": int|None, "metadata_used": {...},
        }
    """
    pair_id = str(row.get("pair_id", "")).strip()
    if not pair_id:
        raise ValueError("row에 pair_id가 없습니다. Human/AI 쌍을 연결할 수 없습니다.")

    genre = str(row.get("genre", "essay"))
    domain = str(row.get("domain", "general"))
    topic = str(row.get("topic", "unspecified_topic")).replace("_", " ")
    purpose = str(row.get("purpose", "information"))
    audience = str(row.get("audience", "general_public"))
    style = str(row.get("style", "objective"))
    language = str(row.get("original_language", "ko")).lower()
    language = "ko" if language.startswith("ko") else "en"

    target_char, target_word = _target_length_from_row(row, language)

    if language == "ko":
        genre_desc = GENRE_DESCRIPTIONS_KO.get(genre, genre)
        purpose_desc = PURPOSE_DESCRIPTIONS_KO.get(purpose, purpose)
        style_desc = STYLE_DESCRIPTIONS_KO.get(style, style)
        audience_desc = AUDIENCE_DESCRIPTIONS_KO.get(audience, audience)

        prompt_text = (
            f"당신은 '{domain}' 분야에서 '{topic}'을(를) 주제로 글을 쓰는 필자입니다.\n"
            f"다음 조건에 맞추어 하나의 완결된 글을 작성하세요.\n\n"
            f"- 장르: {genre_desc}\n"
            f"- 목적: {purpose_desc}\n"
            f"- 예상 독자: {audience_desc}\n"
            f"- 문체: {style_desc} 문체\n"
            f"- 분량: 약 {target_char}자 (문장을 중간에서 자르지 말고, 하나의 완결된 문단 "
            f"또는 자연스럽게 이어지는 짧은 문단들로 구성하세요)\n\n"
            f"글은 특정 사례나 관찰에서 출발해 더 넓은 함의로 사고가 확장되는 구조를 "
            f"취해도 좋습니다. 다른 저자의 문체를 참고하지 말고, 위 조건만을 바탕으로 "
            f"독립적으로 작성하세요."
        )
    else:
        genre_desc = GENRE_DESCRIPTIONS_EN.get(genre, genre)
        purpose_desc = PURPOSE_DESCRIPTIONS_EN.get(purpose, purpose)
        style_desc = STYLE_DESCRIPTIONS_EN.get(style, style)
        audience_desc = AUDIENCE_DESCRIPTIONS_EN.get(audience, audience)

        prompt_text = (
            f"You are a writer producing a piece in the field of '{domain}', on the "
            f"topic of '{topic}'.\n"
            f"Write one complete, self-contained piece that meets the following "
            f"conditions.\n\n"
            f"- Genre: {genre_desc}\n"
            f"- Purpose: {purpose_desc}\n"
            f"- Intended audience: {audience_desc}\n"
            f"- Style: write in {style_desc} style\n"
            f"- Length: about {target_word} words (do not cut a sentence mid-way; "
            f"write one complete paragraph, or a few short paragraphs that flow "
            f"naturally into one another)\n\n"
            f"You may structure the piece so that it moves from a specific case or "
            f"observation toward a broader implication. Do not reference or imitate "
            f"any other author's style — write independently from the conditions "
            f"above only."
        )

    # 안전장치: 금칙 표현이 실수로 들어가지 않았는지 검사한다.
    forbidden = _FORBIDDEN_SUBSTRINGS_KO if language == "ko" else _FORBIDDEN_SUBSTRINGS_EN
    for bad in forbidden:
        assert bad not in prompt_text, (
            f"프롬프트에 금칙 표현 '{bad}'이(가) 포함되어 있습니다. "
            "AI가 인간 원문을 직접 참조하도록 유도하는 문구는 금지됩니다."
        )

    prompt_id = _make_prompt_id(pair_id, prompt_text)

    spec = AIPromptSpec(
        pair_id=pair_id,
        prompt_id=prompt_id,
        language=language,
        prompt_text=prompt_text,
        target_char_count=target_char,
        target_word_count=target_word,
        metadata_used={
            "genre": genre, "domain": domain, "topic": row.get("topic", ""),
            "purpose": purpose, "audience": audience, "style": style,
        },
    )
    return {
        "pair_id": spec.pair_id,
        "prompt_id": spec.prompt_id,
        "language": spec.language,
        "prompt_text": spec.prompt_text,
        "target_char_count": spec.target_char_count,
        "target_word_count": spec.target_word_count,
        "metadata_used": spec.metadata_used,
    }


def build_prompts_for_batch(human_records: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Human JSONL 전체(또는 batch)에 대해 순서대로 프롬프트를 생성한다."""
    return [build_ai_prompt(row) for row in human_records]


def _load_jsonl(path: str) -> list[dict[str, Any]]:
    records = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            records.append(json.loads(line))
    return records


if __name__ == "__main__":
    # 간단한 자기 테스트: 샘플 row 하나로 프롬프트가 잘 생성되는지 확인한다.
    sample_row = {
        "pair_id": "P001",
        "genre": "explanatory",
        "domain": "history",
        "topic": "late_joseon_reform",
        "purpose": "information",
        "audience": "students",
        "style": "objective",
        "original_language": "ko",
        "excerpt_char_count": 620,
    }
    result = build_ai_prompt(sample_row)
    print(json.dumps(result, ensure_ascii=False, indent=2))
