"use client";

// 첫 화면: 관심 종목을 고르면 캔들 차트가 나오고, 날짜를 누르면 그날 정보가 옆에 뜬다.

import { useEffect, useMemo, useState } from "react";
import StockChart from "@/components/StockChart";
import { fetchPrices, fetchStocks, type Price, type Stock } from "@/lib/api";

const PERIODS = [
  { label: "3개월", days: 92 },
  { label: "1년", days: 365 },
  { label: "3년", days: 1095 },
];

const won = (n: number) => n.toLocaleString("ko-KR");

export default function Home() {
  const [stocks, setStocks] = useState<Stock[]>([]);
  const [code, setCode] = useState<string | null>(null);
  const [days, setDays] = useState(365);
  const [prices, setPrices] = useState<Price[]>([]);
  const [selectedDate, setSelectedDate] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  // 처음 한 번: 종목 목록
  useEffect(() => {
    fetchStocks()
      .then((list) => {
        setStocks(list);
        setCode((prev) => prev ?? list[0]?.code ?? null);
      })
      .catch(() => setError("백엔드에 연결하지 못했습니다. 백엔드 서버(8100번 포트)가 켜져 있는지 확인해 주세요."));
  }, []);

  // 종목이나 기간이 바뀔 때마다: 주가
  useEffect(() => {
    if (!code) return;
    let cancelled = false;
    fetchPrices(code, days)
      .then((list) => {
        if (cancelled) return;
        setPrices(list);
        setSelectedDate(list.at(-1)?.date ?? null);
      })
      .catch(() => !cancelled && setError("주가를 불러오지 못했습니다."));
    return () => {
      cancelled = true;
    };
  }, [code, days]);

  const stock = stocks.find((s) => s.code === code);
  const last = prices.at(-1);
  const prev = prices.at(-2);
  const change = last && prev ? last.close - prev.close : 0;
  const changePct = last && prev ? (change / prev.close) * 100 : 0;

  // 선택한 날과 그 전날 (등락 계산용)
  const selected = useMemo(() => {
    const i = prices.findIndex((p) => p.date === selectedDate);
    return i < 0 ? null : { day: prices[i], before: prices[i - 1] };
  }, [prices, selectedDate]);

  const tone = (n: number) => (n > 0 ? "up" : n < 0 ? "down" : "");
  const sign = (n: number) => (n > 0 ? "+" : "");

  return (
    <div className="page">
      <header className="top">
        <h1>주식초보나들이</h1>
        <nav className="stocks">
          {stocks.map((s) => (
            <button
              key={s.code}
              className={s.code === code ? "chip active" : "chip"}
              onClick={() => setCode(s.code)}
            >
              {s.name}
            </button>
          ))}
        </nav>
      </header>

      {error && <p className="notice">{error}</p>}
      {!error && stocks.length === 0 && (
        <p className="notice">아직 종목이 없습니다. 백엔드에서 주가 수집을 먼저 실행해 주세요.</p>
      )}

      {stock && last && (
        <main className="main">
          <section className="card chart-card">
            <div className="quote">
              <div>
                <span className="name">{stock.name}</span>
                <span className="code">{stock.code}</span>
              </div>
              <div className="price-line">
                <span className="price">{won(last.close)}원</span>
                <span className={`change ${tone(change)}`}>
                  {sign(change)}
                  {won(change)} ({sign(changePct)}
                  {changePct.toFixed(2)}%)
                </span>
                <span className="asof">{last.date} 종가</span>
              </div>
              <div className="periods">
                {PERIODS.map((p) => (
                  <button
                    key={p.days}
                    className={p.days === days ? "chip small active" : "chip small"}
                    onClick={() => setDays(p.days)}
                  >
                    {p.label}
                  </button>
                ))}
              </div>
            </div>
            <StockChart prices={prices} onSelectDate={setSelectedDate} />
            <p className="hint">차트에서 날짜를 누르면 그날의 정보가 오른쪽에 나옵니다.</p>
          </section>

          <aside className="side">
            {selected && (
              <section className="card">
                <h2>{selected.day.date}</h2>
                {selected.before && (
                  <p className={`day-change ${tone(selected.day.close - selected.before.close)}`}>
                    전날보다 {sign(selected.day.close - selected.before.close)}
                    {won(selected.day.close - selected.before.close)}원 (
                    {sign(selected.day.close - selected.before.close)}
                    {(((selected.day.close - selected.before.close) / selected.before.close) * 100).toFixed(2)}%)
                  </p>
                )}
                <dl className="ohlc">
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
                <p className="placeholder">이 날의 뉴스와 리포트는 다음 단계에서 여기에 표시됩니다.</p>
              </section>
            )}

            <section className="card guide">
              <h2>캔들 읽는 법</h2>
              <ul>
                <li>
                  <b className="up">빨간 막대</b>는 그날 시작가보다 오른 채로 끝난 날, <b className="down">파란 막대</b>는
                  내린 채로 끝난 날입니다.
                </li>
                <li>막대의 두꺼운 부분은 시가와 종가 사이, 위아래 가는 선은 그날의 최고가와 최저가입니다.</li>
                <li>아래쪽 옅은 막대는 거래량입니다. 길수록 그날 사고판 주식이 많았다는 뜻입니다.</li>
              </ul>
            </section>
          </aside>
        </main>
      )}
    </div>
  );
}
