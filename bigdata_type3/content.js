// 빅분기 TYPE 3 — 템플릿, 개념, 퀴즈, 암기카드, 학습계획 (수동 작성 콘텐츠)
window.TEMPLATES = [
  {
    id: 'T01', name: '단일표본 t검정', func: 'ttest_1samp', level: 1, day: 1, core: true,
    imp: 'from scipy.stats import ttest_1samp',
    keys: 'ttest_1samp 단일표본 t검정 one sample 평균 기준값 popmean 모평균',
    when: '한 집단의 평균이 주어진 기준값(예: 70점, 500시간)과 다른지 볼 때.',
    h0: 'H0: 모평균 = 기준값 (mu = mu0)', h1: 'H1: 모평균 != 기준값',
    code: `from scipy.stats import ttest_1samp
a = df['score'].dropna()
result = ttest_1samp(a, 70)
print(result.statistic)
print(result.pvalue)
print(result.pvalue < 0.05)`,
    blanks: ['ttest_1samp', 'dropna', 'ttest_1samp', '70', 'statistic', 'pvalue', 'pvalue', '0.05'],
    outputs: [['result.statistic', 't 통계량'], ['result.pvalue', '양측 p-value'], ['len(a) - 1', '자유도 df']],
    pitfalls: ['결측치는 dropna()로 제거 (0으로 채우지 않기)', '단측검정이면 alternative=\'greater\' 또는 \'less\'', '기준값(popmean)은 두 번째 인자'],
  },
  {
    id: 'T02', name: '독립표본 t검정', func: 'ttest_ind', level: 1, day: 1, core: true,
    imp: 'from scipy.stats import ttest_ind',
    keys: 'ttest_ind 독립표본 two sample 두 집단 평균 비교 welch equal_var 등분산',
    when: '서로 다른 두 집단(A반/B반, 실험군/대조군)의 평균을 비교할 때.',
    h0: 'H0: mu1 = mu2', h1: 'H1: mu1 != mu2',
    code: `from scipy.stats import ttest_ind
a = df[df['group']=='A']['score'].dropna()
b = df[df['group']=='B']['score'].dropna()
result = ttest_ind(a, b, equal_var=False)
print(result.statistic)
print(result.pvalue)
print(a.mean()-b.mean())`,
    blanks: ['ttest_ind', 'ttest_ind', 'equal_var', 'False', 'statistic', 'pvalue', 'mean'],
    outputs: [['result.statistic', 't 통계량'], ['result.pvalue', 'p-value'], ['a.mean() - b.mean()', '평균 차이'], ['len(a)+len(b)-2', '자유도(등분산 가정 시)']],
    pitfalls: ['scipy 기본값은 equal_var=True. 등분산 가정 안 하면(Welch) 반드시 False', 'a, b 순서가 바뀌면 t의 부호가 바뀜', '같은 대상의 전후 비교라면 ttest_ind가 아니라 ttest_rel'],
  },
  {
    id: 'T03', name: '대응표본 t검정', func: 'ttest_rel', level: 1, day: 2, core: true,
    imp: 'from scipy.stats import ttest_rel',
    keys: 'ttest_rel 대응표본 paired 전후 before after 짝',
    when: '같은 대상을 두 번 측정한 값(전/후, 왼쪽/오른쪽)을 비교할 때.',
    h0: 'H0: 차이의 평균 = 0', h1: 'H1: 차이의 평균 != 0',
    code: `from scipy.stats import ttest_rel
d = df[['before','after']].dropna()
result = ttest_rel(d['before'], d['after'])
print(result.statistic)
print(result.pvalue)
print(d['after'].mean()-d['before'].mean())`,
    blanks: ['ttest_rel', 'dropna', 'ttest_rel', 'statistic', 'pvalue'],
    outputs: [['result.statistic', 't 통계량 (before - after 기준)'], ['result.pvalue', 'p-value'], ["(d['after']-d['before']).mean()", '평균 변화량']],
    pitfalls: ['두 열을 함께 dropna() 해서 짝을 유지', 'ttest_rel(before, after)는 before - after 기준. 순서를 바꾸면 부호 반대', '독립표본 t검정과 혼동 금지'],
  },
  {
    id: 'T04', name: '일원분산분석', func: 'f_oneway', level: 2, day: 3, core: true,
    imp: 'from scipy.stats import f_oneway',
    keys: 'f_oneway anova 분산분석 세 집단 3개 이상 평균 F통계량',
    when: '세 집단 이상의 평균이 모두 같은지 볼 때.',
    h0: 'H0: 모든 집단 평균이 같다', h1: 'H1: 적어도 한 집단 평균이 다르다',
    code: `from scipy.stats import f_oneway
a = df[df['group']=='A']['score'].dropna()
b = df[df['group']=='B']['score'].dropna()
c = df[df['group']=='C']['score'].dropna()
result = f_oneway(a,b,c)
print(result.statistic)
print(result.pvalue)`,
    blanks: ['f_oneway', 'f_oneway', 'statistic', 'pvalue'],
    outputs: [['result.statistic', 'F 통계량'], ['result.pvalue', 'p-value'], ['k-1, N-k', '집단간·집단내 자유도']],
    pitfalls: ['집단을 각각 나눠 넣는다 (리스트 하나가 아님)', '기각되어도 "어느 집단이 다른지"는 사후검정이 필요', 'statsmodels 방식: anova_lm(smf.ols(\'score ~ C(group)\', df).fit())'],
  },
  {
    id: 'T05', name: '카이제곱 독립성 검정', func: 'chi2_contingency', level: 2, day: 4, core: true,
    imp: 'from scipy.stats import chi2_contingency',
    keys: 'chi2_contingency 카이제곱 독립성 분할표 crosstab 기대도수 expected 자유도 dof 범주형 두 변수',
    when: '두 범주형 변수(성별 x 구매여부)가 서로 관련 있는지(독립인지) 볼 때.',
    h0: 'H0: 두 변수는 독립이다', h1: 'H1: 두 변수는 독립이 아니다(연관 있음)',
    code: `import pandas as pd
from scipy.stats import chi2_contingency
table = pd.crosstab(df['gender'], df['purchase'])
chi2,p,dof,expected = chi2_contingency(table)
print(chi2)
print(p)
print(dof)
print(expected)`,
    blanks: ['chi2_contingency', 'crosstab', 'chi2_contingency', 'dof', 'expected'],
    outputs: [['chi2', '카이제곱 통계량'], ['p', 'p-value'], ['dof', '자유도 (행-1)x(열-1)'], ['expected', '기대도수 배열']],
    pitfalls: ['원자료는 먼저 pd.crosstab으로 분할표를 만든다', '2x2 표는 기본으로 Yates 보정(correction=True). 보정 없이 하라면 correction=False', '반환값 4개의 순서: chi2, p, dof, expected'],
  },
  {
    id: 'T06', name: '카이제곱 적합도 검정', func: 'chisquare', level: 2, day: 4, core: true,
    imp: 'from scipy.stats import chisquare',
    keys: 'chisquare 적합도 goodness of fit 관측도수 기대비율 균등 한 범주형',
    when: '한 범주형 변수의 관측 빈도가 기대 비율(균등, 알려진 비율)과 맞는지 볼 때.',
    h0: 'H0: 관측 분포 = 기대 분포', h1: 'H1: 관측 분포 != 기대 분포',
    code: `from scipy.stats import chisquare
observed = [30,45,25]
expected = [100/3,100/3,100/3]
result = chisquare(observed,f_exp=expected)
print(result.statistic)
print(result.pvalue)`,
    blanks: ['chisquare', 'chisquare', 'f_exp', 'statistic', 'pvalue'],
    outputs: [['result.statistic', '카이제곱 통계량'], ['result.pvalue', 'p-value'], ['k - 1', '자유도 (범주 수 - 1)']],
    pitfalls: ['기대도수 = 기대비율 x 전체 수. 관측 합과 기대 합이 같아야 함', 'value_counts() 순서를 기대도수 순서와 맞추기(reindex)', 'f_exp 생략 시 균등분포와 비교'],
  },
  {
    id: 'T07', name: '피어슨 상관분석', func: 'pearsonr', level: 1, day: 5, core: false,
    imp: 'from scipy.stats import pearsonr',
    keys: 'pearsonr 피어슨 상관계수 r 선형 상관 correlation',
    when: '두 연속형 변수의 선형 관계 강도와 방향을 볼 때.',
    h0: 'H0: 모상관계수 = 0', h1: 'H1: 모상관계수 != 0',
    code: `from scipy.stats import pearsonr
d = df[['hours','score']].dropna()
result = pearsonr(d['hours'],d['score'])
print(result.statistic)
print(result.pvalue)`,
    blanks: ['pearsonr', 'dropna', 'pearsonr', 'statistic', 'pvalue'],
    outputs: [['result.statistic', '상관계수 r (-1 ~ 1)'], ['result.pvalue', 'p-value'], ["df['x'].corr(df['y'])", 'r만 빠르게 (p-value 없음)']],
    pitfalls: ['두 열을 함께 dropna()', 'r의 제곱 = 단순회귀 R²', '이상치에 민감 → 순위 기반은 spearmanr'],
  },
  {
    id: 'T08', name: '스피어만 상관분석', func: 'spearmanr', level: 1, day: 5, core: false,
    imp: 'from scipy.stats import spearmanr',
    keys: 'spearmanr 스피어만 순위 상관 rho 서열 단조',
    when: '순위·서열 자료, 이상치가 있거나 비선형이지만 단조 관계를 볼 때.',
    h0: 'H0: 순위 상관 = 0', h1: 'H1: 순위 상관 != 0',
    code: `from scipy.stats import spearmanr
d = df[['x','y']].dropna()
result = spearmanr(d['x'],d['y'])
print(result.statistic)
print(result.pvalue)`,
    blanks: ['spearmanr', 'spearmanr', 'statistic', 'pvalue'],
    outputs: [['result.statistic', '스피어만 rho'], ['result.pvalue', 'p-value'], ["df['x'].corr(df['y'], method='spearman')", 'rho만 빠르게']],
    pitfalls: ['값이 아닌 순위끼리의 피어슨 상관', '구버전 scipy에서는 result.correlation (같은 값)'],
  },
  {
    id: 'T09', name: '선형회귀 OLS', func: 'ols', level: 2, day: 6, core: true,
    imp: 'import statsmodels.formula.api as smf',
    keys: 'ols 선형회귀 회귀계수 params pvalues rsquared 결정계수 수정 rsquared_adj fvalue f_pvalue conf_int 신뢰구간 predict 예측값 절편 intercept 유의한 변수',
    when: '연속형 종속변수를 하나 이상의 독립변수로 설명·예측할 때.',
    h0: 'H0(계수별): 회귀계수 = 0 / H0(모형): 모든 계수 = 0', h1: 'H1: 0이 아닌 계수가 있다',
    code: `import statsmodels.formula.api as smf
model = smf.ols('score ~ hours + sleep',data=df).fit()
print(model.summary())
print(model.params['hours'])
print(model.pvalues['hours'])
print(model.rsquared)
print(model.rsquared_adj)
print(model.fvalue)
print(model.f_pvalue)
print(model.conf_int())
print(model.predict({'hours':[5],'sleep':[7]}))`,
    blanks: ['ols', 'fit', 'params', 'pvalues', 'rsquared', 'rsquared_adj', 'fvalue', 'f_pvalue', 'conf_int', 'predict'],
    outputs: [["model.params['x']", '회귀계수'], ["model.params['Intercept']", '절편'], ["model.pvalues['x']", '계수의 p-value'], ['model.rsquared', 'R²'], ['model.rsquared_adj', '수정 R²'], ['model.fvalue', 'F 통계량'], ['model.f_pvalue', '모형 F검정 p-value'], ['model.conf_int()', '95% 신뢰구간 (0열 하한, 1열 상한)'], ['model.predict(...)', '예측값']],
    pitfalls: ['절편 이름은 대문자 \'Intercept\'', '범주형 독립변수는 C(변수)', '유의한 변수 개수 셀 때 절편 제외: model.pvalues.drop(\'Intercept\')', '.fit()을 빼먹지 않기'],
  },
  {
    id: 'T10', name: '로지스틱 회귀', func: 'logit', level: 3, day: 7, core: true,
    imp: 'import statsmodels.formula.api as smf',
    keys: 'logit 로지스틱 회귀 오즈비 odds ratio np.exp 예측확률 이진 0/1 합격 이탈',
    when: '0/1 이진 종속변수(합격, 이탈, 연체)를 설명하고 확률을 예측할 때.',
    h0: 'H0(계수별): 회귀계수 = 0 (오즈비 = 1)', h1: 'H1: 회귀계수 != 0',
    code: `import numpy as np
import statsmodels.formula.api as smf
model = smf.logit('pass_flag ~ hours',data=df).fit(disp=False)
print(model.params['hours'])
print(model.pvalues['hours'])
print(np.exp(model.params['hours']))
print(model.conf_int())
print(model.predict({'hours':[5]}))`,
    blanks: ['logit', 'disp', 'params', 'pvalues', 'exp', 'conf_int', 'predict'],
    outputs: [["model.params['x']", '계수 (로그오즈 변화량)'], ["np.exp(model.params['x'])", '오즈비'], ["model.pvalues['x']", 'p-value'], ['model.conf_int()', '계수 신뢰구간 (exp 적용 시 오즈비 CI)'], ['model.predict(...)', '예측확률 (0~1)']],
    pitfalls: ['오즈비 = np.exp(계수). 계수 그대로 답하면 오답', 'predict는 확률을 반환 (로그오즈 아님)', '종속변수는 0/1 숫자여야 함', 'fit(disp=False)로 반복 로그 숨김'],
  },
  {
    id: 'T11', name: '정규성 검정', func: 'shapiro', level: 1, day: 8, core: false,
    imp: 'from scipy.stats import shapiro',
    keys: 'shapiro 정규성 shapiro-wilk 정규분포 normality W',
    when: '데이터(또는 잔차)가 정규분포를 따르는지 확인할 때. t검정·ANOVA 전제 확인.',
    h0: 'H0: 정규분포를 따른다', h1: 'H1: 정규분포를 따르지 않는다',
    code: `from scipy.stats import shapiro
result = shapiro(df['score'].dropna())
print(result.statistic)
print(result.pvalue)`,
    blanks: ['shapiro', 'shapiro', 'statistic', 'pvalue'],
    outputs: [['result.statistic', 'W 통계량 (1에 가까울수록 정규)'], ['result.pvalue', 'p-value']],
    pitfalls: ['p >= 0.05 → 정규성 만족(기각 못함)', 'p < 0.05 → 정규성 위배 → 비모수 검정 고려'],
  },
  {
    id: 'T12', name: '등분산성 검정', func: 'levene', level: 1, day: 8, core: false,
    imp: 'from scipy.stats import levene',
    keys: 'levene 등분산 분산 동일 equal_var homogeneity',
    when: '집단들의 분산이 같은지 확인할 때. 독립 t검정의 equal_var 선택 근거.',
    h0: 'H0: 집단 분산이 모두 같다', h1: 'H1: 분산이 다른 집단이 있다',
    code: `from scipy.stats import levene
a = df[df['group']=='A']['score'].dropna()
b = df[df['group']=='B']['score'].dropna()
result = levene(a,b)
print(result.statistic)
print(result.pvalue)`,
    blanks: ['levene', 'levene', 'statistic', 'pvalue'],
    outputs: [['result.statistic', 'Levene 통계량'], ['result.pvalue', 'p-value']],
    pitfalls: ['p >= 0.05 → 등분산 → equal_var=True', 'p < 0.05 → 이분산 → equal_var=False (Welch)', 'scipy 기본 center=\'median\''],
  },
  {
    id: 'T13', name: '단일표본 비율 z검정', func: 'proportions_ztest', level: 2, day: 8, core: false,
    imp: 'from statsmodels.stats.proportion import proportions_ztest',
    keys: 'proportions_ztest 비율 z검정 proportion 찬성률 불량률 클릭률 count nobs',
    when: '어떤 사건의 비율(찬성률, 불량률)이 기준 비율과 다른지 볼 때.',
    h0: 'H0: 모비율 = p0', h1: 'H1: 모비율 != p0',
    code: `from statsmodels.stats.proportion import proportions_ztest
count = 60
nobs = 100
z,p = proportions_ztest(count,nobs,value=0.5)
print(z)
print(p)`,
    blanks: ['proportions_ztest', 'proportions_ztest', 'nobs', 'value'],
    outputs: [['z', 'z 통계량'], ['p', 'p-value']],
    pitfalls: ['(z, p) 튜플 반환 — .statistic 속성 없음', '기본 prop_var=False: 표준오차에 표본비율 사용', '0/1 열이면 count = df[col].sum(), nobs = len(df)'],
  },
  {
    id: 'T14', name: 'Mann-Whitney U 검정', func: 'mannwhitneyu', level: 2, day: 8, core: false,
    imp: 'from scipy.stats import mannwhitneyu',
    keys: 'mannwhitneyu 맨휘트니 비모수 U 순위합 정규성 위배 서열 두 집단',
    when: '정규성을 가정할 수 없는 두 독립 집단(서열척도 포함)을 비교할 때. 독립 t검정의 비모수 버전.',
    h0: 'H0: 두 집단 분포가 같다', h1: 'H1: 두 집단 분포가 다르다',
    code: `from scipy.stats import mannwhitneyu
a = df[df['group']=='A']['score'].dropna()
b = df[df['group']=='B']['score'].dropna()
result = mannwhitneyu(a,b,alternative='two-sided')
print(result.statistic)
print(result.pvalue)`,
    blanks: ['mannwhitneyu', 'mannwhitneyu', 'alternative', 'two-sided', 'statistic', 'pvalue'],
    outputs: [['result.statistic', 'U 통계량 (첫 번째 표본 기준)'], ['result.pvalue', 'p-value']],
    pitfalls: ['alternative=\'two-sided\'를 명시', 'U는 첫 번째 인자 기준. 순서 바꾸면 n1*n2 - U', '대응표본의 비모수 버전은 wilcoxon'],
  },
];

// 공통 암기 카드 (front: 코드, back: 의미)
window.CARDS = [
  ['result.statistic', '검정통계량 (t, F, chi2, W, U, r, rho)'],
  ['result.pvalue', 'p-value'],
  ["model.params['x']", '회귀계수'],
  ["model.pvalues['x']", '회귀계수의 p-value'],
  ['model.rsquared', '결정계수 R²'],
  ['model.rsquared_adj', '수정 결정계수'],
  ['model.fvalue', 'F 통계량 (회귀모형 전체)'],
  ['model.f_pvalue', 'F검정 p-value'],
  ['model.conf_int()', '95% 신뢰구간 (0열 하한, 1열 상한)'],
  ["np.exp(model.params['x'])", '오즈비 (로지스틱)'],
  ['model.predict(...)', 'OLS: 예측값 / logit: 예측확률'],
  ['p < 0.05', '5% 유의수준에서 귀무가설 기각'],
  ['chi2, p, dof, expected', 'chi2_contingency 반환 순서'],
  ['z, p = proportions_ztest(...)', '비율검정은 튜플 반환'],
  ["model.params['Intercept']", '절편'],
  ["(model.pvalues.drop('Intercept') < 0.05).sum()", '유의한 변수 개수'],
];

// B. 통계 분석 방법 선택 퀴즈
window.METHOD_QUIZ = [
  ['신제품 과자의 평균 무게가 표시 중량 500g과 다른지 확인하려 한다.', 'T01'],
  ['남성과 여성 직원의 평균 연봉에 차이가 있는지 확인하려 한다.', 'T02'],
  ['같은 환자 20명의 투약 전과 투약 후 혈압을 비교하려 한다.', 'T03'],
  ['세 가지 교수법으로 가르친 반의 평균 점수를 비교하려 한다.', 'T04'],
  ['흡연 여부(예/아니오)와 폐질환 여부(예/아니오)가 관련 있는지 보려 한다.', 'T05'],
  ['주사위를 600번 던진 결과로 주사위가 공정한지 확인하려 한다.', 'T06'],
  ['키와 몸무게의 선형 관계 강도를 수치로 구하려 한다.', 'T07'],
  ['두 심사위원이 매긴 순위가 얼마나 일치하는지 보려 한다.', 'T08'],
  ['TV·라디오 광고비로 매출을 예측하고 각 광고비의 계수를 구하려 한다.', 'T09'],
  ['나이와 소득으로 구매 여부(1/0)의 확률과 오즈비를 구하려 한다.', 'T10'],
  ['회귀모형 잔차가 정규분포를 따르는지 확인하려 한다.', 'T11'],
  ['t검정 전에 두 집단의 분산이 같은지 확인하려 한다.', 'T12'],
  ['1000명 중 640명이 투표했다. 투표율이 60%와 다른지 확인하려 한다.', 'T13'],
  ['정규성을 만족하지 않는 두 독립 집단의 대기시간을 비교하려 한다.', 'T14'],
  ['다이어트 프로그램 참여자 15명의 참여 전후 체중을 비교하려 한다.', 'T03'],
  ['4개 지역 매장의 평균 매출이 모두 같은지 검정하려 한다.', 'T04'],
  ['교육수준(3범주)과 선호 정당(4범주)이 독립인지 검정하려 한다.', 'T05'],
  ['요일별 방문객 수가 균등하게 분포하는지 확인하려 한다.', 'T06'],
  ['만족도 순위와 재방문 의향 순위 사이의 관계를 보려 한다(서열자료).', 'T08'],
  ['공부시간 1시간 증가 시 합격 오즈가 몇 배 되는지 구하려 한다.', 'T10'],
  ['면적으로 아파트 가격을 설명하는 모형의 결정계수를 구하려 한다.', 'T09'],
  ['불량품 비율이 기준 3%와 다른지 400개 표본으로 검정하려 한다.', 'T13'],
  ['1~5점 만족도(서열척도)를 두 매장 간 비교하려 한다.', 'T14'],
  ['ANOVA 전에 세 집단의 분산이 같은지 확인하려 한다.', 'T12'],
  ['수강생 평균 점수가 기준 70점과 같은지 검정하려 한다.', 'T01'],
  ['무작위로 나눈 실험군과 대조군의 평균 회복일수를 비교하려 한다.', 'T02'],
  ['공부시간과 점수의 피어슨 상관계수 r과 p-value를 구하려 한다.', 'T07'],
  ['표본 30개가 정규분포를 따르는지 Shapiro-Wilk로 확인하려 한다.', 'T11'],
];
// 혼동하기 쉬운 유형 묶음 (오답 보기 구성용)
window.CONFUSE = {
  T01: ['T02', 'T03', 'T13'], T02: ['T03', 'T14', 'T04'], T03: ['T02', 'T01', 'T14'], T04: ['T02', 'T12', 'T05'],
  T05: ['T06', 'T04', 'T07'], T06: ['T05', 'T13', 'T01'], T07: ['T08', 'T09', 'T05'], T08: ['T07', 'T14', 'T05'],
  T09: ['T10', 'T07', 'T04'], T10: ['T09', 'T05', 'T13'], T11: ['T12', 'T14', 'T01'], T12: ['T11', 'T04', 'T02'],
  T13: ['T06', 'T01', 'T05'], T14: ['T02', 'T08', 'T03'],
};

// D. 출력값 해석 퀴즈 [tpl, 출력, 질문, 보기[], 정답 index, 해설]
window.INTERP_QUIZ = [
  ['T01', 'TtestResult(statistic=-2.31, pvalue=0.031, df=24)', '유의수준 5%에서 결론은?', ['귀무가설 기각: 평균이 기준값과 다르다', '귀무가설 채택: 평균이 기준값과 같다고 본다', 't가 음수이므로 판단 불가', '자유도가 24라서 기각 불가'], 0, 'p = 0.031 < 0.05 → 기각. t의 부호는 표본평균이 기준값보다 작다는 방향 정보일 뿐이다.'],
  ['T01', 'TtestResult(statistic=1.12, pvalue=0.274, df=19)', '이 결과에서 p-value를 꺼내는 코드는?', ['result.pvalue', 'result.statistic', 'result.df', 'result[0]'], 0, 'p-value는 result.pvalue (또는 result[1]).'],
  ['T02', 'ttest_ind(a, b, equal_var=False) → statistic=2.05, pvalue=0.048', '이 검정의 이름과 결론으로 옳은 것은?', ['Welch t검정, 5%에서 기각', '합동분산 t검정, 5%에서 기각', 'Welch t검정, 5%에서 채택', '대응표본 t검정, 기각'], 0, 'equal_var=False는 Welch t검정. p = 0.048 < 0.05 → 기각.'],
  ['T02', 'levene p-value = 0.003', '이어서 독립표본 t검정을 할 때 옵션은?', ['equal_var=False', 'equal_var=True', "alternative='less'", 'correction=False'], 0, 'Levene p < 0.05 → 등분산 기각 → Welch(equal_var=False).'],
  ['T03', 'ttest_rel(before, after) → statistic=-4.00, pvalue=0.0013', 't가 음수인 이유로 가장 알맞은 것은?', ['after 평균이 before 평균보다 크다', 'before 평균이 after 평균보다 크다', '검정이 잘못되었다', 'p-value가 작기 때문'], 0, 'ttest_rel(x, y)는 x - y 기준. before - after가 음수 → after가 더 크다.'],
  ['T04', 'F_onewayResult(statistic=15.15, pvalue=3.9e-05)', '올바른 해석은?', ['적어도 한 집단의 평균이 다르다', '모든 집단의 평균이 다르다', 'A 집단의 평균이 가장 크다', '세 집단의 분산이 다르다'], 0, 'ANOVA 기각은 "적어도 하나가 다르다"까지만 말한다. 어느 집단인지는 사후검정.'],
  ['T04', '집단 4개, 전체 관측치 36개', '집단내(잔차) 자유도는?', ['32', '3', '35', '36'], 0, '집단내 자유도 = N - k = 36 - 4 = 32. 집단간은 k - 1 = 3.'],
  ['T05', 'chi2=14.27, p=0.0065, dof=4', '이 표의 크기로 가능한 것은?', ['3 x 3', '2 x 4', '2 x 2', '4 x 4'], 0, 'dof = (행-1)(열-1) = 4 → 3x3 (2x4는 3, 4x4는 9).'],
  ['T05', 'chi2, p, dof, expected = chi2_contingency(table)', '기대도수 표에서 첫 행 첫 열 값을 꺼내는 코드는?', ['expected[0][0]', 'table[0][0]', 'dof[0]', 'p[0][0]'], 0, '기대도수는 네 번째 반환값 expected (numpy 배열).'],
  ['T05', '2x2 분할표, chi2_contingency(table) 기본 옵션', '기본으로 적용되는 것은?', ['Yates 연속성 보정', 'Welch 보정', 'Bonferroni 보정', '보정 없음'], 0, '2x2(dof=1)일 때 correction=True가 기본이라 Yates 보정이 적용된다.'],
  ['T06', 'Power_divergenceResult(statistic=6.5, pvalue=0.0388)', '범주 3개 적합도 검정의 자유도와 결론은?', ['자유도 2, 기각', '자유도 3, 기각', '자유도 2, 채택', '자유도 1, 채택'], 0, '자유도 = 범주 수 - 1 = 2. p < 0.05 → 기대 분포와 다르다.'],
  ['T07', 'PearsonRResult(statistic=0.869, pvalue=6.6e-07)', '옳은 해석은?', ['강한 양의 선형 상관이 유의하다', '약한 음의 상관이다', '인과관계가 증명되었다', 'p-value가 커서 유의하지 않다'], 0, 'r = 0.869 → 강한 양의 상관. 상관은 인과를 증명하지 않는다.'],
  ['T08', 'spearman rho = 0.47, pearson r = -0.11 (이상치 1개 포함)', '두 값이 크게 다른 주된 이유는?', ['피어슨은 이상치에 민감하다', '스피어만 계산이 틀렸다', '표본이 정규분포라서', '자유도가 달라서'], 0, '스피어만은 순위를 쓰므로 극단값의 영향이 작다.'],
  ['T09', "model.pvalues → Intercept 0.21, tv 0.000, radio 0.000, newspaper 0.71", '유의수준 5%에서 유의한 독립변수 개수는?', ['2', '3', '1', '4'], 0, '절편은 독립변수가 아니므로 제외. tv, radio → 2개.'],
  ['T09', 'R-squared: 0.781, Adj. R-squared: 0.765', '"수정 결정계수"를 꺼내는 코드는?', ['model.rsquared_adj', 'model.rsquared', 'model.fvalue', 'model.adj_r2'], 0, '수정 R²은 rsquared_adj.'],
  ['T09', "conf_int(): tv [0.039, 0.051]", '해석으로 옳은 것은?', ['구간에 0이 없으므로 tv 계수는 5%에서 유의하다', '구간에 0이 없으므로 유의하지 않다', 'tv의 p-value는 0.05보다 크다', '예측값의 범위다'], 0, '95% 신뢰구간이 0을 포함하지 않으면 5% 유의수준에서 계수 = 0 을 기각한다.'],
  ['T10', "params['hours'] = 0.957", '오즈비는?', ['exp(0.957) ≈ 2.604', '0.957', '1 / 0.957', '0.957 ^ 2'], 0, '오즈비 = np.exp(계수). 1시간 증가 시 오즈가 약 2.6배.'],
  ['T10', "np.exp(params['age']) = 0.95", '올바른 해석은?', ['나이 1세 증가 시 오즈가 약 5% 감소', '나이 1세 증가 시 확률이 0.95 증가', '나이는 영향이 없다', '오즈가 95% 증가'], 0, '오즈비 < 1 → 오즈 감소. (0.95 - 1) = -5%.'],
  ['T10', "model.predict({'hours':[5]}) → 0.705", '이 값의 의미는?', ['hours=5일 때 합격(1) 확률', '로그오즈', '오즈비', '잔차'], 0, 'logit 모형의 predict는 1일 확률을 반환한다.'],
  ['T11', 'ShapiroResult(statistic=0.982, pvalue=0.887)', '결론은?', ['정규성을 만족한다고 본다', '정규성 위배', 'W가 1보다 작아 위배', '판단 불가'], 0, 'p >= 0.05 → 정규성 귀무가설을 기각하지 못함 → 정규성 가정 가능.'],
  ['T12', 'LeveneResult(statistic=0.52, pvalue=0.599)', '결론은?', ['등분산 가정 가능', '분산이 다르다', '평균이 같다', '정규성 만족'], 0, 'Levene p >= 0.05 → 등분산 기각 못함.'],
  ['T13', 'z, p = proportions_ztest(60, 100, value=0.5) → (2.041, 0.0412)', 'z 통계량을 꺼내는 방법은?', ['튜플의 첫 번째 값 z', 'result.statistic', 'result.zvalue', 'p[0]'], 0, 'proportions_ztest는 (z, p) 튜플. 언패킹해서 쓴다.'],
  ['T14', 'MannwhitneyuResult(statistic=118.5, pvalue=0.029)', '이 U 값은 어느 표본 기준인가?', ['첫 번째 인자(a)', '두 번째 인자(b)', '두 표본 중 작은 값', '두 표본의 합'], 0, 'scipy mannwhitneyu의 statistic은 첫 번째 표본의 U.'],
  ['ALL', 'p-value = 0.07, 유의수준 0.05', '결론은?', ['귀무가설을 기각하지 못한다', '귀무가설을 기각한다', '대립가설이 참으로 증명된다', '귀무가설이 참으로 증명된다'], 0, 'p >= 0.05 → 기각하지 못한다. "귀무가설이 참임을 증명"하는 것은 아니다.'],
  ['ALL', 'p-value = 3.2e-05', '이 값을 소수점 넷째 자리까지 쓰면?', ['0.0000', '3.2000', '0.0003', '0.0032'], 0, '3.2e-05 = 0.000032 → 넷째 자리 반올림 0.0000.'],
];

// 10일 학습 계획
window.PLAN = [
  { day: 1, title: '단일·독립표본 t검정', tpls: ['T01', 'T02'], tip: 'statistic / pvalue / equal_var 옵션' },
  { day: 2, title: '대응표본 t검정, p-value 해석', tpls: ['T03'], tip: '인자 순서와 부호, p < 0.05 판단 (해석 퀴즈 병행)' },
  { day: 3, title: 'ANOVA', tpls: ['T04'], tip: '집단 분리 후 f_oneway, 자유도 k-1 / N-k' },
  { day: 4, title: '카이제곱 검정', tpls: ['T05', 'T06'], tip: 'crosstab → chi2_contingency, 기대도수, Yates 보정' },
  { day: 5, title: '피어슨·스피어만 상관분석', tpls: ['T07', 'T08'], tip: '선형 vs 순위, 이상치' },
  { day: 6, title: 'OLS 선형회귀', tpls: ['T09'], tip: 'params, pvalues, rsquared(_adj), fvalue, conf_int, predict' },
  { day: 7, title: '로지스틱 회귀, 오즈비', tpls: ['T10'], tip: 'np.exp(params) = 오즈비, predict = 확률' },
  { day: 8, title: '정규성·등분산·비율·비모수 검정', tpls: ['T11', 'T12', 'T13', 'T14'], tip: 'shapiro, levene, proportions_ztest, mannwhitneyu' },
  { day: 9, title: '30점 모의고사', tpls: [], tip: '모의고사 2회 이상, 10점 이상 목표' },
  { day: 10, title: '오답 및 템플릿 총복습', tpls: [], tip: '오답노트 비우기 + 14개 빈칸 암기 완주' },
];
// 10점 확보 프로젝트 우선순위 경로
window.PRIORITY = ['T01', 'T02', 'T03', 'T05', 'T06', 'T09', 'T10'];
