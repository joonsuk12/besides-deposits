"use client";
// 종목 뉴스 목록. 각 뉴스의 키포인트(한 줄 요약, 다룬 기사 수, 분위기, 주제)를 보여준다.

import type { News } from "@/lib/api";
import styles from "./NewsList.module.css";

const TONE = {
  good: { label: "좋은 소식(추정)", cls: "up" },
  bad: { label: "나쁜 소식(추정)", cls: "down" },
  neutral: null,
};

export default function NewsList({ items, empty }: { items: News[]; empty?: string }) {
  if (items.length === 0) return <p className={styles["empty"]}>{empty ?? "뉴스가 없습니다."}</p>;

  return (
    <ul className={styles["list"]}>
      {items.map((n) => {
        const tone = TONE[n.tone];
        return (
          <li key={n.id} className={styles["item"]}>
            <div className={styles["badges"]}>
              {n.cluster_size > 1 && (
                <span className={`${styles["badge"]} ${n.cluster_size >= 5 ? styles["hot"] : ""}`}>
                  기사 {n.cluster_size}건
                </span>
              )}
              {tone && <span className={`${styles["badge"]} ${tone.cls}`}>{tone.label}</span>}
              {n.topics.map((t) => (
                <span key={t} className={styles["topic"]}>
                  #{t}
                </span>
              ))}
            </div>
            <a href={n.url} target="_blank" rel="noreferrer" className={styles["title"]}>
              {n.title}
            </a>
            <p className={styles["summary"]}>{n.summary}</p>
            <p className={styles["meta"]}>
              {n.office} · {n.published_at.slice(0, 16).replace("T", " ")}
            </p>
          </li>
        );
      })}
    </ul>
  );
}
