"use client";

// 종목 차트 화면 (주소: /005930). NewStocks의 종목 화면 배치를 따른다.
//   왼쪽: 관심 종목 목록 / 가운데: 차트와 그날 뉴스(2단계) / 오른쪽: 선택한 날 정보와 초보 안내

import { use, useCallback, useEffect, useMemo, useState } from "react";
import { FaRegStar, FaStar } from "react-icons/fa";

import StockChart from "@/components/StockChart";
import StockProfile from "@/components/StockProfile/StockProfile";
import WatchlistSidebar from "@/components/WatchlistSidebar/WatchlistSidebar";
import {
  addWatch,
  fetchPrices,
  fetchStock,
  fetchWatchlist,
  removeWatch,
  type Price,
  type Stock,
  type WatchlistItem,
} from "@/lib/api";
import styles from "./stock.module.css";

const PERIODS = [
  { label: "3개월", days: 92 },
  { label: "1년", days: 365 },
  { label: "3년", days: 1095 },
];

const won = (n: number) => n.toLocaleString("ko-KR");
const tone = (n: number) => (n > 0 ? "up" : n < 0 ? "down" : "");
const sign = (n: number) => (n > 0 ? "+" : "");

export default function StockPage({ params }: { params: Promise<{ code: string }> }) {
  const { code } = use(params);

  const [stock, setStock] = useState<Stock | null>(null);
  const [watchlist, setWatchlist] = useState<WatchlistItem[]>([]);
  const [days, setDays] = useState(365);
  const [prices, setPrices] = useState<Price[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedDate, setSelectedDate] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const loadWatchlist = useCallback(() => {
    fetchWatchlist().then(setWatchlist).catch(() => {});
  }, []);

  useEffect(loadWatchlist, [loadWatchlist]);

  useEffect(() => {
    setError(null);
    fetchStock(code)
      .then(setStock)
      .catch(() => setError("종목을 찾을 수 없거나 백엔드(8100번 포트)가 꺼져 있습니다."));
  }, [code]);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    fetchPrices(code, days)
      .then((list) => {
        if (cancelled) return;
        setPrices(list);
        setSelectedDate(list.at(-1)?.date ?? null);
      })
      .catch(() => !cancelled && setPrices([]))
      .finally(() => !cancelled && setLoading(false));
    return () => {
      cancelled = true;
    };
  }, [code, days]);

  const toggleWatch = async () => {
    if (!stock) return;
    const updated = stock.is_watched ? await removeWatch(stock.code) : await addWatch(stock.code);
    setStock(updated);
    loadWatchlist();
  };

  const handleRemove = async (removeCode: string) => {
    await removeWatch(removeCode);
    if (removeCode === code) setStock((s) => (s ? { ...s, is_watched: false } : s));
    loadWatchlist();
  };

  const last = prices.at(-1);
  const prev = prices.at(-2);
  const change = last && prev ? last.close - prev.close : 0;

  // 선택한 날과 그 전날 (등락 계산용)
  const selected = useMemo(() => {
    const i = prices.findIndex((p) => p.date === selectedDate);
    return i < 0 ? null : { day: prices[i], before: prices[i - 1] };
  }, [prices, selectedDate]);
  const dayChange = selected?.before ? selected.day.close - selected.before.close : null;

  return (
    <div className={styles["mainpage"]}>
      <aside className={styles["like-container"]}>
        <WatchlistSidebar items={watchlist} currentCode={code} onRemove={handleRemove} />
      </aside>

      <main className={styles["mid-container"]}>
        {error && <p className={styles["notice"]}>{error}</p>}

        {stock && (
          <div className={styles["chartheader"]}>
            <div className={styles["stockname"]} onClick={toggleWatch} title="관심 종목 추가/제거">
              <StockProfile stockName={stock.name} stockId={stock.code} stockMarket={stock.market} />
              {stock.is_watched ? <FaStar className={styles["star"]} /> : <FaRegStar className={styles["star"]} />}
            </div>
            {last && (
              <div className={styles["price-line"]}>
                <span className={styles["price"]}>{won(last.close)}원</span>
                <span className={`${styles["change"]} ${tone(change)}`}>
                  {sign(change)}
                  {won(change)} ({prev ? `${sign(change)}${((change / prev.close) * 100).toFixed(2)}%` : "-"})
                </span>
                <span className={styles["asof"]}>{last.date} 종가</span>
              </div>
            )}
            <div className={styles["periods"]}>
              {PERIODS.map((p) => (
                <button
                  key={p.days}
                  className={`${styles["chip"]} ${p.days === days ? styles["active"] : ""}`}
                  onClick={() => setDays(p.days)}
                >
                  {p.label}
                </button>
              ))}
            </div>
          </div>
        )}

        <div className={styles["chartbox"]}>
          {loading && <p className={styles["notice"]}>주가를 불러오는 중… (처음 보는 종목은 몇 초 걸립니다)</p>}
          {!loading && prices.length === 0 && !error && (
            <p className={styles["notice"]}>이 종목의 주가 데이터를 가져오지 못했습니다.</p>
          )}
          {!loading && prices.length > 0 && <StockChart prices={prices} onSelectDate={setSelectedDate} />}
        </div>
        <p className={styles["hint"]}>차트에서 날짜를 누르면 그날의 정보가 오른쪽에 나옵니다.</p>

        <section className={styles["news"]}>
          <h2>뉴스</h2>
          <p className={styles["placeholder"]}>
            {selectedDate ?? "날짜"}의 종목 뉴스는 2단계에서 여기에 표시됩니다.
          </p>
        </section>
      </main>

      <aside className={styles["side-container"]}>
        {selected && (
          <section className={styles["card"]}>
            <h2>{selected.day.date}</h2>
            {dayChange !== null && selected.before && (
              <p className={`${styles["day-change"]} ${tone(dayChange)}`}>
                전날보다 {sign(dayChange)}
                {won(dayChange)}원 ({sign(dayChange)}
                {((dayChange / selected.before.close) * 100).toFixed(2)}%)
              </p>
            )}
            <dl className={styles["ohlc"]}>
              <dt>시가</dt>
              <dd>{won(selected.day.open)}</dd>
              <dt>고가</dt>
              <dd>{won(selected.day.high)}</dd>
              <dt>저가</dt>
              <dd>{won(selected.day.low)}</dd>
              <dt>종가</dt>
              <dd>{won(selected.day.close)}</dd>
              <dt>거래량</dt>
              <dd>{won(selected.day.volume)}주</dd>
            </dl>
          </section>
        )}

        <section className={`${styles["card"]} ${styles["guide"]}`}>
          <h2>캔들 읽는 법</h2>
          <ul>
            <li>
              <b className="up">빨간 막대</b>는 그날 시작가보다 오른 채로 끝난 날, <b className="down">파란 막대</b>는
              내린 채로 끝난 날입니다.
            </li>
            <li>막대의 두꺼운 부분은 시가와 종가 사이, 위아래 가는 선은 그날의 최고가와 최저가입니다.</li>
            <li>아래쪽 막대는 거래량입니다. 길수록 그날 사고판 주식이 많았다는 뜻입니다.</li>
          </ul>
        </section>
      </aside>
    </div>
  );
}
