"use client";
// 선택한 날의 뉴스·공시·리포트를 보여주는 옆 패널(드로어).
// - 화면을 덮는 팝업이 아니라 오른쪽에 붙는 패널이라, 열어 둔 채로 차트의 다른 날을 누르면 내용만 바뀐다
// - 휴대폰(좁은 화면)에서는 아래에서 올라오는 시트로 보인다
// - Esc나 ✕로 닫는다

import { useEffect } from "react";

import DisclosureList from "@/components/DisclosureList/DisclosureList";
import NewsList from "@/components/NewsList/NewsList";
import ReportCard from "@/components/ReportCard/ReportCard";
import ShowMore from "@/components/ShowMore/ShowMore";
import ToneFilter, { type Tone } from "@/components/ToneFilter/ToneFilter";
import type { DisclosureList as Disclosures, News, Report } from "@/lib/api";
import styles from "./DayDrawer.module.css";

export type DayTab = "news" | "disc" | "report";

const newsTone = (n: News): Tone | null => (n.tone === "good" ? "good" : n.tone === "bad" ? "bad" : null);

export default function DayDrawer({
  title,
  priceLine,
  tab,
  onTab,
  onClose,
  news,
  disclosures,
  reports,
}: {
  title: string; // 예: "2026-08-24 (월)"
  priceLine: React.ReactNode; // 종가·등락 한 줄
  tab: DayTab;
  onTab: (t: DayTab) => void;
  onClose: () => void;
  news: News[];
  disclosures: Disclosures["items"];
  reports: Report[];
}) {
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  const tabs: { key: DayTab; label: string; n: number }[] = [
    { key: "news", label: "📰 뉴스", n: news.length },
    { key: "disc", label: "📢 공시", n: disclosures.length },
    { key: "report", label: "📄 리포트", n: reports.length },
  ];

  return (
    <aside className={styles["drawer"]} role="dialog" aria-label={`${title}의 소식`}>
      <div className={styles["head"]}>
        <div>
          <b className={styles["title"]}>{title}</b>
          <div className={styles["price"]}>{priceLine}</div>
        </div>
        <button className="ui-btn-ghost" onClick={onClose} aria-label="닫기">
          ✕
        </button>
      </div>
      <div className={styles["tabs"]} role="tablist">
        {tabs.map((t) => (
          <button
            key={t.key}
            role="tab"
            aria-selected={tab === t.key}
            className={`ui-chip ${tab === t.key ? "on" : ""}`}
            onClick={() => onTab(t.key)}
          >
            {t.label} {t.n}
          </button>
        ))}
      </div>
      <div className={styles["body"]}>
        {tab === "news" && (
          <ToneFilter
            key={`news-${title}`}
            items={news}
            toneOf={newsTone}
            labels={{ good: "좋은 소식(추정)", bad: "나쁜 소식(추정)" }}
          >
            {(shown) => <NewsList items={shown} empty="이날 수집된 뉴스가 없습니다. (최근 뉴스 위주로 모읍니다)" />}
          </ToneFilter>
        )}
        {tab === "disc" && (
          <DisclosureList key={`disc-${title}`} items={disclosures} limit={5} empty="이날 나온 공시가 없습니다." />
        )}
        {tab === "report" && (
          <>
            {reports.length === 0 && <p className={styles["muted"]}>이날 나온 리포트가 없습니다.</p>}
            <ShowMore key={`report-${title}`} items={reports} limit={5}>
              {(shown) => (
                <div className={styles["stack"]}>
                  {shown.map((r) => (
                    <ReportCard key={r.nid} report={r} compact showStock={false} />
                  ))}
                </div>
              )}
            </ShowMore>
          </>
        )}
      </div>
      <p className={styles["foot"]}>열어 둔 채로 차트의 다른 날을 누르면 그날 소식으로 바뀌어요.</p>
    </aside>
  );
}
