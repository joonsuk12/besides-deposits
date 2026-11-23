"use client";
// 종목 소식 카드: [이번 주 많이 다뤄진 뉴스 | 최근 공시 | 증권사 리포트]를 탭 하나로.
// 예전에는 뉴스는 가운데, 공시·리포트는 오른쪽에 따로 쌓여 오른쪽이 아주 길었다 (2026-11-23 정리).
// ETF는 회사 공시·리포트가 없어서 뉴스 탭만 보여준다.

import { useState } from "react";

import DisclosureList from "@/components/DisclosureList/DisclosureList";
import NewsList from "@/components/NewsList/NewsList";
import ReportCard from "@/components/ReportCard/ReportCard";
import ToneFilter, { type Tone } from "@/components/ToneFilter/ToneFilter";
import type { DisclosureList as Disclosures, News, Report } from "@/lib/api";
import styles from "./StockFeed.module.css";

type Tab = "news" | "disc" | "report";

const reportTone = (r: Report): Tone | null =>
  r.goal_change === "상향" ? "good" : r.goal_change === "하향" ? "bad" : null;

export default function StockFeed({
  code,
  isEtf,
  keyNews,
  disclosures,
  reports,
}: {
  code: string;
  isEtf: boolean;
  keyNews: News[];
  disclosures: Disclosures | null;
  reports: Report[]; // 최신순
}) {
  const [tab, setTab] = useState<Tab>("news");
  const tabs: { key: Tab; label: string }[] = isEtf
    ? [{ key: "news", label: "📰 많이 다뤄진 뉴스" }]
    : [
        { key: "news", label: "📰 많이 다뤄진 뉴스" },
        { key: "disc", label: "📢 최근 공시" },
        { key: "report", label: "📄 증권사 리포트" },
      ];
  const current = isEtf ? "news" : tab;

  return (
    <section className={styles["feed"]}>
      <div className={styles["tabs"]} role="tablist">
        {tabs.map((t) => (
          <button
            key={t.key}
            role="tab"
            aria-selected={current === t.key}
            className={current === t.key ? styles["on"] : ""}
            onClick={() => setTab(t.key)}
          >
            {t.label}
          </button>
        ))}
      </div>

      {current === "news" && (
        <>
          <p className={styles["desc"]}>
            최근 7일 동안 여러 언론사가 같은 내용을 다룬 뉴스예요. 많이 다룰수록 중요한 소식일 가능성이 커요.
          </p>
          <NewsList items={keyNews} empty="최근 7일 동안 여러 언론사가 함께 다룬 뉴스가 없습니다." />
        </>
      )}

      {current === "disc" && (
        <>
          {!disclosures && <p className={styles["desc"]}>불러오는 중…</p>}
          {disclosures && !disclosures.available && <p className={styles["desc"]}>{disclosures.message}</p>}
          {disclosures?.available && (
            <DisclosureList
              key={code}
              items={disclosures.items}
              limit={5}
              skipInfo
              empty="최근 1년 동안 공시가 없습니다."
            />
          )}
        </>
      )}

      {current === "report" && (
        <>
          {reports.length === 0 && (
            <p className={styles["desc"]}>최근 나온 리포트가 없습니다. 소형주는 리포트가 드뭅니다.</p>
          )}
          <ToneFilter
            key={code}
            items={reports}
            toneOf={reportTone}
            labels={{ good: "▲ 목표가 상향", bad: "▼ 목표가 하향" }}
          >
            {(shown) => (
              <div className={styles["stack"]}>
                {shown.map((r) => (
                  <ReportCard key={r.nid} report={r} compact showStock={false} />
                ))}
              </div>
            )}
          </ToneFilter>
        </>
      )}
    </section>
  );
}
