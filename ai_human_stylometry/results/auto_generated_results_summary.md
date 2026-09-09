## 자동 생성 결과 요약 (Results 초안)

**⚠️ 아래 수치는 SYNTHETIC DEMO 데이터(절차적으로 생성한 더미 텍스트, N=60)로 파이프라인이 정상 작동하는지 확인한 결과다. 실제 AI/인간 문체 차이에 대한 연구 결과가 아니므로 논문에 인용하면 안 된다. USE_SYNTHETIC_DEMO=False로 바꾸고 실제 600개 데이터 경로를 지정한 뒤 다시 실행하면, 이 자리에 실제 연구 결과가 채워진다.**

- 총 60개 샘플(Human 30개, AI 30개)을 분석했다.
- FDR 보정 후 유의(p_adjusted<0.05)했던 feature는 28/30개였다.
- PCA 상위 2개 주성분은 전체 분산의 77.8%를 설명했다.
- 가장 높은 accuracy를 보인 모델은 Logistic Regression (accuracy=1.00, F1=1.00, ROC-AUC=1.00)였다. 다만 연구설계 원칙상 이는 '가장 우수한 모델'이 아니라 '분류 가능성의 확인'으로 해석한다.
- effect size·Random Forest importance·permutation importance·SHAP을 종합했을 때 상위 3개 변수는 sentence_length_cv, pronoun_ratio, verb_ratio였다.
  - **sentence_length_cv**: 본 데이터셋과 분석 조건에서 Human에서 더 높음의 경향을 보였다 (Human 평균=0.653, AI 평균=0.131).
  - **pronoun_ratio**: 본 데이터셋과 분석 조건에서 Human에서 더 높음의 경향을 보였다 (Human 평균=0.104, AI 평균=0.012).
  - **verb_ratio**: 본 데이터셋과 분석 조건에서 Human에서 더 높음의 경향을 보였다 (Human 평균=0.209, AI 평균=0.115).

### 결론 작성 시 주의 (연구설계 §14)
- 위 결과는 '본 데이터셋과 분석 조건'에서의 경향으로만 해석하며, 모든 언어·장르·AI 모델에 일반화된다고 단정하지 않는다.
- '문장력이 떨어진다/우월하다/창의성이 없다'와 같은 가치판단으로 결과를 확장하지 않는다.