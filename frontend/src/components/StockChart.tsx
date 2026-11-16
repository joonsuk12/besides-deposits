"use client";

// 캔들 차트. TradingView Lightweight Charts를 감싼 컴포넌트 (NewStocks와 같은 라이브러리, 버전 5).
// - 일봉(최대 10년)을 받아 일·주·월·연봉으로 묶어 그린다. 줌 아웃하면 주→월→연봉, 줌 인하면 반대로 자동 전환
//   (예전에는 줌 아웃하면 데이터가 없는 왼쪽이 빈 공간으로 보였다). 왼쪽 위 버튼으로 직접 고를 수도 있다.
// - 데이터 양 끝 너머로는 스크롤되지 않게 막는다 (fixLeftEdge / fixRightEdge).
// - markers: 뉴스(N, 캔들 아래), 리포트(R, 캔들 위), 중요 공시(D, 캔들 위). 주·월봉에서는 그 기간 안에 있으면 표시
// - rangeDays: 3개월·1년 같은 기간 버튼. 그 기간이 보이게 맞추고 알맞은 봉으로 바꾼다
// - 날짜를 누르면 onSelectDate로 그 날짜(주·월봉이면 그 기간의 마지막 거래일)를 알려준다

import { useEffect, useRef, useState } from "react";
import {
  CandlestickSeries,
  ColorType,
  CrosshairMode,
  HistogramSeries,
  createChart,
  createSeriesMarkers,
  type IChartApi,
  type ISeriesApi,
  type ISeriesMarkersPluginApi,
  type SeriesMarker,
  type Time,
} from "lightweight-charts";
import type { Price } from "@/lib/api";

// 한국 증시 관례: 오르면 빨강, 내리면 파랑
const UP = "#ff5a5a";
const DOWN = "#5b9bff";

export type DayMarks = { newsDates: Set<string>; reportDates: Set<string>; disclosureDates: Set<string> };

type Interval = "day" | "week" | "month" | "year";
const INTERVALS: { key: Interval; label: string }[] = [
  { key: "day", label: "일" },
  { key: "week", label: "주" },
  { key: "month", label: "월" },
  { key: "year", label: "년" },
];
const ORDER: Interval[] = ["day", "week", "month", "year"];
const NAME: Record<Interval, string> = { day: "일봉", week: "주봉", month: "월봉", year: "연봉" };

// 화면에 보이는 막대 수가 이 범위를 벗어나면 봉을 바꾼다. 위·아래 기준을 떨어뜨려 놔서 왔다 갔다 하지 않는다.
const ZOOM_OUT_AT: Record<Interval, number> = { day: 260, week: 260, month: 150, year: Infinity }; // 10년(120개월)은 월봉으로 보인다
const ZOOM_IN_AT: Record<Interval, number> = { day: 0, week: 40, month: 30, year: 6 };

type Bar = {
  time: string; // 그 기간 첫 거래일 (차트 x축)
  last: string; // 그 기간 마지막 거래일 (눌렀을 때 알려줄 날짜)
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  days: string[]; // 포함된 거래일 (표시용)
};

type Props = {
  prices: Price[];
  marks?: DayMarks;
  rangeDays: number;
  onSelectDate: (date: string) => void;
};

const won = (n: number) => n.toLocaleString("ko-KR");

// 주의 시작(월요일) 날짜를 키로
function weekKey(d: string) {
  const dt = new Date(`${d}T00:00:00`);
  const day = (dt.getDay() + 6) % 7; // 월=0
  dt.setDate(dt.getDate() - day);
  return dt.toISOString().slice(0, 10);
}

function bucketKey(d: string, interval: Interval) {
  if (interval === "week") return weekKey(d);
  if (interval === "month") return d.slice(0, 7);
  if (interval === "year") return d.slice(0, 4);
  return d;
}

function aggregate(prices: Price[], interval: Interval): Bar[] {
  const bars: Bar[] = [];
  let cur: Bar | null = null;
  let curKey = "";
  for (const p of prices) {
    const key = bucketKey(p.date, interval);
    if (!cur || key !== curKey) {
      cur = { time: p.date, last: p.date, open: p.open, high: p.high, low: p.low, close: p.close, volume: p.volume, days: [p.date] };
      curKey = key;
      bars.push(cur);
    } else {
      cur.last = p.date;
      cur.high = Math.max(cur.high, p.high);
      cur.low = Math.min(cur.low, p.low);
      cur.close = p.close;
      cur.volume += p.volume;
      cur.days.push(p.date);
    }
  }
  return bars;
}

// 기간(일수)에 맞는 봉: 보일 막대 수가 기준 안에 들어오는 가장 촘촘한 봉
function intervalForRange(days: number): Interval {
  const tradingDays = days * 0.68;
  if (tradingDays <= ZOOM_OUT_AT.day) return "day";
  if (tradingDays / 5 <= ZOOM_OUT_AT.week) return "week";
  if (tradingDays / 21 <= ZOOM_OUT_AT.month) return "month";
  return "year";
}

function shiftDate(d: string, days: number) {
  const dt = new Date(`${d}T00:00:00`);
  dt.setDate(dt.getDate() + days);
  return dt.toISOString().slice(0, 10);
}

export default function StockChart({ prices, marks, rangeDays, onSelectDate }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const tooltipRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const candlesRef = useRef<ISeriesApi<"Candlestick"> | null>(null);
  const volumeRef = useRef<ISeriesApi<"Histogram"> | null>(null);
  const markersRef = useRef<ISeriesMarkersPluginApi<Time> | null>(null);
  const barsRef = useRef<Bar[]>([]);
  const intervalRef = useRef<Interval>("day");
  const switchingRef = useRef(false);
  const [interval, setIntervalState] = useState<Interval>("day");

  // 최신 콜백·표시를 차트를 다시 만들지 않고 쓰기 위한 보관함
  const onSelectRef = useRef(onSelectDate);
  onSelectRef.current = onSelectDate;
  const marksRef = useRef(marks);
  marksRef.current = marks;

  // 봉을 바꿔 다시 그린다. keep: 지금 보던 날짜 구간을 그대로 유지할지
  const applyInterval = (next: Interval, visible?: { from: string; to: string }) => {
    const chart = chartRef.current;
    const candles = candlesRef.current;
    const volume = volumeRef.current;
    if (!chart || !candles || !volume) return;
    switchingRef.current = true;
    intervalRef.current = next;
    setIntervalState(next);

    const bars = aggregate(prices, next);
    barsRef.current = bars;
    candles.setData(bars.map((b) => ({ time: b.time, open: b.open, high: b.high, low: b.low, close: b.close })));
    volume.setData(
      bars.map((b) => ({
        time: b.time,
        value: b.volume,
        color: b.close >= b.open ? "rgba(255,90,90,0.45)" : "rgba(91,155,255,0.45)",
      })),
    );
    // 일봉에서는 막대를 너무 촘촘히 줄이지 못하게 해서, 더 줄이려 하면 주봉으로 넘어가게 한다
    chart.timeScale().applyOptions({ minBarSpacing: next === "day" ? 2 : 0.5 });
    drawMarkers();

    if (visible) {
      chart.timeScale().setVisibleRange({ from: visible.from as Time, to: visible.to as Time });
    } else {
      chart.timeScale().fitContent();
    }
    // 위에서 바꾼 보이는 범위 때문에 또 봉이 바뀌지 않게 한 박자 쉰다
    setTimeout(() => (switchingRef.current = false), 80);
  };

  const drawMarkers = () => {
    const m = marksRef.current;
    const plugin = markersRef.current;
    if (!plugin) return;
    if (!m) return plugin.setMarkers([]);
    const list: SeriesMarker<Time>[] = [];
    for (const b of barsRef.current) {
      const has = (set: Set<string>) => b.days.some((d) => set.has(d));
      if (has(m.reportDates)) list.push({ time: b.time, position: "aboveBar", color: "#ff7ad9", shape: "circle", text: "R" });
      if (has(m.disclosureDates)) list.push({ time: b.time, position: "aboveBar", color: "#ffc861", shape: "square", text: "D" });
      if (has(m.newsDates)) list.push({ time: b.time, position: "belowBar", color: "#b4ff4a", shape: "circle", text: "N" });
    }
    plugin.setMarkers(list);
  };

  // 차트 만들기 (가격 데이터가 바뀔 때만)
  useEffect(() => {
    const container = containerRef.current;
    const tooltip = tooltipRef.current;
    if (!container || !tooltip || prices.length === 0) return;

    const chart = createChart(container, {
      autoSize: true,
      layout: {
        background: { type: ColorType.Solid, color: "#00051E" },
        textColor: "#c9cdd8",
        fontFamily: "inherit",
      },
      grid: {
        vertLines: { color: "rgba(197, 203, 206, 0.08)" },
        horzLines: { color: "rgba(197, 203, 206, 0.08)" },
      },
      crosshair: { mode: CrosshairMode.Normal },
      rightPriceScale: { borderColor: "rgba(197, 203, 206, 0.4)" },
      timeScale: {
        borderColor: "rgba(197, 203, 206, 0.4)",
        // 데이터 양 끝 너머로 스크롤·줌 아웃되지 않게 (빈 공간 방지)
        fixLeftEdge: true,
        fixRightEdge: true,
      },
      localization: {
        locale: "ko-KR",
        dateFormat: "yyyy-MM-dd",
        priceFormatter: (p: number) => Math.round(p).toLocaleString("ko-KR"),
      },
    });
    chartRef.current = chart;

    candlesRef.current = chart.addSeries(CandlestickSeries, {
      upColor: UP,
      downColor: DOWN,
      wickUpColor: UP,
      wickDownColor: DOWN,
      borderVisible: false,
      priceFormat: { type: "price", precision: 0, minMove: 1 },
    });
    markersRef.current = createSeriesMarkers(candlesRef.current, []);

    // 거래량 막대는 차트 아래 별도 칸(pane 1)에 그린다
    volumeRef.current = chart.addSeries(
      HistogramSeries,
      { priceFormat: { type: "volume" }, lastValueVisible: false, priceLineVisible: false },
      1,
    );
    chart.panes()[1]?.setHeight(80);

    // 줌에 따라 봉 바꾸기
    chart.timeScale().subscribeVisibleLogicalRangeChange((range) => {
      if (!range || switchingRef.current) return;
      const count = range.to - range.from;
      const cur = intervalRef.current;
      const i = ORDER.indexOf(cur);
      const vr = chart.timeScale().getVisibleRange();
      if (!vr) return;
      const visible = { from: String(vr.from), to: String(vr.to) };
      if (count > ZOOM_OUT_AT[cur] && i < ORDER.length - 1) {
        applyInterval(ORDER[i + 1], visible);
      } else if (count < ZOOM_IN_AT[cur] && i > 0) {
        // 줌 인: 이번 봉의 마지막 날까지 보이게
        const lastBar = barsRef.current.find((b) => b.time === visible.to);
        applyInterval(ORDER[i - 1], { from: visible.from, to: lastBar?.last ?? visible.to });
      }
    });

    // 마우스를 올린 막대의 툴팁
    chart.subscribeCrosshairMove((param) => {
      const t = param.time as string | undefined;
      const bar = t ? barsRef.current.find((b) => b.time === t) : undefined;
      if (!param.point || !bar) {
        tooltip.style.display = "none";
        return;
      }
      const m = marksRef.current;
      const has = (set?: Set<string>) => !!set && bar.days.some((d) => set.has(d));
      const tags = [has(m?.newsDates) ? "📰 뉴스" : "", has(m?.reportDates) ? "📄 리포트" : "", has(m?.disclosureDates) ? "📢 공시" : ""].filter(Boolean);
      const label =
        intervalRef.current === "day" ? bar.time : `${NAME[intervalRef.current]} ${bar.time} ~ ${bar.last}`;
      tooltip.innerHTML = `
        <div class="tt-date">${label}</div>
        <div>시가 ${won(bar.open)}</div>
        <div>고가 ${won(bar.high)}</div>
        <div>저가 ${won(bar.low)}</div>
        <div>종가 ${won(bar.close)}</div>
        <div>거래량 ${won(bar.volume)}</div>
        ${tags.length ? `<div class="tt-tags">${tags.join(" · ")} — 눌러서 보기</div>` : ""}`;
      tooltip.style.display = "block";
      const left =
        param.point.x + 20 + tooltip.offsetWidth > container.clientWidth
          ? param.point.x - tooltip.offsetWidth - 20
          : param.point.x + 20;
      tooltip.style.left = `${left}px`;
      tooltip.style.top = `${Math.max(8, param.point.y - 40)}px`;
    });

    chart.subscribeClick((param) => {
      const t = param.time as string | undefined;
      const bar = t ? barsRef.current.find((b) => b.time === t) : undefined;
      if (bar) onSelectRef.current(bar.last);
    });

    return () => {
      chart.remove();
      chartRef.current = null;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [prices]);

  // 기간 버튼(3개월·1년…)이나 데이터가 바뀌면: 알맞은 봉으로 바꾸고 그 기간이 보이게
  useEffect(() => {
    if (!chartRef.current || prices.length === 0) return;
    const last = prices[prices.length - 1].date;
    const from = shiftDate(last, -rangeDays);
    const first = prices[0].date;
    applyInterval(intervalForRange(rangeDays), { from: from < first ? first : from, to: last });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [prices, rangeDays]);

  // 뉴스·리포트·공시 표시는 데이터가 따로 도착하므로 바뀔 때마다 다시 그린다
  useEffect(() => {
    drawMarkers();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [marks]);

  return (
    <div className="chart-wrap">
      <div className="chart-interval" role="group" aria-label="봉 단위">
        {INTERVALS.map((it) => (
          <button
            key={it.key}
            className={interval === it.key ? "on" : ""}
            onClick={() => applyInterval(it.key)}
            title={NAME[it.key]}
          >
            {it.label}
          </button>
        ))}
      </div>
      <div ref={containerRef} className="chart" />
      <div ref={tooltipRef} className="chart-tooltip" />
    </div>
  );
}
