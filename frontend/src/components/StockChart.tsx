"use client";

// 캔들 차트. TradingView Lightweight Charts를 감싼 컴포넌트 (NewStocks와 같은 라이브러리, 버전 5).
// - 일봉(최대 10년)을 받아 일·주·월·연봉으로 묶어 그린다. 줌 아웃하면 주→월→연봉, 줌 인하면 반대로 자동 전환
//   (예전에는 줌 아웃하면 데이터가 없는 왼쪽이 빈 공간으로 보였다). 왼쪽 위 버튼으로 직접 고를 수도 있다.
// - 데이터 양 끝 너머로는 스크롤되지 않게 막는다 (fixLeftEdge / fixRightEdge).
// - markers: 뉴스(N, 캔들 아래), 리포트(R, 캔들 위), 중요 공시(D, 캔들 위), 크게 움직인 날(⚡ 민트 화살표). 주·월봉에서는 그 기간 안에 있으면 표시
// - rangeDays: 3개월·1년 같은 기간 버튼. 그 기간이 보이게 맞추고 알맞은 봉으로 바꾼다
// - 날짜를 누르면 onSelectDate로 그 날짜(주·월봉이면 그 기간의 마지막 거래일)를 알려준다
// - 보조지표: 이동평균선(5·20·60·120), 볼린저밴드, RSI, MACD. 위쪽 "지표" 메뉴로 켜고 끈다(브라우저에 기억).
//   지금 보고 있는 봉 기준으로 계산한다 (주봉에서 5선 = 5주선). 계산은 lib/indicators.ts
// - 라이선스(Apache-2.0)상 TradingView 출처 링크가 필요해, 차트 안 로고 대신 차트 위에 링크를 둔다

import { useEffect, useRef, useState } from "react";
import {
  CandlestickSeries,
  ColorType,
  CrosshairMode,
  HistogramSeries,
  LineSeries,
  LineStyle,
  createChart,
  createSeriesMarkers,
  type IChartApi,
  type ISeriesApi,
  type ISeriesMarkersPluginApi,
  type SeriesMarker,
  type Time,
} from "lightweight-charts";
import type { Price } from "@/lib/api";
import { bollinger, ichimoku, macd, rsi, sma, stochastic, type Series } from "@/lib/indicators";

// 한국 증시 관례: 오르면 빨강, 내리면 파랑
const UP = "#ff5a5a";
const DOWN = "#5b9bff";

export type DayMarks = {
  newsDates: Set<string>;
  reportDates: Set<string>;
  disclosureDates: Set<string>;
  moveDates?: Map<string, number>; // 크게 움직인 날 → 등락률(%)
};

type Interval = "day" | "week" | "month" | "year";
const INTERVALS: { key: Interval; label: string }[] = [
  { key: "day", label: "일" },
  { key: "week", label: "주" },
  { key: "month", label: "월" },
  { key: "year", label: "년" },
];
const ORDER: Interval[] = ["day", "week", "month", "year"];
const NAME: Record<Interval, string> = { day: "일봉", week: "주봉", month: "월봉", year: "연봉" };

// 보조지표 설정. 초보 화면이 복잡하지 않게 기본은 이동평균선만 켠다
type Indicators = {
  ma: number[];
  bb: boolean;
  rsi: boolean;
  macd: boolean;
  w52: boolean; // 52주 최고·최저선
  ichimoku: boolean; // 일목균형표
  stoch: boolean; // 스토캐스틱
};
const MA_PERIODS = [5, 20, 60, 120]; // 한국 증권사 앱 기본값 (1주·1달·3달·6달 거래일)
const MA_COLORS: Record<number, string> = { 5: "#ffd84d", 20: "#ff7ad9", 60: "#4fe7b0", 120: "#b18cff" };
const DEFAULT_IND: Indicators = { ma: MA_PERIODS, bb: false, rsi: false, macd: false, w52: false, ichimoku: false, stoch: false };
const IND_KEY = "stroll.indicators";
const IND_HELP = {
  ma: "최근 N개 봉 종가의 평균을 이은 선. 짧은 선이 긴 선을 뚫고 오르면 골든크로스, 내리면 데드크로스라고 불러요.",
  bb: "20일 평균선 위아래로 평소 움직임 폭(표준편차 2배)만큼 띠를 그려요. 띠 밖으로 나가면 평소보다 많이 움직인 거예요.",
  rsi: "최근 14개 봉 동안 오른 힘이 얼마나 센지 0~100으로. 70 이상은 과열, 30 이하는 침체로 봐요.",
  macd: "짧은 평균(12)과 긴 평균(26)의 차이. 신호선(9)을 위로 뚫으면 오르는 힘이 세지는 신호로 봐요.",
  w52: "최근 1년(52주) 동안 가장 높았던·낮았던 가격을 가로선으로. 지금 주가가 1년 중 어디쯤인지 한눈에 봐요.",
  ichimoku: "일본에서 만든 지표로 한국에서도 인기예요. 전환선·기준선과, 앞으로 밀어 그린 두 선행스팬 사이 '구름'을 봐요. 주가가 구름 위면 강세, 아래면 약세로 봐요.",
  stoch: "최근 14개 봉의 최고·최저 사이에서 지금 가격 위치(0~100). 80 이상 과열, 20 이하 침체. RSI보다 민감해요.",
};
const ICHI = { tenkan: "#ff9f43", kijun: "#54a0ff", spanA: "rgba(255,90,90,0.75)", spanB: "rgba(91,155,255,0.75)", lagging: "rgba(200,200,200,0.5)" };

// 봉 하나 뒤의 날짜 (일목균형표 선행스팬을 미래 자리에 그리기 위해)
function nextTime(t: string, interval: Interval): string {
  const d = new Date(`${t}T00:00:00Z`);
  if (interval === "day") {
    do d.setUTCDate(d.getUTCDate() + 1);
    while (d.getUTCDay() === 0 || d.getUTCDay() === 6); // 주말 건너뛰기
  } else if (interval === "week") d.setUTCDate(d.getUTCDate() + 7);
  else if (interval === "month") d.setUTCMonth(d.getUTCMonth() + 1, 1);
  else d.setUTCFullYear(d.getUTCFullYear() + 1, 0, 1);
  return d.toISOString().slice(0, 10);
}

function loadIndicators(): Indicators {
  try {
    const raw = localStorage.getItem(IND_KEY);
    if (raw) return { ...DEFAULT_IND, ...JSON.parse(raw) };
  } catch {
    // 저장소를 못 쓰면 기본값
  }
  return DEFAULT_IND;
}

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
  // 봉 버튼으로 직접 고르면 그 봉을 유지한다 (자동 전환 끔). 기간 버튼(3개월 등)을 누르면 다시 자동
  const manualRef = useRef(false);
  const [interval, setIntervalState] = useState<Interval>("day");
  const [ind, setInd] = useState<Indicators>(DEFAULT_IND);
  const [menuOpen, setMenuOpen] = useState(false);
  const indRef = useRef<Indicators>(DEFAULT_IND);
  indRef.current = ind;
  const indSeriesRef = useRef<ISeriesApi<"Line" | "Histogram">[]>([]);
  const priceLinesRef = useRef<ReturnType<ISeriesApi<"Candlestick">["createPriceLine"]>[]>([]); // 52주 선
  // 지금 그려진 지표 값 (값 표시줄용)
  const indDataRef = useRef<{
    ma: Record<number, Series>;
    bb?: ReturnType<typeof bollinger>;
    rsi?: Series;
    macd?: ReturnType<typeof macd>;
    stoch?: ReturnType<typeof stochastic>;
    ichimoku?: ReturnType<typeof ichimoku>;
    w52?: { high: number; low: number };
  }>({ ma: {} });
  const legendRef = useRef<HTMLDivElement>(null);

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
    drawIndicators();

    if (visible) {
      chart.timeScale().setVisibleRange({ from: visible.from as Time, to: visible.to as Time });
    } else {
      chart.timeScale().fitContent();
    }
    // 위에서 바꾼 보이는 범위 때문에 또 봉이 바뀌지 않게 한 박자 쉰다
    setTimeout(() => (switchingRef.current = false), 80);
  };

  // 봉 버튼: 그 봉에 알맞은 기간을 보여주고 그 봉을 유지한다 (증권사 앱처럼 월봉을 누르면 긴 기간이 보인다)
  const CHOSEN_RANGE_DAYS: Record<Interval, number | null> = { day: 183, week: 1095, month: null, year: null };
  const chooseInterval = (next: Interval) => {
    manualRef.current = true;
    const days = CHOSEN_RANGE_DAYS[next];
    if (days === null || prices.length === 0) return applyInterval(next);
    const last = prices[prices.length - 1].date;
    const from = shiftDate(last, -days);
    applyInterval(next, { from: from < prices[0].date ? prices[0].date : from, to: last });
  };

  // 보조지표 다시 그리기: 이전 선·칸을 지우고 지금 봉·설정으로 새로 그린다
  const drawIndicators = () => {
    const chart = chartRef.current;
    if (!chart) return;
    for (const sr of indSeriesRef.current) {
      try {
        chart.removeSeries(sr);
      } catch {
        // 이미 사라진 차트의 선이면 무시
      }
    }
    indSeriesRef.current = [];
    const candles = candlesRef.current;
    for (const pl of priceLinesRef.current) {
      try {
        candles?.removePriceLine(pl);
      } catch {
        // 이미 사라진 차트
      }
    }
    priceLinesRef.current = [];
    // 거래량(1번 칸) 아래에 붙였던 RSI·MACD 칸 지우기
    for (let i = chart.panes().length - 1; i >= 2; i--) chart.removePane(i);

    const bars = barsRef.current;
    const closes = bars.map((b) => b.close);
    const highs = bars.map((b) => b.high);
    const lows = bars.map((b) => b.low);
    const cfg = indRef.current;
    const data: typeof indDataRef.current = { ma: {} };
    // 일목균형표를 켜면 선행스팬을 그릴 미래 자리(26칸)를 시간축에 덧붙인다
    const times = bars.map((b) => b.time);
    if (cfg.ichimoku && bars.length) {
      for (let k = 0; k < 26; k++) times.push(nextTime(times[times.length - 1], intervalRef.current));
    }
    if (candles) {
      const candleData = bars.map((b) => ({ time: b.time, open: b.open, high: b.high, low: b.low, close: b.close }));
      candles.setData([...candleData, ...times.slice(bars.length).map((t) => ({ time: t }))]);
    }
    const toLine = (vals: Series) => times.map((t, i) => (vals[i] === null || vals[i] === undefined ? { time: t } : { time: t, value: vals[i] as number }));
    const addLine = (vals: Series, color: string, pane: number, style: LineStyle = LineStyle.Solid, width: 1 | 2 = 1) => {
      const sr = chart.addSeries(
        LineSeries,
        {
          color,
          lineWidth: width,
          lineStyle: style,
          priceLineVisible: false,
          lastValueVisible: false,
          crosshairMarkerVisible: false,
          // 가격 칸의 선(이동평균·볼린저)은 세로축 범위를 넓히지 않게 (월봉 볼린저 아래선이 0 밑으로 내려가 축이 늘어났다)
          ...(pane === 0 ? { autoscaleInfoProvider: () => null } : {}),
        },
        pane,
      );
      sr.setData(toLine(vals));
      indSeriesRef.current.push(sr);
      return sr;
    };

    for (const n of cfg.ma) {
      data.ma[n] = sma(closes, n);
      addLine(data.ma[n], MA_COLORS[n] ?? "#ccc", 0);
    }
    if (cfg.bb) {
      data.bb = bollinger(closes);
      addLine(data.bb.upper, "rgba(200,200,200,0.55)", 0, LineStyle.Dashed);
      addLine(data.bb.lower, "rgba(200,200,200,0.55)", 0, LineStyle.Dashed);
    }
    if (cfg.ichimoku) {
      data.ichimoku = ichimoku(highs, lows, closes);
      addLine(data.ichimoku.spanA, ICHI.spanA, 0);
      addLine(data.ichimoku.spanB, ICHI.spanB, 0);
      addLine(data.ichimoku.tenkan, ICHI.tenkan, 0);
      addLine(data.ichimoku.kijun, ICHI.kijun, 0);
      addLine(data.ichimoku.lagging, ICHI.lagging, 0, LineStyle.Dotted);
    }
    if (cfg.w52 && candles && prices.length) {
      // 봉 단위와 상관없이 일봉 최근 1년(약 250거래일)으로 계산
      const yearAgo = shiftDate(prices[prices.length - 1].date, -365);
      const lastYear = prices.filter((p) => p.date > yearAgo);
      const high = Math.max(...lastYear.map((p) => p.high));
      const low = Math.min(...lastYear.map((p) => p.low));
      data.w52 = { high, low };
      priceLinesRef.current.push(
        candles.createPriceLine({ price: high, color: "rgba(255,90,90,0.8)", lineStyle: LineStyle.LargeDashed, lineWidth: 1, axisLabelVisible: true, title: "52주 최고" }),
        candles.createPriceLine({ price: low, color: "rgba(91,155,255,0.8)", lineStyle: LineStyle.LargeDashed, lineWidth: 1, axisLabelVisible: true, title: "52주 최저" }),
      );
    }
    let pane = 2;
    if (cfg.stoch) {
      data.stoch = stochastic(highs, lows, closes);
      const sr = addLine(data.stoch.k, "#4fe7b0", pane);
      addLine(data.stoch.d, "#ff7ad9", pane);
      sr.createPriceLine({ price: 80, color: "rgba(255,90,90,0.6)", lineStyle: LineStyle.Dashed, lineWidth: 1, axisLabelVisible: true, title: "과열" });
      sr.createPriceLine({ price: 20, color: "rgba(91,155,255,0.6)", lineStyle: LineStyle.Dashed, lineWidth: 1, axisLabelVisible: true, title: "침체" });
      chart.panes()[pane]?.setHeight(90);
      pane += 1;
    }
    if (cfg.rsi) {
      data.rsi = rsi(closes);
      const sr = addLine(data.rsi, "#ffc861", pane);
      sr.createPriceLine({ price: 70, color: "rgba(255,90,90,0.6)", lineStyle: LineStyle.Dashed, lineWidth: 1, axisLabelVisible: true, title: "과열" });
      sr.createPriceLine({ price: 30, color: "rgba(91,155,255,0.6)", lineStyle: LineStyle.Dashed, lineWidth: 1, axisLabelVisible: true, title: "침체" });
      chart.panes()[pane]?.setHeight(90);
      pane += 1;
    }
    if (cfg.macd) {
      data.macd = macd(closes);
      const hist = chart.addSeries(HistogramSeries, { priceLineVisible: false, lastValueVisible: false }, pane);
      hist.setData(
        times.map((t, i) => {
          const v = data.macd!.hist[i];
          return v === null || v === undefined ? { time: t } : { time: t, value: v, color: v >= 0 ? "rgba(255,90,90,0.5)" : "rgba(91,155,255,0.5)" };
        }),
      );
      indSeriesRef.current.push(hist);
      addLine(data.macd.macd, "#4fe7b0", pane);
      addLine(data.macd.signal, "#ff7ad9", pane);
      chart.panes()[pane]?.setHeight(100);
    }
    chart.panes()[1]?.setHeight(70); // 칸을 더하고 빼면 높이가 다시 나뉘므로 거래량 칸 높이를 다시 정한다
    indDataRef.current = data;
    updateLegend(bars.length - 1);
  };

  // 차트 위 값 표시줄: 마우스를 올린 막대(없으면 마지막 막대)의 지표 값
  const updateLegend = (i: number) => {
    const el = legendRef.current;
    if (!el) return;
    const d = indDataRef.current;
    const fmt = (v: number | null | undefined, digits = 0) =>
      v === null || v === undefined ? "-" : v.toLocaleString("ko-KR", { maximumFractionDigits: digits });
    const unit = { day: "일", week: "주", month: "개월", year: "년" }[intervalRef.current];
    const parts: string[] = [];
    for (const n of Object.keys(d.ma).map(Number)) {
      parts.push(`<span style="color:${MA_COLORS[n]}">${n}${unit} ${fmt(d.ma[n][i])}</span>`);
    }
    if (d.bb) parts.push(`<span class="lg-sub">볼린저 ${fmt(d.bb.lower[i])} ~ ${fmt(d.bb.upper[i])}</span>`);
    if (d.rsi) parts.push(`<span style="color:#ffc861">RSI ${fmt(d.rsi[i], 1)}</span>`);
    if (d.macd) parts.push(`<span style="color:#4fe7b0">MACD ${fmt(d.macd.macd[i])}</span> <span style="color:#ff7ad9">신호 ${fmt(d.macd.signal[i])}</span>`);
    if (d.stoch) parts.push(`<span style="color:#4fe7b0">스토캐스틱 %K ${fmt(d.stoch.k[i], 1)}</span> <span style="color:#ff7ad9">%D ${fmt(d.stoch.d[i], 1)}</span>`);
    if (d.ichimoku)
      parts.push(
        `<span style="color:${ICHI.tenkan}">전환 ${fmt(d.ichimoku.tenkan[i])}</span> <span style="color:${ICHI.kijun}">기준 ${fmt(d.ichimoku.kijun[i])}</span> <span class="lg-sub">구름 ${fmt(d.ichimoku.spanA[i])} ~ ${fmt(d.ichimoku.spanB[i])}</span>`,
      );
    if (d.w52) parts.push(`<span class="lg-sub">52주 ${fmt(d.w52.low)} ~ ${fmt(d.w52.high)}</span>`);
    el.innerHTML = parts.join(" · ");
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
      const move = m.moveDates && b.days.map((d) => m.moveDates!.get(d)).find((v) => v !== undefined);
      if (move !== undefined && move !== null)
        list.push(
          move > 0
            ? { time: b.time, position: "belowBar", color: "#4fe7b0", shape: "arrowUp", text: "⚡" }
            : { time: b.time, position: "aboveBar", color: "#4fe7b0", shape: "arrowDown", text: "⚡" },
        );
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
        attributionLogo: false, // 출처 링크는 차트 위에 따로 둔다 (라이선스 조건)
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
    indSeriesRef.current = []; // 새 차트에는 아직 지표 선이 없다

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
      if (!range || switchingRef.current || manualRef.current) return;
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
        updateLegend(barsRef.current.length - 1);
        return;
      }
      updateLegend(barsRef.current.indexOf(bar));
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
    manualRef.current = false;
    applyInterval(intervalForRange(rangeDays), { from: from < first ? first : from, to: last });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [prices, rangeDays]);

  // 지표 설정: 처음 한 번 브라우저 저장소에서 불러온다. 저장은 사용자가 바꿀 때만 한다
  // (효과(useEffect)에서 저장하면 개발 모드가 효과를 두 번 돌리면서 기본값으로 덮어썼다)
  useEffect(() => {
    setInd(loadIndicators());
  }, []);
  useEffect(() => {
    drawIndicators();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [ind]);

  const changeInd = (update: (v: Indicators) => Indicators) =>
    setInd((v) => {
      const next = update(v);
      try {
        localStorage.setItem(IND_KEY, JSON.stringify(next));
      } catch {
        // 저장 못 해도 화면은 그대로
      }
      return next;
    });

  const toggleMa = (n: number) =>
    changeInd((v) => ({ ...v, ma: v.ma.includes(n) ? v.ma.filter((x) => x !== n) : [...v.ma, n].sort((a, b) => a - b) }));

  // 뉴스·리포트·공시 표시는 데이터가 따로 도착하므로 바뀔 때마다 다시 그린다
  useEffect(() => {
    drawMarkers();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [marks]);

  return (
    <div className="chart-wrap">
      <div className="chart-toolbar">
        <div className="chart-interval" role="group" aria-label="봉 단위">
          {INTERVALS.map((it) => (
            <button
              key={it.key}
              className={interval === it.key ? "on" : ""}
              onClick={() => chooseInterval(it.key)}
              title={NAME[it.key]}
            >
              {it.label}
            </button>
          ))}
        </div>
        <div className="chart-ind">
          <button className={`chart-ind-btn ${menuOpen ? "on" : ""}`} onClick={() => setMenuOpen((v) => !v)} aria-expanded={menuOpen}>
            지표 ▾
          </button>
          {menuOpen && (
            <div className="chart-ind-menu">
              <div className="ind-row">
                <b>이동평균선</b>
                <div className="ind-chips">
                  {MA_PERIODS.map((n) => (
                    <button
                      key={n}
                      className={ind.ma.includes(n) ? "on" : ""}
                      style={{ borderColor: MA_COLORS[n], color: ind.ma.includes(n) ? "#00051e" : MA_COLORS[n], background: ind.ma.includes(n) ? MA_COLORS[n] : "none" }}
                      onClick={() => toggleMa(n)}
                    >
                      {n}
                    </button>
                  ))}
                </div>
                <p>{IND_HELP.ma}</p>
              </div>
              {(
                [
                  ["bb", "볼린저밴드"],
                  ["w52", "52주 최고·최저선"],
                  ["ichimoku", "일목균형표"],
                  ["rsi", "RSI (과열·침체)"],
                  ["stoch", "스토캐스틱 (과열·침체)"],
                  ["macd", "MACD (추세 전환)"],
                ] as const
              ).map(([key, label]) => (
                <label key={key} className="ind-row">
                  <span>
                    <input type="checkbox" checked={ind[key]} onChange={() => changeInd((v) => ({ ...v, [key]: !v[key] }))} />{" "}
                    <b>{label}</b>
                  </span>
                  <p>{IND_HELP[key]}</p>
                </label>
              ))}
              <button className="ind-reset" onClick={() => changeInd(() => DEFAULT_IND)}>
                기본값으로
              </button>
            </div>
          )}
        </div>
        <a className="chart-credit" href="https://www.tradingview.com/" target="_blank" rel="noreferrer">
          차트: TradingView Lightweight Charts
        </a>
      </div>
      <div ref={legendRef} className="chart-legend" />
      {/* RSI·MACD 칸을 켜면 그만큼 차트를 키워서 캔들 칸이 눌리지 않게 */}
      <div
        ref={containerRef}
        className="chart"
        style={{ "--chart-extra": `${(ind.rsi ? 90 : 0) + (ind.stoch ? 90 : 0) + (ind.macd ? 100 : 0)}px` } as React.CSSProperties}
      />
      <div ref={tooltipRef} className="chart-tooltip" />
    </div>
  );
}
