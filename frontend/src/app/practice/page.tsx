"use client";
// 타임머신 연습장 (주소: /practice). 과거 어느 날로 돌아가 그날까지의 정보만 보고 6개월 뒤를 예상해 본다.
//   1) 문제: 차트(그날까지 2년) + 그때 알 수 있던 숫자(주가 흐름, PER·PBR, 연간 실적). 종목 이름은 기본으로 가린다
//   2) 답: 올랐다/비슷했다/내렸다 + 이유(여러 개) + 메모 → 서버가 결과를 계산하고 마이데이터에 저장
//   3) 결과: 차트를 6개월 뒤까지 이어서 보여주고, 시장 지수와 비교
//   4) 내 기록: 맞힌 비율, 이유별 정답률 (내 판단 습관 돌아보기)

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";

import StockChart, { type DayMarks } from "@/components/StockChart";
import {
  fetchPracticeHistory,
  fetchPracticeQuestion,
  submitPracticeAnswer,
  type PracticeAnswer,
  type PracticeHistory,
  type PracticeQuestion,
} from "@/lib/api";
import styles from "./practice.module.css";

const NO_MARKS: DayMarks = { newsDates: new Set(), reportDates: new Set(), disclosureDates: new Set() };
const pct = (n: number | null) => (n === null ? "-" : `${n > 0 ? "+" : ""}${n.toFixed(1)}%`);
const tone = (n: number | null) => (n === null ? "" : n > 0 ? "up" : n < 0 ? "down" : "");
// 억원 → "1.2조" / "3,450억"
const eok = (v: number | null) =>
  v === null ? "-" : Math.abs(v) >= 10000 ? `${(v / 10000).toFixed(1)}조` : `${v.toLocaleString("ko-KR")}억`;

export default function PracticePage() {
  const [q, setQ] = useState<PracticeQuestion | null>(null);
  const [failed, setFailed] = useState(false);
  const [showName, setShowName] = useState(false);
  const [guess, setGuess] = useState<string | null>(null);
  const [reasons, setReasons] = useState<string[]>([]);
  const [memo, setMemo] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState<PracticeAnswer | null>(null);
  const [history, setHistory] = useState<PracticeHistory | null>(null);

  const loadHistory = useCallback(() => {
    fetchPracticeHistory()
      .then(setHistory)
      .catch(() => {});
  }, []);

  const next = useCallback(() => {
    setQ(null);
    setFailed(false);
    setShowName(false);
    setGuess(null);
    setReasons([]);
    setMemo("");
    setResult(null);
    fetchPracticeQuestion()
      .then(setQ)
      .catch(() => setFailed(true));
  }, []);

  useEffect(() => {
    next();
    loadHistory();
  }, [next, loadHistory]);

  const marks = useMemo<DayMarks>(
    () => (result && q?.as_of ? { ...NO_MARKS, cutDate: q.as_of } : NO_MARKS),
    [result, q],
  );

  async function submit() {
    if (!q?.code || !q.as_of || !guess) return;
    setSubmitting(true);
    try {
      setResult(await submitPracticeAnswer({ code: q.code, as_of: q.as_of, guess, reasons, memo }));
      loadHistory();
    } finally {
      setSubmitting(false);
    }
  }

  const toggleReason = (key: string) =>
    setReasons((rs) => (rs.includes(key) ? rs.filter((r) => r !== key) : [...rs, key]));

  const label = result || showName ? (result?.name ?? q?.name) : "이름을 가린 종목";

  return (
    <div className={styles["page"]}>
      <h1>⏳ 타임머신 연습장</h1>
      <p className={styles["lead"]}>
        과거 어느 날로 돌아가, <b>그날까지 알 수 있던 정보만</b> 보고 6개월 뒤를 예상해 보는 연습이에요. 돈을 걸지 않는
        기출문제라 틀려도 괜찮아요. 답은 마이데이터에 쌓여서 내 판단 습관을 돌아볼 수 있어요.
      </p>

      {failed && (
        <p className={styles["muted"]}>문제를 불러오지 못했습니다. 백엔드(8100번 포트)가 켜져 있는지 확인해 주세요.</p>
      )}
      {!q && !failed && <p className={styles["muted"]}>문제를 고르는 중…</p>}
      {q && !q.available && <p className={styles["muted"]}>{q.message}</p>}

      {q?.available && (
        <div className={styles["layout"]}>
          <section className={styles["main"]}>
            <div className={styles["qhead"]}>
              <div>
                <span className={styles["date"]}>📅 {q.as_of}</span>
                <b className={styles["name"]}>{label}</b>
                <span className={styles["sub"]}>
                  {q.market}
                  {q.industry && ` · ${q.industry}`}
                </span>
              </div>
              {!result && (
                <button className="ui-btn-ghost" onClick={() => setShowName(!showName)}>
                  {showName ? "이름 가리기" : "이름 보기"}
                </button>
              )}
            </div>
            {!result && !showName && (
              <p className={styles["muted"]}>
                이름을 알면 &quot;그 뒤에 어떻게 됐는지&quot; 기억이 섞일 수 있어서 가려 뒀어요.
              </p>
            )}

            <div className={styles["chart"]}>
              <StockChart
                key={result ? "after" : "before"}
                prices={result ? result.prices : q.prices}
                marks={marks}
                rangeDays={result ? 1095 : 730}
                onSelectDate={() => {}}
              />
            </div>
            {result && (
              <p className={styles["muted"]}>
                민트색 &quot;여기까지 봤어요&quot; 표시가 문제 날짜예요. 그 오른쪽이 그 뒤 6개월({result.end_date}
                까지)이에요.
              </p>
            )}

            <div className={styles["facts"]}>
              <div>
                <h3>📈 주가 흐름 (그날 기준)</h3>
                <dl>
                  {q.price_facts.map((f) => (
                    <div key={f.label} title={f.hint ?? undefined}>
                      <dt>
                        {f.label}
                        {f.hint && <span className={styles["q"]}>?</span>}
                      </dt>
                      <dd className={f.tone}>{f.value}</dd>
                    </div>
                  ))}
                </dl>
              </div>
              <div>
                <h3>💰 그때 알 수 있던 실적</h3>
                {q.value_facts.length === 0 && q.years.length === 0 && (
                  <p className={styles["muted"]}>이 종목은 그 시점 실적 정보가 없어요. 차트만 보고 판단해 보세요.</p>
                )}
                <dl>
                  {q.value_facts.map((f) => (
                    <div key={f.label} title={f.hint ?? undefined}>
                      <dt>
                        {f.label}
                        {f.hint && <span className={styles["q"]}>?</span>}
                      </dt>
                      <dd className={f.tone}>{f.value}</dd>
                    </div>
                  ))}
                </dl>
                {q.years.length > 0 && (
                  <table className={styles["years"]}>
                    <thead>
                      <tr>
                        <th />
                        {q.years.map((y) => (
                          <th key={y.year}>{y.year}년</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {(
                        [
                          ["매출", "revenue"],
                          ["영업이익", "operating_profit"],
                          ["순이익", "net_income"],
                        ] as const
                      ).map(([name, key]) => (
                        <tr key={key}>
                          <td>{name}</td>
                          {q.years.map((y) => (
                            <td key={y.year} className={y[key] !== null && y[key]! < 0 ? "down" : ""}>
                              {eok(y[key])}
                            </td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}
                <p className={styles["muted"]}>
                  사업보고서는 보통 다음 해 3월 말에 나와서, 그날 이미 나와 있던 해까지만 보여줘요.
                </p>
              </div>
            </div>
          </section>

          <aside className={styles["side"]}>
            {!result ? (
              <section className="ui-card">
                <h2>🤔 6개월 뒤 이 종목은?</h2>
                <div className={styles["guesses"]}>
                  {q.guesses.map((g) => (
                    <button
                      key={g.key}
                      className={`ui-chip ${guess === g.key ? "on" : ""}`}
                      onClick={() => setGuess(g.key)}
                    >
                      {g.label}
                    </button>
                  ))}
                </div>
                <h3>왜 그렇게 생각했나요? (여러 개 골라도 돼요)</h3>
                <div className={styles["reasons"]}>
                  {q.reasons.map((r) => (
                    <button
                      key={r.key}
                      className={`ui-chip ${reasons.includes(r.key) ? "on" : ""}`}
                      onClick={() => toggleReason(r.key)}
                    >
                      {r.label}
                    </button>
                  ))}
                </div>
                <input
                  className={styles["memo"]}
                  value={memo}
                  maxLength={500}
                  onChange={(e) => setMemo(e.target.value)}
                  placeholder="한 줄 메모 (선택) — 예: 이익이 줄고 있는데 PER이 높아 보여요"
                />
                <button className="ui-btn" disabled={!guess || submitting} onClick={submit}>
                  {submitting ? "결과 계산 중…" : guess ? "정답 확인하기" : "먼저 예상을 골라 주세요"}
                </button>
              </section>
            ) : (
              <section className={`ui-card ${styles["result"]}`}>
                <h2>{result.correct ? "🎯 맞았어요!" : "🙈 이번엔 달랐어요"}</h2>
                <p className={styles["big"]}>
                  <b className={tone(result.return_pct)}>{pct(result.return_pct)}</b>
                  <span className={styles["sub"]}>
                    {" "}
                    6개월 뒤 ({result.as_of} → {result.end_date})
                  </span>
                </p>
                <ul className={styles["rlist"]}>
                  <li>
                    내 예상: <b>{result.guess_label}</b> · 실제: <b>{result.outcome_label}</b>
                  </li>
                  <li>
                    같은 기간 {result.index_name}:{" "}
                    <b className={tone(result.index_return_pct)}>{pct(result.index_return_pct)}</b>
                  </li>
                  <li>
                    중간에 가장 높았을 때 <b className="up">{pct(result.max_up_pct)}</b>, 가장 낮았을 때{" "}
                    <b className="down">{pct(result.max_down_pct)}</b>
                  </li>
                </ul>
                <p className={styles["comment"]}>{result.comment}</p>
                <div className={styles["actions"]}>
                  <button className="ui-btn" onClick={next}>
                    다음 문제
                  </button>
                  {q.code && (
                    <Link className="ui-btn-ghost" href={`/${q.code}`}>
                      이 종목 지금 차트 보기
                    </Link>
                  )}
                </div>
              </section>
            )}

            <section className="ui-card">
              <h2>📒 내 기록</h2>
              {!history || history.total === 0 ? (
                <p className={styles["muted"]}>아직 푼 문제가 없어요. 첫 문제를 풀어 보세요.</p>
              ) : (
                <>
                  <p className={styles["score"]}>
                    {history.total}문제 중 <b>{history.correct}문제</b> 맞힘 (
                    {Math.round((history.correct / history.total) * 100)}%)
                  </p>
                  {history.by_reason.length > 0 && (
                    <>
                      <h3>이유별로 보면</h3>
                      <ul className={styles["stats"]}>
                        {history.by_reason.map((s) => (
                          <li key={s.key}>
                            <span>{s.label}</span>
                            <b>
                              {s.correct}/{s.total}
                            </b>
                          </li>
                        ))}
                      </ul>
                      <p className={styles["muted"]}>
                        어떤 이유로 판단했을 때 잘 맞았는지 보여줘요. 문제가 쌓일수록 내 판단 습관이 보여요.
                      </p>
                    </>
                  )}
                  <h3>최근 푼 문제</h3>
                  <ul className={styles["recent"]}>
                    {history.items.slice(0, 5).map((h) => (
                      <li key={h.created_at}>
                        <span>{h.correct ? "🎯" : "🙈"}</span>
                        <span className={styles["rname"]}>
                          {h.name} <span className={styles["sub"]}>{h.as_of}</span>
                        </span>
                        <b className={tone(h.return_pct)}>{pct(h.return_pct)}</b>
                      </li>
                    ))}
                  </ul>
                </>
              )}
            </section>
          </aside>
        </div>
      )}
    </div>
  );
}
