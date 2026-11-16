"use client";

// 종목 차트 화면 (주소: /005930). NewStocks의 종목 화면 배치를 따른다.
//   왼쪽: 관심 종목 목록
//   가운데: 차트(뉴스 N·리포트 R·공시 D 표시) → 선택한 날(가격 한 줄 + 그날 뉴스 | 공시·리포트) → 이번 주 많이 다뤄진 뉴스 3개
//   (뉴스·공시·리포트는 3개씩만 먼저 보여주고 나머지는 "더 보기" — 초보가 정보에 묻히지 않게)
//   오른쪽: 이 종목 요약 — [주가 수준 | 연간 흐름 | 회사 소개] 탭 → 최근 공시 → 최근 증권사 리포트 → 캔들 읽는 법

import { use, useCallback, useEffect, useMemo, useState } from "react";
import { FaRegStar, FaStar } from "react-icons/fa";

import DisclosureList from "@/components/DisclosureList/DisclosureList";
import NewsList from "@/components/NewsList/NewsList";
import ReportCard from "@/components/ReportCard/ReportCard";
import ShowMore from "@/components/ShowMore/ShowMore";
import ToneFilter, { type Tone } from "@/components/ToneFilter/ToneFilter";
import StockChart, { type DayMarks } from "@/components/StockChart";
import StockProfile from "@/components/StockProfile/StockProfile";
import EtfCard from "@/components/EtfCard/EtfCard";
import StockInfoCard from "@/components/StockInfoCard/StockInfoCard";
import TrendCard from "@/components/TrendCard/TrendCard";
import WatchlistSidebar from "@/components/WatchlistSidebar/WatchlistSidebar";
import {
  addWatch,
  fetchPrices,
  fetchStock,
  fetchStockDisclosures,
  fetchStockNews,
  fetchStockReports,
  fetchWatchlist,
  removeWatch,
  type DisclosureList as Disclosures,
  type News,
  type Price,
  type Report,
  type Stock,
  type WatchlistItem,
} from "@/lib/api";
import styles from "./stock.module.css";

// 기간 버튼은 데이터를 다시 받지 않고 차트에서 보이는 범위만 바꾼다 (주가는 10년치를 한 번에 받는다)
const PRICE_DAYS = 3650;
const PERIODS = [
  { label: "3개월", days: 92 },
  { label: "1년", days: 365 },
  { label: "3년", days: 1095 },
  { label: "10년", days: 3650 },
];

const won = (n: number) => n.toLocaleString("ko-KR");
const tone = (n: number) => (n > 0 ? "up" : n < 0 ? "down" : "");
const sign = (n: number) => (n > 0 ? "+" : "");
const WEEKDAYS = ["일", "월", "화", "수", "목", "금", "토"];

// 필터 기준: 뉴스는 분위기 추정, 리포트는 목표주가 상향·하향
const newsTone = (n: News): Tone | null => (n.tone === "good" ? "good" : n.tone === "bad" ? "bad" : null);
const reportTone = (r: Report): Tone | null =>
  r.goal_change === "상향" ? "good" : r.goal_change === "하향" ? "bad" : null;

// 주말·휴일에 나온 뉴스·리포트는 그다음 거래일 캔들에 붙인다
function toTradingDay(date: string, tradingDays: string[]): string | null {
  for (const d of tradingDays) if (d >= date) return d;
  return null;
}

export default function StockPage({ params }: { params: Promise<{ code: string }> }) {
  const { code } = use(params);

  const [stock, setStock] = useState<Stock | null>(null);
  const isEtf = stock?.market === "ETF";
  const [watchlist, setWatchlist] = useState<WatchlistItem[]>([]);
  const [days, setDays] = useState(365);
  const [prices, setPrices] = useState<Price[]>([]);
  const [news, setNews] = useState<News[]>([]);
  const [reports, setReports] = useState<Report[]>([]);
  const [disclosures, setDisclosures] = useState<Disclosures | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedDate, setSelectedDate] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const loadWatchlist = useCallback(() => {
    fetchWatchlist()
      .then(setWatchlist)
      .catch(() => {});
  }, []);

  useEffect(loadWatchlist, [loadWatchlist]);

  useEffect(() => {
    setError(null);
    setNews([]);
    setReports([]);
    setDisclosures(null);
    fetchStock(code)
      .then(setStock)
      .catch(() => setError("종목을 찾을 수 없거나 백엔드(8100번 포트)가 꺼져 있습니다."));
    fetchStockNews(code, 365)
      .then(setNews)
      .catch(() => {});
    fetchStockReports(code, 20)
      .then(setReports)
      .catch(() => {});
    fetchStockDisclosures(code, 365)
      .then(setDisclosures)
      .catch(() => {});
  }, [code]);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    fetchPrices(code, PRICE_DAYS)
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
  }, [code]);

  // 뉴스·리포트를 거래일 기준으로 묶는다
  const byDay = useMemo(() => {
    const tradingDays = prices.map((p) => p.date);
    const newsByDay = new Map<string, News[]>();
    const reportsByDay = new Map<string, Report[]>();
    const disclosuresByDay = new Map<string, Disclosures["items"]>();
    for (const n of news) {
      const d = toTradingDay(n.date, tradingDays);
      if (d) newsByDay.set(d, [...(newsByDay.get(d) ?? []), n]);
    }
    for (const r of reports) {
      const d = toTradingDay(r.write_date, tradingDays);
      if (d) reportsByDay.set(d, [...(reportsByDay.get(d) ?? []), r]);
    }
    for (const d of disclosures?.items ?? []) {
      const day = toTradingDay(d.date, tradingDays);
      if (day) disclosuresByDay.set(day, [...(disclosuresByDay.get(day) ?? []), d]);
    }
    return { newsByDay, reportsByDay, disclosuresByDay };
  }, [prices, news, reports, disclosures]);

  const marks: DayMarks = useMemo(
    () => ({
      newsDates: new Set(byDay.newsByDay.keys()),
      reportDates: new Set(byDay.reportsByDay.keys()),
      // 참고용(정기 보고서·지분 보고)은 너무 많아서 차트에는 중요 공시만 표시한다
      disclosureDates: new Set(
        [...byDay.disclosuresByDay].filter(([, list]) => list.some((d) => d.level !== "info")).map(([day]) => day),
      ),
    }),
    [byDay],
  );

  // 최근 7일 동안 여러 언론사가 다룬 뉴스 = 키포인트
  const keyNews = useMemo(() => {
    const weekAgo = new Date(Date.now() - 7 * 86400000).toISOString().slice(0, 10);
    return news
      .filter((n) => n.date >= weekAgo && n.cluster_size > 1)
      .sort((a, b) => b.cluster_size - a.cluster_size)
      .slice(0, 3); // 초보에게는 가장 많이 다뤄진 3개면 충분하다
  }, [news]);

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
  // 목록은 모두 최신순. 좋은/나쁜 소식은 필터 버튼으로 골라 본다
  const dayNews = selectedDate
    ? [...(byDay.newsByDay.get(selectedDate) ?? [])].sort((a, b) => b.published_at.localeCompare(a.published_at))
    : [];
  const latestReports = useMemo(() => [...reports].sort((a, b) => b.write_date.localeCompare(a.write_date)), [reports]);
  const dayReports = selectedDate ? (byDay.reportsByDay.get(selectedDate) ?? []) : [];
  const dayDisclosures = selectedDate ? (byDay.disclosuresByDay.get(selectedDate) ?? []) : [];

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
          {!loading && prices.length > 0 && (
            <StockChart prices={prices} marks={marks} rangeDays={days} onSelectDate={setSelectedDate} />
          )}
        </div>
        <p className={styles["hint"]}>
          <b className={styles["mark-n"]}>N</b> 뉴스가 있는 날 · <b className={styles["mark-r"]}>R</b> 증권사 리포트가
          나온 날 · <b className={styles["mark-d"]}>D</b> 중요 공시가 나온 날 — 차트에서 날짜를 누르면 그날의 내용이
          바로 아래에 나옵니다.
        </p>

        {/* 선택한 날: 차트 바로 아래. 가격은 한 줄 띠로, 그날 내용은 두 칸(왼쪽 뉴스 / 오른쪽 공시·리포트) */}
        {selected && (
          <section className={styles["day-panel"]}>
            <div className={styles["day-strip"]}>
              <b className={styles["day-date"]}>
                {selected.day.date} ({WEEKDAYS[new Date(selected.day.date).getDay()]})
              </b>
              <span>
                종가 <b>{won(selected.day.close)}</b>
                {dayChange !== null && selected.before && (
                  <span className={tone(dayChange)}>
                    {" "}
                    {sign(dayChange)}
                    {((dayChange / selected.before.close) * 100).toFixed(2)}%
                  </span>
                )}
              </span>
              <span className={styles["sub"]}>
                시 {won(selected.day.open)} · 고 {won(selected.day.high)} · 저 {won(selected.day.low)}
              </span>
              <span className={styles["sub"]}>거래량 {won(selected.day.volume)}주</span>
            </div>

            <div className={styles["day-cols"]}>
              <div>
                <h3>📰 이날의 주요 뉴스</h3>
                <ToneFilter
                  key={`news-${selectedDate}`}
                  items={dayNews}
                  toneOf={newsTone}
                  labels={{ good: "좋은 소식(추정)", bad: "나쁜 소식(추정)" }}
                >
                  {(shown) => (
                    <NewsList items={shown} empty="이날 수집된 뉴스가 없습니다. (최근 뉴스 위주로 모읍니다)" />
                  )}
                </ToneFilter>
              </div>
              <div>
                <h3>📢 이날의 공시</h3>
                <DisclosureList
                  key={`disc-${selectedDate}`}
                  items={dayDisclosures}
                  limit={3}
                  empty="이날 나온 공시가 없습니다."
                />
                <h3 className={styles["day-sub-h"]}>📄 이날 나온 리포트</h3>
                {dayReports.length === 0 && <p className={styles["placeholder"]}>이날 나온 리포트가 없습니다.</p>}
                <ShowMore key={`report-${selectedDate}`} items={dayReports} limit={3}>
                  {(shown) => (
                    <div className={styles["stack"]}>
                      {shown.map((r) => (
                        <ReportCard key={r.nid} report={r} compact showStock={false} />
                      ))}
                    </div>
                  )}
                </ShowMore>
              </div>
            </div>
          </section>
        )}

        <section className={styles["news"]}>
          <h2>📰 이번 주 많이 다뤄진 뉴스</h2>
          <p className={styles["desc"]}>여러 언론사가 같은 내용을 다룰수록 중요한 소식일 가능성이 큽니다.</p>
          <NewsList items={keyNews} empty="최근 7일 동안 여러 언론사가 함께 다룬 뉴스가 없습니다." />
        </section>
      </main>

      {/* 오른쪽: 날짜와 상관없는 이 종목 요약 */}
      <aside className={styles["side-container"]}>
        {/* ETF는 회사가 아니라 PER·PBR·공시·리포트 대신 ETF 정보(따라가는 지수·보수·담긴 종목)를 보여준다 */}
        <section className={styles["card"]}>
          {isEtf ? (
            <>
              <h2>🧺 ETF 정보</h2>
              <EtfCard code={code} />
            </>
          ) : (
            <StockInfoCard code={code} />
          )}
        </section>

        <section className={styles["card"]}>
          <h2>👥 투자자별 매매동향</h2>
          <TrendCard code={code} />
        </section>

        {!isEtf && (
          <section className={styles["card"]}>
            <h2>📢 최근 공시</h2>
            {!disclosures && <p className={styles["placeholder"]}>불러오는 중…</p>}
            {disclosures && !disclosures.available && <p className={styles["placeholder"]}>{disclosures.message}</p>}
            {disclosures?.available && (
              <DisclosureList
                key={code}
                items={disclosures.items}
                limit={3}
                skipInfo
                empty="최근 1년 동안 공시가 없습니다. ETF는 회사 공시가 없어요."
              />
            )}
          </section>
        )}

        {!isEtf && (
          <section className={styles["card"]}>
            <h2>증권사 리포트</h2>
            {reports.length === 0 && (
              <p className={styles["placeholder"]}>최근 나온 리포트가 없습니다. ETF나 소형주는 리포트가 드뭅니다.</p>
            )}
            <ToneFilter
              key={code}
              items={latestReports}
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
