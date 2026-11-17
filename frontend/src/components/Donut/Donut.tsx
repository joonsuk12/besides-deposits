// 도넛 차트 (외부 라이브러리 없이 SVG). 비중(%) 목록을 받아 조각과 범례를 그린다.
// - 조각이 많으면 앞의 maxSlices개만 색으로, 나머지는 "기타"로 묶는다
// - 합이 100%가 안 되면 남는 몫을 "기타"로 채운다 (예: ETF 상위 10개 종목 = 78%, 나머지 22%)

import Link from "next/link";

import styles from "./Donut.module.css";

export type Slice = { name: string; weight: number; code?: string | null };

const COLORS = [
  "#4fe7b0",
  "#5b9bff",
  "#ffc861",
  "#ff7ad9",
  "#b18cff",
  "#ff9f43",
  "#b4ff4a",
  "#54a0ff",
  "#ff5a5a",
  "#9aa1b2",
];
const REST_COLOR = "rgba(154, 161, 178, 0.35)";

export default function Donut({
  items,
  maxSlices = 9,
  center,
  centerSub,
  linkable = false,
}: {
  items: Slice[];
  maxSlices?: number;
  center?: string; // 가운데 큰 글자
  centerSub?: string; // 가운데 작은 글자
  linkable?: boolean; // 이름을 누르면 그 종목 차트로
}) {
  const sorted = [...items].filter((i) => i.weight > 0).sort((a, b) => b.weight - a.weight);
  const shown = sorted.slice(0, maxSlices);
  const used = shown.reduce((a, i) => a + i.weight, 0);
  const rest = Math.max(0, 100 - used);
  const slices = rest >= 0.5 ? [...shown, { name: "기타", weight: rest, code: null }] : shown;
  const total = slices.reduce((a, i) => a + i.weight, 0) || 1;

  const R = 40;
  const C = 2 * Math.PI * R;
  let offset = 0;

  return (
    <div className={styles["wrap"]}>
      <svg viewBox="0 0 100 100" className={styles["svg"]} role="img" aria-label="비중 도넛 차트">
        <circle cx="50" cy="50" r={R} className={styles["track"]} />
        {slices.map((s, i) => {
          const len = (s.weight / total) * C;
          const el = (
            <circle
              key={s.name}
              cx="50"
              cy="50"
              r={R}
              fill="none"
              stroke={s.name === "기타" ? REST_COLOR : COLORS[i % COLORS.length]}
              strokeWidth="14"
              strokeDasharray={`${Math.max(len - 0.4, 0)} ${C}`}
              strokeDashoffset={-offset}
              transform="rotate(-90 50 50)"
            >
              <title>{`${s.name} ${s.weight.toFixed(2)}%`}</title>
            </circle>
          );
          offset += len;
          return el;
        })}
        {center && (
          <text x="50" y={centerSub ? 49 : 53} textAnchor="middle" className={styles["center"]}>
            {center}
          </text>
        )}
        {centerSub && (
          <text x="50" y="61" textAnchor="middle" className={styles["center-sub"]}>
            {centerSub}
          </text>
        )}
      </svg>
      <ul className={styles["legend"]}>
        {slices.map((s, i) => (
          <li key={s.name}>
            <i style={{ background: s.name === "기타" ? REST_COLOR : COLORS[i % COLORS.length] }} />
            <span className={styles["name"]}>
              {linkable && s.code ? <Link href={`/${s.code}`}>{s.name}</Link> : s.name}
            </span>
            <span className={styles["val"]}>{s.weight.toLocaleString("ko-KR", { maximumFractionDigits: 2 })}%</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
