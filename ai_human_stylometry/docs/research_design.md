# AI/인간 글쓰기 문체 비교 연구 — 연구 설계 문서

> 이 문서는 `ai_human_stylometry/` 하위 프로젝트 전체의 설계도다. 코드·데이터 스키마·노트북은
> 모두 이 문서에서 정의한 원칙을 따른다. 실제 데이터 수집·분석이 진행되며 세부 사항이
> 바뀌면 이 문서도 함께 갱신해야 한다.

---

## 0. 연구의 핵심 목적

이 연구는 "AI 판별기(detector)를 잘 만드는 것"이 목적이 아니다.

**핵심 질문은 두 가지다.**

1. AI가 생성한 글과 인간이 작성한 글은 문체·구조·어휘·의미 조직 측면에서 정량적으로 구별되는가?
2. 구별된다면, 그 구별을 만드는 **핵심 언어적·문체적 요인은 무엇인가**?

즉 분류 정확도는 "차이가 존재하는지"를 확인하는 도구일 뿐이며, 연구의 결론은 항상
**"왜 구별되는가, 어떤 변수가 그것을 만드는가"**에 초점을 맞춘다.

결론은 실제 분석 결과에 따라 결정된다. 차이가 뚜렷할 수도, 약할 수도, 특정 분야·특정 AI
모델에서만 나타날 수도 있다 — 어느 쪽이든 있는 그대로 보고한다. 아래에 제시된 가설(H1~H7)은
전부 **검증 대상**이지 전제가 아니다.

---

## 1. 연구 제목

- 가제 1: 「텍스트 스타일 특징을 이용한 AI 생성 글과 인간 작성 글의 판별 요인 분석」
- 가제 2: 「머신러닝 기반 텍스트 특징 분석을 통한 AI 생성 글과 인간 작성 글의 구분 요인 탐색」
- 가제 3: 「AI와 인간의 글은 어떻게 다른가?: 텍스트 특성·PCA·ANN 기반 비교 분석」

**최종 제안 제목**

> 「매칭된 주제 쌍(matched pair) 텍스트 분석을 통한 AI 생성 글과 인간 작성 글의
> 문체적 판별 요인 연구: 통계적 검정·PCA·머신러닝·ANN을 중심으로」

이 제목이 가장 정확한 이유:
- "matched pair"를 명시해 이 연구의 핵심 방법론적 기여(주제·장르 통제)를 드러낸다.
- "판별 요인"을 제목에 넣어 분류 정확도가 아니라 요인 탐색이 목적임을 분명히 한다.
- 사용하는 분석 기법(통계 검정, PCA, ML, ANN)을 부제로 명시해 방법론적 다각화를 보여준다.

---

## 2. 핵심 연구 질문 (RQ)

| ID | 질문 |
|----|------|
| RQ1 | AI 생성 글과 인간 작성 글은 텍스트의 정량적 특징만으로 유의미하게 구분될 수 있는가? |
| RQ2 | 두 집단을 구분하는 데 가장 중요한 언어적·문체적 변수는 무엇인가? |
| RQ3 | 장르·분야·주제·목적·독자·문체·길이를 통제한 뒤에도 AI/인간 차이가 나타나는가? |
| RQ4 | AI 글은 인간 글보다 더 규칙적이거나 반복적인 구조를 갖는가? |
| RQ5 | 어휘 다양성·문장 길이 변동성·품사 사용·접속 표현·반복성·감성은 두 집단에서 어떻게 다른가? |
| RQ6 | 30개 변수를 PCA로 압축했을 때 feature space에서 AI/인간이 얼마나 분리되는가? |
| RQ7 | ANN 및 기타 분류 모델은 AI/인간을 얼마나 정확히 분류하는가? |
| RQ8 | ANN이 높은 성능을 보인다면, 해석 가능한 모델로 그 이유를 설명할 수 있는가? |

가설 후보 H1~H7 (§13 참고)은 이 RQ들에 대한 잠정적 답이며, 결과가 반대로 나오면 반대로 보고한다.

---

## 3. 전체 데이터 설계

### 3.1 목표 규모

- Human = 300, AI = 300, 총 600개
- **1:1 matched-pair 구조**: `H001 ↔ A001`, `H002 ↔ A002`, … `H300 ↔ A300`
- 각 pair는 `pair_id`로 연결되며 다음 조건을 최대한 공유한다:
  genre, domain, topic, purpose, audience, style, target length

이 원칙이 무너지면(예: "아무 주제의 인간 글 300개 vs 아무 주제의 AI 글 300개") 모델이
AI/인간의 차이가 아니라 **장르·주제·길이 차이**를 학습하게 된다. 이것이 이 연구 설계
전체에서 가장 중요한 방법론적 제약이다.

### 3.2 Human 집단: Human Classic Corpus

- `group = "human_classic"`
- 원칙적으로 **생성형 AI의 영향을 받지 않은 시기**, 즉 **2018년 이전**에 실제 인간 저자가
  작성·발표·출판한 글을 사용한다.
- 출처: 책, 에세이, 연설문, 철학서, 역사서, 과학 교양서, 사회비평서, 문학적 산문, 자서전,
  칼럼, 공개 강연, 공공 기록.
- 선호하는 글의 구조 (토인비 『역사의 연구』, 세이건 『창백한 푸른 점』을 원형으로 삼음):

  ```
  구체적 사실/장면  →  관점의 전환  →  인간·사회·세계로의 확장  →  하나의 Main Message
  ```

- 선정 기준 (전부 충족해야 함):
  1. 2018년 이전 실제 인간 저작 (존재하지 않는 글 생성 금지)
  2. AI가 특정 작가 문체를 모방해 만든 글이 아닐 것
  3. 하나의 중심 Main Message가 있을 것 ("결국 이 글은 무엇을 말하는가?"에 한 문장으로 답 가능)
  4. 명언 모음이 아니라 사고 전개 과정이 있을 것
  5. 정보 전달보다 인간·사회·역사·문명에 대한 사고의 확장이 있는 글 우선
  6. 구체적 사례/관찰 → 더 큰 의미로 확장되는 글 우선
  7. 주제·논리 구조가 서로 겹치지 않도록 다양화
  8. 원칙적으로 한 저자당 한 작품만 선정
  9. 시대·분야·문체가 서로 다른 글 확보

### 3.3 저작권 규칙 (매우 중요)

- `excerpt_text`에는 **실제로 해당 저자가 쓴 원문 또는 검증 가능한 정식 번역문만** 들어간다.
- AI가 내용을 요약하거나 비슷하게 재작성한 문장은 **절대** `excerpt_text`에 넣지 않는다.
- 원문 전문 제공이 가능하면(공개 도메인 등) 원문을 그대로 입력한다.
- 저작권 보호 중이어서 원문을 제공할 수 없으면 `excerpt_text = ""`로 두고
  `source_location`, `source_url`, `content_summary`를 대신 제공한다.
- **출처를 확실히 검증할 수 없는 후보는 제외한다.**

> **본 세션의 제약 사항 (중요, 투명하게 기록):**
> 이 저장소를 생성한 실행 환경은 네트워크 egress 정책상 Project Gutenberg, Wikisource,
> 일반 웹 페이지(WebFetch)에 대한 접근이 차단되어 있어(`EGRESS_BLOCKED`), 이번 세션에서는
> 원문을 1자 단위로 대조 검증할 수 없었다. 이 규칙을 지키기 위해 스타터 배치
> (`data/human_classic/batch01_human_classic.jsonl`)는 **서지정보(저자/제목/연도/출처
> URL/장르/주제 등)만 확정하고 `excerpt_text`는 비워둔 채 `verified: false`로 표시**했다.
> 실제 원문 대조·붙여넣기는 인터넷 접근이 가능한 환경(연구자의 로컬 PC, Google Colab 등)에서
> 사람이 직접 1차 자료를 열람하며 수행해야 한다. §12(작업 순서)에 이 작업을 STEP 3-1로
> 명시했다.

### 3.4 AI 집단: AI Generated Corpus

- `group = "ai_generated"`
- **AI에게 인간 원문을 보여주고 "비슷하게 써라"라고 요청하지 않는다.** 그렇게 하면 독립적인
  생성 실험이 아니라 패러프레이징 실험이 되어버린다.
- AI에게는 Human 샘플에서 추출한 **metadata만** 제공한다 (genre, domain, topic, purpose,
  audience, style, target length). 문장 구조·표현을 직접 참고하지 않는다.
- 이 규칙을 지키는 자동화 함수가 `src/prompt_builder.py`의 `build_ai_prompt()`다.
- 가능하면 여러 AI 모델(예: ChatGPT 계열, Claude 계열, Gemini 계열)을 균형 있게 사용해
  "특정 모델과 인간의 차이"가 아니라 "생성형 AI 일반과 인간의 차이"를 보도록 한다.
  모델별 배분 예시: ChatGPT 100 / Claude 100 / Gemini 100.
- 모델을 여러 개 쓰면 `ai_model` 자체가 새로운 변수가 되므로 다음을 반드시 기록한다:
  `ai_model`, `model_version`, `generation_date`, `temperature`, `prompt_id`, `pair_id`.

### 3.5 텍스트 길이

- 한국어: 약 500~700자 (목표 약 600자)
- 영어: 약 150~300 words
- 길이를 맞추려고 문장 중간에서 자르지 않는다. 완결된 문단, 또는 이어지는 짧은 연속
  문단을 하나의 데이터로 사용한다.

---

## 4. Human corpus metadata 태깅 체계

각 Human 글은 최소 7가지 정보를 갖는다: `genre`, `domain`, `topic`, `purpose`, `audience`,
`style`, `length`.

- **genre** 예: essay, history, philosophy, science_essay, speech, literature,
  social_criticism, autobiography, explanatory, argumentative, literary_prose
- **domain** 예: history, philosophy, science, geography, mathematics, society, politics,
  economics, literature, environment, technology, education, art
- **topic**: 더 구체적으로 기록 (예: `civilization_and_challenge`, `humanity_and_cosmos`,
  `technology_and_progress`, `place_and_identity`, `freedom_and_responsibility`)
- **purpose** 예: explanation, persuasion, criticism, analysis, reflection, narration,
  information, problem_raising
- **audience** 예: general_public, students, specialists, academic, unknown
- **style** 예: objective, academic, lyrical, emotional, critical, reflective, formal,
  explanatory, narrative

### Main Message vs Value

초기 구상에서는 자유·정의·사랑·책임·희생 등 "가치"를 태깅하려 했으나, value는 연구자
주관이 강하게 개입되는 지표다. 따라서 1차 분석 변수로는 `topic`, `purpose`,
`main_message`만 사용하고, `value_optional`은 보조 metadata로만 남긴다.

`main_message`는 "이 글 전체를 한 문장으로 압축하면 무엇인가?"에 대한 답이며,
**분류 feature로 직접 사용하지 않는다** (§9 데이터 누수 방지 참고 — 사람이 만든 해석
문장이므로 정보 누수 위험이 있다).

인간 글이 고르게 포함해야 할 주제 분야 목록은 `docs/human_corpus_plan.md`(§12에서 생성)에
정리한다: 역사와 문명, 인간과 사회, 인간의 위치, 과학과 우주, 자연과 환경, 도시와 장소,
공간과 인간, 전쟁과 평화, 기술과 진보, 자유와 책임, 삶과 죽음, 시간과 기억, 지식과 무지,
인간의 오만과 한계, 위기와 변화, 협력과 경쟁, 불평등, 문명의 흥망, 개인과 공동체, 환경과
적응, 교육, 경제, 정치, 예술, 지리, 철학.

---

## 5. 데이터 스키마

### 5.1 Human 스키마

`schema/human_schema.json` 파일과 아래 필드가 1:1로 대응한다.

```json
{
  "sample_id": "H001",
  "pair_id": "P001",
  "group": "human_classic",
  "label": 0,
  "author": "",
  "title": "",
  "year": 0,
  "genre": "",
  "domain": "",
  "topic": "",
  "purpose": "",
  "audience": "",
  "style": "",
  "main_message": "",
  "value_optional": "",
  "original_language": "",
  "excerpt_text": "",
  "excerpt_char_count": 0,
  "excerpt_word_count": 0,
  "content_summary": "",
  "argument_structure": "",
  "source_location": "",
  "source_url": "",
  "copyright_status": "",
  "selection_reason": "",
  "verified": false
}
```

### 5.2 AI 스키마

`schema/ai_schema.json` 파일과 대응한다.

```json
{
  "sample_id": "A001",
  "pair_id": "P001",
  "group": "ai_generated",
  "label": 1,
  "ai_model": "",
  "model_version": "",
  "generation_date": "",
  "temperature": null,
  "prompt_id": "",
  "genre": "",
  "domain": "",
  "topic": "",
  "purpose": "",
  "audience": "",
  "style": "",
  "main_message": "",
  "generated_text": "",
  "text_char_count": 0,
  "text_word_count": 0
}
```

두 스키마 모두 JSONL로 저장하며, 각 줄은 독립적으로 `json.loads()` 가능해야 한다.

---

## 6. AI 생성 프롬프트 자동화

`src/prompt_builder.py`의 `build_ai_prompt(row)` 함수는 Human 샘플의 metadata만 읽어
재현 가능한 프롬프트를 만든다. 포함하는 정보: 분야, 구체적 주제, 장르, 목적, 예상 독자,
문체, 목표 길이.

**절대 사용하지 않는 표현**: "아래 인간 글과 비슷하게 작성하라", "○○ 작가처럼 써라",
"아래 글의 문체를 모방하라" 등 원문을 직접 참조시키는 표현. 함수 자체가 human excerpt를
인자로 받지 않도록 설계해 구조적으로 이 실수를 방지한다.

---

## 7. 30개 핵심 Feature

학부 연구 범위에 맞게 최종 feature를 **30개**로 제한한다. 다섯 범주로 균형 있게 구성하며,
정확한 정의·계산식·구현은 `src/feature_extraction.py`와 그 안의 docstring에 있다. 각
feature는 가능한 한 텍스트 길이에 영향을 덜 받도록 **비율(ratio)·per-sentence·per-100-words**
형태로 정규화한다.

### A. 문장 구조 (8개)
1. `sentence_count` — 문장 수
2. `avg_sentence_length` — 문장당 평균 단어 수
3. `sentence_length_std` — 문장 길이 표준편차 (변동성)
4. `sentence_length_cv` — 변동계수 (std/mean, 길이 영향 보정)
5. `max_sentence_length` — 최장 문장 길이
6. `min_sentence_length` — 최단 문장 길이
7. `comma_rate` — 문장당 평균 쉼표 수
8. `punctuation_rate` — 100단어당 구두점 수

### B. 어휘 다양성 (7개)
9. `word_count` — 총 단어 수 (통제 변수로도 사용)
10. `unique_word_count` — 고유 단어 수
11. `type_token_ratio` (TTR) — unique/total
12. `root_ttr` (Guiraud's R) — unique / sqrt(total), 길이 보정
13. `mattr` — Moving-Average TTR (window=50), 길이에 가장 안정적
14. `avg_word_length` — 평균 단어 길이(문자 수)
15. `lexical_repetition_rate` — 상위 빈도 단어가 전체에서 차지하는 비율

### C. 품사 사용 비율 (7개)
16. `noun_ratio`
17. `verb_ratio`
18. `adjective_ratio`
19. `adverb_ratio`
20. `pronoun_ratio`
21. `particle_ratio` (한국어 조사 / 영어는 전치사·관사로 대체 정의)
22. `conjunction_ratio`

모두 "품사 개수 / 전체 토큰 수" 비율로 정규화한다. 한국어는 `kiwipiepy`(설치가 가장
가볍고 Colab/서버 환경에서 안정적)를 1순위로 사용하고, 대안으로 `KoNLPy Okt`를 지원한다.
영어는 표준 태거(NLTK `averaged_perceptron_tagger` 또는 spaCy)를 사용한다.

### D. 반복성·규칙성 (6개)
23. `repeated_word_rate` — 2회 이상 등장한 단어가 전체 단어 토큰에서 차지하는 비율
24. `repeated_bigram_rate` — 2회 이상 등장한 bigram 비율
25. `repeated_trigram_rate` — 2회 이상 등장한 trigram 비율
26. `sentence_start_repetition` — 문장 시작 단어(또는 시작 품사)가 반복되는 비율
27. `conjunction_repetition_rate` — 가장 많이 쓰인 접속 표현이 전체 접속 표현에서 차지하는 비율
28. `three_item_enumeration_rate` — "A, B, and/그리고 C" 형태의 3항 병렬 나열이 문장당
    등장하는 비율 (H3 가설 검증용 실험적 feature)

### E. 감성·정보량 (2개 고정 + 검토 후보)
29. `sentiment_score` — 어휘 기반 극성 점수 (VADER 등, 영어) / 감성사전 기반(한국어)
30. `lexical_entropy` — 단어 사용 분포의 Shannon entropy (정보량·예측가능성 지표)

> 후보로 검토했으나 최종 30개에서 제외한 변수(사유는 `feature_extraction.py` 상단 주석에
> 기록): `positive_word_ratio`/`negative_word_ratio`(29번과 중복 정보), `readability`
> (평균 문장 길이·평균 단어 길이의 선형결합이라 1,14와 다중공선성 위험 높음),
> `stopword_ratio`(장르 의존성이 매우 커서 matched-pair 통제 취지와 충돌),
> `abstract_word_ratio`/`concrete_word_ratio`(신뢰할 만한 한국어 concreteness 사전 부재로
> 구현 신뢰도 낮음), `parallel_structure_rate`/`enumeration_rate`(28번 3항 나열로 대표성
> 확보, 완전한 병렬구조 파서는 학부 연구 범위 초과).

### Feature Engineering 원칙

각 feature는 `feature_extraction.py`에서 다음을 문서화한다: 정확한 정의, 계산식, AI/Human
비교에서 의미 있는 이유, Python 구현, 텍스트 길이 영향 여부, 정규화 필요 여부.

---

## 8. 중복 변수(다중공선성) 처리

`word_count`, `char_count`, `sentence_count`, `avg_sentence_length`, `unique_word_count`
등은 서로 강한 상관을 가질 수 있다. 노트북 SECTION 13(상관관계 분석)에서 다음을 수행한다.

1. 기술통계 + 상관행렬(Pearson) 확인
2. |r| > 0.85 인 변수쌍을 표로 정리하고, 각각 "왜 상관이 높은지"를 설명
3. 개념적으로 완전히 중복되는 경우에만 제거/통합하고, **상관계수만 보고 기계적으로
   삭제하지 않는다** — 예: `word_count`는 통제 변수(길이)로서 의미가 있으므로 상관이
   높아도 유지하고 대신 다른 길이-보정 변수(MATTR 등)를 병행 사용한다.
4. VIF(분산팽창지수)로 다중공선성을 추가 점검한다.

---

## 9. 데이터 누수(data leakage) 방지 — 가장 중요한 원칙

`H001`과 `A001`은 같은 topic/genre/purpose/style을 공유한다. 일반적인 랜덤
`train_test_split`을 쓰면 H001은 train, A001은 test에 들어갈 수 있고, 이 경우 모델이
**주제 정보**를 학습해 실제보다 높은 성능을 보이는 착시가 생긴다.

따라서:
- 모든 샘플에 `pair_id`를 부여한다.
- `GroupShuffleSplit`, `GroupKFold`, `StratifiedGroupKFold` 중 하나를 사용해 **같은
  pair_id의 Human/AI가 항상 같은 fold**에 들어가도록 한다.
- `main_message`처럼 사람이 만든 해석 문장은 feature로 사용하지 않는다(§4 참고).
- `main_message`의 임베딩, `title`/`author` 등 식별 정보도 feature 목록에서 원천 배제한다.

이 원칙은 노트북 SECTION 21에서 코드로 구현하고, 결과 해석에서도 반복 언급한다.

### 9.1 추가 일반화 검증

1. **Pair-aware random group split**: `GroupShuffleSplit`으로 pair 단위 무작위 분할
2. **Domain/genre hold-out**: 예를 들어 `domain == "history"` 전체를 test로 남기고 나머지
   도메인으로 학습한 모델이 history에서도 AI/Human을 구분하는지 확인. 이를 통해 모델이
   "분야 특성"을 학습한 것인지 "일반적 AI/인간 문체 차이"를 학습한 것인지 구분한다.

---

## 10. 분석 파이프라인 개요

| 단계 | 내용 | 도구 |
|------|------|------|
| EDA | 30개 feature의 기술통계·분포 비교 (전체/장르별/모델별) | pandas, seaborn |
| 통계 검정 | pair 구조를 반영한 Wilcoxon signed-rank / paired t-test, effect size, FDR 보정 | scipy, statsmodels |
| PCA | 표준화 후 비지도 차원 축소, PC1/PC2 분리도 시각화, loading 해석 | scikit-learn |
| Logistic Regression | 해석 가능한 baseline, 표준화 계수의 방향 해석 | scikit-learn |
| Decision Tree | 사람이 읽을 수 있는 규칙 (max_depth ≤ 4) | scikit-learn |
| Random Forest | 성능 + impurity/permutation importance + SHAP | scikit-learn, shap |
| ANN | 분류 가능성 확인 (해석은 다른 모델에 위임) | TensorFlow/Keras |
| 평가 | Accuracy/Precision/Recall/F1/ROC-AUC/Confusion Matrix + Group-aware CV | scikit-learn |
| 강건성 | AI 모델별, 장르/도메인 hold-out별 비교 | pandas, scikit-learn |
| 결과 종합 | Top10 feature, 자동 결과 요약 | pandas |

각 모델의 **역할 분담**(§13 원문의 원칙을 그대로 유지):

- **ANN**: 분류 가능성 자체를 확인 (성능이 가장 높다고 해서 "최종 결론 모델"로 취급하지 않는다)
- **Random Forest / Permutation Importance / SHAP**: 어떤 변수가 중요한지, 그 값이 커질수록
  AI/Human 어느 쪽으로 작용하는지 확인
- **Logistic Regression**: 영향의 방향(+/-)을 계수로 확인
- **Decision Tree**: 사람이 이해 가능한 분류 규칙 제시
- **PCA**: feature space 전체 구조 확인 (지도학습이 아니므로 "겹친다 = 구분 불가"로
  단정하지 않는다)

---

## 11. 교란변수(confounder)

다음을 반드시 논의·기록한다: text length, genre, domain, topic, author, publication year,
translation 여부, original_language, AI model, prompt wording.

- 번역문과 원문을 섞으면 번역가의 문체가 개입할 수 있으므로, 분석 언어를 통일하고
  `original_language`/번역 여부를 metadata로 명시한다.
- AI가 번역한 문장은 Human 데이터에 절대 포함하지 않는다.

---

## 12. 작업 순서 (STEP)

원 지시사항의 §56을 그대로 따르되, 본 세션의 네트워크 제약(§3.3 참고)을 반영해 STEP 3을
두 단계로 나눈다.

1. STEP 1 — 연구 설계 검토 *(본 문서, 완료)*
2. STEP 2 — Human corpus schema 확정 *(완료, §5.1)*
3. STEP 3-0 — Human corpus 25개 단위 batch **후보 서지정보** 조사 (저자/제목/연도/출처/장르
   /주제/구조 분석) — 이번 세션에서 batch 1(12개)을 시범 진행
4. STEP 3-1 — **원문 대조 검증** (`verified: true`로 전환) — 인터넷 접근이 되는 환경에서
   사람이 Gutenberg/Wikisource/원서를 직접 대조하며 `excerpt_text` 채움. *(이번 세션에서는
   수행 불가 — 후속 작업으로 명시)*
5. STEP 4 — 각 Human 데이터 metadata 정제
6. STEP 5 — Human metadata 기반 AI 생성 프롬프트 생성 (`build_ai_prompt`)
7. STEP 6 — AI corpus 생성 (여러 모델에 분산)
8. STEP 7 — Human/AI pair quality 검사 (길이 분포, 장르 분포 시각화)
9. STEP 8 — 30개 feature 확정 *(완료, §7)*
10. STEP 9 — feature extraction 코드 작성 *(완료, `src/feature_extraction.py`)*
11. STEP 10 — 통계 분석 + PCA
12. STEP 11 — Decision Tree / Random Forest / Logistic Regression
13. STEP 12 — ANN
14. STEP 13 — 모델 비교 및 해석
15. STEP 14 — 논문용 결과표·그래프 생성
16. STEP 15 — Results / Discussion / Conclusion 작성

25개 단위 batch 처리 원칙(§47 원문)은 `docs/human_corpus_plan.md`에 batch 진행 체크리스트로
구체화한다.

---

## 13. 검증 대상 가설 (사실이 아니라 가설)

| ID | 가설 |
|----|------|
| H1 | AI 글은 인간 글보다 문장 길이의 분산이 작을 수 있다 |
| H2 | AI 글은 특정 접속 표현을 반복적으로 사용할 수 있다 |
| H3 | AI 글은 인간 글보다 병렬 구조(특히 3항 나열)가 규칙적으로 나타날 수 있다 |
| H4 | Human classic corpus는 AI 글보다 어휘 다양성이 높을 수 있다 |
| H5 | AI 글은 명사·형용사·부사 등 일부 품사 비율에서 특징적 차이를 보일 수 있다 |
| H6 | AI 글은 문단/문장의 구조적 균형성이 더 높을 수 있다 |
| H7 | Human 글은 문장 길이·구조의 burstiness(불규칙성)가 더 클 수 있다 |

결과가 가설과 반대로 나오면 반대로, 유의하지 않으면 유의하지 않다고 그대로 보고한다.

---

## 14. 결론 작성 시 원칙 (과장 금지)

다음과 같은 결론은 **금지**한다: "AI는 인간보다 문장력이 떨어진다", "인간의 글은 AI보다
우월하다", "AI는 창의성이 없다". 이 연구의 feature와 분석 설계만으로는 가치판단을 증명할
수 없다.

대신 다음과 같이 제한적으로 표현한다:

> "본 데이터셋과 분석 조건에서 AI 생성 글은 인간 글에 비해 ○○의 경향을 보였다."
> "○○ 변수는 AI와 인간을 구분하는 데 비교적 높은 기여를 보였다."
> "해당 결과가 모든 언어·장르·AI 모델에 일반화된다고 단정할 수 없다."

---

## 15. 연구의 한계 (미리 인지해야 할 것들)

- Human corpus 선정 편향, '명문'이라는 기준 자체의 주관성
- AI 모델 선택 편향, prompt dependency (프롬프트 문구를 바꾸면 결과가 달라질 수 있음)
- 번역 텍스트 문제 (번역가 문체 개입 가능성)
- 600개라는 데이터 규모의 통계적 한계(특히 ANN 등 딥러닝 모델의 과적합 위험)
- feature engineering 자체의 한계 (30개로 포착 못하는 문체적 차이가 존재할 수 있음)
- 품사 분석기(POS tagger) 오류 가능성, 특히 한국어 형태소 분석의 중의성
- 시대별 인간 문체 변화, 장르별 차이가 "AI다움"과 뒤섞일 위험
- 저작권으로 인한 원문 확보 제한 (일부 샘플은 `excerpt_text`가 비어 feature 계산에서
  제외되거나 별도 처리 필요)
- AI 모델이 계속 발전하므로 이 결과가 미래의 AI 글쓰기에도 적용된다고 보장할 수 없음

---

## 16. 후속 확장 연구 아이디어

- AI vs 인간 일반 텍스트 (명문이 아닌 일상적 글)
- AI vs 고전 명문 (본 연구)
- AI vs 현대 인간 글
- AI vs 연구자 본인의 글/일기
- 고전 명문 vs 연구자 본인의 글

이를 통해 단순 AI 판별기를 넘어 "좋은 글은 어떤 문체적 특징을 갖는가?", "나의 글은 AI와
인간 명문의 어느 쪽에 가까운가?"라는 질문으로 확장할 수 있다.
