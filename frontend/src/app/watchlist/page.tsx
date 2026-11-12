"use client";

// 내 관심종목 화면 (주소: /watchlist).
// 종목마다 최근 종가와 함께 증권사 리포트 요약(3단계), 공시·사업보고서(4단계)를 모아 보는 곳.
// 요약 기능이 붙기 전까지는 원문을 볼 수 있는 무료 사이트로 바로 가는 링크를 둔다.

import Link from "next/link";
import { useEffect, useState } from "react";

import StockProfile from "@/components/StockProfile/StockProfile";
import { fetchWatchlist, removeWatch, type WatchlistItem } from "@/lib/api";
import styles from "./watchlist.module.css";

const won = (n: number) => n.toLocaleString("ko-KR");

// 원문을 볼 수 있는 무료 사이트
const naverResearchUrl = (code: string) =>
  `https://finance.naver.com/research/company_list.naver?searchType=itemCode&itemCode=${code}`;
// DART는 주소로 회사명을 미리 채울 수 없어 검색 화면으로만 보낸다 (2026-11-12 확인)
const DART_SEARCH_URL = "https://dart.fss.or.kr/dsab007/main.do";

export default function WatchlistPage() {
  const [items, setItems] = useState<WatchlistItem[] | null>(null);
  const [error, setError] = useState(false);

  const load = () =>
    fetchWatchlist()
      .then(setItems)
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
        <p>종목마다 증권사 리포트와 공시를 모아 봅니다. 종목 추가는 차트 화면의 ☆로 합니다.</p>
      </div>

      {error && <p className={styles["notice"]}>백엔드(8100번 포트)에 연결하지 못했습니다.</p>}
      {items?.length === 0 && <p className={styles["notice"]}>아직 관심 종목이 없습니다. 종목을 검색해서 ☆를 눌러 주세요.</p>}

      <div className={styles["list"]}>
        {items?.map((s) => {
          const t = s.change === null ? "" : s.change > 0 ? "up" : s.change < 0 ? "down" : "";
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
                  <h2>증권사 리포트</h2>
                  <p className={styles["placeholder"]}>
                    3단계에서 리포트를 모아 <b>초보용 요약</b>(한 줄 결론, 목표주가 변화, 핵심 근거, 리스크, 용어 풀이)으로 보여 줍니다.
                  </p>
                  <a className={styles["ext"]} href={naverResearchUrl(s.code)} target="_blank" rel="noreferrer">
                    지금은 네이버 금융 리서치에서 원문 보기 ↗
                  </a>
                </section>
                <section className={styles["section"]}>
                  <h2>공시 · 사업보고서</h2>
                  <p className={styles["placeholder"]}>
                    4단계에서 실적·증자·전환사채 같은 공시를 모아, 무엇이 중요한지 쉬운 말로 보여 줍니다.
                  </p>
                  <a className={styles["ext"]} href={DART_SEARCH_URL} target="_blank" rel="noreferrer">
                    지금은 DART 전자공시에서 &quot;{s.name}&quot; 검색 ↗
                  </a>
                </section>
              </div>
            </article>
          );
        })}
      </div>
    </div>
  );
}
