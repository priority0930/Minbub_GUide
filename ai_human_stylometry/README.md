# AI/인간 글쓰기 문체 비교 연구 (`ai_human_stylometry`)

학부 학술 연구 프로젝트: **"AI가 생성한 글과 인간이 작성한 글은 문체·구조·어휘·의미 조직
측면에서 정량적으로 구별될 수 있는가? 구별된다면 그 핵심 요인은 무엇인가?"**를 다룬다.
이 연구는 AI 판별기(detector)를 잘 만드는 것이 목적이 아니라, **왜 구별되는지를 밝히는
것**이 목적이다. 전체 설계 원칙과 근거는 [`docs/research_design.md`](docs/research_design.md)에
모두 정리되어 있다 — 이 README를 읽기 전에 먼저 그 문서를 읽는 것을 권한다.

## 지금 이 저장소에 있는 것 / 아직 없는 것

| 구성 요소 | 상태 |
|---|---|
| 연구 설계 문서 (`docs/research_design.md`) | ✅ 완료 |
| 데이터 스키마 (`schema/*.json`) | ✅ 완료 |
| AI 프롬프트 자동 생성 함수 (`src/prompt_builder.py`) | ✅ 완료, 자기 테스트 통과 |
| 30개 feature 추출 코드 (`src/feature_extraction.py`) | ✅ 완료, 동작 확인 |
| Human corpus 서지정보 스타터 배치 12개 | ✅ 완료 (`data/human_classic/batch01_human_classic.jsonl`) — **단, `excerpt_text`는 원문 대조 검증 전까지 비어 있음** |
| 대응 AI corpus 12개 | ✅ 완료 (`data/ai_generated/batch01_ai_generated.jsonl`) |
| Synthetic demo 데이터 (파이프라인 테스트용) | ✅ 완료 (`data/sample_synthetic/synthetic_test_data.jsonl`, 30쌍) |
| 전체 분석 파이프라인 노트북 | ✅ 완료, synthetic demo 데이터로 처음부터 끝까지 실행 검증 완료 |
| **Human 300 + AI 300 최종 코퍼스** | ❌ **미완성** — 이 저장소가 만들어진 세션은 네트워크 정책상 원문 검증용 웹 접근이 차단되어 있어 진행하지 못했다 |
| 실제 데이터 기반 연구 결과 (통계/PCA/ML/ANN 결론) | ❌ **아직 없음** — 노트북은 synthetic demo 데이터로만 실행되었다 |

**가장 중요한 점**: `notebooks/ai_human_stylometry_analysis.ipynb`를 지금 열어 보면 그래프와
표가 이미 채워져 있지만, 이것은 **실제 연구 결과가 아니라 절차적으로 생성한 더미 텍스트
(synthetic demo)로 코드가 정상 작동하는지 확인한 결과**다. 노트북 맨 위와
SECTION 3, SECTION 34에 이 사실이 반복해서 명시되어 있다. 실제 결론은 §"다음 단계" 문단대로
Human 300 + AI 300 코퍼스를 완성한 뒤에 나온다.

## 왜 corpus가 아직 없는가 (투명하게 기록)

이 프로젝트의 지시사항은 Human 글의 `excerpt_text`에 **실제 원문만** 넣고, AI가 요약하거나
재작성한 문장은 절대 넣지 말라고 요구한다(저작권 원칙, `docs/research_design.md` §3.3).
원문을 1자 단위로 정확히 대조하려면 Project Gutenberg/Wikisource 같은 1차 자료에 접근해야
하는데, 이 저장소가 만들어진 실행 환경은 네트워크 egress 정책상 그런 웹 페이지 접근
(`WebFetch`)이 전부 차단되어 있었다. 그래서:

- Human 스타터 배치 12건은 **저자·제목·연도·장르·주제·출처 URL·내용 요약·논증 구조**까지는
  확정했지만, `excerpt_text`는 비워 두고 `verified: false`로 표시했다.
- AI 대응 배치 12건은 Human 쪽의 metadata만 사용해 (`build_ai_prompt()`가 생성한 프롬프트로)
  실제로 생성한 텍스트다 — 이쪽은 진짜 데이터다.
- 파이프라인 자체를 검증하기 위해 30쌍짜리 synthetic demo 데이터를 별도로 만들어 노트북을
  실제로 실행했다.

## 다음 단계 (인터넷 접근이 되는 환경에서 이어서 할 일)

1. `data/human_classic/batch01_human_classic.jsonl`의 12건에 대해, `source_url`에 적힌
   Project Gutenberg/Avalon Project 페이지를 직접 열어 `source_location`에 적힌 문단을
   1자 단위로 대조하고 `excerpt_text`를 채운 뒤 `verified: true`로 바꾼다.
2. `docs/research_design.md` §12(STEP 3~7)를 따라 25개 단위 batch로 Human corpus를
   300개까지 확장한다. `selection_reason`, `content_summary`, `argument_structure`는
   이번 12건과 같은 형식으로 계속 채운다.
3. 새 Human batch마다 `python src/prompt_builder.py`의 `build_ai_prompt()`로 프롬프트를
   생성하고, 여러 AI 모델(ChatGPT/Claude/Gemini 등)에 입력해 대응 AI corpus를 만든다.
4. 완성된 Human 300개와 AI 300개를 각각 `data/human_classic/human_classic_full.jsonl`,
   `data/ai_generated/ai_generated_full.jsonl`로 합친다.
5. `notebooks/ai_human_stylometry_analysis.ipynb`의 SECTION 3에서
   `USE_SYNTHETIC_DEMO = False`로 바꾸고 두 경로를 위 파일로 지정한 뒤 **Run All**을 실행한다.
6. `results/`에 쌓인 CSV·그래프와 `results/auto_generated_results_summary.md`를 바탕으로
   논문 Results/Discussion/Conclusion을 작성한다 (과장 금지 원칙, 연구설계 §14 참고).

## 폴더 구조

```
ai_human_stylometry/
├── docs/
│   └── research_design.md          # 연구 설계 전체 문서 (반드시 먼저 읽기)
├── schema/
│   ├── human_schema.json           # Human JSONL 스키마
│   └── ai_schema.json              # AI JSONL 스키마
├── src/
│   ├── prompt_builder.py           # build_ai_prompt(): Human metadata -> AI 생성 프롬프트
│   └── feature_extraction.py       # extract_features(): 30개 feature 계산
├── data/
│   ├── human_classic/
│   │   └── batch01_human_classic.jsonl   # 서지정보 확정 12건 (excerpt_text 검증 대기)
│   ├── ai_generated/
│   │   └── batch01_ai_generated.jsonl    # 위 12건에 대응하는 실제 AI 생성 텍스트
│   └── sample_synthetic/
│       └── synthetic_test_data.jsonl     # 파이프라인 테스트용 더미 데이터 (30쌍)
├── notebooks/
│   └── ai_human_stylometry_analysis.ipynb  # 전체 분석 파이프라인 (실행 완료 상태로 커밋됨)
├── results/                         # 노트북 실행 시 자동 생성되는 CSV 결과표
│   └── figures/                     # 노트북 실행 시 자동 생성되는 PNG 그래프
└── requirements.txt
```

## 실행 방법

```bash
cd ai_human_stylometry
pip install -r requirements.txt

# 노트북을 처음부터 끝까지 실행 (Jupyter UI에서 Run All을 눌러도 동일)
jupyter nbconvert --to notebook --execute --inplace notebooks/ai_human_stylometry_analysis.ipynb
```

영어 분석에 필요한 NLTK 리소스(`punkt`, POS tagger, VADER)는 `src/feature_extraction.py`의
`ensure_nltk_resources()`가 최초 1회 자동으로 내려받는다. 일반 PC나 Google Colab에서는
별도 설정 없이 동작한다 (이 저장소를 만든 샌드박스 환경에서만 프록시 정책 때문에
`NLTK_ALLOW_PROXIED_URLOPEN=1` 환경변수가 필요했다 — 코드에 이미 반영되어 있다).

한국어 분석은 `kiwipiepy`를 사용하도록 구현되어 있다. `pip install kiwipiepy`로 설치한다
(일반 환경에서는 문제없이 설치되지만, 이 저장소를 만든 샌드박스는 시스템 setuptools
버전 문제로 설치가 실패해 한국어 경로는 이번 세션에서 직접 실행 검증하지 못했다 —
`src/feature_extraction.py` 상단 주석 참고).

## 핵심 설계 원칙 요약 (자세한 내용은 `docs/research_design.md`)

- **1:1 matched-pair**: 모든 Human 샘플은 genre/domain/topic/purpose/audience/style이
  최대한 유사한 AI 샘플과 `pair_id`로 짝지어진다.
- **AI는 원문을 보지 않는다**: `build_ai_prompt()`는 Human 원문을 인자로 받지 않으며,
  "비슷하게 써라" 류의 표현을 코드 레벨에서 금지한다.
- **데이터 누수 방지**: `GroupShuffleSplit`/`GroupKFold`로 같은 `pair_id`의 Human/AI가
  항상 같은 fold에 들어가도록 강제한다.
- **역할 분담**: ANN=분류 가능성 확인, Random Forest/Permutation/SHAP=중요 변수 확인,
  Logistic Regression=영향 방향 확인, Decision Tree=사람이 이해 가능한 규칙,
  PCA=feature space 구조 확인. 어느 한 모델의 정확도만으로 결론을 내리지 않는다.
- **과장 금지**: "AI가 열등하다/우월하다" 식의 가치판단이 아니라 "본 데이터셋과 분석
  조건에서 ○○ 경향을 보였다"는 제한적 문장으로만 결론을 서술한다.
