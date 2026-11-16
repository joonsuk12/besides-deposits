import { BRAND } from "@/lib/brand";
import type { Metadata } from "next";
import { Suspense } from "react";
import Header from "@/components/Header/Header";
import { pretendard } from "./fonts";
import "./globals.css";
import "./chart.css";

export const metadata: Metadata = {
  title: `${BRAND.ko} | ${BRAND.en}`,
  description: BRAND.tagline,
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ko" className={pretendard.variable}>
      <body>
        <Suspense>
          <Header />
        </Suspense>
        {children}
      </body>
    </html>
  );
}
