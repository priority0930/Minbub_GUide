"""빅분기 TYPE 3 — 10일 완성: 문제은행 생성기

모든 연습문제의 데이터와 정답을 실제 scipy / statsmodels로 계산해서
data.js 와 csv/ 폴더로 저장한다. 앱에 표시되는 정답은 전부 이 스크립트의 계산 결과다.

    pip install numpy pandas scipy statsmodels
    python generate_problems.py
"""
import json
import os
import warnings

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from scipy import stats
from statsmodels.stats.proportion import proportions_ztest

warnings.filterwarnings("ignore")
HERE = os.path.dirname(os.path.abspath(__file__))
CSV_DIR = os.path.join(HERE, "csv")

PROBLEMS = []

# 코드 정답 패턴: "=a|b" 는 정규화 후 완전일치 후보, 그 외는 "&&" 로 묶인 포함 토큰
STAT = "=X.statistic|X[0]"
PVAL = "=X.pvalue|X[1]"


def r(x, d=6):
    return float(round(float(x), d))


def sub(q, ans, pattern, code, accept, exp, dec=3, kind="num", opts=None, traps=None, unit=""):
    s = {
        "q": q,
        "kind": kind,
        "pattern": pattern,
        "code": code,
        "accept": accept,
        "exp": exp,
    }
    if kind == "num":
        s["ans"] = r(ans, 8)
        s["dec"] = dec
        s["traps"] = [{"v": r(v, 8), "why": w} for v, w in (traps or []) if v is not None and np.isfinite(v)]
        s["unit"] = unit
    else:
        s["ans"] = ans
        s["opts"] = opts
    return s


def reject_sub(p, code="result.pvalue < 0.05", accept="X.pvalue&&<0.05", what="귀무가설"):
    rej = p < 0.05
    return sub(
        f"유의수준 5%에서 {what}을 기각하는가?",
        "기각" if rej else "채택",
        "귀무가설 기각 여부",
        code,
        accept,
        f"p-value = {p:.4f} {'< 0.05 이므로 귀무가설을 기각한다.' if rej else '>= 0.05 이므로 귀무가설을 기각하지 못한다(채택).'}",
        kind="choice",
        opts=["기각", "채택"],
    )


def add(pid, tpl, level, title, story, df, func, solution, subs, note=""):
    df = df.reset_index(drop=True)
    os.makedirs(CSV_DIR, exist_ok=True)
    fname = f"{pid.lower().replace('-', '_')}.csv"
    df.to_csv(os.path.join(CSV_DIR, fname), index=False)
    rows = []
    for rec in df.itertuples(index=False):
        row = []
        for v in rec:
            if isinstance(v, (float, np.floating)) and np.isnan(v):
                row.append(None)
            elif isinstance(v, (np.integer,)):
                row.append(int(v))
            elif isinstance(v, (np.floating,)):
                row.append(float(v))
            else:
                row.append(v)
        rows.append(row)
    for i, s in enumerate(subs):
        s["id"] = f"{pid}-{i + 1}"
    PROBLEMS.append(
        {
            "id": pid,
            "tpl": tpl,
            "level": level,
            "title": title,
            "story": story,
            "file": fname,
            "columns": list(df.columns),
            "rows": rows,
            "func": func,
            "solution": solution.strip("\n"),
            "subs": subs,
            "note": note,
        }
    )


def rng(seed):
    return np.random.default_rng(seed)


def with_nan(series, idx):
    s = series.astype(float).copy()
    s.iloc[idx] = np.nan
    return s


# ------------------------------------------------------------------ T01 단일표본 t검정
g = rng(101)
df = pd.DataFrame({"id": range(1, 21), "score": np.round(g.normal(74, 8, 20)).astype(int)})
a = df["score"].dropna()
res = stats.ttest_1samp(a, 70)
add("T01-1", "T01", 1, "학생 평균 점수 70점 검정",
    "한 학원의 학생 20명 점수(score)이다. 학생들의 모평균 점수가 70점과 다른지 양측 단일표본 t검정을 수행하시오.",
    df, "ttest_1samp",
    """from scipy.stats import ttest_1samp
a = df['score'].dropna()
result = ttest_1samp(a, 70)
print(result.statistic)   # t 통계량
print(result.pvalue)      # p-value
print(result.pvalue < 0.05)""",
    [
        sub("검정통계량 t를 구하시오. (소수점 셋째 자리까지)", res.statistic, "검정통계량", "result.statistic", STAT,
            f"t = (표본평균 - 70) / (s / sqrt(n)) = {res.statistic:.3f}. 표본평균 {a.mean():.2f}가 70보다 크므로 양수.",
            traps=[(stats.ttest_1samp(a, 75).statistic, "검정 기준값(popmean)을 문제의 70이 아닌 값으로 넣었습니다.")]),
        sub("p-value를 구하시오. (소수점 넷째 자리까지)", res.pvalue, "p-value", "result.pvalue", PVAL,
            f"양측검정 p-value = {res.pvalue:.4f}.", dec=4,
            traps=[(res.pvalue / 2, "단측 p-value(양측의 절반)를 입력했습니다. ttest_1samp 기본값은 양측검정입니다.")]),
        reject_sub(res.pvalue),
    ])

g = rng(102)
life = pd.Series(np.round(g.normal(492, 14, 15), 1))
life = with_nan(life, [3, 11])
df = pd.DataFrame({"battery_id": [f"B{i:02d}" for i in range(1, 16)], "hours": life})
a = df["hours"].dropna()
res = stats.ttest_1samp(a, 500)
add("T01-2", "T01", 1, "배터리 수명 500시간 검정",
    "배터리 15개의 수명(hours) 데이터이며 결측치가 있다. 결측치를 제거한 뒤 평균 수명이 500시간과 다른지 단일표본 t검정을 수행하시오.",
    df, "ttest_1samp",
    """from scipy.stats import ttest_1samp
a = df['hours'].dropna()
print(a.mean())
result = ttest_1samp(a, 500)
print(result.statistic)
print(result.pvalue)""",
    [
        sub("결측치를 제거한 표본평균을 구하시오. (소수점 셋째 자리까지)", a.mean(), "평균", "a.mean()", "mean()",
            f"dropna() 후 n = {len(a)}개, 평균 = {a.mean():.3f}. 결측치를 0으로 채우면 평균이 크게 왜곡된다.",
            traps=[(df['hours'].fillna(0).mean(), "결측치를 0으로 채워 평균을 계산했습니다. dropna()로 제거해야 합니다.")]),
        sub("검정통계량 t를 구하시오. (소수점 셋째 자리까지)", res.statistic, "검정통계량", "result.statistic", STAT,
            f"t = {res.statistic:.3f}. 표본평균이 500보다 작아 음수가 나온다."),
        sub("p-value를 구하시오. (소수점 넷째 자리까지)", res.pvalue, "p-value", "result.pvalue", PVAL,
            f"p-value = {res.pvalue:.4f}.", dec=4),
    ])

g = rng(103)
df = pd.DataFrame({"cup": range(1, 26), "volume_ml": np.round(g.normal(247.2, 4.5, 25), 1)})
a = df["volume_ml"].dropna()
res = stats.ttest_1samp(a, 250)
add("T01-3", "T01", 2, "커피 용량 250ml 검정",
    "카페에서 판매한 커피 25잔의 용량(volume_ml)이다. 표시 용량 250ml와 평균 용량이 다른지 검정하시오.",
    df, "ttest_1samp",
    """from scipy.stats import ttest_1samp
a = df['volume_ml'].dropna()
result = ttest_1samp(a, 250)
print(result.statistic)
print(result.pvalue)
print(len(a) - 1)          # 자유도
print(result.pvalue < 0.05)""",
    [
        sub("검정통계량 t를 구하시오. (소수점 셋째 자리까지)", res.statistic, "검정통계량", "result.statistic", STAT,
            f"t = {res.statistic:.3f}."),
        sub("자유도를 구하시오. (정수)", len(a) - 1, "자유도", "len(a) - 1", "len(&&-1",
            f"단일표본 t검정의 자유도 = n - 1 = {len(a)} - 1 = {len(a) - 1}.", dec=0,
            traps=[(len(a), "표본 수 n을 그대로 입력했습니다. 자유도는 n - 1 입니다.")]),
        sub("p-value를 구하시오. (소수점 넷째 자리까지)", res.pvalue, "p-value", "result.pvalue", PVAL,
            f"p-value = {res.pvalue:.4f}.", dec=4),
        reject_sub(res.pvalue),
    ])

# ------------------------------------------------------------------ T02 독립표본 t검정
g = rng(201)
A = np.round(g.normal(78, 6, 14)).astype(int)
B = np.round(g.normal(72, 11, 16)).astype(int)
df = pd.DataFrame({"group": ["A"] * 14 + ["B"] * 16, "score": np.concatenate([A, B])})
a = df[df["group"] == "A"]["score"].dropna()
b = df[df["group"] == "B"]["score"].dropna()
res = stats.ttest_ind(a, b, equal_var=False)
res_eq = stats.ttest_ind(a, b, equal_var=True)
add("T02-1", "T02", 1, "A반 vs B반 평균 (Welch)",
    "A반 14명과 B반 16명의 점수이다. 등분산을 가정하지 않고(Welch) 두 반의 평균 점수에 차이가 있는지 검정하시오.",
    df, "ttest_ind",
    """from scipy.stats import ttest_ind
a = df[df['group']=='A']['score'].dropna()
b = df[df['group']=='B']['score'].dropna()
result = ttest_ind(a, b, equal_var=False)
print(result.statistic)
print(result.pvalue)
print(a.mean() - b.mean())""",
    [
        sub("검정통계량 t를 구하시오. (소수점 셋째 자리까지)", res.statistic, "검정통계량", "result.statistic", STAT,
            f"Welch t = {res.statistic:.3f}. equal_var=False 를 반드시 지정해야 한다.",
            traps=[(res_eq.statistic, "equal_var=True(합동분산 t검정) 결과입니다. 문제는 등분산을 가정하지 않습니다(equal_var=False)."),
                   (-res.statistic, "a, b 순서를 바꿨습니다. 문제의 순서(A - B)대로 넣으세요.")]),
        sub("p-value를 구하시오. (소수점 넷째 자리까지)", res.pvalue, "p-value", "result.pvalue", PVAL,
            f"Welch p-value = {res.pvalue:.4f}.", dec=4,
            traps=[(res_eq.pvalue, "equal_var=True 결과의 p-value입니다. Welch 검정은 equal_var=False.")]),
        sub("평균 차이(A반 평균 - B반 평균)를 구하시오. (소수점 셋째 자리까지)", a.mean() - b.mean(), "평균 차이",
            "a.mean() - b.mean()", ".mean()-&&.mean()",
            f"{a.mean():.3f} - {b.mean():.3f} = {a.mean() - b.mean():.3f}.",
            traps=[(b.mean() - a.mean(), "B - A로 계산했습니다. 문제는 A - B.")]),
    ])

g = rng(202)
drug = np.round(g.normal(128, 9, 18), 1)
plac = np.round(g.normal(134, 9, 18), 1)
df = pd.DataFrame({"treat": ["drug"] * 18 + ["placebo"] * 18, "bp": np.concatenate([drug, plac])})
a = df[df["treat"] == "drug"]["bp"].dropna()
b = df[df["treat"] == "placebo"]["bp"].dropna()
res = stats.ttest_ind(a, b, equal_var=True)
res_w = stats.ttest_ind(a, b, equal_var=False)
add("T02-2", "T02", 2, "신약 vs 위약 혈압 (등분산 가정)",
    "신약군(drug)과 위약군(placebo) 각 18명의 수축기 혈압(bp)이다. 두 집단의 분산이 같다고 가정하고 평균 혈압 차이를 검정하시오. (drug를 첫 번째 집단으로)",
    df, "ttest_ind",
    """from scipy.stats import ttest_ind
a = df[df['treat']=='drug']['bp'].dropna()
b = df[df['treat']=='placebo']['bp'].dropna()
result = ttest_ind(a, b, equal_var=True)
print(result.statistic)
print(result.pvalue)
print(len(a) + len(b) - 2)   # 자유도""",
    [
        sub("검정통계량 t를 구하시오. (소수점 셋째 자리까지)", res.statistic, "검정통계량", "result.statistic", STAT,
            f"합동분산 t = {res.statistic:.3f}. 등분산 가정이므로 equal_var=True.",
            traps=[(res_w.statistic, "Welch(equal_var=False) 결과입니다. 문제에서 등분산을 가정하라고 했습니다.")]),
        sub("p-value를 구하시오. (소수점 넷째 자리까지)", res.pvalue, "p-value", "result.pvalue", PVAL,
            f"p-value = {res.pvalue:.4f}.", dec=4),
        sub("이 검정의 자유도를 구하시오. (정수)", len(a) + len(b) - 2, "자유도", "len(a) + len(b) - 2", "len(&&-2",
            f"등분산 독립표본 t검정의 자유도 = n1 + n2 - 2 = {len(a)} + {len(b)} - 2 = {len(a) + len(b) - 2}.", dec=0,
            traps=[(len(a) + len(b) - 1, "n1 + n2 - 1이 아니라 n1 + n2 - 2 입니다.")]),
    ])

g = rng(203)
m = np.round(g.normal(8200, 1800, 17))
f = np.round(g.normal(7300, 1300, 17))
df = pd.DataFrame({"gender": ["M"] * 17 + ["F"] * 17, "steps": np.concatenate([m, f])})
df["steps"] = with_nan(df["steps"], [5, 22])
a = df[df["gender"] == "M"]["steps"].dropna()
b = df[df["gender"] == "F"]["steps"].dropna()
res = stats.ttest_ind(a, b, equal_var=False)
res_eq = stats.ttest_ind(a, b, equal_var=True)
add("T02-3", "T02", 2, "성별 하루 걸음 수 (결측 포함)",
    "남성(M)과 여성(F)의 하루 걸음 수(steps)이며 결측치가 있다. 결측치 제거 후 Welch t검정으로 두 집단 평균 차이를 검정하시오. (M을 첫 번째 집단으로)",
    df, "ttest_ind",
    """from scipy.stats import ttest_ind
a = df[df['gender']=='M']['steps'].dropna()
b = df[df['gender']=='F']['steps'].dropna()
result = ttest_ind(a, b, equal_var=False)
print(result.statistic)
print(result.pvalue)
print(result.pvalue < 0.05)""",
    [
        sub("검정통계량 t를 구하시오. (소수점 셋째 자리까지)", res.statistic, "검정통계량", "result.statistic", STAT,
            f"Welch t = {res.statistic:.3f}.",
            traps=[(res_eq.statistic, "equal_var=True 결과입니다. Welch는 equal_var=False.")]),
        sub("p-value를 구하시오. (소수점 넷째 자리까지)", res.pvalue, "p-value", "result.pvalue", PVAL,
            f"p-value = {res.pvalue:.4f}.", dec=4),
        reject_sub(res.pvalue),
    ])

# ------------------------------------------------------------------ T03 대응표본 t검정
g = rng(301)
before = np.round(g.normal(65, 8, 15)).astype(int)
after = np.round(before + g.normal(4, 5, 15)).astype(int)
df = pd.DataFrame({"id": range(1, 16), "before": before, "after": after})
d = df[["before", "after"]].dropna()
res = stats.ttest_rel(d["before"], d["after"])
res_ind = stats.ttest_ind(d["before"], d["after"])
add("T03-1", "T03", 1, "교육 전후 점수",
    "직원 15명의 교육 전(before)과 교육 후(after) 점수이다. 교육 전후 평균 점수에 차이가 있는지 대응표본 t검정을 수행하시오. (before, after 순서로 입력)",
    df, "ttest_rel",
    """from scipy.stats import ttest_rel
d = df[['before','after']].dropna()
result = ttest_rel(d['before'], d['after'])
print(result.statistic)
print(result.pvalue)
print(d['after'].mean() - d['before'].mean())""",
    [
        sub("검정통계량 t를 구하시오. (소수점 셋째 자리까지)", res.statistic, "검정통계량", "result.statistic", STAT,
            f"t = {res.statistic:.3f}. before - after 차이의 평균이 음수라서 t가 음수다.",
            traps=[(-res.statistic, "after, before 순서로 넣었습니다. 문제의 순서(before, after)를 지키세요."),
                   (res_ind.statistic, "독립표본 t검정(ttest_ind) 결과입니다. 같은 사람의 전후 비교는 ttest_rel.")]),
        sub("p-value를 구하시오. (소수점 넷째 자리까지)", res.pvalue, "p-value", "result.pvalue", PVAL,
            f"p-value = {res.pvalue:.4f}.", dec=4,
            traps=[(res_ind.pvalue, "독립표본 t검정의 p-value입니다.")]),
        sub("교육 후 평균 - 교육 전 평균을 구하시오. (소수점 셋째 자리까지)", d["after"].mean() - d["before"].mean(),
            "평균 차이", "d['after'].mean() - d['before'].mean()", ".mean()-&&.mean()",
            f"{d['after'].mean():.3f} - {d['before'].mean():.3f} = {d['after'].mean() - d['before'].mean():.3f}점 향상.",
            traps=[(d["before"].mean() - d["after"].mean(), "전 - 후로 계산했습니다. 문제는 후 - 전.")]),
    ])

g = rng(302)
wb = np.round(g.normal(78, 9, 12), 1)
wa = np.round(wb - g.normal(1.2, 2.2, 12), 1)
df = pd.DataFrame({"member": [f"M{i:02d}" for i in range(1, 13)], "weight_before": wb, "weight_after": wa})
d = df[["weight_before", "weight_after"]].dropna()
res = stats.ttest_rel(d["weight_before"], d["weight_after"])
add("T03-2", "T03", 1, "다이어트 프로그램 체중 변화",
    "회원 12명의 프로그램 참여 전(weight_before)과 후(weight_after) 체중이다. 참여 전후 체중에 차이가 있는지 대응표본 t검정을 수행하시오. (weight_before, weight_after 순서)",
    df, "ttest_rel",
    """from scipy.stats import ttest_rel
d = df[['weight_before','weight_after']].dropna()
result = ttest_rel(d['weight_before'], d['weight_after'])
print(result.statistic)
print(result.pvalue)
print(result.pvalue < 0.05)""",
    [
        sub("검정통계량 t를 구하시오. (소수점 셋째 자리까지)", res.statistic, "검정통계량", "result.statistic", STAT,
            f"t = {res.statistic:.3f}.", traps=[(-res.statistic, "인자 순서가 반대입니다.")]),
        sub("p-value를 구하시오. (소수점 넷째 자리까지)", res.pvalue, "p-value", "result.pvalue", PVAL,
            f"p-value = {res.pvalue:.4f}.", dec=4),
        reject_sub(res.pvalue),
    ])

g = rng(303)
pre = np.round(g.normal(148, 10, 16)).astype(float)
post = np.round(pre - g.normal(6, 7, 16)).astype(float)
df = pd.DataFrame({"patient": range(1, 17), "bp_pre": pre, "bp_post": post})
df["bp_post"] = with_nan(df["bp_post"], [4])
df["bp_pre"] = with_nan(df["bp_pre"], [9])
d = df[["bp_pre", "bp_post"]].dropna()
res = stats.ttest_rel(d["bp_pre"], d["bp_post"])
add("T03-3", "T03", 2, "혈압약 투여 전후 (결측 포함)",
    "환자 16명의 투여 전(bp_pre), 투여 후(bp_post) 혈압이다. 두 열 중 하나라도 결측인 행은 제거하고 대응표본 t검정을 수행하시오. (bp_pre, bp_post 순서)",
    df, "ttest_rel",
    """from scipy.stats import ttest_rel
d = df[['bp_pre','bp_post']].dropna()      # 행 단위로 함께 제거
diff = d['bp_post'] - d['bp_pre']
print(diff.mean())
result = ttest_rel(d['bp_pre'], d['bp_post'])
print(result.statistic)
print(result.pvalue)""",
    [
        sub("(투여 후 - 투여 전) 차이의 평균을 구하시오. (소수점 셋째 자리까지)", (d["bp_post"] - d["bp_pre"]).mean(),
            "평균 차이", "(d['bp_post'] - d['bp_pre']).mean()", ".mean()",
            f"결측 행 2개를 제거한 n = {len(d)} 쌍의 차이 평균 = {(d['bp_post'] - d['bp_pre']).mean():.3f}.",
            traps=[(df["bp_post"].mean() - df["bp_pre"].mean(), "열별로 따로 dropna 해서 평균을 냈습니다. 대응표본은 두 열을 함께 dropna 해야 합니다.")]),
        sub("검정통계량 t를 구하시오. (소수점 셋째 자리까지)", res.statistic, "검정통계량", "result.statistic", STAT,
            f"t = {res.statistic:.3f}."),
        sub("p-value를 구하시오. (소수점 넷째 자리까지)", res.pvalue, "p-value", "result.pvalue", PVAL,
            f"p-value = {res.pvalue:.4f}.", dec=4),
    ])

# ------------------------------------------------------------------ T04 일원분산분석
g = rng(401)
grp = {"A": g.normal(70, 7, 10), "B": g.normal(75, 7, 10), "C": g.normal(80, 7, 10)}
df = pd.DataFrame({"group": sum([[k] * 10 for k in grp], []), "score": np.round(np.concatenate(list(grp.values()))).astype(int)})
a, b, c = [df[df["group"] == k]["score"].dropna() for k in "ABC"]
res = stats.f_oneway(a, b, c)
add("T04-1", "T04", 1, "세 집단 점수 ANOVA",
    "A, B, C 세 집단(각 10명)의 점수이다. 세 집단의 평균에 차이가 있는지 일원분산분석을 수행하시오.",
    df, "f_oneway",
    """from scipy.stats import f_oneway
a = df[df['group']=='A']['score'].dropna()
b = df[df['group']=='B']['score'].dropna()
c = df[df['group']=='C']['score'].dropna()
result = f_oneway(a, b, c)
print(result.statistic)   # F 통계량
print(result.pvalue)""",
    [
        sub("F 통계량을 구하시오. (소수점 셋째 자리까지)", res.statistic, "F통계량", "result.statistic", STAT,
            f"F = 집단간 평균제곱 / 집단내 평균제곱 = {res.statistic:.3f}."),
        sub("p-value를 구하시오. (소수점 넷째 자리까지)", res.pvalue, "p-value", "result.pvalue", PVAL,
            f"p-value = {res.pvalue:.4f}.", dec=4),
        reject_sub(res.pvalue, what="'세 집단의 평균이 모두 같다'는 귀무가설"),
    ])

g = rng(402)
fert = {"F1": g.normal(52, 5, 8), "F2": g.normal(55, 5, 8), "F3": g.normal(51, 5, 8)}
df = pd.DataFrame({"fertilizer": sum([[k] * 8 for k in fert], []), "yield_kg": np.round(np.concatenate(list(fert.values())), 1)})
grps = [df[df["fertilizer"] == k]["yield_kg"].dropna() for k in ["F1", "F2", "F3"]]
res = stats.f_oneway(*grps)
means = df.groupby("fertilizer")["yield_kg"].mean()
add("T04-2", "T04", 2, "비료 3종 수확량",
    "비료 F1, F2, F3을 각각 8개 밭에 사용했을 때 수확량(yield_kg)이다. 비료 종류에 따라 평균 수확량이 다른지 검정하시오.",
    df, "f_oneway",
    """from scipy.stats import f_oneway
print(df.groupby('fertilizer')['yield_kg'].mean())
g1 = df[df['fertilizer']=='F1']['yield_kg'].dropna()
g2 = df[df['fertilizer']=='F2']['yield_kg'].dropna()
g3 = df[df['fertilizer']=='F3']['yield_kg'].dropna()
result = f_oneway(g1, g2, g3)
print(result.statistic)
print(result.pvalue)""",
    [
        sub("평균 수확량이 가장 큰 비료는?", means.idxmax(), "집단 평균", "df.groupby('fertilizer')['yield_kg'].mean()",
            "groupby(&&.mean()", f"집단 평균: " + ", ".join(f"{k}={v:.2f}" for k, v in means.items()) + f". 가장 큰 것은 {means.idxmax()}.",
            kind="choice", opts=["F1", "F2", "F3"]),
        sub("F 통계량을 구하시오. (소수점 셋째 자리까지)", res.statistic, "F통계량", "result.statistic", STAT,
            f"F = {res.statistic:.3f}."),
        sub("p-value를 구하시오. (소수점 넷째 자리까지)", res.pvalue, "p-value", "result.pvalue", PVAL,
            f"p-value = {res.pvalue:.4f}. " + ("0.05보다 작으므로 비료별 평균 차이가 유의하다." if res.pvalue < 0.05 else "0.05 이상이므로 비료별 평균 차이가 유의하지 않다."), dec=4),
    ])

g = rng(403)
reg = {"서울": g.normal(320, 40, 9), "부산": g.normal(290, 40, 9), "대구": g.normal(280, 40, 9), "광주": g.normal(300, 40, 9)}
df = pd.DataFrame({"region": sum([[k] * 9 for k in reg], []), "sales": np.round(np.concatenate(list(reg.values()))).astype(int)})
grps = [df[df["region"] == k]["sales"].dropna() for k in reg]
res = stats.f_oneway(*grps)
k, N = 4, len(df)
add("T04-3", "T04", 2, "4개 지역 매장 매출",
    "서울, 부산, 대구, 광주 4개 지역 매장(각 9곳)의 월매출(sales, 백만원)이다. 지역별 평균 매출 차이를 일원분산분석으로 검정하시오.",
    df, "f_oneway",
    """from scipy.stats import f_oneway
groups = [df[df['region']==r]['sales'].dropna() for r in ['서울','부산','대구','광주']]
result = f_oneway(*groups)
print(result.statistic)
print(result.pvalue)
k = df['region'].nunique()
N = len(df)
print(k - 1, N - k)   # 집단간 자유도, 집단내 자유도""",
    [
        sub("F 통계량을 구하시오. (소수점 셋째 자리까지)", res.statistic, "F통계량", "result.statistic", STAT,
            f"F = {res.statistic:.3f}."),
        sub("p-value를 구하시오. (소수점 넷째 자리까지)", res.pvalue, "p-value", "result.pvalue", PVAL,
            f"p-value = {res.pvalue:.4f}.", dec=4),
        sub("집단내(잔차) 자유도를 구하시오. (정수)", N - k, "자유도", "N - k", "-",
            f"집단간 자유도 = k - 1 = {k - 1}, 집단내 자유도 = N - k = {N} - {k} = {N - k}.", dec=0,
            traps=[(k - 1, "집단간 자유도(k - 1)를 입력했습니다. 집단내 자유도는 N - k."), (N - 1, "전체 자유도(N - 1)입니다.")]),
    ])

# ------------------------------------------------------------------ T05 카이제곱 독립성
g = rng(501)
gender = np.array(["M"] * 55 + ["F"] * 65)
p_buy = np.where(gender == "M", 0.35, 0.55)
purchase = np.where(g.random(120) < p_buy, "Y", "N")
df = pd.DataFrame({"gender": gender, "purchase": purchase}).sample(frac=1, random_state=1)
table = pd.crosstab(df["gender"], df["purchase"])
chi2, p, dof, exp_ = stats.chi2_contingency(table)
chi2_nc, p_nc, _, _ = stats.chi2_contingency(table, correction=False)
add("T05-1", "T05", 2, "성별과 구매 여부 (2x2)",
    "고객 120명의 성별(gender)과 구매 여부(purchase)이다. 두 변수가 독립인지 카이제곱 독립성 검정을 수행하시오. (chi2_contingency 기본 옵션 사용)",
    df, "chi2_contingency",
    """import pandas as pd
from scipy.stats import chi2_contingency
table = pd.crosstab(df['gender'], df['purchase'])
chi2, p, dof, expected = chi2_contingency(table)   # 2x2 는 기본으로 Yates 보정
print(chi2)
print(p)
print(dof)""",
    [
        sub("카이제곱 통계량을 구하시오. (소수점 셋째 자리까지)", chi2, "검정통계량", "chi2", "=chi2|X[0]|X.statistic|stat|chi|chi_2|chi2_stat",
            f"chi2 = {chi2:.3f}. 2x2 표는 기본값 correction=True 로 Yates 연속성 보정이 적용된다.",
            traps=[(chi2_nc, "correction=False(보정 없음) 값입니다. 기본 옵션은 2x2에서 Yates 보정을 적용합니다.")]),
        sub("p-value를 구하시오. (소수점 넷째 자리까지)", p, "p-value", "p", "=p|X[1]|X.pvalue|pval|p_value|pvalue",
            f"p-value = {p:.4f}.", dec=4, traps=[(p_nc, "보정 없는 카이제곱의 p-value입니다.")]),
        sub("자유도를 구하시오. (정수)", dof, "자유도", "dof", "=dof|X[2]|X.dof|df",
            f"자유도 = (행 수 - 1) x (열 수 - 1) = (2-1) x (2-1) = {dof}.", dec=0),
    ],
    note="2x2 분할표는 chi2_contingency 기본값으로 Yates 연속성 보정이 들어갑니다. 문제에서 '보정하지 말 것'이라 하면 correction=False.")

g = rng(502)
age = g.choice(["20대", "30대", "40대"], size=150, p=[0.35, 0.35, 0.30])
probs = {"20대": [0.55, 0.30, 0.15], "30대": [0.40, 0.35, 0.25], "40대": [0.25, 0.35, 0.40]}
channel = np.array([g.choice(["앱", "웹", "매장"], p=probs[x]) for x in age])
df = pd.DataFrame({"age_group": age, "channel": channel})
table = pd.crosstab(df["age_group"], df["channel"])
chi2, p, dof, exp_ = stats.chi2_contingency(table)
add("T05-2", "T05", 2, "연령대와 선호 채널 (3x3)",
    "고객 150명의 연령대(age_group)와 선호 구매채널(channel)이다. 두 변수의 독립성을 검정하시오. 기대도수는 pd.crosstab의 기본 정렬 순서(행: 20대, 30대, 40대 / 열: 매장, 앱, 웹) 기준이다.",
    df, "chi2_contingency",
    """import pandas as pd
from scipy.stats import chi2_contingency
table = pd.crosstab(df['age_group'], df['channel'])
print(table)
chi2, p, dof, expected = chi2_contingency(table)
print(chi2)
print(p)
print(dof)
print(expected[0][0])   # 20대-매장 기대도수""",
    [
        sub("카이제곱 통계량을 구하시오. (소수점 셋째 자리까지)", chi2, "검정통계량", "chi2", "=chi2|X[0]|X.statistic|stat|chi|chi_2|chi2_stat",
            f"chi2 = {chi2:.3f}. 3x3 표는 Yates 보정이 적용되지 않는다(2x2에서만)."),
        sub("자유도를 구하시오. (정수)", dof, "자유도", "dof", "=dof|X[2]|X.dof|df",
            f"(3-1) x (3-1) = {dof}.", dec=0, traps=[(8, "셀 수 - 1이 아닙니다. (행-1)x(열-1).")]),
        sub("20대-매장 셀의 기대도수를 구하시오. (소수점 셋째 자리까지)", exp_[0][0], "기대도수", "expected[0][0]", "=expected[0][0]|expected[0,0]|X.expected_freq[0][0]|X[3][0][0]|exp[0][0]|ex[0][0]|expected.iloc[0,0]",
            f"기대도수 = (20대 행합 x 매장 열합) / 전체 = {table.iloc[0].sum()} x {table.iloc[:, 0].sum()} / {table.values.sum()} = {exp_[0][0]:.3f}.",
            traps=[(table.iloc[0, 0], "관측도수를 입력했습니다. 기대도수는 expected 배열에서 꺼냅니다.")]),
        sub("p-value를 구하시오. (소수점 넷째 자리까지)", p, "p-value", "p", "=p|X[1]|X.pvalue|pval|p_value|pvalue",
            f"p-value = {p:.4f}.", dec=4),
    ])

g = rng(503)
region = g.choice(["도시", "농촌"], size=90, p=[0.6, 0.4])
pr = {"도시": [0.3, 0.4, 0.3], "농촌": [0.25, 0.4, 0.35]}
sat = np.array([g.choice(["불만", "보통", "만족"], p=pr[x]) for x in region])
df = pd.DataFrame({"region": region, "satisfaction": sat})
table = pd.crosstab(df["region"], df["satisfaction"])
chi2, p, dof, exp_ = stats.chi2_contingency(table)
add("T05-3", "T05", 1, "거주지와 만족도 (2x3)",
    "응답자 90명의 거주지(region)와 만족도(satisfaction)이다. 거주지와 만족도가 독립인지 검정하시오.",
    df, "chi2_contingency",
    """import pandas as pd
from scipy.stats import chi2_contingency
table = pd.crosstab(df['region'], df['satisfaction'])
chi2, p, dof, expected = chi2_contingency(table)
print(chi2)
print(p)
print(p < 0.05)""",
    [
        sub("카이제곱 통계량을 구하시오. (소수점 셋째 자리까지)", chi2, "검정통계량", "chi2", "=chi2|X[0]|X.statistic|stat|chi|chi_2|chi2_stat",
            f"chi2 = {chi2:.3f}. 2x3 표이므로 보정 없음."),
        sub("p-value를 구하시오. (소수점 넷째 자리까지)", p, "p-value", "p", "=p|X[1]|X.pvalue|pval|p_value|pvalue",
            f"p-value = {p:.4f}.", dec=4),
        reject_sub(p, code="p < 0.05", accept="<0.05", what="'두 변수는 독립이다'라는 귀무가설"),
    ])

# ------------------------------------------------------------------ T06 카이제곱 적합도
observed = [30, 45, 25]
expected = [100 / 3] * 3
res = stats.chisquare(observed, f_exp=expected)
df = pd.DataFrame({"menu": ["A", "B", "C"], "count": observed})
add("T06-1", "T06", 1, "메뉴 3종 선호 균등성",
    "메뉴 A, B, C를 고른 손님 수(count)이다. 세 메뉴의 선호가 균등한지(기대비율 1:1:1) 카이제곱 적합도 검정을 수행하시오.",
    df, "chisquare",
    """from scipy.stats import chisquare
observed = df['count'].tolist()       # [30, 45, 25]
n = sum(observed)
expected = [n/3, n/3, n/3]
result = chisquare(observed, f_exp=expected)
print(result.statistic)
print(result.pvalue)""",
    [
        sub("카이제곱 통계량을 구하시오. (소수점 셋째 자리까지)", res.statistic, "검정통계량", "result.statistic", STAT,
            f"합( (관측 - 기대)^2 / 기대 ) = {res.statistic:.3f}."),
        sub("p-value를 구하시오. (소수점 넷째 자리까지)", res.pvalue, "p-value", "result.pvalue", PVAL,
            f"p-value = {res.pvalue:.4f}. 자유도는 범주수 - 1 = 2.", dec=4),
        reject_sub(res.pvalue, what="'선호가 균등하다'는 귀무가설"),
    ])

g = rng(602)
ratio = {"A": 0.34, "B": 0.27, "O": 0.28, "AB": 0.11}
blood = g.choice(list(ratio), size=200, p=[0.30, 0.25, 0.31, 0.14])
df = pd.DataFrame({"person": range(1, 201), "blood": blood})
obs = df["blood"].value_counts().reindex(["A", "B", "O", "AB"])
exp_ = [ratio[k] * len(df) for k in ["A", "B", "O", "AB"]]
res = stats.chisquare(obs, f_exp=exp_)
res_eq = stats.chisquare(obs)
add("T06-2", "T06", 2, "혈액형 비율 적합도",
    "200명의 혈액형(blood) 자료이다. 알려진 비율 A:B:O:AB = 0.34:0.27:0.28:0.11 을 따르는지 적합도 검정을 수행하시오. (범주 순서 A, B, O, AB)",
    df, "chisquare",
    """from scipy.stats import chisquare
obs = df['blood'].value_counts().reindex(['A','B','O','AB'])
n = len(df)
exp = [0.34*n, 0.27*n, 0.28*n, 0.11*n]
result = chisquare(obs, f_exp=exp)
print(obs.tolist())
print(result.statistic)
print(result.pvalue)""",
    [
        sub("O형 관측도수는? (정수)", obs["O"], "관측도수", "df['blood'].value_counts()", "value_counts(",
            f"value_counts() 결과 O형 = {obs['O']}명.", dec=0),
        sub("카이제곱 통계량을 구하시오. (소수점 셋째 자리까지)", res.statistic, "검정통계량", "result.statistic", STAT,
            f"기대도수 = 비율 x 200 = {[round(x, 1) for x in exp_]}. chi2 = {res.statistic:.3f}.",
            traps=[(res_eq.statistic, "f_exp를 생략해 균등분포(1:1:1:1)와 비교했습니다. 주어진 비율로 기대도수를 넣어야 합니다.")]),
        sub("p-value를 구하시오. (소수점 넷째 자리까지)", res.pvalue, "p-value", "result.pvalue", PVAL,
            f"p-value = {res.pvalue:.4f}.", dec=4),
    ],
    note="value_counts()는 빈도 내림차순이라 순서가 바뀝니다. reindex로 기대도수와 같은 순서를 맞추세요.")

g = rng(603)
color = g.choice(["빨강", "파랑", "검정", "흰색"], size=120, p=[0.22, 0.25, 0.33, 0.20])
df = pd.DataFrame({"order_id": range(1, 121), "color": color})
obs = df["color"].value_counts().sort_index()
res = stats.chisquare(obs)
add("T06-3", "T06", 1, "제품 색상 선호 균등성",
    "주문 120건의 색상(color)이다. 네 가지 색상이 같은 비율로 팔리는지 적합도 검정을 수행하시오.",
    df, "chisquare",
    """from scipy.stats import chisquare
obs = df['color'].value_counts()
result = chisquare(obs)          # f_exp 생략 = 균등 기대도수
print(result.statistic)
print(result.pvalue)
print(len(obs) - 1)              # 자유도""",
    [
        sub("카이제곱 통계량을 구하시오. (소수점 셋째 자리까지)", res.statistic, "검정통계량", "result.statistic", STAT,
            f"기대도수 = 120 / 4 = 30. chi2 = {res.statistic:.3f}. (균등 비교는 순서와 무관)"),
        sub("자유도를 구하시오. (정수)", len(obs) - 1, "자유도", "len(obs) - 1", "-1",
            f"적합도 검정 자유도 = 범주 수 - 1 = {len(obs) - 1}.", dec=0, traps=[(len(obs), "범주 수를 그대로 입력했습니다.")]),
        sub("p-value를 구하시오. (소수점 넷째 자리까지)", res.pvalue, "p-value", "result.pvalue", PVAL,
            f"p-value = {res.pvalue:.4f}.", dec=4),
    ])

# ------------------------------------------------------------------ T07 피어슨
g = rng(701)
hours = np.round(g.uniform(1, 10, 20), 1)
score = np.round(50 + 4 * hours + g.normal(0, 7, 20)).astype(int)
df = pd.DataFrame({"hours": hours, "score": score})
d = df[["hours", "score"]].dropna()
res = stats.pearsonr(d["hours"], d["score"])
sp = stats.spearmanr(d["hours"], d["score"])
add("T07-1", "T07", 1, "공부시간과 점수",
    "학생 20명의 공부시간(hours)과 시험점수(score)이다. 두 변수의 피어슨 상관계수와 유의성을 구하시오.",
    df, "pearsonr",
    """from scipy.stats import pearsonr
d = df[['hours','score']].dropna()
result = pearsonr(d['hours'], d['score'])
print(result.statistic)   # 상관계수 r
print(result.pvalue)""",
    [
        sub("피어슨 상관계수 r을 구하시오. (소수점 셋째 자리까지)", res.statistic, "상관계수", "result.statistic", STAT,
            f"r = {res.statistic:.3f}. 강한 양의 선형관계.", traps=[(sp.statistic, "스피어만 순위상관계수입니다. 선형 상관은 pearsonr.")]),
        sub("p-value를 구하시오. (소수점 넷째 자리까지)", res.pvalue, "p-value", "result.pvalue", PVAL,
            f"p-value = {res.pvalue:.4f} (매우 작으면 0.0000).", dec=4),
    ])

g = rng(702)
temp = np.round(g.uniform(18, 34, 24), 1)
ice = np.round(120 + 9 * temp + g.normal(0, 30, 24)).astype(float)
df = pd.DataFrame({"temp": temp, "ice_sales": ice})
df["ice_sales"] = with_nan(df["ice_sales"], [2, 15])
df["temp"] = with_nan(df["temp"], [8])
d = df[["temp", "ice_sales"]].dropna()
res = stats.pearsonr(d["temp"], d["ice_sales"])
add("T07-2", "T07", 1, "기온과 아이스크림 판매량",
    "24일간 기온(temp)과 아이스크림 판매량(ice_sales)이다. 결측 행을 제거하고 피어슨 상관분석을 수행하시오.",
    df, "pearsonr",
    """from scipy.stats import pearsonr
d = df[['temp','ice_sales']].dropna()
print(len(d))
result = pearsonr(d['temp'], d['ice_sales'])
print(result.statistic)
print(result.pvalue)""",
    [
        sub("결측 행 제거 후 남은 행 수는? (정수)", len(d), "표본 수", "len(d)", "len(",
            f"temp 1개, ice_sales 2개 결측 → {len(df)} - 3 = {len(d)}행.", dec=0),
        sub("피어슨 상관계수 r을 구하시오. (소수점 셋째 자리까지)", res.statistic, "상관계수", "result.statistic", STAT,
            f"r = {res.statistic:.3f}."),
        reject_sub(res.pvalue, what="'상관계수가 0이다'라는 귀무가설"),
    ])

g = rng(703)
adv = np.round(g.uniform(10, 60, 18), 1)
rev = np.round(200 + 2.2 * adv + g.normal(0, 35, 18), 1)
df = pd.DataFrame({"ad_cost": adv, "revenue": rev})
d = df[["ad_cost", "revenue"]].dropna()
res = stats.pearsonr(d["ad_cost"], d["revenue"])
add("T07-3", "T07", 2, "광고비와 매출",
    "18개 매장의 광고비(ad_cost)와 매출(revenue)이다. 피어슨 상관계수, 그 제곱(설명력), p-value를 구하시오.",
    df, "pearsonr",
    """from scipy.stats import pearsonr
result = pearsonr(df['ad_cost'], df['revenue'])
r = result.statistic
print(r)
print(r ** 2)
print(result.pvalue)""",
    [
        sub("피어슨 상관계수 r을 구하시오. (소수점 셋째 자리까지)", res.statistic, "상관계수", "result.statistic", STAT,
            f"r = {res.statistic:.3f}."),
        sub("r의 제곱을 구하시오. (소수점 셋째 자리까지)", res.statistic ** 2, "상관계수", "result.statistic ** 2", "X.statistic&&**2",
            f"r^2 = {res.statistic ** 2:.3f}. 단순회귀의 R²과 같은 값.", traps=[(res.statistic, "r을 제곱하지 않았습니다.")]),
        sub("p-value를 구하시오. (소수점 넷째 자리까지)", res.pvalue, "p-value", "result.pvalue", PVAL,
            f"p-value = {res.pvalue:.4f}.", dec=4),
    ])

# ------------------------------------------------------------------ T08 스피어만
g = rng(801)
x = g.integers(1, 50, 15)
y = np.round(np.sqrt(x) * 10 + g.normal(0, 8, 15)).astype(int)
df = pd.DataFrame({"x": x, "y": y})
d = df[["x", "y"]].dropna()
res = stats.spearmanr(d["x"], d["y"])
pe = stats.pearsonr(d["x"], d["y"])
add("T08-1", "T08", 1, "x와 y 순위상관",
    "두 변수 x, y의 관측값 15쌍이다. 스피어만 순위상관계수와 p-value를 구하시오.",
    df, "spearmanr",
    """from scipy.stats import spearmanr
d = df[['x','y']].dropna()
result = spearmanr(d['x'], d['y'])
print(result.statistic)   # 스피어만 rho
print(result.pvalue)""",
    [
        sub("스피어만 상관계수(rho)를 구하시오. (소수점 셋째 자리까지)", res.statistic, "상관계수", "result.statistic", STAT,
            f"rho = {res.statistic:.3f}. 값 자체가 아니라 순위끼리의 피어슨 상관이다.",
            traps=[(pe.statistic, "피어슨 r입니다. 순위상관은 spearmanr.")]),
        sub("p-value를 구하시오. (소수점 넷째 자리까지)", res.pvalue, "p-value", "result.pvalue", PVAL,
            f"p-value = {res.pvalue:.4f}.", dec=4),
    ])

g = rng(802)
j1 = g.permutation(np.arange(1, 13))
j2 = np.argsort(np.argsort(j1 + g.normal(0, 3.5, 12))) + 1
df = pd.DataFrame({"contestant": [f"P{i:02d}" for i in range(1, 13)], "judge1": j1, "judge2": j2})
res = stats.spearmanr(df["judge1"], df["judge2"])
add("T08-2", "T08", 1, "심사위원 2명의 순위 일치도",
    "참가자 12명에 대해 심사위원 두 명이 매긴 순위(judge1, judge2)이다. 두 심사위원 순위의 스피어만 상관을 검정하시오.",
    df, "spearmanr",
    """from scipy.stats import spearmanr
result = spearmanr(df['judge1'], df['judge2'])
print(result.statistic)
print(result.pvalue)
print(result.pvalue < 0.05)""",
    [
        sub("스피어만 상관계수를 구하시오. (소수점 셋째 자리까지)", res.statistic, "상관계수", "result.statistic", STAT,
            f"rho = {res.statistic:.3f}."),
        sub("p-value를 구하시오. (소수점 넷째 자리까지)", res.pvalue, "p-value", "result.pvalue", PVAL,
            f"p-value = {res.pvalue:.4f}.", dec=4),
        reject_sub(res.pvalue, what="'순위 상관이 없다'는 귀무가설"),
    ])

g = rng(803)
inc = np.round(g.lognormal(8, 0.5, 16)).astype(int)
hap = np.clip(np.round(3 + 1.2 * np.log(inc / 1000) + g.normal(0, 0.8, 16), 1), 1, 10)
inc[3] = 90000  # 이상치
df = pd.DataFrame({"income": inc, "happiness": hap})
d = df[["income", "happiness"]].dropna()
res = stats.spearmanr(d["income"], d["happiness"])
pe = stats.pearsonr(d["income"], d["happiness"])
add("T08-3", "T08", 2, "소득과 행복도 (이상치 포함)",
    "16명의 월소득(income, 천원)과 행복도(happiness)이다. 소득에 극단적 이상치가 있다. 스피어만 상관계수와 p-value, 그리고 비교용 피어슨 상관계수를 구하시오.",
    df, "spearmanr",
    """from scipy.stats import spearmanr, pearsonr
d = df[['income','happiness']].dropna()
s = spearmanr(d['income'], d['happiness'])
p = pearsonr(d['income'], d['happiness'])
print(s.statistic)
print(s.pvalue)
print(p.statistic)""",
    [
        sub("스피어만 상관계수를 구하시오. (소수점 셋째 자리까지)", res.statistic, "상관계수", "result.statistic", STAT,
            f"rho = {res.statistic:.3f}. 순위 기반이라 이상치 영향이 작다.", traps=[(pe.statistic, "피어슨 r을 입력했습니다.")]),
        sub("스피어만 검정의 p-value를 구하시오. (소수점 넷째 자리까지)", res.pvalue, "p-value", "result.pvalue", PVAL,
            f"p-value = {res.pvalue:.4f}.", dec=4),
        sub("피어슨 상관계수를 구하시오. (소수점 셋째 자리까지)", pe.statistic, "상관계수", "p.statistic  # p = pearsonr(...)", ".statistic",
            f"pearson r = {pe.statistic:.3f}. 이상치 때문에 스피어만({res.statistic:.3f})과 차이가 난다."),
    ])

# ------------------------------------------------------------------ T09 OLS
g = rng(901)
n = 30
hours = np.round(g.uniform(1, 10, n), 1)
sleep = np.round(g.uniform(4, 9, n), 1)
score = np.round(40 + 3.5 * hours + 2.0 * sleep + g.normal(0, 6, n), 1)
df = pd.DataFrame({"hours": hours, "sleep": sleep, "score": score})
model = smf.ols("score ~ hours + sleep", data=df).fit()
pred = model.predict(pd.DataFrame({"hours": [5], "sleep": [7]}))[0]
add("T09-1", "T09", 2, "공부시간·수면시간 → 점수",
    "학생 30명의 공부시간(hours), 수면시간(sleep), 점수(score)이다. score ~ hours + sleep 선형회귀모형을 적합하시오.",
    df, "ols",
    """import statsmodels.formula.api as smf
model = smf.ols('score ~ hours + sleep', data=df).fit()
print(model.summary())
print(model.params['hours'])
print(model.pvalues['hours'])
print(model.rsquared)
print(model.predict({'hours':[5], 'sleep':[7]}))""",
    [
        sub("hours의 회귀계수를 구하시오. (소수점 셋째 자리까지)", model.params["hours"], "회귀계수", "model.params['hours']", "X.params['hours']",
            f"hours 계수 = {model.params['hours']:.3f}. 수면시간이 같을 때 공부 1시간당 점수가 이만큼 증가.",
            traps=[(model.params["Intercept"], "절편(Intercept)을 입력했습니다."), (model.params["sleep"], "sleep의 계수입니다.")]),
        sub("hours 회귀계수의 p-value를 구하시오. (소수점 넷째 자리까지)", model.pvalues["hours"], "회귀계수의 p-value", "model.pvalues['hours']", "X.pvalues['hours']",
            f"p-value = {model.pvalues['hours']:.4f}. (params가 아니라 pvalues)", dec=4),
        sub("결정계수 R²을 구하시오. (소수점 셋째 자리까지)", model.rsquared, "R²", "model.rsquared", "=X.rsquared",
            f"R² = {model.rsquared:.3f}.", traps=[(model.rsquared_adj, "수정 R²(rsquared_adj)입니다. 결정계수는 rsquared.")]),
        sub("hours=5, sleep=7 일 때 예측 점수를 구하시오. (소수점 셋째 자리까지)", pred, "예측값", "model.predict({'hours':[5], 'sleep':[7]})", "X.predict(",
            f"예측값 = {model.params['Intercept']:.3f} + {model.params['hours']:.3f} x 5 + {model.params['sleep']:.3f} x 7 = {pred:.3f}."),
    ])

g = rng(902)
area = np.round(g.uniform(40, 130, 25)).astype(int)
price = np.round(1.5 + 0.08 * area + g.normal(0, 0.9, 25), 2)
df = pd.DataFrame({"area": area, "price": price})
model = smf.ols("price ~ area", data=df).fit()
add("T09-2", "T09", 1, "면적 → 아파트 가격 (단순회귀)",
    "아파트 25채의 전용면적(area, m2)과 가격(price, 억원)이다. price ~ area 단순선형회귀를 적합하시오.",
    df, "ols",
    """import statsmodels.formula.api as smf
model = smf.ols('price ~ area', data=df).fit()
print(model.params['Intercept'])   # 절편
print(model.params['area'])        # 기울기
print(model.rsquared)
print(model.fvalue)""",
    [
        sub("절편을 구하시오. (소수점 셋째 자리까지)", model.params["Intercept"], "절편", "model.params['Intercept']", "X.params['Intercept']",
            f"절편 = {model.params['Intercept']:.3f}. 이름은 대문자 I로 시작하는 'Intercept'.",
            traps=[(model.params["area"], "기울기(area 계수)를 입력했습니다.")]),
        sub("area의 회귀계수(기울기)를 구하시오. (소수점 넷째 자리까지)", model.params["area"], "회귀계수", "model.params['area']", "X.params['area']",
            f"기울기 = {model.params['area']:.4f}. 면적 1m2 증가 시 가격 변화(억원).", dec=4),
        sub("결정계수 R²을 구하시오. (소수점 셋째 자리까지)", model.rsquared, "R²", "model.rsquared", "=X.rsquared",
            f"R² = {model.rsquared:.3f}."),
        sub("모형의 F 통계량을 구하시오. (소수점 셋째 자리까지)", model.fvalue, "F통계량", "model.fvalue", "=X.fvalue",
            f"F = {model.fvalue:.3f}. 단순회귀에서는 F = t^2 (area의 t값 제곱).",
            traps=[(model.tvalues["area"], "area의 t값입니다. F = t^2.")]),
    ])

g = rng(903)
n = 40
tv = np.round(g.uniform(10, 300, n), 1)
radio = np.round(g.uniform(0, 50, n), 1)
news = np.round(g.uniform(0, 80, n), 1)
sales = np.round(3 + 0.045 * tv + 0.18 * radio + 0.0 * news + g.normal(0, 1.6, n), 1)
df = pd.DataFrame({"tv": tv, "radio": radio, "newspaper": news, "sales": sales})
model = smf.ols("sales ~ tv + radio + newspaper", data=df).fit()
nsig = int((model.pvalues.drop("Intercept") < 0.05).sum())
ci = model.conf_int()
add("T09-3", "T09", 3, "광고 채널 3개 → 매출 (다중회귀)",
    "40개 시장의 TV·라디오·신문 광고비(tv, radio, newspaper)와 매출(sales)이다. sales ~ tv + radio + newspaper 를 적합하시오.",
    df, "ols",
    """import statsmodels.formula.api as smf
model = smf.ols('sales ~ tv + radio + newspaper', data=df).fit()
print(model.rsquared_adj)
print((model.pvalues.drop('Intercept') < 0.05).sum())   # 유의한 변수 개수
print(model.conf_int().loc['tv'])                     # 95% 신뢰구간
print(model.f_pvalue)""",
    [
        sub("수정 결정계수(adjusted R²)를 구하시오. (소수점 셋째 자리까지)", model.rsquared_adj, "수정 R²", "model.rsquared_adj", "=X.rsquared_adj",
            f"수정 R² = {model.rsquared_adj:.3f}.", traps=[(model.rsquared, "일반 R²(rsquared)입니다.")]),
        sub("유의수준 5%에서 유의한 독립변수(절편 제외)의 개수는? (정수)", nsig, "유의한 변수 개수", "(model.pvalues.drop('Intercept') < 0.05).sum()", "X.pvalues&&<0.05",
            "변수별 p-value: " + ", ".join(f"{k}={v:.4f}" for k, v in model.pvalues.drop('Intercept').items()) + f" → {nsig}개.", dec=0,
            traps=[(int((model.pvalues < 0.05).sum()), "절편까지 세었습니다. 독립변수만 셉니다.")]),
        sub("tv 회귀계수의 95% 신뢰구간 하한을 구하시오. (소수점 넷째 자리까지)", ci.loc["tv", 0], "신뢰구간", "model.conf_int().loc['tv', 0]", "X.conf_int(",
            f"95% CI = [{ci.loc['tv', 0]:.4f}, {ci.loc['tv', 1]:.4f}]. conf_int()의 0열이 하한, 1열이 상한.", dec=4,
            traps=[(ci.loc["tv", 1], "상한을 입력했습니다. 0열이 하한입니다.")]),
        sub("모형 전체 F검정의 p-value를 구하시오. (소수점 넷째 자리까지)", model.f_pvalue, "p-value", "model.f_pvalue", "=X.f_pvalue",
            f"F = {model.fvalue:.3f}, p = {model.f_pvalue:.4g} → 0.0000.", dec=4),
    ])

# ------------------------------------------------------------------ T10 로지스틱
g = rng(1001)
n = 60
hours = np.round(g.uniform(0, 10, n), 1)
p_ = 1 / (1 + np.exp(-(-3 + 0.6 * hours)))
pass_flag = (g.random(n) < p_).astype(int)
df = pd.DataFrame({"hours": hours, "pass_flag": pass_flag})
model = smf.logit("pass_flag ~ hours", data=df).fit(disp=False)
pr5 = model.predict(pd.DataFrame({"hours": [5]}))[0]
add("T10-1", "T10", 2, "공부시간 → 합격 여부",
    "수험생 60명의 공부시간(hours)과 합격 여부(pass_flag, 1=합격)이다. pass_flag ~ hours 로지스틱 회귀를 적합하시오.",
    df, "logit",
    """import numpy as np
import statsmodels.formula.api as smf
model = smf.logit('pass_flag ~ hours', data=df).fit(disp=False)
print(model.params['hours'])
print(np.exp(model.params['hours']))   # 오즈비
print(model.pvalues['hours'])
print(model.predict({'hours':[5]}))    # 예측확률""",
    [
        sub("hours의 회귀계수를 구하시오. (소수점 셋째 자리까지)", model.params["hours"], "회귀계수", "model.params['hours']", "X.params['hours']",
            f"계수 = {model.params['hours']:.3f}. 로그오즈의 증가량.",
            traps=[(np.exp(model.params["hours"]), "오즈비(exp 적용값)를 입력했습니다. 계수는 exp 전 값.")]),
        sub("hours의 오즈비를 구하시오. (소수점 셋째 자리까지)", np.exp(model.params["hours"]), "오즈비", "np.exp(model.params['hours'])", "exp(&&X.params['hours']",
            f"오즈비 = exp({model.params['hours']:.3f}) = {np.exp(model.params['hours']):.3f}. 공부 1시간 증가 시 합격 오즈가 이 배수만큼 증가.",
            traps=[(model.params["hours"], "계수에 np.exp()를 적용하지 않았습니다.")]),
        sub("hours 계수의 p-value를 구하시오. (소수점 넷째 자리까지)", model.pvalues["hours"], "회귀계수의 p-value", "model.pvalues['hours']", "X.pvalues['hours']",
            f"p-value = {model.pvalues['hours']:.4f}.", dec=4),
        sub("hours=5 일 때 합격 예측확률을 구하시오. (소수점 셋째 자리까지)", pr5, "예측확률", "model.predict({'hours':[5]})", "X.predict(",
            f"확률 = 1 / (1 + exp(-({model.params['Intercept']:.3f} + {model.params['hours']:.3f} x 5))) = {pr5:.3f}.",
            traps=[(model.params["Intercept"] + model.params["hours"] * 5, "로그오즈(선형예측값)를 입력했습니다. predict()는 확률을 돌려줍니다.")]),
    ])

g = rng(1002)
n = 80
age = g.integers(20, 65, n)
fee = np.round(g.uniform(20, 90, n), 1)
p_ = 1 / (1 + np.exp(-(-3.2 - 0.03 * age + 0.07 * fee)))
churn = (g.random(n) < p_).astype(int)
df = pd.DataFrame({"age": age, "monthly_fee": fee, "churn": churn})
model = smf.logit("churn ~ age + monthly_fee", data=df).fit(disp=False)
pr = model.predict(pd.DataFrame({"age": [30], "monthly_fee": [60]}))[0]
add("T10-2", "T10", 3, "고객 이탈 예측",
    "고객 80명의 나이(age), 월요금(monthly_fee, 천원), 이탈 여부(churn, 1=이탈)이다. churn ~ age + monthly_fee 로지스틱 회귀를 적합하시오.",
    df, "logit",
    """import numpy as np
import statsmodels.formula.api as smf
model = smf.logit('churn ~ age + monthly_fee', data=df).fit(disp=False)
print(np.exp(model.params['monthly_fee']))
print(model.pvalues['age'])
print(model.predict({'age':[30], 'monthly_fee':[60]}))""",
    [
        sub("monthly_fee의 오즈비를 구하시오. (소수점 셋째 자리까지)", np.exp(model.params["monthly_fee"]), "오즈비", "np.exp(model.params['monthly_fee'])", "exp(&&X.params['monthly_fee']",
            f"오즈비 = {np.exp(model.params['monthly_fee']):.3f}. 월요금 1천원 증가 시 이탈 오즈 {100 * (np.exp(model.params['monthly_fee']) - 1):.1f}% 증가.",
            traps=[(model.params["monthly_fee"], "exp를 적용하지 않은 계수입니다.")]),
        sub("age 계수의 p-value를 구하시오. (소수점 넷째 자리까지)", model.pvalues["age"], "회귀계수의 p-value", "model.pvalues['age']", "X.pvalues['age']",
            f"p-value = {model.pvalues['age']:.4f}.", dec=4),
        sub("age=30, monthly_fee=60 고객의 이탈 예측확률을 구하시오. (소수점 셋째 자리까지)", pr, "예측확률", "model.predict({'age':[30], 'monthly_fee':[60]})", "X.predict(",
            f"예측확률 = {pr:.3f}."),
    ])

g = rng(1003)
n = 90
income = np.round(g.uniform(20, 120, n), 1)
debt = np.round(g.uniform(0.1, 0.9, n), 2)
p_ = 1 / (1 + np.exp(-(-1.0 - 0.025 * income + 3.5 * debt)))
default = (g.random(n) < p_).astype(int)
df = pd.DataFrame({"income": income, "debt_ratio": debt, "default": default})
model = smf.logit("default ~ income + debt_ratio", data=df).fit(disp=False)
ci = model.conf_int()
nsig = int((model.pvalues.drop("Intercept") < 0.05).sum())
add("T10-3", "T10", 3, "대출 연체 예측",
    "대출자 90명의 연소득(income, 백만원), 부채비율(debt_ratio), 연체 여부(default, 1=연체)이다. default ~ income + debt_ratio 로지스틱 회귀를 적합하시오.",
    df, "logit",
    """import numpy as np
import statsmodels.formula.api as smf
model = smf.logit('default ~ income + debt_ratio', data=df).fit(disp=False)
print(model.params['debt_ratio'])
print(model.conf_int().loc['debt_ratio'])
print(np.exp(model.conf_int().loc['debt_ratio']))   # 오즈비 신뢰구간
print((model.pvalues.drop('Intercept') < 0.05).sum())""",
    [
        sub("debt_ratio의 회귀계수를 구하시오. (소수점 셋째 자리까지)", model.params["debt_ratio"], "회귀계수", "model.params['debt_ratio']", "X.params['debt_ratio']",
            f"계수 = {model.params['debt_ratio']:.3f}."),
        sub("debt_ratio 계수의 95% 신뢰구간 하한을 구하시오. (소수점 셋째 자리까지)", ci.loc["debt_ratio", 0], "신뢰구간", "model.conf_int().loc['debt_ratio', 0]", "X.conf_int(",
            f"95% CI = [{ci.loc['debt_ratio', 0]:.3f}, {ci.loc['debt_ratio', 1]:.3f}]. 오즈비 CI는 여기에 np.exp 적용: [{np.exp(ci.loc['debt_ratio', 0]):.3f}, {np.exp(ci.loc['debt_ratio', 1]):.3f}].",
            traps=[(np.exp(ci.loc["debt_ratio", 0]), "오즈비 신뢰구간 하한(exp 적용)입니다. 계수의 신뢰구간을 물었습니다."), (ci.loc["debt_ratio", 1], "상한입니다.")]),
        sub("유의수준 5%에서 유의한 독립변수(절편 제외) 개수는? (정수)", nsig, "유의한 변수 개수", "(model.pvalues.drop('Intercept') < 0.05).sum()", "X.pvalues&&<0.05",
            "p-value: " + ", ".join(f"{k}={v:.4f}" for k, v in model.pvalues.drop('Intercept').items()) + f" → {nsig}개.", dec=0),
    ])

# ------------------------------------------------------------------ T11 정규성
g = rng(1101)
df = pd.DataFrame({"score": np.round(g.normal(70, 10, 30), 1)})
res = stats.shapiro(df["score"].dropna())
add("T11-1", "T11", 1, "점수의 정규성",
    "30명의 점수(score)이다. Shapiro-Wilk 검정으로 정규성을 검정하시오.",
    df, "shapiro",
    """from scipy.stats import shapiro
result = shapiro(df['score'].dropna())
print(result.statistic)   # W
print(result.pvalue)""",
    [
        sub("검정통계량 W를 구하시오. (소수점 셋째 자리까지)", res.statistic, "검정통계량", "result.statistic", STAT,
            f"W = {res.statistic:.3f}. 1에 가까울수록 정규분포에 가깝다."),
        sub("p-value를 구하시오. (소수점 넷째 자리까지)", res.pvalue, "p-value", "result.pvalue", PVAL,
            f"p-value = {res.pvalue:.4f}.", dec=4),
        reject_sub(res.pvalue, what="'정규분포를 따른다'는 귀무가설"),
    ])

g = rng(1102)
df = pd.DataFrame({"income": np.round(g.exponential(300, 25) + 150).astype(int)})
res = stats.shapiro(df["income"].dropna())
add("T11-2", "T11", 1, "소득의 정규성 (치우친 분포)",
    "가구 25곳의 월소득(income, 만원)이다. Shapiro-Wilk 검정을 수행하고 정규성 가정 여부를 판단하시오.",
    df, "shapiro",
    """from scipy.stats import shapiro
result = shapiro(df['income'].dropna())
print(result.statistic)
print(result.pvalue)""",
    [
        sub("검정통계량 W를 구하시오. (소수점 셋째 자리까지)", res.statistic, "검정통계량", "result.statistic", STAT, f"W = {res.statistic:.3f}."),
        sub("p-value를 구하시오. (소수점 넷째 자리까지)", res.pvalue, "p-value", "result.pvalue", PVAL, f"p-value = {res.pvalue:.4f}.", dec=4),
        sub("정규성 가정을 만족한다고 볼 수 있는가?", "아니오" if res.pvalue < 0.05 else "예", "귀무가설 기각 여부", "result.pvalue >= 0.05", "X.pvalue",
            f"p = {res.pvalue:.4f} {'< 0.05 → 정규성 귀무가설 기각 → 정규성 불만족. 비모수 검정(Mann-Whitney 등)을 고려.' if res.pvalue < 0.05 else '>= 0.05 → 정규성 만족.'}",
            kind="choice", opts=["예", "아니오"]),
    ])

g = rng(1103)
w = np.round(g.normal(500, 3, 22), 1)
df = pd.DataFrame({"line": ["L1"] * 11 + ["L2"] * 11, "weight_g": w})
df["weight_g"] = with_nan(df["weight_g"], [6])
a = df[df["line"] == "L1"]["weight_g"].dropna()
res = stats.shapiro(a)
add("T11-3", "T11", 2, "생산라인 L1 무게의 정규성",
    "두 생산라인(L1, L2)의 제품 무게(weight_g)이다. L1 라인 데이터만(결측 제거) Shapiro-Wilk 정규성 검정을 수행하시오.",
    df, "shapiro",
    """from scipy.stats import shapiro
a = df[df['line']=='L1']['weight_g'].dropna()
print(len(a))
result = shapiro(a)
print(result.statistic)
print(result.pvalue)""",
    [
        sub("검정에 사용된 L1 표본 수는? (정수)", len(a), "표본 수", "len(a)", "len(", f"L1 11개 중 결측 1개 → {len(a)}개.", dec=0),
        sub("검정통계량 W를 구하시오. (소수점 셋째 자리까지)", res.statistic, "검정통계량", "result.statistic", STAT, f"W = {res.statistic:.3f}.",
            traps=[(stats.shapiro(df["weight_g"].dropna()).statistic, "전체(L1+L2) 데이터로 검정했습니다. L1만 필터링하세요.")]),
        sub("p-value를 구하시오. (소수점 넷째 자리까지)", res.pvalue, "p-value", "result.pvalue", PVAL, f"p-value = {res.pvalue:.4f}.", dec=4),
    ])

# ------------------------------------------------------------------ T12 등분산성
g = rng(1201)
A = np.round(g.normal(70, 5, 15), 1)
B = np.round(g.normal(72, 12, 15), 1)
df = pd.DataFrame({"group": ["A"] * 15 + ["B"] * 15, "score": np.concatenate([A, B])})
a = df[df["group"] == "A"]["score"].dropna()
b = df[df["group"] == "B"]["score"].dropna()
res = stats.levene(a, b)
add("T12-1", "T12", 1, "두 집단 등분산성",
    "A, B 두 집단 각 15명의 점수(score)이다. Levene 검정으로 두 집단 분산이 같은지 검정하시오.",
    df, "levene",
    """from scipy.stats import levene
a = df[df['group']=='A']['score'].dropna()
b = df[df['group']=='B']['score'].dropna()
result = levene(a, b)
print(result.statistic)
print(result.pvalue)""",
    [
        sub("Levene 검정통계량을 구하시오. (소수점 셋째 자리까지)", res.statistic, "검정통계량", "result.statistic", STAT, f"W = {res.statistic:.3f}. (기본 center='median')",
            traps=[(stats.levene(a, b, center="mean").statistic, "center='mean' 결과입니다. scipy 기본값은 center='median'.")]),
        sub("p-value를 구하시오. (소수점 넷째 자리까지)", res.pvalue, "p-value", "result.pvalue", PVAL, f"p-value = {res.pvalue:.4f}.", dec=4),
        sub("두 집단의 분산이 같다고(등분산) 볼 수 있는가?", "아니오" if res.pvalue < 0.05 else "예", "귀무가설 기각 여부", "result.pvalue >= 0.05", "X.pvalue",
            f"p = {res.pvalue:.4f} {'< 0.05 → 등분산 기각 → t검정 시 equal_var=False.' if res.pvalue < 0.05 else '>= 0.05 → 등분산 가정 가능 → equal_var=True 사용 가능.'}",
            kind="choice", opts=["예", "아니오"]),
    ])

g = rng(1202)
mats = {"M1": g.normal(30, 2, 10), "M2": g.normal(31, 2.5, 10), "M3": g.normal(30, 2.2, 10)}
df = pd.DataFrame({"material": sum([[k] * 10 for k in mats], []), "strength": np.round(np.concatenate(list(mats.values())), 2)})
grps = [df[df["material"] == k]["strength"].dropna() for k in mats]
res = stats.levene(*grps)
add("T12-2", "T12", 2, "재료 3종 강도의 등분산성",
    "재료 M1, M2, M3 각 10개 시편의 강도(strength)이다. ANOVA 전에 세 집단의 등분산성을 Levene 검정으로 확인하시오.",
    df, "levene",
    """from scipy.stats import levene
g1 = df[df['material']=='M1']['strength'].dropna()
g2 = df[df['material']=='M2']['strength'].dropna()
g3 = df[df['material']=='M3']['strength'].dropna()
result = levene(g1, g2, g3)
print(result.statistic)
print(result.pvalue)""",
    [
        sub("Levene 검정통계량을 구하시오. (소수점 셋째 자리까지)", res.statistic, "검정통계량", "result.statistic", STAT, f"W = {res.statistic:.3f}."),
        sub("p-value를 구하시오. (소수점 넷째 자리까지)", res.pvalue, "p-value", "result.pvalue", PVAL, f"p-value = {res.pvalue:.4f}.", dec=4),
        reject_sub(res.pvalue, what="'세 집단의 분산이 같다'는 귀무가설"),
    ])

g = rng(1203)
X1 = np.round(g.normal(100, 6, 16), 1)
X2 = np.round(g.normal(106, 15, 14), 1)
df = pd.DataFrame({"plant": ["P1"] * 16 + ["P2"] * 14, "output": np.concatenate([X1, X2])})
a = df[df["plant"] == "P1"]["output"].dropna()
b = df[df["plant"] == "P2"]["output"].dropna()
lv = stats.levene(a, b)
eq = bool(lv.pvalue >= 0.05)
tt = stats.ttest_ind(a, b, equal_var=eq)
tt_other = stats.ttest_ind(a, b, equal_var=not eq)
add("T12-3", "T12", 3, "등분산 검정 후 t검정 선택",
    "공장 P1(16일), P2(14일)의 일일 생산량(output)이다. 먼저 Levene 검정(유의수준 5%)으로 등분산 여부를 판단하고, 그 결과에 맞는 equal_var 옵션으로 독립표본 t검정을 수행하시오. (P1을 첫 번째 집단으로)",
    df, "levene",
    f"""from scipy.stats import levene, ttest_ind
a = df[df['plant']=='P1']['output'].dropna()
b = df[df['plant']=='P2']['output'].dropna()
lv = levene(a, b)
print(lv.pvalue)
eq = lv.pvalue >= 0.05          # 등분산이면 True
result = ttest_ind(a, b, equal_var=eq)   # 이 데이터에서는 equal_var={eq}
print(result.statistic)""",
    [
        sub("Levene 검정의 p-value를 구하시오. (소수점 넷째 자리까지)", lv.pvalue, "p-value", "lv.pvalue", PVAL, f"Levene p = {lv.pvalue:.4f}.", dec=4),
        sub("t검정에 사용할 equal_var 값은?", str(eq), "귀무가설 기각 여부", "lv.pvalue >= 0.05", "X.pvalue",
            f"Levene p {'>= 0.05 → 등분산 → True' if eq else '< 0.05 → 이분산 → False (Welch)'}.", kind="choice", opts=["True", "False"]),
        sub("선택한 옵션으로 수행한 t 통계량을 구하시오. (소수점 셋째 자리까지)", tt.statistic, "검정통계량", "result.statistic", STAT,
            f"t = {tt.statistic:.3f}.", traps=[(tt_other.statistic, f"equal_var={not eq} 결과입니다. Levene 결과에 맞는 옵션을 쓰세요.")]),
    ])

# ------------------------------------------------------------------ T13 비율 z검정
z, p = proportions_ztest(60, 100, value=0.5)
df = pd.DataFrame({"항목": ["설문 응답자 수", "찬성 응답 수"], "값": [100, 60]})
add("T13-1", "T13", 1, "찬성 비율 50% 검정",
    "100명 중 60명이 정책에 찬성했다. 찬성 비율이 0.5와 다른지 단일표본 비율 z검정을 수행하시오. (statsmodels 기본 옵션)",
    df, "proportions_ztest",
    """from statsmodels.stats.proportion import proportions_ztest
count = 60
nobs = 100
z, p = proportions_ztest(count, nobs, value=0.5)
print(z)
print(p)""",
    [
        sub("z 통계량을 구하시오. (소수점 셋째 자리까지)", z, "검정통계량", "z", "=z|z_stat|stat|zstat|X[0]|zscore",
            f"z = (0.6 - 0.5) / sqrt(0.6 x 0.4 / 100) = {z:.3f}. 기본값(prop_var=False)은 분모에 표본비율 0.6을 쓴다.",
            traps=[((0.6 - 0.5) / np.sqrt(0.5 * 0.5 / 100), "분모에 귀무비율(0.5)을 넣은 교과서 공식 값입니다. statsmodels 기본은 표본비율을 사용합니다.")]),
        sub("p-value를 구하시오. (소수점 넷째 자리까지)", p, "p-value", "p", "=p|pval|p_value|pvalue|X[1]", f"p-value = {p:.4f}.", dec=4),
        reject_sub(p, code="p < 0.05", accept="<0.05"),
    ],
    note="proportions_ztest(count, nobs, value)는 (z, p) 튜플을 돌려줍니다. .statistic 속성이 없습니다.")

g = rng(1302)
click = (g.random(200) < 0.36).astype(int)
df = pd.DataFrame({"user": range(1, 201), "click": click})
cnt = int(df["click"].sum())
z, p = proportions_ztest(cnt, len(df), value=0.3)
add("T13-2", "T13", 2, "광고 클릭률 30% 검정",
    "광고 노출 200건의 클릭 여부(click, 1=클릭)이다. 클릭률이 0.3과 다른지 비율 z검정을 수행하시오.",
    df, "proportions_ztest",
    """from statsmodels.stats.proportion import proportions_ztest
count = df['click'].sum()
nobs = len(df)
z, p = proportions_ztest(count, nobs, value=0.3)
print(count)
print(z)
print(p)""",
    [
        sub("클릭 수(count)는? (정수)", cnt, "관측도수", "df['click'].sum()", ".sum()", f"0/1 변수의 합 = 클릭 수 = {cnt}.", dec=0),
        sub("z 통계량을 구하시오. (소수점 셋째 자리까지)", z, "검정통계량", "z", "=z|z_stat|stat|zstat|X[0]|zscore", f"표본비율 {cnt / 200:.3f}, z = {z:.3f}."),
        sub("p-value를 구하시오. (소수점 넷째 자리까지)", p, "p-value", "p", "=p|pval|p_value|pvalue|X[1]", f"p-value = {p:.4f}.", dec=4),
    ])

z, p = proportions_ztest(18, 250, value=0.05)
df = pd.DataFrame({"항목": ["검사 제품 수", "불량 제품 수"], "값": [250, 18]})
add("T13-3", "T13", 2, "불량률 5% 검정",
    "제품 250개를 검사한 결과 18개가 불량이었다. 불량률이 5%와 다른지 양측 비율 z검정을 수행하시오.",
    df, "proportions_ztest",
    """from statsmodels.stats.proportion import proportions_ztest
z, p = proportions_ztest(18, 250, value=0.05)
print(z)
print(p)
print(p < 0.05)""",
    [
        sub("z 통계량을 구하시오. (소수점 셋째 자리까지)", z, "검정통계량", "z", "=z|z_stat|stat|zstat|X[0]|zscore",
            f"표본비율 = 18/250 = 0.072. z = {z:.3f}.",
            traps=[((0.072 - 0.05) / np.sqrt(0.05 * 0.95 / 250), "귀무비율로 표준오차를 계산한 값입니다. 기본 옵션은 표본비율 사용.")]),
        sub("p-value를 구하시오. (소수점 넷째 자리까지)", p, "p-value", "p", "=p|pval|p_value|pvalue|X[1]", f"p-value = {p:.4f}.", dec=4),
        reject_sub(p, code="p < 0.05", accept="<0.05"),
    ])

# ------------------------------------------------------------------ T14 Mann-Whitney
g = rng(1401)
A = np.round(g.normal(72, 9, 12)).astype(int)
B = np.round(g.normal(64, 9, 13)).astype(int)
df = pd.DataFrame({"group": ["A"] * 12 + ["B"] * 13, "score": np.concatenate([A, B])})
a = df[df["group"] == "A"]["score"].dropna()
b = df[df["group"] == "B"]["score"].dropna()
res = stats.mannwhitneyu(a, b, alternative="two-sided")
add("T14-1", "T14", 1, "두 집단 점수 (비모수)",
    "A 12명, B 13명의 점수(score)이다. 정규성을 가정하지 않고 Mann-Whitney U 검정(양측)으로 두 집단 분포 차이를 검정하시오. (A를 첫 번째로)",
    df, "mannwhitneyu",
    """from scipy.stats import mannwhitneyu
a = df[df['group']=='A']['score'].dropna()
b = df[df['group']=='B']['score'].dropna()
result = mannwhitneyu(a, b, alternative='two-sided')
print(result.statistic)   # U (첫 번째 표본 기준)
print(result.pvalue)""",
    [
        sub("U 통계량을 구하시오. (소수점 첫째 자리까지)", res.statistic, "검정통계량", "result.statistic", STAT,
            f"U = {res.statistic:.1f}. scipy는 첫 번째 표본(a)의 U를 돌려준다.", dec=1,
            traps=[(len(a) * len(b) - res.statistic, "두 번째 표본 기준 U(n1 x n2 - U)입니다. a, b 순서를 확인하세요.")]),
        sub("p-value를 구하시오. (소수점 넷째 자리까지)", res.pvalue, "p-value", "result.pvalue", PVAL, f"p-value = {res.pvalue:.4f}.", dec=4),
        reject_sub(res.pvalue),
    ])

g = rng(1402)
s1 = g.choice([1, 2, 3, 4, 5], size=20, p=[0.05, 0.1, 0.25, 0.35, 0.25])
s2 = g.choice([1, 2, 3, 4, 5], size=18, p=[0.15, 0.25, 0.3, 0.2, 0.1])
df = pd.DataFrame({"store": ["강남"] * 20 + ["홍대"] * 18, "rating": np.concatenate([s1, s2])})
a = df[df["store"] == "강남"]["rating"].dropna()
b = df[df["store"] == "홍대"]["rating"].dropna()
res = stats.mannwhitneyu(a, b, alternative="two-sided")
add("T14-2", "T14", 2, "매장별 만족도 (5점 척도)",
    "강남점 20명, 홍대점 18명의 만족도(rating, 1~5점 서열척도)이다. Mann-Whitney U 검정(양측)으로 두 매장의 만족도 차이를 검정하시오. (강남을 첫 번째로)",
    df, "mannwhitneyu",
    """from scipy.stats import mannwhitneyu
a = df[df['store']=='강남']['rating'].dropna()
b = df[df['store']=='홍대']['rating'].dropna()
result = mannwhitneyu(a, b, alternative='two-sided')
print(result.statistic)
print(result.pvalue)""",
    [
        sub("U 통계량을 구하시오. (소수점 첫째 자리까지)", res.statistic, "검정통계량", "result.statistic", STAT, f"U = {res.statistic:.1f}. 동점이 많아도 그대로 계산된다.", dec=1,
            traps=[(len(a) * len(b) - res.statistic, "홍대 기준 U입니다. 강남을 첫 번째 인자로 넣으세요.")]),
        sub("p-value를 구하시오. (소수점 넷째 자리까지)", res.pvalue, "p-value", "result.pvalue", PVAL, f"p-value = {res.pvalue:.4f}.", dec=4),
        reject_sub(res.pvalue),
    ])

g = rng(1403)
w1 = np.round(g.exponential(8, 15) + 2, 1)
w2 = np.round(g.exponential(14, 15) + 2, 1)
df = pd.DataFrame({"counter": ["무인"] * 15 + ["유인"] * 15, "wait_min": np.concatenate([w1, w2])})
df["wait_min"] = with_nan(df["wait_min"], [3, 20])
a = df[df["counter"] == "무인"]["wait_min"].dropna()
b = df[df["counter"] == "유인"]["wait_min"].dropna()
res = stats.mannwhitneyu(a, b, alternative="two-sided")
add("T14-3", "T14", 2, "무인 vs 유인 계산대 대기시간",
    "무인·유인 계산대의 대기시간(wait_min, 분)이며 분포가 오른쪽으로 치우쳐 있고 결측이 있다. 결측 제거 후 중앙값 차이와 Mann-Whitney U 검정(양측) 결과를 구하시오. (무인을 첫 번째로)",
    df, "mannwhitneyu",
    """from scipy.stats import mannwhitneyu
a = df[df['counter']=='무인']['wait_min'].dropna()
b = df[df['counter']=='유인']['wait_min'].dropna()
print(a.median() - b.median())
result = mannwhitneyu(a, b, alternative='two-sided')
print(result.statistic)
print(result.pvalue)""",
    [
        sub("중앙값 차이(무인 - 유인)를 구하시오. (소수점 둘째 자리까지)", a.median() - b.median(), "평균 차이", "a.median() - b.median()", ".median()-&&.median()",
            f"{a.median():.2f} - {b.median():.2f} = {a.median() - b.median():.2f}분.", dec=2,
            traps=[(a.mean() - b.mean(), "평균 차이를 계산했습니다. 중앙값(median)을 물었습니다.")]),
        sub("U 통계량을 구하시오. (소수점 첫째 자리까지)", res.statistic, "검정통계량", "result.statistic", STAT, f"U = {res.statistic:.1f}.", dec=1),
        sub("p-value를 구하시오. (소수점 넷째 자리까지)", res.pvalue, "p-value", "result.pvalue", PVAL, f"p-value = {res.pvalue:.4f}.", dec=4),
    ])


if __name__ == "__main__":
    nsub = sum(len(p["subs"]) for p in PROBLEMS)
    out = os.path.join(HERE, "data.js")
    with open(out, "w", encoding="utf-8") as fp:
        fp.write("// 자동 생성 파일: generate_problems.py 로 다시 만드세요. 정답은 scipy/statsmodels 계산값입니다.\n")
        fp.write("window.PROBLEMS = ")
        json.dump(PROBLEMS, fp, ensure_ascii=False, separators=(",", ":"))
        fp.write(";\n")
    import scipy, statsmodels
    print(f"problems={len(PROBLEMS)} subs={nsub} scipy={scipy.__version__} statsmodels={statsmodels.__version__}")
    for p in PROBLEMS:
        print(p["id"], " | ".join(f"{s['ans']:.4g}" if s["kind"] == "num" else str(s["ans"]) for s in p["subs"]))
