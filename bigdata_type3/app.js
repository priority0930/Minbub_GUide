/* 빅분기 TYPE 3 — 10일 완성 : 앱 로직 (의존성 없음) */
(function () {
  'use strict';
  const TPL = window.TEMPLATES;
  const PROBS = window.PROBLEMS;
  const TMAP = Object.fromEntries(TPL.map(t => [t.id, t]));
  const PMAP = Object.fromEntries(PROBS.map(p => [p.id, p]));
  const SUBMAP = {};
  PROBS.forEach(p => p.subs.forEach((s, i) => { SUBMAP[s.id] = { sub: s, prob: p, no: i + 1 }; }));
  const byTpl = id => PROBS.filter(p => p.tpl === id);
  const KEY = 'bbk-type3-v1';
  const MOCK_PTS = 5; // 가상 배점: 소문항당 5점, 2문제 x 3소문항 = 30점

  // ---------------------------------------------------------------- state
  const DAY = 86400000;
  const today0 = () => { const d = new Date(); d.setHours(0, 0, 0, 0); return d; };
  const iso = d => { const z = new Date(d); return z.getFullYear() + '-' + String(z.getMonth() + 1).padStart(2, '0') + '-' + String(z.getDate()).padStart(2, '0'); };
  function fresh() {
    return {
      examDate: iso(today0().getTime() + 10 * DAY),
      subs: {}, funcs: {}, codes: {}, blanks: {}, quizB: {}, quizD: {}, wrong: {},
      stats: { tries: 0, correct: 0 }, mocks: [], mock: null, dayDone: {}, drafts: {},
      ui: { view: 'home', tpl: 'T01', mode: 'E', pi: 0, bIdx: 0, cardRev: false, retry: null },
    };
  }
  let S;
  try { S = Object.assign(fresh(), JSON.parse(localStorage.getItem(KEY) || 'null') || {}); } catch (e) { S = fresh(); }
  S.ui = Object.assign(fresh().ui, S.ui || {});
  let saveTimer = null;
  function save() { clearTimeout(saveTimer); saveTimer = setTimeout(() => { try { localStorage.setItem(KEY, JSON.stringify(S)); } catch (e) { /* 저장 불가 환경 */ } }, 120); }
  const T = { inputs: {}, choice: {}, flips: {}, blankRes: {}, blankShow: {}, search: '', listOpen: false, pyOut: {}, confirmReset: false };

  // ---------------------------------------------------------------- helpers
  const $ = s => document.querySelector(s);
  const esc = s => String(s == null ? '' : s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const pct = (a, b) => b ? Math.round(100 * a / b) : 0;
  const stars = n => '★'.repeat(n) + '☆'.repeat(3 - n);
  function toast(msg) { const t = $('#toast'); t.textContent = msg; t.hidden = false; clearTimeout(toast.h); toast.h = setTimeout(() => { t.hidden = true; }, 1900); }
  function hl(code) {
    return esc(code).replace(/\b(from|import|as|print|True|False|None)\b/g, '<span class="k">$1</span>');
  }
  function fmtAns(s) {
    if (s.kind !== 'num') return s.ans === '채택' ? '채택 (귀무가설 기각 못함)' : String(s.ans);
    const v = Number(s.ans);
    let t = v.toFixed(s.dec);
    if (s.dec > 0 && v !== 0 && Math.abs(v) < 0.001) t += '  (= ' + v.toExponential(3) + ')';
    return t;
  }
  const tolOf = s => s.dec === 0 ? 1e-9 : Math.pow(10, -s.dec) + 1e-12;
  const tolText = s => s.dec === 0 ? '정수 정확히' : '허용 오차 ±' + Math.pow(10, -s.dec).toFixed(s.dec);
  function parseNum(str) {
    const t = String(str || '').trim().replace(/,/g, '').replace(/^\+/, '');
    if (!t || !/^-?(\d+\.?\d*|\.\d+)(e-?\d+)?$/i.test(t)) return NaN;
    return Number(t);
  }
  // 코드 정규화: print() 제거, 공백 제거, 따옴표 통일, 결과 변수명을 X로 통일
  const ATTR = 'statistic|pvalue|params|pvalues|rsquared_adj|rsquared|fvalue|f_pvalue|conf_int|predict|tvalues|bse|expected_freq|dof|correlation';
  function normCode(s) {
    s = String(s || '').trim();
    const m = s.match(/^print\(([\s\S]*)\)\s*$/);
    if (m) s = m[1];
    s = s.replace(/\s+/g, '').replace(/"/g, "'");
    s = s.replace(new RegExp('\\b[A-Za-z_]\\w*(?=\\.(' + ATTR + ')\\b)', 'g'), 'X');
    s = s.replace(/\b[A-Za-z_]\w*(?=\[[0-3]\])/g, 'X');
    return s;
  }
  function codeOk(input, accept) {
    const n = normCode(input);
    if (!n) return false;
    if (accept.startsWith('=')) return accept.slice(1).split('|').some(c => normCode(c) === n);
    return accept.split('&&').every(tok => n.includes(normCode(tok)));
  }
  function funcOk(input, func) {
    let t = String(input || '').trim().replace(/\(.*$/s, '').replace(/\s+/g, '');
    t = t.split('.').pop().toLowerCase();
    return t === func.toLowerCase();
  }
  function csvOf(p) {
    const q = v => { if (v == null) return ''; const s = String(v); return /[",\n]/.test(s) ? '"' + s.replace(/"/g, '""') + '"' : s; };
    return [p.columns.map(q).join(',')].concat(p.rows.map(r => r.map(q).join(','))).join('\n') + '\n';
  }
  function copyText(text, okMsg) {
    try {
      navigator.clipboard.writeText(text).then(() => toast(okMsg || '복사했습니다'), () => fallbackCopy(text, okMsg));
    } catch (e) { fallbackCopy(text, okMsg); }
  }
  function fallbackCopy(text, okMsg) {
    const ta = document.createElement('textarea'); ta.value = text; document.body.appendChild(ta); ta.select();
    let ok = false; try { ok = document.execCommand('copy'); } catch (e) { ok = false; }
    ta.remove(); toast(ok ? (okMsg || '복사했습니다') : '복사가 막혀 있습니다. 직접 선택해서 복사하세요.');
  }
  function shuffleSeed(arr, seed) {
    const a = arr.slice(); let x = seed * 9301 + 49297;
    for (let i = a.length - 1; i > 0; i--) { x = (x * 9301 + 49297) % 233280; const j = Math.floor(x / 233280 * (i + 1)); [a[i], a[j]] = [a[j], a[i]]; }
    return a;
  }

  // ---------------------------------------------------------------- metrics
  const subState = id => S.subs[id] || (S.subs[id] = { tries: 0, ok: false, lvl: 0, revealed: false, first: null, why: '', last: '' });
  function tplMastery(id) {
    const subs = byTpl(id).flatMap(p => p.subs);
    const ok = subs.filter(s => S.subs[s.id] && S.subs[s.id].ok).length;
    return { ok, total: subs.length, p: pct(ok, subs.length) };
  }
  function daysLeft() { return Math.round((new Date(S.examDate + 'T00:00:00') - today0()) / DAY); }
  function dayNum() { const d = daysLeft(); return Math.max(1, Math.min(10, 11 - d)); }
  function firstTry() {
    const vals = Object.values(S.subs).filter(x => x.first !== null && x.first !== undefined);
    return { n: vals.length, ok: vals.filter(x => x.first).length };
  }
  function estScore() { const f = firstTry(); return f.n ? Math.round(30 * f.ok / f.n) : null; }
  function bestMock() { return S.mocks.length ? Math.max(...S.mocks.map(m => m.score)) : null; }
  const tenDone = () => (bestMock() || 0) >= 10;
  function dayProgress(pl) {
    if (pl.day === 9) return { a: Math.min(S.mocks.length, 2), b: 2, txt: '모의고사 ' + S.mocks.length + '회 (목표 2회)' };
    if (pl.day === 10) {
      const w = openWrong().length; const bl = TPL.filter(t => S.blanks[t.id] && S.blanks[t.id].done).length;
      return { a: bl, b: 14, txt: '빈칸 완주 ' + bl + '/14, 남은 오답 ' + w + '개' };
    }
    let a = 0, b = 0; pl.tpls.forEach(t => { const m = tplMastery(t); a += m.ok; b += m.total; });
    return { a, b, txt: '소문항 정답 ' + a + '/' + b };
  }
  const isDayDone = pl => !!S.dayDone[pl.day] || (dayProgress(pl).b > 0 && dayProgress(pl).a >= dayProgress(pl).b);
  function openWrong() { return Object.entries(S.wrong).filter(([, v]) => !v.resolved).sort((a, b) => b[1].at - a[1].at); }
  function markWrong(key, extra) { const w = S.wrong[key] || { n: 0 }; S.wrong[key] = Object.assign(w, { n: w.n + 1, at: Date.now(), resolved: false }, extra || {}); }
  function resolveWrong(key) { if (S.wrong[key]) S.wrong[key].resolved = true; }
  function tally(ok) { S.stats.tries++; if (ok) S.stats.correct++; }

  // ---------------------------------------------------------------- top bar
  function renderTop() {
    const dl = daysLeft(); const pl = window.PLAN[dayNum() - 1]; const dp = dayProgress(pl);
    const acc = S.stats.tries ? pct(S.stats.correct, S.stats.tries) + '%' : '-';
    const est = estScore(); const bm = bestMock();
    const nav = [['home', '홈'], ['study', '학습'], ['mock', '모의고사'], ['wrong', '오답노트'], ['plan', '10일 계획'], ['project', '10점 프로젝트']];
    $('#top').innerHTML = `
      <button class="brand" data-act="go" data-v="home" aria-label="홈으로"><b>빅분기 TYPE 3</b><span>10일 완성</span></button>
      <nav class="nav">${nav.map(([v, l]) => `<button data-act="go" data-v="${v}" class="${S.ui.view === v ? 'on' : ''}">${l}${v === 'wrong' && openWrong().length ? ' <span class="chip bad">' + openWrong().length + '</span>' : ''}</button>`).join('')}</nav>
      <div class="kpis">
        <div class="kpi"><small>시험까지</small><b>${dl > 0 ? 'D-' + dl : dl === 0 ? 'D-DAY' : 'D+' + (-dl)}</b></div>
        <div class="kpi goal"><small>오늘 목표 · Day ${pl.day}</small><b>${esc(pl.title)} <span class="muted small">${esc(dp.txt)}</span></b></div>
        <div class="kpi"><small>누적 정답률</small><b>${acc}</b></div>
        <div class="kpi"><small>모의 최고 / 예상</small><b>${bm == null ? '-' : bm}/${est == null ? '-' : est}<span class="muted small"> /30</span></b></div>
        <span class="badge10 ${tenDone() ? 'on' : ''}">${tenDone() ? '10점 달성' : '10점 도전 중'}</span>
        <button class="iconbtn" data-act="settings" aria-label="설정">설정</button>
      </div>`;
  }

  // ---------------------------------------------------------------- views
  function render() {
    renderTop();
    const v = S.ui.view;
    const fn = { home: vHome, study: vStudy, plan: vPlan, mock: vMock, wrong: vWrong, project: vProject }[v] || vHome;
    $('#view').innerHTML = fn();
    afterRender();
    save();
  }
  function go(view, extra) {
    Object.assign(S.ui, extra || {}); S.ui.view = view;
    try { if (location.hash !== '#' + view) history.replaceState(null, '', '#' + view); } catch (e) { /* ignore */ }
    render(); window.scrollTo(0, 0);
  }

  // ---------- home
  function vHome() {
    const dl = daysLeft(); const pl = window.PLAN[dayNum() - 1]; const dp = dayProgress(pl);
    const f = firstTry(); const est = estScore(); const bm = bestMock();
    const solved = Object.values(S.subs).filter(x => x.ok).length; const totalSubs = Object.keys(SUBMAP).length;
    return `
    <section class="hero">
      <div class="panel hero-main">
        <div class="row" style="justify-content:space-between;align-items:flex-end">
          <div><div class="label">작업형 3유형 · 통계 분석</div><h1>빅분기 TYPE 3 — 10일 완성</h1></div>
          <div class="dday">${dl > 0 ? 'D-' + dl : dl === 0 ? 'D-DAY' : 'D+' + (-dl)}</div>
        </div>
        <p class="muted" style="margin:0">14개 통계 템플릿을 <b>함수 이름 → 출력 코드 → 수치 답</b> 순서로 직접 입력하며 익힙니다. 문제 ${PROBS.length}개, 소문항 ${totalSubs}개의 정답은 모두 scipy·statsmodels로 미리 계산해 검증한 값입니다.</p>
        <div class="hero-cta">
          <button class="cta pri" data-act="today"><b>오늘의 학습 시작</b><span>Day ${pl.day} · ${esc(pl.title)}<br>${esc(dp.txt)}</span></button>
          <button class="cta" data-act="go" data-v="project"><b>10점 확보 프로젝트</b><span>t검정 3종 → 카이제곱 2종 → OLS → 로지스틱<br>${tenDone() ? '모의고사 10점 달성 완료' : '핵심 7유형으로 가상 30점 중 10점 확보'}</span></button>
        </div>
      </div>
      <div class="panel pad stack">
        <div class="label">내 진행 상황</div>
        <div class="statgrid">
          <div class="stat"><small>누적 정답률</small><b>${S.stats.tries ? pct(S.stats.correct, S.stats.tries) + '%' : '-'}</b><div class="muted small">${S.stats.correct}/${S.stats.tries} 채점</div></div>
          <div class="stat"><small>푼 소문항</small><b>${solved}<span class="muted small">/${totalSubs}</span></b><div class="bar ok"><i style="width:${pct(solved, totalSubs)}%"></i></div></div>
          <div class="stat"><small>모의고사 최고</small><b>${bm == null ? '-' : bm}<span class="muted small">/30</span></b><div class="muted small">${S.mocks.length}회 응시</div></div>
          <div class="stat"><small>예상 점수 (연습)</small><b>${est == null ? '-' : est}<span class="muted small">/30</span></b><div class="muted small">첫 시도 ${f.ok}/${f.n}</div></div>
        </div>
        <p class="disclaim" style="margin:0">모의고사·예상 점수는 이 앱의 가상 배점(소문항당 5점, 30점 만점)입니다. 실제 시험의 3유형 배점과 문항 구성은 회차마다 다를 수 있습니다.</p>
      </div>
    </section>
    <div class="section-h"><h2>10일 학습 계획</h2><button class="btn sm" data-act="go" data-v="plan">전체 보기</button></div>
    ${daysGrid()}
    <div class="section-h"><h2>14개 템플릿</h2><span class="muted small">눌러서 바로 학습</span></div>
    <div class="path">${TPL.map(t => { const m = tplMastery(t.id); return `
      <button class="panel pnode" data-act="tpl" data-v="${t.id}" style="text-align:left">
        <span class="ord">${t.id} · Day ${t.day} ${t.core ? '<span class="chip acc">핵심</span>' : ''}</span>
        <b>${esc(t.name)}</b><code class="small">${esc(t.func)}</code>
        <span class="row small muted"><span class="stars" aria-label="난이도">${stars(t.level)}</span> 정답 ${m.ok}/${m.total}</span>
        <div class="bar ok"><i style="width:${m.p}%"></i></div>
      </button>`; }).join('')}</div>`;
  }
  function daysGrid() {
    const dn = dayNum();
    return `<div class="days">${window.PLAN.map(pl => { const dp = dayProgress(pl); const done = isDayDone(pl); return `
      <button class="day ${pl.day === dn ? 'today' : ''} ${done ? 'done' : ''}" data-act="day" data-v="${pl.day}">
        <span class="dn">DAY ${pl.day}${pl.day === dn ? ' · 오늘' : ''}${done ? ' · 완료' : ''}</span>
        <b>${esc(pl.title)}</b>
        <span class="small muted">${pl.tpls.length ? pl.tpls.join(' · ') : (pl.day === 9 ? '모의고사' : '총복습')}</span>
        <div class="bar ok"><i style="width:${pct(dp.a, dp.b)}%"></i></div>
      </button>`; }).join('')}</div>`;
  }

  // ---------- plan
  function vPlan() {
    return `<div class="section-h" style="margin-top:0"><h2>10일 학습 계획</h2>
      <label class="row small">시험일 <input type="date" id="examDate" value="${esc(S.examDate)}" style="width:auto"></label></div>
      ${daysGrid()}
      <div class="stack" style="margin-top:16px">${window.PLAN.map(pl => { const dp = dayProgress(pl); return `
        <div class="panel pad row" style="justify-content:space-between">
          <div class="stack" style="gap:4px;min-width:0;flex:1">
            <span class="label">Day ${pl.day}${pl.day === dayNum() ? ' · 오늘' : ''}</span>
            <b>${esc(pl.title)}</b>
            <span class="small muted">${esc(pl.tip)} · ${esc(dp.txt)}</span>
          </div>
          <div class="row">
            ${pl.tpls.map(t => `<button class="btn sm" data-act="tpl" data-v="${t}">${t} ${esc(TMAP[t].name)}</button>`).join('')}
            ${pl.day === 9 ? '<button class="btn sm pri" data-act="go" data-v="mock">모의고사</button>' : ''}
            ${pl.day === 10 ? '<button class="btn sm pri" data-act="retryAll">오답 재학습</button><button class="btn sm" data-act="tplmode" data-v="T01" data-m="C">빈칸 암기</button>' : ''}
            <button class="btn sm ${S.dayDone[pl.day] ? 'pri' : ''}" data-act="dayDone" data-v="${pl.day}">${S.dayDone[pl.day] ? '완료 표시됨' : '완료 표시'}</button>
          </div>
        </div>`; }).join('')}</div>`;
  }

  // ---------- project
  function vProject() {
    const bm = bestMock();
    return `<div class="section-h" style="margin-top:0"><h2>10점 확보 프로젝트</h2><span class="badge10 ${tenDone() ? 'on' : ''}">${tenDone() ? '목표 달성: 모의고사 ' + bm + '점' : '목표: 모의고사 10점 이상'}</span></div>
    <div class="grid2">
      <div class="panel pad stack">
        <b>전략</b>
        <p style="margin:0">3유형 점수는 <b>유형 선택 → 함수 → 출력 속성</b>을 정확히 고르는 데서 나옵니다. 14개를 순서대로 다 외우기보다 출제 빈도가 높은 7개를 먼저 완성하세요.</p>
        <ol style="margin:0;padding-left:20px" class="small">
          <li>t검정 3종 (ttest_1samp, ttest_ind, ttest_rel)</li>
          <li>카이제곱 2종 (chi2_contingency, chisquare)</li>
          <li>OLS 선형회귀 (params, pvalues, rsquared, predict)</li>
          <li>로지스틱 회귀 (np.exp(params) = 오즈비)</li>
        </ol>
        <p class="disclaim" style="margin:0">이 앱의 모의고사는 가상 배점(2문제 x 소문항 3개 x 5점 = 30점)입니다. 소문항 2개를 맞히면 10점이 됩니다. 실제 시험 배점과는 별개입니다.</p>
        <div class="row"><button class="btn pri" data-act="go" data-v="mock">모의고사 응시</button><button class="btn" data-act="today">오늘의 학습 시작</button></div>
      </div>
      <div class="panel pad stack">
        <b>모의고사 기록</b>
        ${S.mocks.length ? `<div class="wlist">${S.mocks.slice(-6).reverse().map(m => `<div class="witem"><span class="t">${esc(m.date)} · ${esc(m.items.join(', '))}</span><b class="mono">${m.score}/30</b></div>`).join('')}</div>` : '<div class="empty">아직 응시 기록이 없습니다. 핵심 유형을 2~3개 익힌 뒤 응시해 보세요.</div>'}
      </div>
    </div>
    <div class="section-h"><h2>우선순위 경로</h2><span class="muted small">각 유형: 개념 확인 → 빈칸 완주 → 실전 3문제</span></div>
    <div class="path">${window.PRIORITY.map((id, i) => { const t = TMAP[id]; const m = tplMastery(id); const bl = S.blanks[id] && S.blanks[id].done;
      const probsDone = byTpl(id).filter(p => p.subs.every(s => S.subs[s.id] && S.subs[s.id].ok)).length; return `
      <div class="panel pnode">
        <span class="ord">STEP ${i + 1} · ${id}</span><b>${esc(t.name)}</b>
        <div class="checks">
          <span class="${bl ? 'y' : 'n'}">${bl ? '✓' : '○'} 코드 빈칸 완주</span>
          <span class="${probsDone >= 3 ? 'y' : 'n'}">${probsDone >= 3 ? '✓' : '○'} 실전 문제 ${probsDone}/3 완벽</span>
          <span class="${m.p >= 80 ? 'y' : 'n'}">${m.p >= 80 ? '✓' : '○'} 소문항 정답률 ${m.p}%</span>
        </div>
        <div class="bar ok"><i style="width:${m.p}%"></i></div>
        <div class="row"><button class="btn sm" data-act="tplmode" data-v="${id}" data-m="C">빈칸</button><button class="btn sm pri" data-act="tplmode" data-v="${id}" data-m="E">실전</button></div>
      </div>`; }).join('')}</div>`;
  }

  // ---------- study
  function vStudy() {
    const t = TMAP[S.ui.tpl] || TPL[0]; const mode = S.ui.mode;
    const modes = [['A', '개념'], ['B', '방법 선택'], ['C', '코드 빈칸'], ['D', '해석 퀴즈'], ['E', '실전 문제'], ['F', '모의고사'], ['G', '오답 재학습']];
    let center = '', right = '';
    if (mode === 'A') [center, right] = modeA(t);
    else if (mode === 'B') [center, right] = modeB(t);
    else if (mode === 'C') [center, right] = modeC(t);
    else if (mode === 'D') [center, right] = modeD(t);
    else [center, right] = modeE(t);
    return `
    ${retryBanner()}
    <div class="study">
      <aside class="panel side">${sidebar()}</aside>
      <section class="center">
        <div class="panel">
          <div class="modes" role="tablist">${modes.map(([k, l]) => `<button role="tab" data-act="mode" data-v="${k}" class="${mode === k ? 'on' : ''}"><b>${k}</b>${l}</button>`).join('')}</div>
          <div class="pad stack">${center}</div>
        </div>
      </section>
      <section class="right">${right}</section>
    </div>
    ${bottom(t)}`;
  }
  function retryBanner() {
    const r = S.ui.retry; if (!r || !r.queue.length) return '';
    return `<div class="banner"><b>오답 재학습</b><span>${r.pos + 1} / ${r.queue.length}</span>
      <button class="btn sm" data-act="retryNext">다음 오답</button><button class="btn sm" data-act="retryStop">종료</button></div>`;
  }
  function sidebar() {
    const q = T.search.trim().toLowerCase();
    const items = TPL.map(t => {
      let hits = [];
      if (q) {
        const hay = (t.id + ' ' + t.name + ' ' + t.func + ' ' + t.keys + ' ' + t.imp).toLowerCase();
        hits = t.outputs.filter(o => (o[0] + ' ' + o[1]).toLowerCase().includes(q));
        if (!hay.includes(q) && !hits.length) return '';
      }
      const m = tplMastery(t.id);
      return `<button class="titem ${S.ui.tpl === t.id ? 'on' : ''}" data-act="tpl" data-v="${t.id}">
          <span class="tid">${t.id}</span><span class="tn">${esc(t.name)}</span>
          <span class="tm"><span class="stars">${stars(t.level)}</span><code>${esc(t.func)}</code><span class="bar ok"><i style="width:${m.p}%"></i></span></span>
        </button>${hits.map(h => `<div class="hit">${esc(h[0])} → ${esc(h[1])}</div>`).join('')}`;
    }).join('');
    return `<label class="label" for="search">함수·개념 검색</label>
      <input type="text" id="search" placeholder="예: 오즈비, pvalue, chi2" value="${esc(T.search)}" autocomplete="off" style="margin-top:6px">
      <button class="btn sm ghost" data-act="toggleList" style="margin-top:8px;display:none" id="listToggle">유형 목록 ${T.listOpen ? '접기' : '펼치기'}</button>
      <div class="tlist ${T.listOpen ? '' : 'collapsed'}" id="tlist">${items || '<div class="empty">검색 결과가 없습니다.</div>'}</div>`;
  }
  function bottom(t) {
    const cards = t.outputs.map(o => [o[0], o[1]]).concat(window.CARDS);
    const rev = S.ui.cardRev;
    const ow = openWrong().slice(0, 5);
    return `<section class="bottom">
      <div class="panel pad">
        <div class="row" style="justify-content:space-between"><b>코드 암기 카드</b>
          <button class="btn sm" data-act="cardRev">${rev ? '의미 → 코드' : '코드 → 의미'}</button></div>
        <div class="cards">${cards.map((c, i) => { const f = rev ? [c[1], c[0]] : c; return `
          <button class="fcard ${T.flips[i] ? 'flip' : ''}" data-act="flip" data-v="${i}" aria-label="카드 뒤집기">
            <div class="in"><div class="face ${rev ? 'back' : 'front'}" style="transform:none">${esc(f[0])}</div>
            <div class="face ${rev ? 'front' : 'back'}" style="transform:rotateY(180deg)">${esc(f[1])}</div></div>
          </button>`; }).join('')}</div>
      </div>
      <div class="panel pad">
        <div class="row" style="justify-content:space-between"><b>오답 복습</b>${ow.length ? '<button class="btn sm pri" data-act="retryAll">틀린 문제만 재학습</button>' : ''}</div>
        <div class="wlist" style="margin-top:8px">${ow.length ? ow.map(([k, w]) => wrongRow(k, w, true)).join('') : '<div class="empty">오답이 없습니다.</div>'}</div>
      </div>
    </section>`;
  }

  // ---------- mode A : 개념
  function modeA(t) {
    const probs = byTpl(t.id);
    const center = `
      <div class="row" style="justify-content:space-between"><div><span class="label">${t.id} · Day ${t.day}</span><h2>${esc(t.name)}</h2></div><span class="stars">${stars(t.level)}</span></div>
      <p style="margin:0"><b>언제 쓰나</b> ${esc(t.when)}</p>
      <div class="grid2"><div class="note"><b>귀무가설</b><br>${esc(t.h0)}</div><div class="note" style="background:var(--accent-soft)"><b style="color:var(--accent)">대립가설</b><br>${esc(t.h1)}</div></div>
      <div class="row" style="justify-content:space-between"><b>필수 템플릿</b><button class="btn sm" data-act="copyTpl">코드 복사</button></div>
      <pre class="code">${hl(t.code)}</pre>
      <b>자주 하는 실수</b>
      <ul style="margin:0;padding-left:20px">${t.pitfalls.map(x => `<li>${esc(x)}</li>`).join('')}</ul>
      <div class="row"><button class="btn" data-act="mode" data-v="C">빈칸 암기로</button><button class="btn pri" data-act="mode" data-v="E">실전 문제로</button></div>`;
    const right = `<div class="panel pad stack">
      <b>출력 속성 → 답</b>
      <table class="kv">${t.outputs.map(o => `<tr><td>${esc(o[0])}</td><td>${esc(o[1])}</td></tr>`).join('')}</table>
      <b>이 유형의 소문항 패턴</b>
      <div class="row">${[...new Set(probs.flatMap(p => p.subs.map(s => s.pattern)))].map(x => `<span class="chip acc">${esc(x)}</span>`).join('')}</div>
      <p class="disclaim" style="margin:0">p &lt; 0.05 이면 5% 유의수준에서 귀무가설을 기각합니다. 기각하지 못했다고 귀무가설이 참임이 증명되는 것은 아닙니다.</p>
    </div>`;
    return [center, right];
  }

  // ---------- mode B : 방법 선택 퀴즈
  function modeB() {
    const Q = window.METHOD_QUIZ; const i = ((S.ui.bIdx % Q.length) + Q.length) % Q.length;
    const [txt, ans] = Q[i];
    const opts = shuffleSeed([ans].concat(window.CONFUSE[ans]), i + 7);
    const st = S.quizB[i];
    const answered = T.inputs['B' + i];
    const center = `
      <div class="row" style="justify-content:space-between"><span class="label">B. 통계 분석 방법 선택 · ${i + 1} / ${Q.length}</span>
        <span class="chip">${Object.values(S.quizB).filter(Boolean).length} 정답 / ${Object.keys(S.quizB).length} 응답</span></div>
      <div class="qcard">
        <p class="story" style="margin:0">${esc(txt)}</p>
        <b>어떤 분석을 써야 할까?</b>
        <div class="opts">${opts.map(o => { let c = ''; if (answered) { if (o === ans) c = 'ok'; else if (o === answered) c = 'bad'; } return `
          <button class="opt ${c}" data-act="pickB" data-v="${o}" ${answered ? 'disabled' : ''}><b class="mono">${o}</b> ${esc(TMAP[o].name)} <span class="muted small mono">${esc(TMAP[o].func)}</span></button>`; }).join('')}</div>
        ${answered ? `<div class="fb ${answered === ans ? 'ok' : 'bad'}">${answered === ans ? '정답입니다.' : '오답입니다.'} ${esc(TMAP[ans].name)}: ${esc(TMAP[ans].when)}</div>` : ''}
        <div class="row"><button class="btn" data-act="bMove" data-v="-1">이전</button><button class="btn pri" data-act="bMove" data-v="1">다음 문제</button></div>
      </div>`;
    const right = `<div class="panel pad stack"><b>선택 기준 요약</b>
      <table class="kv">
        <tr><td>평균 1집단</td><td>ttest_1samp</td></tr><tr><td>평균 독립 2집단</td><td>ttest_ind</td></tr>
        <tr><td>평균 전후(짝)</td><td>ttest_rel</td></tr><tr><td>평균 3집단+</td><td>f_oneway</td></tr>
        <tr><td>범주 x 범주</td><td>chi2_contingency</td></tr><tr><td>범주 1개 vs 기대</td><td>chisquare</td></tr>
        <tr><td>연속 x 연속</td><td>pearsonr / spearmanr</td></tr><tr><td>연속 y 예측</td><td>smf.ols</td></tr>
        <tr><td>0/1 y 예측</td><td>smf.logit</td></tr><tr><td>정규성 / 등분산</td><td>shapiro / levene</td></tr>
        <tr><td>비율 1개</td><td>proportions_ztest</td></tr><tr><td>비정규 2집단</td><td>mannwhitneyu</td></tr>
      </table></div>`;
    return [center, right];
  }

  // ---------- mode C : 코드 빈칸
  function blankParts(t) {
    const code = t.code; const parts = []; let pos = 0;
    t.blanks.forEach((b, bi) => {
      const re = new RegExp('(?<![A-Za-z0-9_])' + b.replace(/[.*+?^${}()|[\]\\]/g, '\\$&') + '(?![A-Za-z0-9_])', 'g');
      re.lastIndex = pos; const m = re.exec(code);
      if (!m) return;
      parts.push(code.slice(pos, m.index)); parts.push({ bi, ans: b }); pos = m.index + b.length;
    });
    parts.push(code.slice(pos));
    return parts;
  }
  function modeC(t) {
    const parts = blankParts(t); const res = T.blankRes[t.id]; const show = T.blankShow[t.id];
    const nb = parts.filter(x => typeof x === 'object').length;
    const html = parts.map(x => {
      if (typeof x === 'string') return esc(x);
      const key = 'C' + t.id + '_' + x.bi; const val = show ? x.ans : (T.inputs[key] || '');
      const cls = res ? (res[x.bi] ? 'ok' : 'bad') : '';
      return `<input data-blank="${key}" class="${cls}" value="${esc(val)}" size="${Math.max(4, x.ans.length + 1)}" aria-label="빈칸 ${x.bi + 1}" autocomplete="off" spellcheck="false">`;
    }).join('');
    const okN = res ? Object.values(res).filter(Boolean).length : 0;
    const bs = S.blanks[t.id];
    const center = `
      <div class="row" style="justify-content:space-between"><span class="label">C. 코드 빈칸 암기 · ${t.id} ${esc(t.name)}</span><span class="chip">빈칸 ${nb}개</span></div>
      <p class="muted small" style="margin:0">함수 이름, 옵션, 출력 속성을 직접 채우세요. 대소문자와 철자까지 채점합니다.</p>
      <pre class="code blankcode">${html}</pre>
      ${res ? `<div class="fb ${okN === nb ? 'ok' : 'bad'}">${okN} / ${nb} 정답. ${okN === nb ? '완벽합니다. 다음 유형으로 넘어가세요.' : '빨간 칸을 고친 뒤 다시 채점하세요. 정답 보기로 확인할 수 있습니다.'}</div>` : ''}
      <div class="row"><button class="btn pri" data-act="gradeBlank">채점</button><button class="btn" data-act="showBlank">정답 보기</button><button class="btn ghost" data-act="clearBlank">다시 풀기</button></div>`;
    const right = `<div class="panel pad stack"><b>빈칸 기록</b>
      ${bs ? `<p style="margin:0">최고 ${bs.best}/${bs.total} · ${bs.done ? '<span class="chip ok">완주</span>' : '<span class="chip warn">미완주</span>'}</p>` : '<p class="muted" style="margin:0">아직 채점 기록이 없습니다.</p>'}
      <b>14개 유형 빈칸 현황</b>
      <div class="row">${TPL.map(x => { const b = S.blanks[x.id]; return `<button class="chip ${b && b.done ? 'ok' : b ? 'warn' : ''}" data-act="tplmode" data-v="${x.id}" data-m="C">${x.id}</button>`; }).join('')}</div>
      <p class="disclaim" style="margin:0">코드를 실제로 실행하지 않고, 정답 템플릿과 글자 단위로 비교해 채점합니다.</p></div>`;
    return [center, right];
  }

  // ---------- mode D : 출력값 해석 퀴즈
  function modeD(t) {
    const list = window.INTERP_QUIZ.map((q, i) => [q, i]).filter(([q]) => q[0] === t.id || q[0] === 'ALL');
    const center = `<div class="row" style="justify-content:space-between"><span class="label">D. 출력값 해석 · ${t.id} ${esc(t.name)} + 공통</span>
        <span class="chip">${list.filter(([, i]) => S.quizD[i]).length}/${list.length} 정답</span></div>
      ${list.map(([q, i]) => { const pick = T.inputs['D' + i]; const opts = shuffleSeed(q[3].map((o, k) => [o, k]), i + 3); return `
        <div class="qcard" style="border-top:1px solid var(--line);padding-top:12px">
          <div class="outbox">${esc(q[1])}</div>
          <b>${esc(q[2])}</b>
          <div class="opts">${opts.map(([o, k]) => { let c = ''; if (pick != null) { if (k === q[4]) c = 'ok'; else if (k === pick) c = 'bad'; } return `<button class="opt ${c}" data-act="pickD" data-v="${i}" data-k="${k}" ${pick != null ? 'disabled' : ''}>${esc(o)}</button>`; }).join('')}</div>
          ${pick != null ? `<div class="fb ${pick === q[4] ? 'ok' : 'bad'}">${esc(q[5])}</div>` : ''}
        </div>`; }).join('')}
      <div class="row"><button class="btn ghost" data-act="resetD">이 유형 다시 풀기</button></div>`;
    const right = `<div class="panel pad stack"><b>p-value 판단 규칙</b>
      <table class="kv"><tr><td>p &lt; 0.05</td><td>귀무가설 기각 (유의함)</td></tr><tr><td>p &gt;= 0.05</td><td>기각하지 못함 (채택)</td></tr>
      <tr><td>shapiro p &gt;= 0.05</td><td>정규성 만족</td></tr><tr><td>levene p &gt;= 0.05</td><td>등분산 → equal_var=True</td></tr>
      <tr><td>CI가 0 미포함</td><td>계수 유의</td></tr><tr><td>오즈비 &gt; 1</td><td>오즈 증가</td></tr></table></div>`;
    return [center, right];
  }

  // ---------- mode E : 소문항 실전
  function modeE(t) {
    const probs = byTpl(t.id); const pi = Math.min(S.ui.pi || 0, probs.length - 1); const p = probs[pi];
    const fs = S.funcs[p.id] || {};
    const nOk = p.subs.filter(s => S.subs[s.id] && S.subs[s.id].ok).length;
    const draft = S.drafts[p.id] != null ? S.drafts[p.id] : `import pandas as pd\ndf = pd.read_csv('${p.file}')\n\n# 1) 함수를 import 하고  2) 결과를 result 에 담고  3) 필요한 속성을 print\n`;
    const allTouched = p.subs.every(s => S.subs[s.id] && (S.subs[s.id].ok || S.subs[s.id].revealed));
    const center = `
      <div class="ptabs">${probs.map((q, i) => { const k = q.subs.filter(s => S.subs[s.id] && S.subs[s.id].ok).length; return `
        <button class="ptab ${i === pi ? 'on' : ''}" data-act="pi" data-v="${i}"><b class="mono">${q.id}</b><span class="stars">${stars(q.level)}</span><span class="chip ${k === q.subs.length ? 'ok' : ''}">${k}/${q.subs.length}</span></button>`; }).join('')}</div>
      <div><span class="label">E. 소문항별 실전 · ${esc(t.name)}</span><h2 style="margin-top:4px">${esc(p.title)}</h2></div>
      <p class="story" style="margin:0">${esc(p.story)}</p>
      ${p.note ? `<div class="note"><b>주의</b> ${esc(p.note)}</div>` : ''}
      <div class="row" style="justify-content:space-between"><b>데이터 미리보기 <span class="muted small mono">${esc(p.file)} · ${p.rows.length}행 x ${p.columns.length}열</span></b>
        <span class="row"><button class="btn sm" data-act="copyCsv">CSV 복사</button><button class="btn sm" data-act="dlCsv">CSV 다운로드</button></span></div>
      ${dataTable(p)}
      <div class="row" style="justify-content:space-between"><b>코드 작성 공간</b>
        <span class="row"><button class="btn sm" data-act="runPy">Python 실행</button><button class="btn sm" data-act="copyCode">코드 복사</button>
        ${allTouched ? '<button class="btn sm" data-act="showSol">정답 코드</button>' : ''}</span></div>
      <textarea class="editor" id="editor" spellcheck="false" aria-label="코드 작성">${esc(draft)}</textarea>
      <pre class="out" id="pyout">${esc(T.pyOut[p.id] || '실행 결과가 여기에 표시됩니다. [Python 실행]은 브라우저용 Python(Pyodide, 약 30MB)을 처음 한 번 불러옵니다. 불러올 수 없는 환경에서는 실행하지 않고, 검증된 정답으로만 채점합니다.')}</pre>
      ${T.showSol === p.id ? `<b>정답 코드</b><pre class="code">${hl(p.solution)}</pre>` : ''}`;
    const right = `
      <div class="panel pad stack">
        <div class="score-line"><div><span class="label">소문항 점수 (연습)</span><div class="bigscore">${nOk}<span class="muted small"> / ${p.subs.length}</span></div></div>
          <span class="chip">소문항마다 독립 채점 · 1점씩</span></div>
        <div class="sub ${fs.ok ? 'ok' : fs.tried ? 'bad' : ''}">
          <div class="sub-h"><span class="no">1단계</span><span class="chip acc">함수 이름</span>${fs.ok ? '<span class="chip ok">정답</span>' : ''}</div>
          <div class="q">이 문제에 사용할 함수 이름을 입력하세요.</div>
          <div class="inrow"><span>함수</span><input type="text" class="mono" data-in="F${p.id}" value="${esc(T.inputs['F' + p.id] != null ? T.inputs['F' + p.id] : (fs.input || ''))}" placeholder="예: ttest_ind" autocomplete="off" spellcheck="false"><button class="btn sm pri" data-act="checkFunc">확인</button></div>
          ${fs.tried ? (fs.ok ? `<div class="fb ok">정답: <code>${esc(TMAP[p.tpl].imp)}</code></div>` : `<div class="fb bad">${funcHint(p, fs)}</div>`) : ''}
        </div>
      </div>
      <div class="panel pad stack">${p.subs.map((s, i) => subCard(p, s, i)).join('')}</div>`;
    return [center, right];
  }
  function funcHint(p, fs) {
    const t = TMAP[p.tpl];
    if (fs.n >= 2) return `1) 유형: <b>${esc(t.name)}</b> — ${esc(t.when)}<br>2) 함수: <code>${esc(t.func)}</code> (<code>${esc(t.imp)}</code>)`;
    return `1) 먼저 유형을 고르세요: 이 문제는 <b>${esc(t.name)}</b> 상황입니다. 다시 입력해 보세요.`;
  }
  function dataTable(p) {
    const show = p.rows.slice(0, 60);
    return `<div class="tablewrap"><table class="data"><thead><tr><th class="idx"></th>${p.columns.map(c => `<th>${esc(c)}</th>`).join('')}</tr></thead>
      <tbody>${show.map((r, i) => `<tr><td class="idx">${i}</td>${r.map(v => v == null ? '<td class="nan">NaN</td>' : `<td>${esc(v)}</td>`).join('')}</tr>`).join('')}</tbody></table></div>
      ${p.rows.length > show.length ? `<div class="muted small">앞 ${show.length}행만 표시. 전체 ${p.rows.length}행은 CSV로 확인하세요.</div>` : ''}`;
  }
  function subCard(p, s, i) {
    const st = S.subs[s.id] || {}; const fs = S.funcs[p.id] || {}; const cs = S.codes[s.id] || {};
    const canReveal = fs.tried && cs.tried;
    const status = st.ok ? '<span class="chip ok">정답</span>' : st.revealed ? '<span class="chip warn">정답 공개됨</span>' : st.tries ? '<span class="chip bad">오답</span>' : '';
    const ansIn = s.kind === 'num'
      ? `<div class="inrow"><span>답</span><input type="text" class="mono" inputmode="decimal" data-in="A${s.id}" value="${esc(T.inputs['A' + s.id] != null ? T.inputs['A' + s.id] : (st.last || ''))}" placeholder="${s.dec ? '0.' + '0'.repeat(s.dec) : '정수'}" autocomplete="off"><button class="btn sm pri" data-act="grade" data-v="${s.id}">채점</button></div>
         <div class="muted small">${tolText(s)}</div>`
      : `<div class="choices">${s.opts.map(o => `<button class="choice ${(T.choice[s.id] || st.last) === o ? 'sel' : ''}" data-act="choose" data-v="${s.id}" data-o="${esc(o)}">${esc(o === '채택' ? '채택 (기각 못함)' : o)}</button>`).join('')}
         <button class="btn sm pri" data-act="grade" data-v="${s.id}">채점</button></div>`;
    return `<div class="sub ${st.ok ? 'ok' : st.tries ? 'bad' : ''}" id="sub-${s.id}">
      <div class="sub-h"><span class="no">${i + 1})</span><span class="chip acc">${esc(s.pattern)}</span>${status}<span class="pts">1점</span></div>
      <div class="q">${esc(s.q)}</div>
      <div class="inrow"><span>출력 코드</span><input type="text" class="mono" data-in="K${s.id}" value="${esc(T.inputs['K' + s.id] != null ? T.inputs['K' + s.id] : (cs.input || ''))}" placeholder="예: result.statistic" autocomplete="off" spellcheck="false"><button class="btn sm" data-act="checkCode" data-v="${s.id}">확인</button></div>
      ${cs.tried ? (cs.ok ? `<div class="fb ok">코드 정답: <code>${esc(s.code)}</code></div>` : `<div class="fb bad">출력 코드가 다릅니다. ${cs.n >= 2 ? '정답 코드: <code>' + esc(s.code) + '</code>' : '이 소문항은 <b>' + esc(s.pattern) + '</b>을(를) 묻습니다. 어떤 속성에서 꺼내야 할까요?'}</div>`) : ''}
      ${ansIn}
      <div class="row">
        <button class="btn sm" data-act="hint" data-v="${s.id}" data-l="2">힌트 1단계</button>
        <button class="btn sm" data-act="hint" data-v="${s.id}" data-l="3">힌트 2단계</button>
        <button class="btn sm" data-act="reveal" data-v="${s.id}" ${canReveal ? '' : 'disabled title="먼저 함수 이름과 출력 코드를 입력해 확인하세요"'}>정답 공개</button>
      </div>
      ${!canReveal && (st.tries || st.lvl) ? '<div class="muted small">정답 공개는 1단계 함수 이름과 이 소문항의 출력 코드를 먼저 입력해 확인한 뒤 열립니다.</div>' : ''}
      ${st.why && !st.ok ? `<div class="fb bad"><b>오답 사유</b> ${esc(st.why)}</div>` : ''}
      ${st.ok ? `<div class="fb ok">정답 ${esc(fmtAns(s))}. ${esc(s.exp)}</div>` : ''}
      ${!st.ok && st.lvl ? stepsHtml(p, s, st.lvl) : ''}
    </div>`;
  }
  function stepsHtml(p, s, lvl) {
    const t = TMAP[p.tpl];
    const steps = [
      ['어떤 유형을 골라야 하나', `<b>${esc(t.name)}</b> — ${esc(t.when)}`],
      ['어떤 함수를 쓰나', `<code>${esc(t.imp)}</code> → <code>${esc(t.func)}()</code>`],
      ['어떤 속성에서 답을 꺼내나', `<code>${esc(s.code)}</code>`],
      ['최종 정답과 해석', `<b class="mono">${esc(fmtAns(s))}</b> — ${esc(s.exp)}`],
    ];
    return `<ol class="steps">${steps.slice(0, lvl).map((x, i) => `<li><i>${i + 1}</i><div><b>${x[0]}</b>${x[1]}</div></li>`).join('')}</ol>`;
  }

  // ---------- wrong notebook
  function wrongInfo(k) {
    const [type, id] = [k[0], k.slice(2)];
    if (type === 'S' && SUBMAP[id]) { const { sub, prob, no } = SUBMAP[id]; return { title: `${prob.id} ${prob.title} · 소문항 ${no}`, desc: sub.q, act: `data-act="openSub" data-v="${id}"` }; }
    if (type === 'C' && TMAP[id]) return { title: `${id} ${TMAP[id].name} · 코드 빈칸`, desc: '빈칸 암기에서 틀린 칸이 있었습니다.', act: `data-act="tplmode" data-v="${id}" data-m="C"` };
    if (type === 'B') { const q = window.METHOD_QUIZ[+id]; return q ? { title: '방법 선택 퀴즈', desc: q[0], act: `data-act="openB" data-v="${id}"` } : null; }
    if (type === 'D') { const q = window.INTERP_QUIZ[+id]; return q ? { title: '해석 퀴즈 · ' + (q[0] === 'ALL' ? '공통' : q[0]), desc: q[2], act: `data-act="openD" data-v="${id}"` } : null; }
    return null;
  }
  function wrongRow(k, w, compact) {
    const info = wrongInfo(k); if (!info) return '';
    return `<div class="witem"><div style="min-width:0"><div class="t"><b>${esc(info.title)}</b></div>
      ${compact ? '' : `<div class="small muted">${esc(info.desc)}</div>${w.why ? `<div class="small" style="color:var(--bad)">${esc(w.why)}</div>` : ''}`}
      <div class="small muted">틀린 횟수 ${w.n}${w.src === 'mock' ? ' · 모의고사' : ''}</div></div>
      <button class="btn sm" ${info.act}>다시 풀기</button></div>`;
  }
  function vWrong() {
    const ow = openWrong(); const done = Object.entries(S.wrong).filter(([, v]) => v.resolved);
    return `<div class="section-h" style="margin-top:0"><h2>오답노트</h2>
      <div class="row">${ow.some(([k]) => k[0] === 'S') ? '<button class="btn pri" data-act="retryAll">G. 틀린 소문항만 재학습</button>' : ''}</div></div>
      <div class="grid2">
        <div class="panel pad stack"><b>복습할 오답 ${ow.length}개</b>
          <div class="wlist">${ow.length ? ow.map(([k, w]) => wrongRow(k, w, false)).join('') : '<div class="empty">남은 오답이 없습니다. 실전 문제나 모의고사를 더 풀어 보세요.</div>'}</div></div>
        <div class="panel pad stack"><b>해결한 오답 ${done.length}개</b>
          <div class="wlist">${done.length ? done.slice(0, 30).map(([k]) => { const i = wrongInfo(k); return i ? `<div class="witem"><span class="t">${esc(i.title)}</span><span class="chip ok">해결</span></div>` : ''; }).join('') : '<div class="empty">다시 풀어서 맞히면 이곳으로 옮겨집니다.</div>'}</div>
          <p class="disclaim" style="margin:0">오답은 다시 풀어 정답을 입력해야 해결됩니다. 정답 공개만 한 소문항은 오답노트에 남습니다.</p></div>
      </div>`;
  }

  // ---------- mock exam (F)
  function newMock() {
    const pick = arr => arr[Math.floor(Math.random() * arr.length)];
    const g1 = PROBS.filter(p => !['T09', 'T10'].includes(p.tpl));
    const g2 = PROBS.filter(p => ['T09', 'T10'].includes(p.tpl));
    const items = [pick(g1), pick(g2)].map(p => {
      let subs = p.subs.map(s => s.id);
      while (subs.length > 3) subs.splice(Math.floor(Math.random() * subs.length), 1);
      return { pid: p.id, subs };
    });
    S.mock = { items, ans: {}, funcs: {}, started: Date.now(), submitted: false, score: 0, res: {} };
  }
  function vMock() {
    const m = S.mock;
    if (!m) {
      return `<div class="section-h" style="margin-top:0"><h2>F. 30점 만점 모의고사</h2></div>
      <div class="grid2"><div class="panel pad stack">
        <p style="margin:0">문제 2개(검정·상관 계열 1개 + 회귀 계열 1개), 소문항 3개씩 출제됩니다. 소문항마다 <b>5점</b>, 총 <b>30점</b>.</p>
        <p style="margin:0">권장 시간 30분. 힌트 없이 풀고, 제출하면 소문항별로 독립 채점됩니다. 틀린 소문항은 오답노트로 갑니다.</p>
        <p class="disclaim" style="margin:0">가상 배점입니다. 실제 시험의 3유형 배점·문항 수와 다를 수 있습니다.</p>
        <div class="row"><button class="btn pri" data-act="mockStart">모의고사 시작</button></div></div>
        <div class="panel pad stack"><b>응시 기록</b>${S.mocks.length ? `<div class="wlist">${S.mocks.slice(-8).reverse().map(x => `<div class="witem"><span class="t">${esc(x.date)} · ${esc(x.items.join(', '))}</span><b class="mono">${x.score}/30</b></div>`).join('')}</div>` : '<div class="empty">기록 없음</div>'}</div></div>`;
    }
    const el = Math.floor((Date.now() - m.started) / 1000);
    return `<div class="section-h" style="margin-top:0"><h2>F. 30점 만점 모의고사</h2>
      <div class="row">${m.submitted ? `<span class="bigscore">${m.score}<span class="muted small"> / 30</span></span><span class="badge10 ${m.score >= 10 ? 'on' : ''}">${m.score >= 10 ? '10점 달성' : '10점 미달'}</span>` : `<span class="chip mono" id="timer">${Math.floor(el / 60)}:${String(el % 60).padStart(2, '0')} / 권장 30:00</span>`}
      ${m.submitted ? '<button class="btn pri" data-act="mockStart">새 모의고사</button><button class="btn" data-act="mockClose">닫기</button>' : '<button class="btn ghost" data-act="mockAbort">포기</button>'}</div></div>
      <p class="disclaim">가상 배점: 소문항당 5점 x 6 = 30점. 함수 이름 칸은 학습용이며 채점에 들어가지 않습니다. 실제 시험 배점과 다를 수 있습니다.</p>
      <div class="stack">${m.items.map((it, qi) => { const p = PMAP[it.pid]; return `
        <div class="panel pad mockq">
          <div class="row" style="justify-content:space-between"><h3>문제 ${qi + 1}. ${esc(p.title)}</h3><span class="chip">15점</span></div>
          <p class="story" style="margin:0">${esc(p.story)}</p>
          <div class="row" style="justify-content:space-between"><b class="small mono">${esc(p.file)} · ${p.rows.length}행</b><span class="row"><button class="btn sm" data-act="copyCsvP" data-v="${p.id}">CSV 복사</button><button class="btn sm" data-act="dlCsvP" data-v="${p.id}">CSV 다운로드</button></span></div>
          ${dataTable(p)}
          <div class="inrow"><span>함수 (채점 제외)</span><input type="text" class="mono" data-in="MF${p.id}" value="${esc(T.inputs['MF' + p.id] || m.funcs[p.id] || '')}" ${m.submitted ? 'disabled' : ''} autocomplete="off" spellcheck="false"><span></span></div>
          ${m.submitted ? `<div class="fb ${funcOk(m.funcs[p.id] || '', p.func) ? 'ok' : 'info'}">사용 함수: <code>${esc(TMAP[p.tpl].imp)}</code></div>` : ''}
          ${it.subs.map((sid, si) => { const s = SUBMAP[sid].sub; const r = m.res[sid]; return `
            <div class="sub ${r == null ? '' : r ? 'ok' : 'bad'}">
              <div class="sub-h"><span class="no">(${si + 1})</span><span class="chip acc">${esc(s.pattern)}</span>${r == null ? '' : r ? '<span class="chip ok">+5</span>' : '<span class="chip bad">0</span>'}<span class="pts">5점</span></div>
              <div class="q">${esc(s.q)}</div>
              ${s.kind === 'num' ? `<div class="inrow"><span>답</span><input type="text" class="mono" inputmode="decimal" data-in="M${sid}" value="${esc(T.inputs['M' + sid] != null ? T.inputs['M' + sid] : (m.ans[sid] || ''))}" ${m.submitted ? 'disabled' : ''} autocomplete="off"><span class="muted small">${tolText(s)}</span></div>`
                : `<div class="choices">${s.opts.map(o => `<button class="choice ${(T.choice['M' + sid] || m.ans[sid]) === o ? 'sel' : ''}" data-act="mchoose" data-v="${sid}" data-o="${esc(o)}" ${m.submitted ? 'disabled' : ''}>${esc(o === '채택' ? '채택 (기각 못함)' : o)}</button>`).join('')}</div>`}
              ${m.submitted ? `<div class="fb ${r ? 'ok' : 'bad'}">${r ? '정답' : '오답 · 입력: ' + esc(m.ans[sid] || '(없음)')} → 정답 <b class="mono">${esc(fmtAns(s))}</b><br><code>${esc(s.code)}</code> · ${esc(s.exp)}</div>` : ''}
            </div>`; }).join('')}
          ${m.submitted ? `<details><summary>정답 코드</summary><pre class="code">${hl(p.solution)}</pre></details>` : ''}
        </div>`; }).join('')}</div>
      ${m.submitted ? '' : '<div class="row" style="margin-top:14px"><button class="btn pri" data-act="mockSubmit">제출하고 채점</button></div>'}`;
  }
  function gradeValue(s, raw) {
    if (s.kind === 'num') { const x = parseNum(raw); return !isNaN(x) && Math.abs(x - s.ans) <= tolOf(s); }
    return raw === s.ans;
  }

  // ---------------------------------------------------------------- grading (practice)
  function wrongReason(p, s, raw) {
    if (s.kind !== 'num') return '선택이 틀렸습니다. p-value와 0.05를 비교한 결과를 다시 확인하세요.';
    const x = parseNum(raw); if (isNaN(x)) return '숫자로 입력하세요. (예: 0.0123, -2.5, 1.2e-05)';
    const near = v => Math.abs(x - v) <= Math.max(tolOf(s) * 2, Math.abs(v) * 0.002);
    for (const tr of (s.traps || [])) if (near(tr.v)) return tr.why;
    for (const o of p.subs) if (o !== s && o.kind === 'num' && near(o.ans)) return `다른 소문항(${o.pattern}) 값을 입력했습니다. 이 소문항은 ${s.pattern}을(를) 묻습니다.`;
    if (s.ans !== 0 && near(-s.ans)) return '부호가 반대입니다. 인자 순서(a, b / before, after)나 뺄셈 방향을 확인하세요.';
    if (Math.abs(x - s.ans) <= tolOf(s) * 10) return '거의 맞았습니다. 소수점 자릿수와 반올림을 확인하세요.';
    if (s.pattern === 'p-value' && x > 1) return 'p-value는 0~1 사이 값입니다. 통계량을 넣지 않았는지 확인하세요.';
    return '값이 다릅니다. 함수와 데이터 필터링(그룹, 결측치 제거)을 다시 확인하세요.';
  }
  function gradeSub(id) {
    const { sub: s, prob: p } = SUBMAP[id]; const st = subState(id);
    const raw = s.kind === 'num' ? (T.inputs['A' + id] != null ? T.inputs['A' + id] : st.last) : (T.choice[id] || st.last);
    if (raw == null || String(raw).trim() === '') { toast(s.kind === 'num' ? '답을 입력하세요' : '보기를 선택하세요'); return; }
    if (s.kind === 'num' && isNaN(parseNum(raw))) { st.why = wrongReason(p, s, raw); render(); return; }
    const ok = gradeValue(s, raw);
    st.tries++; st.last = String(raw);
    if (st.first == null && !st.revealed) st.first = ok;
    tally(ok);
    if (ok) { st.ok = true; st.why = ''; resolveWrong('S:' + id); toast('정답입니다 +1점'); }
    else {
      st.ok = false; st.why = wrongReason(p, s, raw);
      st.lvl = Math.max(st.lvl, Math.min(4, st.tries + 1)); // 1회: 유형+함수, 2회: +속성, 3회: +정답
      markWrong('S:' + id, { why: st.why, last: String(raw) });
    }
    render();
    const el = document.getElementById('sub-' + id); if (el && el.scrollIntoView) el.scrollIntoView({ block: 'nearest' });
  }

  // ---------------------------------------------------------------- pyodide (optional)
  let py = null, pyLoading = null;
  function loadScript(src) { return new Promise((res, rej) => { const s = document.createElement('script'); s.src = src; s.onload = res; s.onerror = () => rej(new Error('스크립트를 불러오지 못했습니다')); document.head.appendChild(s); }); }
  async function ensurePy(out) {
    if (py) return py;
    if (!pyLoading) pyLoading = (async () => {
      out('Python 실행 엔진(Pyodide) 불러오는 중... 처음 한 번은 수십 초 걸릴 수 있습니다.');
      if (!window.loadPyodide) await loadScript('https://cdn.jsdelivr.net/pyodide/v0.26.4/full/pyodide.js');
      const inst = await window.loadPyodide();
      out('pandas, scipy, statsmodels 패키지 불러오는 중...');
      await inst.loadPackage(['pandas', 'scipy', 'statsmodels']);
      py = inst; return inst;
    })().catch(e => { pyLoading = null; throw e; });
    return pyLoading;
  }
  async function runPy(p) {
    const outEl = $('#pyout'); const code = $('#editor').value;
    const show = t => { T.pyOut[p.id] = t; if (outEl) outEl.textContent = t; };
    try {
      const inst = await ensurePy(show);
      const buf = [];
      inst.setStdout({ batched: s => buf.push(s) }); inst.setStderr({ batched: s => buf.push(s) });
      PROBS.forEach(q => { try { inst.FS.writeFile(q.file, csvOf(q)); } catch (e) { /* ignore */ } });
      show('실행 중...');
      await inst.runPythonAsync(`import pandas as pd\ndf = pd.read_csv(${JSON.stringify(p.file)})\n`);
      await inst.runPythonAsync(code);
      show(buf.join('\n') || '(출력 없음 — print()로 값을 출력하세요)');
    } catch (e) {
      const msg = String(e && e.message || e);
      if (!py) show('이 환경에서는 Python 실행 엔진을 불러올 수 없습니다.\n코드는 실행되지 않았습니다. [코드 복사]·[CSV 복사]로 본인 Python(또는 Colab)에서 실행하고, 오른쪽 소문항에서 검증된 정답으로 채점하세요.\n(' + msg.slice(0, 160) + ')');
      else show('오류:\n' + msg.split('\n').slice(-8).join('\n'));
    }
  }

  // ---------------------------------------------------------------- settings modal
  function openSettings() {
    $('#modal').innerHTML = `<div class="modal" data-act="closeModal"><div class="panel pad stack" data-stop="1">
      <div class="row" style="justify-content:space-between"><b>설정</b><button class="btn sm ghost" data-act="closeModal">닫기</button></div>
      <label class="stack" style="gap:4px"><span class="small muted">시험일 (D-day와 오늘의 Day 계산 기준)</span><input type="date" id="examDate2" value="${esc(S.examDate)}"></label>
      <div class="stack" style="gap:6px"><span class="small muted">학습 기록은 이 브라우저(localStorage)에 자동 저장되고, 다시 열면 이어서 복구됩니다.</span>
        ${T.confirmReset ? '<div class="note"><b>정말 초기화할까요?</b> 모든 정답 기록, 오답노트, 모의고사 기록이 지워집니다.</div><div class="row"><button class="btn pri" data-act="doReset">초기화</button><button class="btn" data-act="cancelReset">취소</button></div>'
          : '<div class="row"><button class="btn" data-act="askReset">진행 기록 초기화</button></div>'}</div>
    </div></div>`;
  }

  // ---------------------------------------------------------------- events
  function afterRender() {
    const lt = document.getElementById('listToggle');
    if (lt) lt.style.display = window.matchMedia('(max-width: 900px)').matches ? 'inline-block' : 'none';
    if (!window.matchMedia('(max-width: 900px)').matches) { const tl = document.getElementById('tlist'); if (tl) tl.classList.remove('collapsed'); }
  }
  document.addEventListener('input', e => {
    const el = e.target;
    if (el.dataset.in) T.inputs[el.dataset.in] = el.value;
    else if (el.dataset.blank) T.inputs[el.dataset.blank] = el.value;
    else if (el.id === 'editor') { const p = byTpl(S.ui.tpl)[S.ui.pi || 0]; if (p) { S.drafts[p.id] = el.value; save(); } }
    else if (el.id === 'search') {
      T.search = el.value; const side = document.querySelector('.side');
      if (side) { side.innerHTML = sidebar(); const s = document.getElementById('search'); s.focus(); s.setSelectionRange(s.value.length, s.value.length); afterRender(); if (T.search) document.getElementById('tlist').classList.remove('collapsed'); }
    }
  });
  document.addEventListener('change', e => {
    if (e.target.id === 'examDate' || e.target.id === 'examDate2') { if (e.target.value) { S.examDate = e.target.value; render(); toast('시험일을 저장했습니다'); if (e.target.id === 'examDate2') openSettings(); } }
  });
  document.addEventListener('keydown', e => {
    const el = e.target;
    if (e.key === 'Enter' && el.dataset && el.dataset.in) {
      const k = el.dataset.in;
      if (k[0] === 'A') gradeSub(k.slice(1));
      else if (k[0] === 'K') act('checkCode', { v: k.slice(1) });
      else if (k[0] === 'F') act('checkFunc', {});
    }
    if (e.key === 'Tab' && el.id === 'editor') {
      e.preventDefault(); const s = el.selectionStart; el.value = el.value.slice(0, s) + '    ' + el.value.slice(el.selectionEnd); el.selectionStart = el.selectionEnd = s + 4;
      const p = byTpl(S.ui.tpl)[S.ui.pi || 0]; if (p) { S.drafts[p.id] = el.value; save(); }
    }
    if (e.key === 'Escape' && $('#modal').innerHTML) { $('#modal').innerHTML = ''; }
  });
  document.addEventListener('click', e => {
    const b = e.target.closest('[data-act]');
    if (!b) return;
    if (b.dataset.act === 'closeModal' && e.target.closest('[data-stop]') && !e.target.closest('button[data-act="closeModal"]')) return;
    act(b.dataset.act, b.dataset, b);
  });

  function curProb() { const probs = byTpl(S.ui.tpl); return probs[Math.min(S.ui.pi || 0, probs.length - 1)]; }
  function dl(name, text) {
    try { const a = document.createElement('a'); a.href = URL.createObjectURL(new Blob(['﻿' + text], { type: 'text/csv;charset=utf-8' })); a.download = name; document.body.appendChild(a); a.click(); a.remove(); toast(name + ' 다운로드 (막힌 환경에서는 CSV 복사를 쓰세요)'); }
    catch (e) { copyText(text, '다운로드가 막혀 CSV를 복사했습니다'); }
  }

  function act(a, d) {
    const t = TMAP[S.ui.tpl];
    switch (a) {
      case 'go': go(d.v); break;
      case 'today': { const pl = window.PLAN[dayNum() - 1];
        if (pl.day === 9) go('mock'); else if (pl.day === 10) { if (openWrong().length) startRetry(); else go('study', { tpl: 'T01', mode: 'C' }); }
        else { const nxt = pl.tpls.find(id => tplMastery(id).p < 100) || pl.tpls[0]; go('study', { tpl: nxt, mode: (S.blanks[nxt] && S.blanks[nxt].done) ? 'E' : 'A', pi: 0 }); } break; }
      case 'day': { const pl = window.PLAN[+d.v - 1]; if (pl.day === 9) go('mock'); else if (pl.day === 10) go('wrong'); else go('study', { tpl: pl.tpls[0], mode: 'A', pi: 0 }); break; }
      case 'dayDone': S.dayDone[d.v] = !S.dayDone[d.v]; render(); break;
      case 'tpl': S.ui.pi = 0; T.listOpen = false; go('study', { tpl: d.v, mode: S.ui.view === 'study' ? (['F', 'G'].includes(S.ui.mode) ? 'E' : S.ui.mode) : 'A' }); break;
      case 'tplmode': go('study', { tpl: d.v, mode: d.m, pi: 0 }); break;
      case 'mode':
        if (d.v === 'F') { go('mock'); break; }
        if (d.v === 'G') { startRetry(); break; }
        S.ui.mode = d.v; render(); break;
      case 'pi': S.ui.pi = +d.v; T.showSol = null; render(); break;
      case 'toggleList': T.listOpen = !T.listOpen; render(); break;
      case 'settings': T.confirmReset = false; openSettings(); break;
      case 'closeModal': $('#modal').innerHTML = ''; break;
      case 'askReset': T.confirmReset = true; openSettings(); break;
      case 'cancelReset': T.confirmReset = false; openSettings(); break;
      case 'doReset': S = fresh(); Object.keys(T.inputs).forEach(k => delete T.inputs[k]); T.choice = {}; T.blankRes = {}; T.blankShow = {}; T.pyOut = {};
        try { localStorage.removeItem(KEY); } catch (e) { /* ignore */ } $('#modal').innerHTML = ''; go('home'); toast('초기화했습니다'); break;
      case 'cardRev': S.ui.cardRev = !S.ui.cardRev; T.flips = {}; render(); break;
      case 'flip': T.flips[d.v] = !T.flips[d.v]; { const el = document.querySelector(`.fcard[data-v="${d.v}"]`); if (el) el.classList.toggle('flip', !!T.flips[d.v]); } break;
      case 'copyTpl': copyText(t.code, '템플릿 코드를 복사했습니다'); break;
      // B
      case 'pickB': { const i = ((S.ui.bIdx % window.METHOD_QUIZ.length) + window.METHOD_QUIZ.length) % window.METHOD_QUIZ.length; const ans = window.METHOD_QUIZ[i][1];
        T.inputs['B' + i] = d.v; const ok = d.v === ans; S.quizB[i] = ok; tally(ok); if (ok) resolveWrong('B:' + i); else markWrong('B:' + i, { why: `정답은 ${ans} ${TMAP[ans].name}` }); render(); break; }
      case 'bMove': S.ui.bIdx = (S.ui.bIdx || 0) + (+d.v); delete T.inputs['B' + (((S.ui.bIdx % window.METHOD_QUIZ.length) + window.METHOD_QUIZ.length) % window.METHOD_QUIZ.length)]; render(); break;
      case 'openB': S.ui.bIdx = +d.v; delete T.inputs['B' + d.v]; go('study', { mode: 'B' }); break;
      // C
      case 'gradeBlank': { const parts = blankParts(t).filter(x => typeof x === 'object'); const res = {}; let n = 0;
        parts.forEach(x => { const v = (T.inputs['C' + t.id + '_' + x.bi] || '').trim().replace(/^['"]|['"]$/g, ''); res[x.bi] = v === x.ans.replace(/^['"]|['"]$/g, ''); if (res[x.bi]) n++; });
        T.blankRes[t.id] = res; T.blankShow[t.id] = false; const all = n === parts.length; tally(all);
        const prev = S.blanks[t.id] || { best: 0 }; S.blanks[t.id] = { best: Math.max(prev.best, n), total: parts.length, done: prev.done || all };
        if (all) resolveWrong('C:' + t.id); else markWrong('C:' + t.id, { why: `${parts.length - n}칸 오답` }); render(); break; }
      case 'showBlank': T.blankShow[t.id] = true; T.blankRes[t.id] = null; render(); break;
      case 'clearBlank': Object.keys(T.inputs).filter(k => k.startsWith('C' + t.id + '_')).forEach(k => delete T.inputs[k]); T.blankRes[t.id] = null; T.blankShow[t.id] = false; render(); break;
      // D
      case 'pickD': { const q = window.INTERP_QUIZ[+d.v]; const k = +d.k; T.inputs['D' + d.v] = k; const ok = k === q[4]; S.quizD[d.v] = ok; tally(ok);
        if (ok) resolveWrong('D:' + d.v); else markWrong('D:' + d.v, { why: q[5] }); render(); break; }
      case 'resetD': window.INTERP_QUIZ.forEach((q, i) => { if (q[0] === t.id || q[0] === 'ALL') delete T.inputs['D' + i]; }); render(); break;
      case 'openD': { const q = window.INTERP_QUIZ[+d.v]; delete T.inputs['D' + d.v]; go('study', { tpl: q[0] === 'ALL' ? S.ui.tpl : q[0], mode: 'D' }); break; }
      // E
      case 'checkFunc': { const p = curProb(); const v = T.inputs['F' + p.id] != null ? T.inputs['F' + p.id] : ''; if (!v.trim()) { toast('함수 이름을 입력하세요'); break; }
        const fs = S.funcs[p.id] || { n: 0 }; fs.tried = true; fs.input = v; fs.ok = funcOk(v, p.func); if (!fs.ok) fs.n = (fs.n || 0) + 1; S.funcs[p.id] = fs; tally(fs.ok); render(); break; }
      case 'checkCode': { const { sub: s } = SUBMAP[d.v]; const v = T.inputs['K' + d.v] != null ? T.inputs['K' + d.v] : ''; if (!v.trim()) { toast('출력 코드를 입력하세요'); break; }
        const cs = S.codes[d.v] || { n: 0 }; cs.tried = true; cs.input = v; cs.ok = codeOk(v, s.accept); if (!cs.ok) cs.n = (cs.n || 0) + 1; S.codes[d.v] = cs; render(); break; }
      case 'choose': T.choice[d.v] = d.o; render(); break;
      case 'grade': gradeSub(d.v); break;
      case 'hint': { const st = subState(d.v); st.lvl = Math.max(st.lvl, +d.l); render(); break; }
      case 'reveal': { const st = subState(d.v); const fs = S.funcs[SUBMAP[d.v].prob.id] || {}; const cs = S.codes[d.v] || {};
        if (!fs.tried || !cs.tried) { toast('먼저 함수 이름과 출력 코드를 입력하세요'); break; }
        st.lvl = 4; if (!st.ok) { st.revealed = true; if (st.first == null) st.first = false; markWrong('S:' + d.v, { why: st.why || '정답 공개' }); } render(); break; }
      case 'copyCsv': copyText(csvOf(curProb()), 'CSV를 복사했습니다'); break;
      case 'dlCsv': dl(curProb().file, csvOf(curProb())); break;
      case 'copyCsvP': copyText(csvOf(PMAP[d.v]), 'CSV를 복사했습니다'); break;
      case 'dlCsvP': dl(PMAP[d.v].file, csvOf(PMAP[d.v])); break;
      case 'copyCode': copyText($('#editor').value, '코드를 복사했습니다'); break;
      case 'showSol': T.showSol = T.showSol === curProb().id ? null : curProb().id; render(); break;
      case 'runPy': runPy(curProb()); break;
      case 'openSub': openSub(d.v, true); break;
      // G
      case 'retryAll': startRetry(); break;
      case 'retryNext': { const r = S.ui.retry; if (!r) break; r.pos = (r.pos + 1) % r.queue.length; openSub(r.queue[r.pos], true); break; }
      case 'retryStop': S.ui.retry = null; render(); break;
      // F
      case 'mockStart': newMock(); Object.keys(T.inputs).filter(k => k[0] === 'M').forEach(k => delete T.inputs[k]); Object.keys(T.choice).filter(k => k[0] === 'M').forEach(k => delete T.choice[k]); go('mock'); break;
      case 'mockAbort': case 'mockClose': S.mock = null; render(); break;
      case 'mchoose': T.choice['M' + d.v] = d.o; S.mock.ans[d.v] = d.o; render(); break;
      case 'mockSubmit': submitMock(); break;
      default: break;
    }
  }
  function openSub(id, reset) {
    const { prob } = SUBMAP[id]; const probs = byTpl(prob.tpl);
    if (reset) { const st = subState(id); if (!st.ok) { st.lvl = 0; st.revealed = false; st.why = ''; } delete T.inputs['A' + id]; delete T.choice[id]; }
    go('study', { tpl: prob.tpl, mode: 'E', pi: probs.indexOf(prob) });
    setTimeout(() => { const el = document.getElementById('sub-' + id); if (el) { el.scrollIntoView({ block: 'center' }); el.style.boxShadow = '0 0 0 2px var(--accent)'; } }, 30);
  }
  function startRetry() {
    const q = openWrong().filter(([k]) => k[0] === 'S').map(([k]) => k.slice(2)).filter(id => SUBMAP[id]);
    if (!q.length) { go('wrong'); toast('재학습할 소문항 오답이 없습니다'); return; }
    S.ui.retry = { queue: q, pos: 0 }; openSub(q[0], true);
  }
  function submitMock() {
    const m = S.mock; let score = 0;
    m.items.forEach(it => {
      const p = PMAP[it.pid]; m.funcs[p.id] = T.inputs['MF' + p.id] || m.funcs[p.id] || '';
      it.subs.forEach(sid => {
        const s = SUBMAP[sid].sub;
        const raw = s.kind === 'num' ? (T.inputs['M' + sid] != null ? T.inputs['M' + sid] : (m.ans[sid] || '')) : (T.choice['M' + sid] || m.ans[sid] || '');
        m.ans[sid] = raw; const ok = String(raw).trim() !== '' && gradeValue(s, raw);
        m.res[sid] = ok; tally(ok); if (ok) score += MOCK_PTS;
        else markWrong('S:' + sid, { why: '모의고사 오답 · 입력: ' + (raw || '(없음)'), src: 'mock' });
      });
    });
    m.submitted = true; m.score = score;
    S.mocks.push({ date: iso(Date.now()) + ' ' + new Date().toTimeString().slice(0, 5), score, items: m.items.map(i => i.pid) });
    render(); toast(`${score} / 30점${score >= 10 ? ' · 10점 달성' : ''}`);
  }
  setInterval(() => { const el = document.getElementById('timer'); if (el && S.mock && !S.mock.submitted) { const s = Math.floor((Date.now() - S.mock.started) / 1000); el.textContent = `${Math.floor(s / 60)}:${String(s % 60).padStart(2, '0')} / 권장 30:00`; } }, 1000);
  window.addEventListener('resize', afterRender);
  window.addEventListener('hashchange', () => { const h = location.hash.slice(1); if (h && h !== S.ui.view && ['home', 'study', 'plan', 'mock', 'wrong', 'project'].includes(h)) { S.ui.view = h; render(); } });

  // boot
  const h = location.hash.slice(1);
  if (['home', 'study', 'plan', 'mock', 'wrong', 'project'].includes(h)) S.ui.view = h;
  render();
  // self-check hooks for tests
  window.__bbk = { normCode, codeOk, funcOk, gradeValue, SUBMAP };
})();
