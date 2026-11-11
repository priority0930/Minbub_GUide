#!/usr/bin/env node
// index.html 안의 문제 데이터 무결성 검사. 실패하면 exit 1.
// 사용: node validate.mjs [index.html 경로]
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';

const file = process.argv[2] || fileURLToPath(new URL('./index.html', import.meta.url));
const html = readFileSync(file, 'utf8');

const FIELDS = ['id', 'ch', 'ref', 'q', 'a', 'b', 'exp'];
const CHAPTERS = ['A', 'B', 'C', 'D', 'E', 'F', 'N'];
const LIMITS = { q: 40, a: 24, b: 24, exp: 70 };
const len = (s) => [...s].length;

const errors = [];
const fail = (msg) => errors.push(msg);

const m = html.match(/\/\*DATA-START\*\/([\s\S]*?)\/\*DATA-END\*\//);
let data = [];
if (!m) {
  fail('데이터 마커(/*DATA-START*/ … /*DATA-END*/)를 찾지 못함');
} else {
  try {
    data = JSON.parse(m[1]);
    if (!Array.isArray(data)) { fail('데이터가 배열이 아님'); data = []; }
  } catch (e) {
    fail('데이터 JSON 파싱 실패: ' + e.message);
  }
}
if (m && data.length === 0 && errors.length === 0) fail('문항이 0개');

const seen = new Set();
const tooLong = [];
const perCh = Object.fromEntries(CHAPTERS.map((c) => [c, 0]));

data.forEach((x, i) => {
  const tag = (x && typeof x.id === 'string' && x.id) || `#${i + 1}`;
  if (!x || typeof x !== 'object') { fail(`${tag}: 객체가 아님`); return; }

  // 7개 필드 모두 존재 (exp만 빈 문자열 허용)
  let fieldsOk = true;
  for (const f of FIELDS) {
    if (typeof x[f] !== 'string') { fail(`${tag}: 필드 '${f}' 없음/문자열 아님`); fieldsOk = false; }
    else if (f !== 'exp' && x[f].trim() === '') { fail(`${tag}: 필드 '${f}' 비어 있음`); fieldsOk = false; }
  }
  const extra = Object.keys(x).filter((k) => !FIELDS.includes(k));
  if (extra.length) fail(`${tag}: 알 수 없는 필드 ${extra.join(', ')}`);
  if (!fieldsOk) return;

  if (seen.has(x.id)) fail(`${tag}: id 중복`);
  seen.add(x.id);

  if (!CHAPTERS.includes(x.ch)) fail(`${tag}: ch '${x.ch}'는 허용 범위(A,B,C,D,E,F,N) 밖`);
  else perCh[x.ch] += 1;

  if (x.a === x.b) fail(`${tag}: 정답(a)과 오답(b)이 같음`);

  for (const [f, max] of Object.entries(LIMITS)) {
    const n = len(x[f]);
    if (n > max) tooLong.push(`${tag}: ${f} ${n}자 > ${max}자 — ${x[f]}`);
  }
});

if (tooLong.length) {
  fail(`길이 초과 ${tooLong.length}건`);
  console.error('길이 초과 목록:');
  for (const t of tooLong) console.error('  ' + t);
}

console.log(`총 문항 수: ${data.length}`);
console.log('장별 개수: ' + CHAPTERS.map((c) => `${c} ${perCh[c]}`).join(' / '));

if (errors.length) {
  console.error(`\n검증 실패 (${errors.length}건)`);
  for (const e of errors) console.error('  - ' + e);
  process.exit(1);
}
console.log('검증 통과');
