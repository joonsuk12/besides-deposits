"use client";

// 내 관심종목 화면 (주소: /watchlist).
// 종목마다 최근 종가, 최신 증권사 리포트 요약, 이번 주 많이 다뤄진 뉴스, 최근 공시를 한눈에 본다.

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

type Extra = { reports: Report[]; news: News[]; disclosures: Disclosures | null };

export default function WatchlistPage() {
  const [items, setItems] = useState<WatchlistItem[] | null>(null);
  const [extra, setExtra] = useState<Record<string, Extra>>({});
  const [error, setError] = useState(false);

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
            setExtra((prev) => ({ ...prev, [s.code]: { reports, news, disclosures } })),
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
        <p>종목마다 최신 증권사 리포트 요약과 이번 주 많이 다뤄진 뉴스를 모아 봅니다. 종목 추가는 차트 화면의 ☆로 합니다.</p>
      </div>

      {error && <p className={styles["notice"]}>백엔드(8100번 포트)에 연결하지 못했습니다.</p>}
      {items?.length === 0 && <p className={styles["notice"]}>아직 관심 종목이 없습니다. 종목을 검색해서 ☆를 눌러 주세요.</p>}

      <div className={styles["list"]}>
        {items?.map((s) => {
          const t = s.change === null ? "" : s.change > 0 ? "up" : s.change < 0 ? "down" : "";
          const ex = extra[s.code];
          const topNews = ex ? [...ex.news].sort((a, b) => b.cluster_size - a.cluster_size).slice(0, 3) : [];
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
                  <Link href={`/${s.code}`} className={styles["btn"]}>
                    차트 보기
                  </Link>
                  <button className={styles["btn-ghost"]} onClick={() => handleRemove(s.code)}>
                    관심 해제
                  </button>
                </div>
              </header>

              <div className={styles["sections"]}>
                <section className={styles["section"]}>
                  <h2>📄 최신 증권사 리포트</h2>
                  {!ex && <p className={styles["placeholder"]}>불러오는 중…</p>}
                  {ex && ex.reports.length === 0 && (
                    <p className={styles["placeholder"]}>최근 나온 리포트가 없습니다. ETF나 소형주는 리포트가 드뭅니다.</p>
                  )}
                  {ex && ex.reports[0] && <ReportCard report={ex.reports[0]} compact showStock={false} />}
                  {ex && ex.reports.length > 1 && (
                    <Link href={`/${s.code}`} className={styles["ext"]}>
                      이전 리포트 {ex.reports.length - 1}건 더 보기 →
                    </Link>
                  )}
                </section>
                <section className={styles["section"]}>
                  <h2>📰 이번 주 주요 뉴스</h2>
                  {!ex && <p className={styles["placeholder"]}>불러오는 중…</p>}
                  {ex && <NewsList items={topNews} empty="최근 7일 동안 뉴스가 없습니다." />}
                </section>
                <section className={styles["section"]}>
                  <h2>💰 주가 수준 (PER·PBR)</h2>
                  <ValuationCard code={s.code} compact />
                </section>
              </div>
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
            </article>
          );
        })}
      </div>
    </div>
  );
}
