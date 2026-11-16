"use client";
// 좋은 소식 / 나쁜 소식 필터 + "더 보기". 뉴스·리포트·공시 목록이 같이 쓴다.
// 목록은 받은 순서(최신순)를 그대로 두고, 버튼으로 골라 볼 수만 있게 한다.
//   <ToneFilter items={list} toneOf={(n) => n.tone} labels={{ good: "좋은 소식", bad: "나쁜 소식" }}>
//     {(shown) => <NewsList items={shown} />}
//   </ToneFilter>

import { useState, type ReactNode } from "react";

import ShowMore from "@/components/ShowMore/ShowMore";
import styles from "./ToneFilter.module.css";

export type Tone = "good" | "bad" | "check";

const ORDER: Tone[] = ["good", "bad", "check"];

export default function ToneFilter<T>({
  items,
  toneOf,
  labels,
  limit = 3,
  children,
}: {
  items: T[];
  toneOf: (item: T) => Tone | null;
  labels: Partial<Record<Tone, string>>; // 보여줄 버튼만 넣는다
  limit?: number;
  children: (shown: T[]) => ReactNode;
}) {
  const [tone, setTone] = useState<Tone | "all">("all");
  const counts = { good: 0, bad: 0, check: 0 };
  for (const it of items) {
    const t = toneOf(it);
    if (t) counts[t] += 1;
  }
  const filtered = tone === "all" ? items : items.filter((it) => toneOf(it) === tone);
  const buttons = ORDER.filter((t) => labels[t] && counts[t] > 0);

  return (
    <>
      {buttons.length > 0 && (
        <div className={styles["chips"]}>
          <button className={tone === "all" ? styles["on"] : ""} onClick={() => setTone("all")}>
            전체 {items.length}
          </button>
          {buttons.map((t) => (
            <button
              key={t}
              className={`${styles[t]} ${tone === t ? styles["on"] : ""}`}
              onClick={() => setTone(t)}
            >
              {labels[t]} {counts[t]}
            </button>
          ))}
        </div>
      )}
      {/* 필터를 바꾸면 "더 보기"도 다시 접는다 */}
      <ShowMore key={tone} items={filtered} limit={limit}>
        {children}
      </ShowMore>
    </>
  );
}
