"use client";

// 오늘의 리포트 (주소: /reports). 그날 나온 증권사 종목 리포트 전체를 초보용 요약으로 본다.

import { useEffect, useMemo, useState } from "react";

import ReportCard from "@/components/ReportCard/ReportCard";
import { fetchReportFeed, fetchWatchlist, type Report } from "@/lib/api";
import styles from "./reports.module.css";

const FILTERS = [
  { key: "all", label: "전체" },
  { key: "watch", label: "⭐ 내 관심종목" },
  { key: "up", label: "▲ 목표주가 상향" },
  { key: "down", label: "▼ 목표주가 하향" },
  { key: "noop", label: "의견 없음 (산업·탐방)" },
] as const;
type FilterKey = (typeof FILTERS)[number]["key"];

const toIso = (d: Date) => {
  const tz = d.getTimezoneOffset() * 60000;
  return new Date(d.getTime() - tz).toISOString().slice(0, 10);
};
const shiftDay = (iso: string, days: number) => {
  const d = new Date(`${iso}T00:00:00`);
  d.setDate(d.getDate() + days);
  return toIso(d);
};
const WEEKDAY = ["일", "월", "화", "수", "목", "금", "토"];

export default function ReportsPage() {
  const today = toIso(new Date());
  const [day, setDay] = useState(today);
  const [reports, setReports] = useState<Report[] | null>(null);
  const [watchCodes, setWatchCodes] = useState<Set<string>>(new Set());
  const [filter, setFilter] = useState<FilterKey>("all");
  const [query, setQuery] = useState("");
  const [error, setError] = useState(false);

  useEffect(() => {
    fetchWatchlist()
      .then((list) => setWatchCodes(new Set(list.map((s) => s.code))))
      .catch(() => {});
  }, []);

  useEffect(() => {
    setReports(null);
    setError(false);
    fetchReportFeed(day)
      .then((feed) => setReports(feed.reports))
      .catch(() => setError(true));
  }, [day]);

  const shown = useMemo(() => {
    if (!reports) return [];
    const q = query.trim();
    return reports
      .filter((r) => {
        if (filter === "watch" && !watchCodes.has(r.item_code)) return false;
        if (filter === "up" && r.goal_change !== "상향") return false;
        if (filter === "down" && r.goal_change !== "하향") return false;
        if (filter === "noop" && (r.opinion || r.goal_price)) return false;
        return !q || r.item_name.includes(q) || r.broker.includes(q) || r.title.includes(q);
      })
      .sort((a, b) => Number(watchCodes.has(b.item_code)) - Number(watchCodes.has(a.item_code)));
  }, [reports, filter, query, watchCodes]);

  const counts = useMemo(() => {
    const list = reports ?? [];
    return {
      all: list.length,
      watch: list.filter((r) => watchCodes.has(r.item_code)).length,
      up: list.filter((r) => r.goal_change === "상향").length,
      down: list.filter((r) => r.goal_change === "하향").length,
      noop: list.filter((r) => !r.opinion && !r.goal_price).length,
    };
  }, [reports, watchCodes]);

  const weekday = WEEKDAY[new Date(`${day}T00:00:00`).getDay()];

  return (
    <div className={styles["page"]}>
      <div className={styles["head"]}>
        <div>
          <h1>오늘의 리포트</h1>
          <p>증권사 애널리스트가 쓴 종목 리포트를 초보 눈높이로 정리했습니다. 매수·매도 권유가 아니라 리포트 내용 정리입니다.</p>
        </div>
        <div className={styles["day-nav"]}>
          <button onClick={() => setDay(shiftDay(day, -1))}>◀</button>
          <span>
            {day} ({weekday})
          </span>
          <button onClick={() => setDay(shiftDay(day, 1))} disabled={day >= today}>
            ▶
          </button>
        </div>
      </div>

      <div className={styles["tools"]}>
        <div className={styles["filters"]}>
          {FILTERS.map((f) => (
            <button
              key={f.key}
              className={`${styles["chip"]} ${filter === f.key ? styles["active"] : ""}`}
              onClick={() => setFilter(f.key)}
            >
              {f.label} <span className={styles["count"]}>{counts[f.key]}</span>
            </button>
          ))}
        </div>
        <input
          className={styles["search"]}
          placeholder="종목·증권사 검색"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
      </div>

      {error && <p className={styles["notice"]}>리포트를 불러오지 못했습니다. 백엔드(8100번 포트)를 확인해 주세요.</p>}
      {!error && reports === null && <p className={styles["notice"]}>리포트를 불러오는 중… (처음 여는 날짜는 몇 초 걸립니다)</p>}
      {reports?.length === 0 && <p className={styles["notice"]}>이 날은 나온 리포트가 없습니다. 주말·휴일이면 전날을 확인해 보세요.</p>}
      {reports && reports.length > 0 && shown.length === 0 && <p className={styles["notice"]}>조건에 맞는 리포트가 없습니다.</p>}

      <div className={styles["grid"]}>
        {shown.map((r) => (
          <ReportCard key={r.nid} report={r} compact />
        ))}
      </div>
    </div>
  );
}
