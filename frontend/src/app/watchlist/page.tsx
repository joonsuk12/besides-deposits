"use client";

// 내 관심종목 화면 (주소: /watchlist).
// 종목마다 최근 종가, 최신 증권사 리포트 요약, 이번 주 많이 다뤄진 뉴스, 최근 공시를 한눈에 본다.
// 종목이 많으면 페이지가 너무 길어져서(예전 약 6,400px), 처음에는 종목마다 한 줄 요약만 보이고 눌러서 펼친다.

import Link from "next/link";
import { useEffect, useState } from "react";

import DisclosureList from "@/components/DisclosureList/DisclosureList";
import NewsList from "@/components/NewsList/NewsList";
import ReportCard from "@/components/ReportCard/ReportCard";
import ValuationCard from "@/components/ValuationCard/ValuationCard";
import StockProfile from "@/components/StockProfile/StockProfile";
import {
  fetchStockDisclosures,
  fetchStockNews,
  fetchStockReports,
  fetchWatchlist,
  removeWatch,
  type DisclosureList as Disclosures,
  type News,
  type Report,
  type WatchlistItem,
} from "@/lib/api";
import styles from "./watchlist.module.css";

const won = (n: number) => n.toLocaleString("ko-KR");

type Extra = {
  reports: Report[];
  news: News[];
  disclosures: Disclosures | null;
};

export default function WatchlistPage() {
  const [items, setItems] = useState<WatchlistItem[] | null>(null);
  const [extra, setExtra] = useState<Record<string, Extra>>({});
  const [error, setError] = useState(false);
  const [open, setOpen] = useState<Set<string>>(new Set());
  const toggle = (code: string) =>
    setOpen((prev) => {
      const next = new Set(prev);
      if (next.has(code)) next.delete(code);
      else next.add(code);
      return next;
    });
  const allOpen = !!items && items.length > 0 && items.every((s) => open.has(s.code));

  const load = () =>
    fetchWatchlist()
      .then((list) => {
        setItems(list);
        // 종목마다 리포트·뉴스를 따로 불러와 도착하는 대로 채운다
        for (const s of list) {
          Promise.all([
            fetchStockReports(s.code, 3).catch(() => []),
            fetchStockNews(s.code, 7).catch(() => []),
            fetchStockDisclosures(s.code, 90).catch(() => null),
          ]).then(([reports, news, disclosures]) =>
            setExtra((prev) => ({
              ...prev,
              [s.code]: { reports, news, disclosures },
            })),
          );
        }
      })
      .catch(() => setError(true));

  useEffect(() => {
    load();
  }, []);

  const handleRemove = async (code: string) => {
    await removeWatch(code);
    load();
  };

  return (
    <div className={styles["page"]}>
      <div className={styles["head"]}>
        <h1>내 관심종목</h1>
        <p>
          종목마다 최신 증권사 리포트 요약과 이번 주 많이 다뤄진 뉴스를 모아 봅니다. 종목 추가는 차트 화면의 ☆로 합니다.
        </p>
        {items && items.length > 0 && (
          <button
            className={styles["btn-ghost"]}
            onClick={() => setOpen(allOpen ? new Set() : new Set(items.map((s) => s.code)))}
          >
            {allOpen ? "모두 접기 ▲" : "모두 펼치기 ▼"}
          </button>
        )}
      </div>

      {error && <p className={styles["notice"]}>백엔드(8100번 포트)에 연결하지 못했습니다.</p>}
      {items?.length === 0 && (
        <p className={styles["notice"]}>아직 관심 종목이 없습니다. 종목을 검색해서 ☆를 눌러 주세요.</p>
      )}

      <div className={styles["list"]}>
        {items?.map((s) => {
          const t = s.change === null ? "" : s.change > 0 ? "up" : s.change < 0 ? "down" : "";
          const ex = extra[s.code];
          const isEtf = s.market === "ETF";
          const topNews = ex ? [...ex.news].sort((a, b) => b.cluster_size - a.cluster_size).slice(0, 3) : [];
          const isOpen = open.has(s.code);
          // 접었을 때 보여줄 한 줄 요약
          const important = ex?.disclosures?.available ? ex.disclosures.items.filter((d) => d.level !== "info") : [];
          const goodD = important.filter((d) => d.level === "good").length;
          const badD = important.filter((d) => d.level === "warn").length;
          return (
            <article key={s.code} className={styles["card"]}>
              <header className={styles["card-head"]}>
                <Link href={`/${s.code}`} className={styles["name"]}>
                  <StockProfile stockName={s.name} stockId={s.code} stockMarket={s.market} />
                </Link>
                {s.close !== null && (
                  <div className={styles["quote"]}>
                    <span className={styles["price"]}>{won(s.close)}원</span>
                    {s.change !== null && s.change_pct !== null && (
                      <span className={t}>
                        {s.change > 0 ? "+" : ""}
                        {won(s.change)} ({s.change > 0 ? "+" : ""}
                        {s.change_pct.toFixed(2)}%)
                      </span>
                    )}
                    <span className={styles["asof"]}>{s.date} 종가</span>
                  </div>
                )}
                <div className={styles["actions"]}>
                  <button className={styles["btn-ghost"]} onClick={() => toggle(s.code)} aria-expanded={isOpen}>
                    {isOpen ? "접기 ▲" : "펼치기 ▼"}
                  </button>
                  <Link href={`/${s.code}`} className={styles["btn"]}>
                    차트 보기
                  </Link>
                  <button className={styles["btn-ghost"]} onClick={() => handleRemove(s.code)}>
                    관심 해제
                  </button>
                </div>
              </header>

              {!isOpen && (
                <button className={styles["summary"]} onClick={() => toggle(s.code)}>
                  {!ex && <span>불러오는 중…</span>}
                  {ex && (
                    <>
                      {!isEtf && <span>최근 리포트 {ex.reports.length}</span>}
                      <span>이번 주 뉴스 {ex.news.length}</span>
                      {!isEtf && <span className={styles["good"]}>좋은 공시 {goodD}</span>}
                      {!isEtf && <span className={styles["bad"]}>나쁜 공시 {badD}</span>}
                      {ex.reports[0]?.easy && <span className={styles["one"]}>🧒 {ex.reports[0].easy.one_liner}</span>}
                    </>
                  )}
                </button>
              )}

              {isOpen && (
                <>
                  {/* ETF는 회사가 아니라 리포트·공시·PER이 없다. 빈 칸 세 개 대신 한 줄로 알려 준다 */}
                  {isEtf && (
                    <p className={styles["placeholder"]}>
                      ETF는 회사가 아니라서 증권사 리포트·공시·PER이 없어요. 뉴스만 모아 봐요.
                    </p>
                  )}
                  {!isEtf && ex && ex.reports.length === 0 && (
                    <p className={styles["placeholder"]}>
                      최근 나온 증권사 리포트가 없어요. 소형주는 리포트가 드물어요.
                    </p>
                  )}
                  <div className={styles["sections"]}>
                    {/* 리포트가 있을 때만 칸을 만든다 */}
                    {!isEtf && (!ex || ex.reports.length > 0) && (
                      <section className={styles["section"]}>
                        <h2>📄 최신 증권사 리포트</h2>
                        {!ex && <p className={styles["placeholder"]}>불러오는 중…</p>}
                        {ex && ex.reports[0] && <ReportCard report={ex.reports[0]} compact showStock={false} />}
                        {ex && ex.reports.length > 1 && (
                          <Link href={`/${s.code}`} className={styles["ext"]}>
                            이전 리포트 {ex.reports.length - 1}건 더 보기 →
                          </Link>
                        )}
                      </section>
                    )}
                    <section className={styles["section"]}>
                      <h2>📰 이번 주 주요 뉴스</h2>
                      {!ex && <p className={styles["placeholder"]}>불러오는 중…</p>}
                      {ex && <NewsList items={topNews} empty="최근 7일 동안 뉴스가 없습니다." />}
                    </section>
                    {!isEtf && (
                      <section className={styles["section"]}>
                        <h2>💰 주가 수준 (PER·PBR)</h2>
                        <ValuationCard code={s.code} compact />
                      </section>
                    )}
                  </div>
                  {!isEtf && (
                    <section className={`${styles["section"]} ${styles["disclosure"]}`}>
                      <h2>📢 최근 3개월 공시</h2>
                      {!ex && <p className={styles["placeholder"]}>불러오는 중…</p>}
                      {ex && !ex.disclosures && <p className={styles["placeholder"]}>공시를 불러오지 못했습니다.</p>}
                      {ex?.disclosures && !ex.disclosures.available && (
                        <p className={styles["placeholder"]}>{ex.disclosures.message}</p>
                      )}
                      {ex?.disclosures?.available && (
                        <>
                          {ex.disclosures.message && <p className={styles["placeholder"]}>{ex.disclosures.message}</p>}
                          <DisclosureList
                            items={ex.disclosures.items}
                            limit={3}
                            skipInfo
                            empty="최근 3개월 동안 공시가 없습니다. ETF는 회사 공시가 없어요."
                          />
                        </>
                      )}
                    </section>
                  )}
                </>
              )}
            </article>
          );
        })}
      </div>
    </div>
  );
}
