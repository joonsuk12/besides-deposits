"use client";

// 종목 차트 화면 (주소: /005930). NewStocks의 종목 화면 배치를 따른다.
//   왼쪽: 관심 종목 목록
//   가운데: 차트(뉴스 N·리포트 R·공시 D 표시) → 선택한 날 한 줄(뉴스·공시·리포트 개수, 누르면 옆 패널) → 소식 탭 카드(많이 다뤄진 뉴스 | 최근 공시 | 리포트)
//   (뉴스·공시·리포트는 3개씩만 먼저 보여주고 나머지는 "더 보기" — 초보가 정보에 묻히지 않게)
//   오른쪽: 이 종목 요약만 — [주가 수준 | 연간 흐름 | 회사 소개] 탭 → 위험 신호 → 투자자별 매매동향

import { use, useCallback, useEffect, useMemo, useState } from "react";
import { FaRegStar, FaStar } from "react-icons/fa";

import DayDrawer, { type DayTab } from "@/components/DayDrawer/DayDrawer";
import StockFeed from "@/components/StockFeed/StockFeed";
import StockChart, { type DayMarks } from "@/components/StockChart";
import StockProfile from "@/components/StockProfile/StockProfile";
import EtfCard from "@/components/EtfCard/EtfCard";
import RiskCard from "@/components/RiskCard/RiskCard";
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

const DAY_TABS: { key: DayTab; label: string }[] = [
  { key: "news", label: "📰 뉴스" },
  { key: "disc", label: "📢 공시" },
  { key: "report", label: "📄 리포트" },
];

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
  const [drawerTab, setDrawerTab] = useState<DayTab | null>(null); // 옆 패널: 열려 있으면 어느 탭인지
  const closeDrawer = useCallback(() => setDrawerTab(null), []);
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
    setDrawerTab(null);
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
  // 옆 패널을 연 채로 다른 날을 눌렀는데 그 탭이 비어 있으면, 내용이 있는 탭을 대신 보여준다
  const dayCounts: Record<DayTab, number> = {
    news: dayNews.length,
    disc: dayDisclosures.length,
    report: dayReports.length,
  };
  const shownTab: DayTab | null =
    drawerTab && dayCounts[drawerTab] === 0
      ? (DAY_TABS.find((t) => dayCounts[t.key] > 0)?.key ?? drawerTab)
      : drawerTab;
  const dayTitle = selected ? `${selected.day.date} (${WEEKDAYS[new Date(selected.day.date).getDay()]})` : "";
  const dayPriceLine = selected && (
    <>
      종가 <b>{won(selected.day.close)}</b>
      {dayChange !== null && selected.before && (
        <span className={tone(dayChange)}>
          {" "}
          {sign(dayChange)}
          {((dayChange / selected.before.close) * 100).toFixed(2)}%
        </span>
      )}
    </>
  );

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
        <div className={styles["hint"]}>
          <span>
            <b className={styles["mark-n"]}>N</b> 뉴스 · <b className={styles["mark-r"]}>R</b> 리포트 ·{" "}
            <b className={styles["mark-d"]}>D</b> 중요 공시가 있는 날 — 날짜를 누르면 아래 줄이 그날로 바뀌어요.
          </span>
          <details className={styles["candle-help"]}>
            <summary>❔ 캔들 읽는 법</summary>
            <ul>
              <li>
                <b className="up">빨간 막대</b>는 시작가보다 오른 채로 끝난 날, <b className="down">파란 막대</b>는 내린
                채로 끝난 날이에요.
              </li>
              <li>두꺼운 부분은 시가와 종가 사이, 위아래 가는 선은 그날의 최고가와 최저가예요.</li>
              <li>아래쪽 막대는 거래량이에요. 길수록 그날 사고판 주식이 많았다는 뜻이에요.</li>
            </ul>
          </details>
        </div>

        {/* 선택한 날: 한 줄 요약. 뉴스·공시·리포트 숫자를 누르면 옆 패널(드로어)이 열린다 */}
        {selected && (
          <div className={styles["day-strip"]}>
            <b className={styles["day-date"]}>{dayTitle}</b>
            <span>{dayPriceLine}</span>
            <span className={styles["sub"]}>
              시 {won(selected.day.open)} · 고 {won(selected.day.high)} · 저 {won(selected.day.low)} · 거래량{" "}
              {won(selected.day.volume)}주
            </span>
            <span className={styles["day-btns"]}>
              {DAY_TABS.map((t) => {
                const n = dayCounts[t.key];
                return (
                  <button
                    key={t.key}
                    className={`ui-chip ${shownTab === t.key ? "on" : ""}`}
                    disabled={n === 0}
                    onClick={() => setDrawerTab(t.key)}
                    title={n === 0 ? "이날은 없어요" : "옆 패널에서 보기"}
                  >
                    {t.label} {n}
                  </button>
                );
              })}
            </span>
          </div>
        )}
        {selected && shownTab && (
          <DayDrawer
            title={dayTitle}
            priceLine={dayPriceLine}
            tab={shownTab}
            onTab={setDrawerTab}
            onClose={closeDrawer}
            news={dayNews}
            disclosures={dayDisclosures}
            reports={dayReports}
          />
        )}

        <StockFeed code={code} isEtf={isEtf} keyNews={keyNews} disclosures={disclosures} reports={latestReports} />
      </main>

      {/* 오른쪽: 날짜와 상관없는 이 종목 요약만. 소식(공시·리포트)은 가운데 탭 카드로, 캔들 읽는 법은 차트 아래 ❔로 옮겼다 (2026-11-23) */}
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

        {!isEtf && (
          <section className={styles["card"]}>
            <h2>🚦 위험 신호 점검</h2>
            <RiskCard code={code} />
          </section>
        )}

        <section className={styles["card"]}>
          <h2>👥 투자자별 매매동향</h2>
          <TrendCard code={code} />
        </section>
      </aside>
    </div>
  );
}
