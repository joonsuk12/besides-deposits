"use client";
// 차트 화면 오른쪽 맨 위 카드. 공간이 좁아서 탭으로 오간다.
//   주가 수준 : 지금의 PER·PBR과 업종 비교 (ValuationCard)
//   연간 흐름 : 연도별 PER·PBR 막대 차트 + 실적 표
//   회사 소개 : 이 회사가 무슨 일을 하는지

import { useEffect, useState } from "react";

import ValuationCard from "@/components/ValuationCard/ValuationCard";
import { fetchOverview, type Overview, type YearValuation } from "@/lib/api";
import styles from "./StockInfoCard.module.css";

const TABS = [
  { key: "now", label: "💰 주가 수준" },
  { key: "trend", label: "📈 연간 흐름" },
  { key: "about", label: "🏢 회사 소개" },
] as const;
type TabKey = (typeof TABS)[number]["key"];

const num = (n: number | null, digits = 0) =>
  n === null ? "-" : n.toLocaleString("ko-KR", { maximumFractionDigits: digits });
// 억원 단위 숫자를 읽기 쉽게: 12,345억 → 1.2조
const eok = (n: number | null) =>
  n === null ? "-" : Math.abs(n) >= 10000 ? `${(n / 10000).toFixed(1)}조` : `${num(n)}억`;

// 연도별 막대 차트 하나 (PER 또는 PBR). 예상치는 점선 막대, 적자인 해는 "적자"라고 쓴다.
function Bars({ title, hint, years, pick }: { title: string; hint: string; years: YearValuation[]; pick: (y: YearValuation) => number | null }) {
  const values = years.map(pick);
  const max = Math.max(...values.map((v) => v ?? 0), 0.01);
  const W = 300;
  const H = 110;
  const slot = W / years.length;
  const barW = Math.min(44, slot * 0.55);
  const many = years.length > 6; // 해가 많으면 글자를 줄여 겹치지 않게

  return (
    <figure className={styles["chart"]}>
      <figcaption>
        <b>{title}</b> <span>{hint}</span>
      </figcaption>
      <svg viewBox={`0 0 ${W} ${H + 34}`} role="img" aria-label={`${title} 연도별 막대 차트`}>
        <line x1="0" y1={H + 14} x2={W} y2={H + 14} className={styles["axis"]} />
        {years.map((y, i) => {
          const v = values[i];
          const cx = slot * i + slot / 2;
          const h = v === null ? 0 : Math.max(3, (v / max) * (H - 6));
          return (
            <g key={y.label}>
              {v !== null && (
                <rect
                  x={cx - barW / 2}
                  y={H + 14 - h}
                  width={barW}
                  height={h}
                  rx="3"
                  className={y.is_estimate ? styles["bar-est"] : y.source === "dart" ? styles["bar-dart"] : styles["bar"]}
                />
              )}
              <text x={cx} y={H + 8 - h} textAnchor="middle" className={styles["val"]}>
                {v === null ? "적자" : many ? num(v, 1) : `${num(v, 1)}배`}
              </text>
              <text x={cx} y={H + 29} textAnchor="middle" className={styles["year"]}>
                {many ? `'${y.label.slice(2, 4)}` : y.label.slice(0, 4)}
                {y.is_estimate ? (many ? "e" : " 예상") : ""}
              </text>
            </g>
          );
        })}
      </svg>
    </figure>
  );
}

function Trend({ o }: { o: Overview }) {
  if (o.years.length === 0) return <p className={styles["muted"]}>연도별 실적 정보가 없어요.</p>;
  return (
    <div>
      {o.trend_comment && <p className={styles["comment"]}>{o.trend_comment}</p>}
      <Bars title="PER" hint="그해 이익의 몇 배에 주가가 매겨졌나" years={o.years} pick={(y) => y.per} />
      <Bars title="PBR" hint="순자산의 몇 배에 주가가 매겨졌나" years={o.years} pick={(y) => y.pbr} />
      <table className={styles["table"]}>
        <thead>
          <tr>
            <th></th>
            {o.years.slice(-4).map((y) => (
              <th key={y.label}>
                {y.label.slice(0, 4)}
                {y.is_estimate ? " 예상" : ""}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          <tr>
            <td>매출</td>
            {o.years.slice(-4).map((y) => (
              <td key={y.label}>{eok(y.revenue)}</td>
            ))}
          </tr>
          <tr>
            <td>영업이익</td>
            {o.years.slice(-4).map((y) => (
              <td key={y.label}>{eok(y.operating_profit)}</td>
            ))}
          </tr>
          <tr>
            <td title="자기자본으로 1년에 버는 비율">ROE</td>
            {o.years.slice(-4).map((y) => (
              <td key={y.label}>{y.roe === null ? "-" : `${num(y.roe, 1)}%`}</td>
            ))}
          </tr>
          <tr>
            <td>주당 배당금</td>
            {o.years.slice(-4).map((y) => (
              <td key={y.label}>{y.dividend === null ? "-" : `${num(y.dividend)}원`}</td>
            ))}
          </tr>
        </tbody>
      </table>
      <p className={styles["note"]}>
        표는 최근 4개 해만 보여줘요. 연도별 PER·PBR은 그해 말 주가 기준이에요.
        {o.years.some((y) => y.source === "dart") &&
          " 옅은 막대(네이버가 주지 않는 오래된 해)는 공시 사업보고서 숫자로 직접 계산한 근사치예요(최근 주식 수 기준, 비지배주주 몫 포함)."} 흐린 점선 막대는 증권사들의 예상치라 실제와 다를 수 있어요.
        &quot;주가 수준&quot; 탭의 숫자는 최근 1년 실적과 최근 종가 기준이라 조금 달라요.
      </p>
    </div>
  );
}

function About({ o }: { o: Overview }) {
  if (o.summary.length === 0) return <p className={styles["muted"]}>회사 소개 정보가 없어요.</p>;
  return (
    <div>
      {o.industry_name && <p className={styles["muted"]}>업종: {o.industry_name}</p>}
      <ul className={styles["about"]}>
        {o.summary.map((s) => (
          <li key={s}>{s.replace(/^동사는 /, "이 회사는 ").replace(/동사는/g, "이 회사는")}</li>
        ))}
      </ul>
      <p className={styles["note"]}>출처: 네이버 증권 기업개요. 더 자세한 내용은 공시의 사업보고서에 있어요.</p>
    </div>
  );
}

export default function StockInfoCard({ code }: { code: string }) {
  const [tab, setTab] = useState<TabKey>("now");
  const [overview, setOverview] = useState<Overview | null>(null);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    setOverview(null);
    setFailed(false);
    fetchOverview(code).then(setOverview).catch(() => setFailed(true));
  }, [code]);

  return (
    <div>
      <div className={styles["tabs"]} role="tablist">
        {TABS.map((t) => (
          <button
            key={t.key}
            role="tab"
            aria-selected={tab === t.key}
            className={tab === t.key ? styles["on"] : ""}
            onClick={() => setTab(t.key)}
          >
            {t.label}
          </button>
        ))}
      </div>

      {tab === "now" && <ValuationCard code={code} />}
      {tab !== "now" && failed && <p className={styles["muted"]}>정보를 불러오지 못했습니다.</p>}
      {tab !== "now" && !failed && !overview && <p className={styles["muted"]}>불러오는 중…</p>}
      {tab !== "now" && overview && !overview.available && <p className={styles["muted"]}>{overview.message}</p>}
      {tab === "trend" && overview?.available && <Trend o={overview} />}
      {tab === "about" && overview?.available && <About o={overview} />}
    </div>
  );
}
