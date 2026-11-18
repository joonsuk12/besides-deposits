// "오늘 왜 움직였지?"
// - MoveChips: 차트 아래 "크게 움직인 날" 칩 줄. 누르면 그날을 선택한다 (아래 날짜 칸에 그날 내용이 나온다)
// - WhyMoved: 선택한 날이 크게 움직인 날이면 날짜 칸 맨 위에 나오는 상자.
//   시장 전체가 같이 움직였는지 / 이 종목만 움직였는지, 같은 날 공시, 투자자별 매매, 거래량을 한곳에.
//   원인을 단정하지 않고 "같은 날 있었던 일"로만 보여준다.

import type { BigMove, Moves } from "@/lib/api";
import styles from "./WhyMoved.module.css";

const SCOPE_LABEL: Record<BigMove["scope"], string> = {
  market: "🌊 시장 전체가 움직인 날",
  both: "🌊+🎯 시장도, 이 종목도",
  stock: "🎯 이 종목만 움직인 날",
  unknown: "❔ 시장 비교 불가",
};
const pct = (n: number) => `${n > 0 ? "+" : ""}${n.toFixed(2)}%`;
const tone = (n: number) => (n > 0 ? "up" : n < 0 ? "down" : "");
const qty = (n: number) => {
  const a = Math.abs(n);
  const s = a >= 10_000 ? `${Math.round(a / 10_000).toLocaleString("ko-KR")}만` : a.toLocaleString("ko-KR");
  return `${n > 0 ? "+" : n < 0 ? "−" : ""}${s}`;
};

export function MoveChips({
  moves,
  selectedDate,
  onSelect,
}: {
  moves: Moves | null;
  selectedDate: string | null;
  onSelect: (date: string) => void;
}) {
  if (!moves?.available || moves.moves.length === 0) return null;
  return (
    <div className={styles["chips-wrap"]}>
      <span className={styles["chips-title"]}>⚡ 크게 움직인 날</span>
      <div className={styles["chips"]}>
        {moves.moves.slice(0, 12).map((m) => (
          <button
            key={m.date}
            className={`ui-chip ${selectedDate === m.date ? "on" : ""}`}
            onClick={() => onSelect(m.date)}
            title={m.scope_text}
          >
            {m.date.slice(2).replaceAll("-", ".")} <span className={tone(m.change_pct)}>{pct(m.change_pct)}</span>
          </button>
        ))}
      </div>
      {moves.threshold_text && <p className={styles["muted"]}>{moves.threshold_text}</p>}
    </div>
  );
}

export default function WhyMoved({ move }: { move: BigMove }) {
  return (
    <div className={styles["box"]}>
      <div className={styles["head"]}>
        <b>⚡ 이날 왜 움직였을까?</b>
        <span className={`${styles["badge"]} ${styles[move.scope]}`}>{SCOPE_LABEL[move.scope]}</span>
      </div>
      <ul className={styles["facts"]}>
        <li>
          <span className={styles["k"]}>이 종목</span>
          <b className={tone(move.change_pct)}>{pct(move.change_pct)}</b>
          {move.index_change_pct !== null && (
            <>
              <span className={styles["k"]}>{move.index_name}</span>
              <b className={tone(move.index_change_pct)}>{pct(move.index_change_pct)}</b>
            </>
          )}
          {move.volume_ratio !== null && (
            <>
              <span className={styles["k"]}>거래량</span>
              <b>평소의 {move.volume_ratio}배</b>
            </>
          )}
        </li>
      </ul>
      <p className={styles["text"]}>{move.scope_text}</p>

      {move.disclosures.length > 0 ? (
        <>
          <p className={styles["sub-h"]}>📢 이 무렵 나온 공시</p>
          <ul className={styles["discs"]}>
            {move.disclosures.map((d) => (
              <li key={d.url}>
                <span className={styles["timing"]}>{d.timing}</span>
                <a href={d.url} target="_blank" rel="noreferrer">
                  [{d.category}] {d.title} ↗
                </a>
              </li>
            ))}
          </ul>
        </>
      ) : (
        <p className={styles["text"]}>📢 이날과 전 거래일에 눈에 띄는 공시는 없었어요. 아래 뉴스·리포트를 같이 보세요.</p>
      )}

      {move.trend && (
        <p className={styles["text"]}>
          👥 외국인 <b className={tone(move.trend.foreign)}>{qty(move.trend.foreign)}</b>주 · 기관{" "}
          <b className={tone(move.trend.organ)}>{qty(move.trend.organ)}</b>주 · 개인{" "}
          <b className={tone(move.trend.individual)}>{qty(move.trend.individual)}</b>주 — {move.trend_text}
        </p>
      )}
      <p className={styles["muted"]}>
        같은 날 있었던 일을 모은 것이지, 이것 때문이라고 단정할 수는 없어요. 큰 발표가 없는데 크게 움직였다면 소문이나
        수급(사고파는 힘)일 수도 있어요.
      </p>
    </div>
  );
}
