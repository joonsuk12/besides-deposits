"use client";
// 내 기록 (주소: /mydata). 마이데이터를 가공해서 "내가 그때 이렇게 생각했고, 그 뒤 이렇게 됐다"를 보여준다.
//   1) 한 줄 돌아보기 (위험 신호 + 타임머신)
//   2) 위험 신호를 보고 남긴 생각 → 그 뒤 주가
//   3) 타임머신 연습: 예상별·이유별 정답률
//   4) 전체 기록 내보내기 (JSON)
// 좋고 나쁨을 판정하거나 매수·매도를 권하지 않는다.

import Link from "next/link";
import { useEffect, useState } from "react";

import {
  MYDATA_EXPORT_URL,
  fetchMyInsights,
  fetchPracticeHistory,
  type MyInsights,
  type PracticeHistory,
  type PracticeStat,
} from "@/lib/api";
import styles from "./mydata.module.css";

const pct = (n: number | null) => (n === null ? "-" : `${n > 0 ? "+" : ""}${n.toFixed(1)}%`);
const tone = (n: number | null) => (n === null ? "" : n > 0 ? "up" : n < 0 ? "down" : "");
const won = (n: number | null) => (n === null ? "-" : n.toLocaleString("ko-KR"));

function Rate({ items }: { items: PracticeStat[] }) {
  return (
    <ul className={styles["rates"]}>
      {items.map((s) => (
        <li key={s.key}>
          <span className={styles["rlabel"]}>{s.label}</span>
          <span className={styles["track"]}>
            <span className={styles["fill"]} style={{ width: `${(s.correct / s.total) * 100}%` }} />
          </span>
          <b>
            {s.correct}/{s.total}
          </b>
        </li>
      ))}
    </ul>
  );
}

export default function MyDataPage() {
  const [ins, setIns] = useState<MyInsights | null>(null);
  const [hist, setHist] = useState<PracticeHistory | null>(null);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    fetchMyInsights()
      .then(setIns)
      .catch(() => setFailed(true));
    fetchPracticeHistory()
      .then(setHist)
      .catch(() => setFailed(true));
  }, []);

  const lines = [...(ins?.lines ?? []), ...(hist?.lines ?? [])];
  const empty = ins && hist && ins.risk_items.length === 0 && hist.total === 0;

  return (
    <div className={styles["page"]}>
      <h1>📒 내 기록</h1>
      <p className={styles["lead"]}>
        화면에서 답한 생각들이 여기 모여요. 그때 내가 어떻게 생각했고 그 뒤 어떻게 됐는지 보면서, <b>내 판단 습관</b>을
        돌아보는 곳이에요. 맞고 틀림보다 &quot;왜 그렇게 생각했는지&quot;가 더 중요해요.
      </p>

      {failed && (
        <p className={styles["muted"]}>기록을 불러오지 못했습니다. 백엔드(8100번 포트)가 켜져 있는지 확인해 주세요.</p>
      )}
      {!failed && (!ins || !hist) && <p className={styles["muted"]}>불러오는 중…</p>}

      {empty && (
        <section className={`ui-card ${styles["empty"]}`}>
          <h2>아직 쌓인 기록이 없어요</h2>
          <p>두 군데서 기록이 쌓여요.</p>
          <ul>
            <li>
              종목 화면 오른쪽 <b>🚦 위험 신호 점검</b> 카드 아래 &quot;📝 내 생각 기록하기&quot;
            </li>
            <li>
              <Link href="/practice">⏳ 타임머신 연습장</Link>에서 문제 풀기
            </li>
          </ul>
        </section>
      )}

      {lines.length > 0 && (
        <section className={`ui-card ${styles["summary"]}`}>
          <h2>💡 한 줄 돌아보기</h2>
          <ul>
            {lines.map((l) => (
              <li key={l}>{l}</li>
            ))}
          </ul>
        </section>
      )}

      <div className={styles["grid"]}>
        {ins && ins.risk_items.length > 0 && (
          <section className="ui-card">
            <h2>🚦 위험 신호를 보고 남긴 생각</h2>
            {ins.risk_groups.length > 0 && (
              <div className={styles["groups"]}>
                {ins.risk_groups.map((g) => (
                  <div key={g.answer}>
                    <span>{g.label}</span>
                    <b className={tone(g.avg_change_pct)}>{pct(g.avg_change_pct)}</b>
                    <small>
                      {g.count}번{g.counted < g.count ? ` (일주일 지난 ${g.counted}개 평균)` : " 평균"}
                    </small>
                  </div>
                ))}
              </div>
            )}
            <ul className={styles["items"]}>
              {ins.risk_items.map((i) => (
                <li key={i.id}>
                  <div className={styles["row"]}>
                    <Link href={`/${i.stock_code}`} className={styles["name"]}>
                      {i.name}
                    </Link>
                    <span className={styles["badge"]}>{i.answer_label}</span>
                    <b className={tone(i.change_pct)}>{pct(i.change_pct)}</b>
                  </div>
                  <div className={styles["sub"]}>
                    {i.close_then_date} {won(i.close_then)}원 → {i.close_now_date} {won(i.close_now)}원
                    {i.days !== null && ` · ${i.days}일 지남`}
                  </div>
                  {i.flagged.length > 0 && <div className={styles["sub"]}>그때 신호: {i.flagged.join(", ")}</div>}
                  {i.memo && <div className={styles["memo"]}>“{i.memo}”</div>}
                </li>
              ))}
            </ul>
          </section>
        )}

        {hist && hist.total > 0 && (
          <section className="ui-card">
            <h2>⏳ 타임머신 연습</h2>
            <p className={styles["score"]}>
              {hist.total}문제 중 <b>{hist.correct}문제</b> 맞힘 ({Math.round((hist.correct / hist.total) * 100)}%)
            </p>
            <h3>예상별로</h3>
            <Rate items={hist.by_guess} />
            {hist.by_reason.length > 0 && (
              <>
                <h3>이유별로</h3>
                <Rate items={hist.by_reason} />
              </>
            )}
            <h3>최근 푼 문제</h3>
            <ul className={styles["recent"]}>
              {hist.items.slice(0, 8).map((h) => (
                <li key={h.created_at}>
                  <span>{h.correct ? "🎯" : "🙈"}</span>
                  <span className={styles["rname"]}>
                    {h.name} <small>{h.as_of}</small>
                  </span>
                  <span className={styles["sub"]}>
                    {h.guess_label.split(" ")[0]} → {h.outcome_label}
                  </span>
                  <b className={tone(h.return_pct)}>{pct(h.return_pct)}</b>
                </li>
              ))}
            </ul>
            <Link className="ui-btn" href="/practice">
              문제 더 풀기
            </Link>
          </section>
        )}
      </div>

      {ins && ins.total_records > 0 && (
        <p className={styles["muted"]}>
          기록 {ins.total_records}개는 이 PC의 DB에만 있어요.{" "}
          <a href={MYDATA_EXPORT_URL} target="_blank" rel="noreferrer">
            전체 기록 내보내기(JSON) ↗
          </a>
        </p>
      )}
    </div>
  );
}
