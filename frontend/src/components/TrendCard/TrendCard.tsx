"use client";
// 투자자별 매매동향 카드: 외국인·기관·개인이 최근 이 종목을 사고 있는지 팔고 있는지.
//   1) 흐름 한 줄  2) 최근 5·20·60거래일 순매수 합계 표  3) 최근 20거래일 외국인·기관 막대(눌렀을 때만)
// 단위는 "주"(주식 수). 순매수(+)는 산 쪽이 많았다는 뜻, 순매도(-)는 판 쪽이 많았다는 뜻.

import { useEffect, useState } from "react";

import { fetchTrend, type Trend } from "@/lib/api";
import styles from "./TrendCard.module.css";

const BAR_DAYS = 20;

// 1,234,567 → "+123만", 큰 수는 만 단위로 줄여 읽기 쉽게
function qty(n: number) {
  const sign = n > 0 ? "+" : n < 0 ? "−" : "";
  const a = Math.abs(n);
  if (a >= 100_000_000) return `${sign}${(a / 100_000_000).toFixed(1)}억`;
  if (a >= 10_000) return `${sign}${Math.round(a / 10_000).toLocaleString("ko-KR")}만`;
  return `${sign}${a.toLocaleString("ko-KR")}`;
}
const tone = (n: number) => (n > 0 ? "up" : n < 0 ? "down" : "");

export default function TrendCard({ code }: { code: string }) {
  const [t, setT] = useState<Trend | null>(null);
  const [failed, setFailed] = useState(false);
  const [showBars, setShowBars] = useState(false); // 막대 그림은 눌렀을 때만 (카드가 길어지지 않게)

  useEffect(() => {
    setT(null);
    setFailed(false);
    fetchTrend(code)
      .then(setT)
      .catch(() => setFailed(true));
  }, [code]);

  if (failed) return <p className={styles["muted"]}>매매동향을 불러오지 못했습니다.</p>;
  if (!t) return <p className={styles["muted"]}>불러오는 중…</p>;
  if (!t.available) return <p className={styles["muted"]}>{t.message}</p>;

  const recent = t.items.slice(-BAR_DAYS);
  const max = Math.max(...recent.flatMap((d) => [Math.abs(d.foreign), Math.abs(d.organ)]), 1);
  const last = t.items[t.items.length - 1];

  return (
    <div>
      {t.comment && <p className={styles["comment"]}>{t.comment}</p>}

      <table className={styles["table"]}>
        <thead>
          <tr>
            <th>순매수 합계</th>
            <th>외국인</th>
            <th>기관</th>
            <th>개인</th>
          </tr>
        </thead>
        <tbody>
          {t.summary.map((s) => (
            <tr key={s.days}>
              <td>최근 {s.days}일</td>
              <td className={tone(s.foreign)}>{qty(s.foreign)}</td>
              <td className={tone(s.organ)}>{qty(s.organ)}</td>
              <td className={tone(s.individual)}>{qty(s.individual)}</td>
            </tr>
          ))}
        </tbody>
      </table>

      <button className={`ui-more ${styles["toggle"]}`} onClick={() => setShowBars(!showBars)}>
        {showBars ? "날짜별 막대 접기" : `📊 최근 ${recent.length}거래일 날짜별로 보기`}
      </button>
      {showBars && (
        <figure className={styles["bars"]}>
          <figcaption>
            최근 {recent.length}거래일 · <span className={styles["f"]}>■ 외국인</span>{" "}
            <span className={styles["o"]}>■ 기관</span> (위 = 순매수, 아래 = 순매도)
          </figcaption>
          <svg
            viewBox={`0 0 ${recent.length * 14} 80`}
            preserveAspectRatio="none"
            role="img"
            aria-label="외국인·기관 일별 순매수 막대"
          >
            <line x1="0" y1="40" x2={recent.length * 14} y2="40" className={styles["axis"]} />
            {recent.map((d, i) => {
              const fh = (Math.abs(d.foreign) / max) * 38;
              const oh = (Math.abs(d.organ) / max) * 38;
              return (
                <g key={d.date}>
                  <title>{`${d.date} 외국인 ${qty(d.foreign)}주 · 기관 ${qty(d.organ)}주`}</title>
                  <rect
                    x={i * 14 + 1}
                    y={d.foreign >= 0 ? 40 - fh : 40}
                    width="5"
                    height={Math.max(fh, 0.5)}
                    className={styles["bf"]}
                  />
                  <rect
                    x={i * 14 + 7}
                    y={d.organ >= 0 ? 40 - oh : 40}
                    width="5"
                    height={Math.max(oh, 0.5)}
                    className={styles["bo"]}
                  />
                </g>
              );
            })}
          </svg>
        </figure>
      )}

      <p className={styles["note"]}>
        단위: 주(주식 수).{" "}
        {last.foreign_ratio !== null && `외국인 보유 비율 ${last.foreign_ratio}% (${last.date} 기준). `}
        외국인·기관이 함께 꾸준히 사는 종목은 주목받는 경우가 많지만, 사고판 이유는 알 수 없으니 참고만 하세요.
      </p>
    </div>
  );
}
