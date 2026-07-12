import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "민법 가이드 | 변리사 1차 민법개론 학습 코치",
  description:
    "PDF·TXT 자료를 업로드하면 논점 단위로 세션을 나눠 변리사 1차 민법개론을 코칭해주는 학습 도우미",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="ko">
      <body>{children}</body>
    </html>
  );
}
