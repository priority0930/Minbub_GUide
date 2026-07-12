# 민법 가이드 (Minbub Guide)

변리사 1차 민법개론 학습을 위한 AI 코칭 웹앱입니다. PDF 또는 TXT 학습 자료를 업로드하면,
내용을 논점 단위로 분리해 최대 10개의 10분 학습 세션으로 나누고 세션별로 핵심 요약, 유사 개념 비교,
기본/사례형/5지선다 문제, 자기설명 문제, 오답 포인트, 암기 한 줄, 복습 시점을 순서대로 안내합니다.

## 시작하기

```bash
npm install
cp .env.example .env.local   # ANTHROPIC_API_KEY 입력
npm run dev
```

브라우저에서 http://localhost:3000 접속 후, 우측 상단의 "PDF/TXT 업로드" 버튼으로 학습 자료를 올리면
자동으로 세션 목차와 세션 1이 시작됩니다.

## 구조

- `app/page.tsx` — 채팅 UI 및 파일 업로드
- `app/api/upload/route.ts` — PDF/TXT 텍스트 추출 API
- `app/api/chat/route.ts` — Anthropic API 호출 및 코칭 응답 생성
- `lib/systemPrompt.ts` — 학습 코치 시스템 프롬프트 (세션 구성 규칙, 정답 비공개 원칙 등)

## 참고

- 업로드 파일은 25MB, 추출 텍스트는 약 18만자까지 반영됩니다. 분량이 이를 초과하면 앞부분만 반영되고
  "다음 학습 묶음" 안내가 함께 표시됩니다.
- 스캔 이미지로만 이루어진 PDF는 텍스트 추출이 되지 않을 수 있습니다 (OCR 미지원).
