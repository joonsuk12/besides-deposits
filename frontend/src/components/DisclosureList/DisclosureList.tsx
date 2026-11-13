"use client";
// 공시 목록. 공시마다 좋은 소식/나쁜 소식 꼬리표, 분류, 쉬운 설명 한 줄을 보여준다.
// 리포트 카드처럼 "자세히"(왜 그렇게 보는지 + 원문에서 확인할 것)와 "원문 ↗"이 있다.
// limit: 중요한 순서(나쁜 소식 → 좋은 소식 → 중요 → 참고, 같으면 최신순)로 앞의 몇 개만 보여주고
//        나머지는 "더 보기"로 펼친다.

import { useState } from "react";

import type { Disclosure } from "@/lib/api";
import ShowMore from "@/components/ShowMore/ShowMore";
import styles from "./DisclosureList.module.css";

// 공시 이름만 보고 붙이는 것이라 "보통"이라고 단서를 단다 (뉴스의 "추정"과 같은 뜻)
const TONE = {
  warn: { label: "⚠️ 나쁜 소식 (보통)", cls: "tone-bad" },
  good: { label: "👍 좋은 소식 (보통)", cls: "tone-good" },
  key: { label: "🔎 중요 · 내용을 봐야 알아요", cls: "tone-key" },
  info: null,
};
const LEVEL_RANK = { warn: 0, good: 1, key: 2, info: 3 };

export const byImportance = (a: Disclosure, b: Disclosure) =>
  LEVEL_RANK[a.level] - LEVEL_RANK[b.level] || b.date.localeCompare(a.date);

function Item({ d }: { d: Disclosure }) {
  const [open, setOpen] = useState(false);
  const tone = TONE[d.level];
  const hasDetail = !!d.why || d.checks.length > 0;

  return (
    <li className={`${styles["item"]} ${styles[`item-${d.level}`]}`}>
      <div className={styles["badges"]}>
        {tone && <span className={`${styles["tone"]} ${styles[tone.cls]}`}>{tone.label}</span>}
        <span className={`${styles["badge"]} ${styles[d.level]}`}>{d.category}</span>
        {d.is_correction && <span className={styles["sub"]}>정정</span>}
        {!d.by_company && <span className={styles["sub"]}>제출: {d.filer}</span>}
        <span className={styles["date"]}>{d.date}</span>
      </div>
      <p className={styles["title"]}>{d.title}</p>
      <p className={styles["explain"]}>{d.explain}</p>

      {open && (
        <div className={styles["detail"]}>
          {d.why && (
            <>
              <h4>왜 그렇게 보나요</h4>
              <p>{d.why}</p>
            </>
          )}
          {d.checks.length > 0 && (
            <>
              <h4>원문에서 확인할 것</h4>
              <ul>
                {d.checks.map((c) => (
                  <li key={c}>{c}</li>
                ))}
              </ul>
            </>
          )}
        </div>
      )}

      <div className={styles["actions"]}>
        {hasDetail && <button onClick={() => setOpen((v) => !v)}>{open ? "접기" : "자세히"}</button>}
        <a href={d.url} target="_blank" rel="noreferrer">
          원문 ↗
        </a>
      </div>
    </li>
  );
}

export default function DisclosureList({
  items,
  empty,
  limit,
  skipInfo = false,
}: {
  items: Disclosure[];
  empty?: string;
  limit?: number;
  skipInfo?: boolean; // 참고용(정기 보고서·지분 보고)은 아예 빼고 건수만 알려준다. 삼성전자는 1년에 3천 건 가까이 된다
}) {
  if (items.length === 0) return <p className={styles["empty"]}>{empty ?? "공시가 없습니다."}</p>;

  const kept = skipInfo ? items.filter((d) => d.level !== "info") : items;
  const skipped = items.length - kept.length;
  const sorted = limit ? [...kept].sort(byImportance) : kept;
  const skipNote =
    skipped > 0 ? (
      <p className={styles["empty"]}>
        정기 보고서·임원 지분 보고 같은 참고용 공시 {skipped.toLocaleString("ko-KR")}건은 뺐어요.
      </p>
    ) : null;

  if (sorted.length === 0)
    return (
      <>
        <p className={styles["empty"]}>중요 공시는 없어요.</p>
        {skipNote}
      </>
    );

  return (
    <>
      <ShowMore items={sorted} limit={limit ?? sorted.length}>
        {(shown) => (
          <ul className={styles["list"]}>
            {shown.map((d) => (
              <Item key={d.rcept_no} d={d} />
            ))}
          </ul>
        )}
      </ShowMore>
      {skipNote}
    </>
  );
}
