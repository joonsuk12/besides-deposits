"use client";

// 홈 화면 (주소: /). 매일 열면 "오늘 무슨 일이 있었지?"를 한 화면에서 본다.
//   관심종목이 있으면: 종목별 오늘 등락과 최근 3일 소식 개수 → 최근 3일 새 소식(공시·리포트·뉴스) → 오늘의 리포트 요약
//   관심종목이 없으면(처음 방문): 시작 안내 3단계 + 오늘의 리포트 요약
// 처음 온 사람을 위한 긴 소개는 /intro, 기능 설명은 /guide에 있다.

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

import ShowMore from "@/components/ShowMore/ShowMore";
import SiteNote from "@/components/SiteNote/SiteNote";
import {
  fetchReportFeed,
  fetchStockDisclosures,
  fetchStockNews,
  fetchStockReports,
  fetchWatchlist,
  type Disclosure,
  type News,
  type Report,
  type ReportFeed,
  type WatchlistItem,
} from "@/lib/api";
import styles from "./home.module.css";

const RECENT_DAYS = 3; // 주말을 넘겨도 지난 거래일 소식이 보이게 3일
const WEEKDAYS = ["일", "월", "화", "수", "목", "금", "토"];
const won = (n: number) => n.toLocaleString("ko-KR");

type Recent = { disclosures: Disclosure[]; reports: Report[]; news: News[] };

// 최근 소식 한 줄 (공시·리포트·뉴스를 한 목록에 섞어 최신순으로)
type Item = {
  key: string;
  date: string;
  stock: string;
  code: string;
  kind: "공시" | "리포트" | "뉴스";
  title: string;
  href: string;
  external: boolean;
  tone: "good" | "bad" | "check" | null;
};

const TONE_LABEL = { good: "좋은 소식", bad: "나쁜 소식", check: "내용 확인" };
const KIND_ORDER = { 공시: 0, 리포트: 1, 뉴스: 2 };
const NEWS_PER_STOCK = 2;

function sinceDate(days: number) {
  const d = new Date(Date.now() - days * 86400000);
  return d.toISOString().slice(0, 10);
}

export default function HomePage() {
  const [watchlist, setWatchlist] = useState<WatchlistItem[] | null>(null);
  const [recent, setRecent] = useState<Record<string, Recent>>({});
  const [feed, setFeed] = useState<ReportFeed | null>(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    fetchReportFeed().then(setFeed).catch(() => {});
    fetchWatchlist()
      .then((list) => {
        setWatchlist(list);
        const since = sinceDate(RECENT_DAYS);
        // 종목마다 따로 불러와 도착하는 대로 채운다
        for (const s of list) {
          Promise.all([
            fetchStockDisclosures(s.code, RECENT_DAYS).catch(() => null),
            fetchStockReports(s.code, 5).catch(() => []),
            fetchStockNews(s.code, RECENT_DAYS).catch(() => []),
          ]).then(([d, reports, news]) =>
            setRecent((prev) => ({
              ...prev,
              [s.code]: {
                // 참고용(정기 보고서·지분 보고)은 홈에서 뺀다
                disclosures: (d?.available ? d.items : []).filter((x) => x.level !== "info"),
                reports: reports.filter((r) => r.write_date >= since),
                news,
              },
            })),
          );
        }
      })
      .catch(() => setError(true));
  }, []);

  const items: Item[] = useMemo(() => {
    if (!watchlist) return [];
    const out: Item[] = [];
    for (const s of watchlist) {
      const r = recent[s.code];
      if (!r) continue;
      for (const d of r.disclosures)
        out.push({
          key: `d${d.rcept_no}`,
          date: d.date,
          stock: s.name,
          code: s.code,
          kind: "공시",
          title: d.title,
          href: d.url,
          external: true,
          tone: d.level === "good" ? "good" : d.level === "warn" ? "bad" : "check",
        });
      for (const rep of r.reports)
        out.push({
          key: `r${rep.nid}`,
          date: rep.write_date,
          stock: s.name,
          code: s.code,
          kind: "리포트",
          title: rep.easy?.one_liner ?? rep.headline ?? rep.title,
          href: `/${s.code}`,
          external: false,
          tone: rep.goal_change === "상향" ? "good" : rep.goal_change === "하향" ? "bad" : null,
        });
      // 뉴스는 종목마다 가장 많이 다뤄진 2건만 — 다 넣으면 뉴스 많은 종목이 목록을 덮는다
      const topNews = r.news
        .filter((x) => x.cluster_size > 1)
        .sort((a, b) => b.cluster_size - a.cluster_size)
        .slice(0, NEWS_PER_STOCK);
      for (const n of topNews)
        out.push({
          key: `n${n.id}`,
          date: n.date,
          stock: s.name,
          code: s.code,
          kind: "뉴스",
          title: n.title,
          href: n.url,
          external: true,
          tone: n.tone === "good" ? "good" : n.tone === "bad" ? "bad" : null,
        });
    }
    // 최신순. 같은 날이면 공시 → 리포트 → 뉴스
    return out.sort((a, b) => b.date.localeCompare(a.date) || KIND_ORDER[a.kind] - KIND_ORDER[b.kind]);
  }, [watchlist, recent]);

  const today = new Date();
  const todayLabel = `${today.getMonth() + 1}월 ${today.getDate()}일 (${WEEKDAYS[today.getDay()]})`;
  const firstVisit = watchlist?.length === 0;

  return (
    <div className={styles["page"]}>
      <div className={styles["head"]}>
        <div>
          <p className={styles["date"]}>{todayLabel}</p>
          <h1>{firstVisit ? "주식초보나들이에 오신 걸 환영해요" : "오늘 볼 것"}</h1>
        </div>
        <div className={styles["head-links"]}>
          <Link href="/guide">처음이라면 도움말 →</Link>
        </div>
      </div>

      {error && <p className={styles["notice"]}>백엔드(8100번 포트)에 연결하지 못했습니다.</p>}

      {firstVisit && (
        <section className={styles["welcome"]}>
          <p>관심 있는 종목을 모아 두면, 이 화면에서 매일 그 종목의 새 공시·리포트·뉴스를 한 번에 볼 수 있어요.</p>
          <ol>
            <li>
              맨 위 검색창에서 종목 이름을 찾아요. <span>예: 삼성전자</span>
            </li>
            <li>
              차트 화면에서 종목 이름 옆 <b>☆</b>을 눌러 관심종목에 담아요.
            </li>
            <li>홈으로 돌아오면 그 종목의 오늘 소식이 모여 있어요.</li>
          </ol>
          <p className={styles["sub"]}>
            서비스가 처음이라면 <Link href="/intro">서비스 소개</Link>나 <Link href="/guide">도움말</Link>을 먼저 둘러보세요.
          </p>
        </section>
      )}

      {watchlist && watchlist.length > 0 && (
        <>
          <section className={styles["section"]}>
            <h2>
              내 관심종목 <span className={styles["count"]}>{watchlist.length}</span>
            </h2>
            <div className={styles["stocks"]}>
              {watchlist.map((s) => {
                const r = recent[s.code];
                const t = s.change === null ? "" : s.change > 0 ? "up" : s.change < 0 ? "down" : "";
                const bad = r ? r.disclosures.filter((d) => d.level === "warn").length : 0;
                const good = r ? r.disclosures.filter((d) => d.level === "good").length : 0;
                return (
                  <Link key={s.code} href={`/${s.code}`} className={styles["stock"]}>
                    <div className={styles["stock-name"]}>{s.name}</div>
                    {s.close !== null && (
                      <div className="num">
                        <b>{won(s.close)}</b>{" "}
                        {s.change_pct !== null && (
                          <span className={t}>
                            {s.change_pct > 0 ? "+" : ""}
                            {s.change_pct.toFixed(2)}%
                          </span>
                        )}
                      </div>
                    )}
                    <div className={styles["badges"]}>
                      {!r && <span className={styles["muted"]}>불러오는 중…</span>}
                      {r && bad > 0 && <span className={`${styles["badge"]} ${styles["bad"]}`}>나쁜 공시 {bad}</span>}
                      {r && good > 0 && <span className={`${styles["badge"]} ${styles["good"]}`}>좋은 공시 {good}</span>}
                      {r && r.reports.length > 0 && <span className={styles["badge"]}>리포트 {r.reports.length}</span>}
                      {r && r.news.length > 0 && <span className={styles["badge"]}>뉴스 {r.news.length}</span>}
                      {r && !bad && !good && !r.reports.length && !r.news.length && (
                        <span className={styles["muted"]}>최근 {RECENT_DAYS}일 조용해요</span>
                      )}
                    </div>
                  </Link>
                );
              })}
            </div>
          </section>

          <section className={styles["section"]}>
            <h2>최근 {RECENT_DAYS}일 새 소식</h2>
            <p className={styles["desc"]}>
              관심종목의 중요 공시, 증권사 리포트, 여러 언론사가 함께 다룬 뉴스를 최신순으로 모았어요.
            </p>
            {items.length === 0 && <p className={styles["muted"]}>아직 모인 소식이 없어요.</p>}
            <ShowMore items={items} limit={8}>
              {(shown) => (
                <ul className={styles["feed"]}>
                  {shown.map((it) => (
                    <li key={it.key}>
                      <span className={styles["feed-date"]}>{it.date.slice(5)}</span>
                      <span className={`${styles["kind"]} ${styles[`kind-${it.kind}`]}`}>{it.kind}</span>
                      <Link href={`/${it.code}`} className={styles["feed-stock"]}>
                        {it.stock}
                      </Link>
                      {it.external ? (
                        <a href={it.href} target="_blank" rel="noreferrer" className={styles["feed-title"]}>
                          {it.title}
                        </a>
                      ) : (
                        <Link href={it.href} className={styles["feed-title"]}>
                          {it.title}
                        </Link>
                      )}
                      {it.tone && (
                        <span className={`${styles["tone"]} ${styles[it.tone]}`}>{TONE_LABEL[it.tone]}</span>
                      )}
                    </li>
                  ))}
                </ul>
              )}
            </ShowMore>
          </section>
        </>
      )}

      <section className={styles["section"]}>
        <h2>
          오늘의 리포트 {feed && <span className={styles["count"]}>{feed.total}</span>}
        </h2>
        {!feed && <p className={styles["muted"]}>불러오는 중…</p>}
        {feed && feed.total === 0 && <p className={styles["muted"]}>오늘은 아직 나온 리포트가 없어요.</p>}
        {feed && feed.total > 0 && (
          <>
            <p className={styles["desc"]}>
              {feed.date} 기준 · 목표주가 상향 {feed.reports.filter((r) => r.goal_change === "상향").length}건 · 하향{" "}
              {feed.reports.filter((r) => r.goal_change === "하향").length}건
            </p>
            <ul className={styles["feed"]}>
              {feed.reports.slice(0, 5).map((r) => (
                <li key={r.nid}>
                  <Link href={`/${r.item_code}`} className={styles["feed-stock"]}>
                    {r.item_name}
                  </Link>
                  <span className={styles["feed-title"]}>{r.easy?.one_liner ?? r.headline ?? r.title}</span>
                  <span className={styles["feed-date"]}>{r.broker}</span>
                </li>
              ))}
            </ul>
            <Link href="/reports" className={styles["more"]}>
              오늘의 리포트 전체 보기 →
            </Link>
          </>
        )}
      </section>

      <SiteNote />
    </div>
  );
}
