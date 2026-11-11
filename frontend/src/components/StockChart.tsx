"use client";

// 캔들 차트. TradingView Lightweight Charts를 감싼 컴포넌트.
// prices를 받으면 그리고, 차트의 날짜를 누르면 onSelectDate로 그 날짜를 알려준다.

import { useEffect, useRef } from "react";
import {
  CandlestickSeries,
  ColorType,
  HistogramSeries,
  createChart,
} from "lightweight-charts";
import type { Price } from "@/lib/api";

// 한국 증시 관례: 오르면 빨강, 내리면 파랑
const UP = "#e0443e";
const DOWN = "#2f6fde";

type Props = {
  prices: Price[];
  onSelectDate: (date: string) => void;
};

export default function StockChart({ prices, onSelectDate }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  // 최신 onSelectDate를 차트를 다시 만들지 않고 쓰기 위한 보관함
  const onSelectRef = useRef(onSelectDate);
  onSelectRef.current = onSelectDate;

  useEffect(() => {
    const container = containerRef.current;
    if (!container || prices.length === 0) return;

    const chart = createChart(container, {
      autoSize: true,
      layout: {
        background: { type: ColorType.Solid, color: "transparent" },
        textColor: "#6b7280",
        fontFamily: "inherit",
      },
      grid: {
        vertLines: { color: "#f0f1f3" },
        horzLines: { color: "#f0f1f3" },
      },
      rightPriceScale: { borderVisible: false },
      timeScale: { borderVisible: false },
      localization: {
        locale: "ko-KR",
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
      prices.map((p) => ({
        time: p.date,
        open: p.open,
        high: p.high,
        low: p.low,
        close: p.close,
      })),
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
        color: p.close >= p.open ? "rgba(224,68,62,0.35)" : "rgba(47,111,222,0.35)",
      })),
    );
    chart.panes()[1]?.setHeight(100);

    chart.timeScale().fitContent();

    chart.subscribeClick((param) => {
      // 누른 위치의 캔들에서 날짜를 꺼낸다 (캔들 데이터의 time은 "YYYY-MM-DD" 문자열)
      const time = param.seriesData.get(candles)?.time ?? param.time;
      if (typeof time === "string") onSelectRef.current(time);
    });

    return () => chart.remove();
  }, [prices]);

  return <div ref={containerRef} className="chart" />;
}
