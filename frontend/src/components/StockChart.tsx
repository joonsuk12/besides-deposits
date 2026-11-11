"use client";

// 캔들 차트. TradingView Lightweight Charts를 감싼 컴포넌트 (NewStocks와 같은 라이브러리, 버전 5).
// - prices를 받아 캔들 + 거래량을 그린다
// - 마우스를 올리면 그날 시가·고가·저가·종가·거래량 툴팁 (NewStocks와 같은 방식)
// - 날짜를 누르면 onSelectDate로 그 날짜를 알려준다 (2단계부터 그날 뉴스·리포트를 띄우는 데 쓴다)

import { useEffect, useRef } from "react";
import {
  CandlestickSeries,
  ColorType,
  CrosshairMode,
  HistogramSeries,
  createChart,
} from "lightweight-charts";
import type { Price } from "@/lib/api";

// 한국 증시 관례: 오르면 빨강, 내리면 파랑
const UP = "#ff5a5a";
const DOWN = "#5b9bff";

type Props = {
  prices: Price[];
  onSelectDate: (date: string) => void;
};

const won = (n: number) => n.toLocaleString("ko-KR");

export default function StockChart({ prices, onSelectDate }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const tooltipRef = useRef<HTMLDivElement>(null);
  // 최신 onSelectDate를 차트를 다시 만들지 않고 쓰기 위한 보관함
  const onSelectRef = useRef(onSelectDate);
  onSelectRef.current = onSelectDate;

  useEffect(() => {
    const container = containerRef.current;
    const tooltip = tooltipRef.current;
    if (!container || !tooltip || prices.length === 0) return;

    const chart = createChart(container, {
      autoSize: true,
      layout: {
        background: { type: ColorType.Solid, color: "#00051E" },
        textColor: "#d6d8e0",
        fontFamily: "inherit",
      },
      grid: {
        vertLines: { color: "rgba(197, 203, 206, 0.1)" },
        horzLines: { color: "rgba(197, 203, 206, 0.1)" },
      },
      crosshair: { mode: CrosshairMode.Normal },
      rightPriceScale: { borderColor: "rgba(197, 203, 206, 0.5)" },
      timeScale: { borderColor: "rgba(197, 203, 206, 0.5)" },
      localization: {
        locale: "ko-KR",
        dateFormat: "yyyy-MM-dd",
        priceFormatter: (p: number) => Math.round(p).toLocaleString("ko-KR"),
      },
    });

    const candles = chart.addSeries(CandlestickSeries, {
      upColor: UP,
      downColor: DOWN,
      wickUpColor: UP,
      wickDownColor: DOWN,
      borderVisible: false,
      priceFormat: { type: "price", precision: 0, minMove: 1 },
    });
    candles.setData(
      prices.map((p) => ({ time: p.date, open: p.open, high: p.high, low: p.low, close: p.close })),
    );

    // 거래량 막대는 차트 아래 별도 칸(pane 1)에 그린다
    const volume = chart.addSeries(
      HistogramSeries,
      { priceFormat: { type: "volume" }, lastValueVisible: false, priceLineVisible: false },
      1,
    );
    volume.setData(
      prices.map((p) => ({
        time: p.date,
        value: p.volume,
        color: p.close >= p.open ? "rgba(255,90,90,0.45)" : "rgba(91,155,255,0.45)",
      })),
    );
    chart.panes()[1]?.setHeight(90);
    chart.timeScale().fitContent();

    // 마우스를 올린 날의 툴팁
    const volumeByDate = new Map(prices.map((p) => [p.date, p.volume]));
    chart.subscribeCrosshairMove((param) => {
      const bar = param.seriesData.get(candles) as
        | { time: string; open: number; high: number; low: number; close: number }
        | undefined;
      if (!param.point || !bar) {
        tooltip.style.display = "none";
        return;
      }
      tooltip.innerHTML = `
        <div class="tt-date">${bar.time}</div>
        <div>시가 ${won(bar.open)}</div>
        <div>고가 ${won(bar.high)}</div>
        <div>저가 ${won(bar.low)}</div>
        <div>종가 ${won(bar.close)}</div>
        <div>거래량 ${won(volumeByDate.get(bar.time) ?? 0)}</div>`;
      tooltip.style.display = "block";
      const left = param.point.x + 20 + tooltip.offsetWidth > container.clientWidth
        ? param.point.x - tooltip.offsetWidth - 20
        : param.point.x + 20;
      tooltip.style.left = `${left}px`;
      tooltip.style.top = `${Math.max(8, param.point.y - 40)}px`;
    });

    chart.subscribeClick((param) => {
      // 누른 위치의 캔들에서 날짜를 꺼낸다 (캔들 데이터의 time은 "YYYY-MM-DD" 문자열)
      const time = param.seriesData.get(candles)?.time ?? param.time;
      if (typeof time === "string") onSelectRef.current(time);
    });

    return () => chart.remove();
  }, [prices]);

  return (
    <div className="chart-wrap">
      <div ref={containerRef} className="chart" />
      <div ref={tooltipRef} className="chart-tooltip" />
    </div>
  );
}
