import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "주식초보나들이",
  description: "차트, 뉴스, 증권사 리포트를 초보 눈높이로",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ko">
      <body>{children}</body>
    </html>
  );
}
