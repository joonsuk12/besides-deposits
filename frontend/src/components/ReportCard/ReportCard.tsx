"use client";
// 증권사 리포트 한 건을 초보용 틀로 보여주는 카드.
// compact: 한 줄 결론과 숫자만 (목록용) / 기본: 근거·리스크·용어까지

import Link from "next/link";
import { useState } from "react";

import type { Report } from "@/lib/api";
import styles from "./ReportCard.module.css";

const won = (n: number) => n.toLocaleString("ko-KR");

const OPINION_CLASS = { buy: styles["op-buy"], neutral: styles["op-neutral"], sell: styles["op-sell"] };

export default function ReportCard({
  report: r,
  compact = false,
  showStock = true,
}: {
  report: Report;
  compact?: boolean;
  showStock?: boolean;
}) {
  const [open, setOpen] = useState(!compact);

  return (
    <article className={styles["card"]}>
      <header className={styles["head"]}>
        {showStock && (
          <Link href={`/${r.item_code}`} className={styles["stock"]}>
            {r.item_name}
          </Link>
        )}
        <span className={styles["meta"]}>
          {r.broker} · {r.write_date}
        </span>
      </header>

      <p className={styles["headline"]}>💡 {r.headline}</p>

      <div className={styles["badges"]}>
        {r.opinion && (
          <span className={`${styles["badge"]} ${r.opinion_type ? OPINION_CLASS[r.opinion_type] : ""}`}>
            투자의견 {r.opinion}
          </span>
        )}
        {r.goal_price && (
          <span className={styles["badge"]}>
            목표주가 {won(r.goal_price)}원
            {r.goal_change === "상향" && <b className="up"> ▲ 상향</b>}
            {r.goal_change === "하향" && <b className="down"> ▼ 하향</b>}
            {r.goal_change === "유지" && <b> 유지</b>}
            {r.prev_goal_price && r.goal_change !== "유지" && (
              <span className={styles["prev"]}> (이전 {won(r.prev_goal_price)})</span>
            )}
          </span>
        )}
        {r.gap_pct !== null && (
          <span className={styles["badge"]} title="최근 종가와 이 리포트 목표주가의 차이입니다. 증권사의 예상일 뿐입니다.">
            최근 종가와 차이 {r.gap_pct > 0 ? "+" : ""}
            {r.gap_pct}%
          </span>
        )}
        {!r.opinion && !r.goal_price && <span className={styles["badge"]}>투자의견·목표주가 없음</span>}
      </div>

      {open && (
        <div className={styles["body"]}>
          {r.points.length > 0 && (
            <section>
              <h4>핵심 근거</h4>
              <ul>
                {r.points.map((p) => (
                  <li key={p}>{p}</li>
                ))}
              </ul>
            </section>
          )}
          {r.risks.length > 0 && (
            <section className={styles["risk"]}>
              <h4>⚠ 조심할 점</h4>
              <ul>
                {r.risks.map((p) => (
                  <li key={p}>{p}</li>
                ))}
              </ul>
            </section>
          )}
          {r.terms.length > 0 && (
            <section className={styles["terms"]}>
              <h4>📖 용어 풀이</h4>
              <dl>
                {r.terms.map((t) => (
                  <div key={t.term}>
                    <dt>{t.term}</dt>
                    <dd>{t.meaning}</dd>
                  </div>
                ))}
              </dl>
            </section>
          )}
        </div>
      )}

      <footer className={styles["foot"]}>
        <span className={styles["title"]}>「{r.title}」</span>
        <span className={styles["actions"]}>
          {compact && (
            <button onClick={() => setOpen((v) => !v)}>{open ? "접기" : "자세히"}</button>
          )}
          <a href={r.url} target="_blank" rel="noreferrer">
            원문 ↗
          </a>
        </span>
      </footer>
    </article>
  );
}
