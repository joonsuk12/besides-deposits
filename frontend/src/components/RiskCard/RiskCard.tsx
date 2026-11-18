"use client";
// 위험 신호 카드: 초보가 놓치기 쉬운 함정을 신호등(🔴🟡🟢)으로. 문제가 있는 것부터, 문제 없는 항목도 보여준다.
// 항목을 누르면 왜 봐야 하는지와 근거(공시 원문 링크·연도별 숫자)가 펼쳐진다.
// 맨 아래 질문에 답하면 마이데이터(/mydata)에 그때 상황과 함께 저장된다.

import { useEffect, useState } from "react";

import { fetchMyRecords, fetchRisk, saveMyRecord, type MyRecord, type Risk, type RiskStatus } from "@/lib/api";
import styles from "./RiskCard.module.css";

const ICON: Record<RiskStatus, string> = { danger: "🔴", caution: "🟡", ok: "🟢" };
const KIND = "risk_reaction";
const QUESTION = "이 신호들을 보고 어떤 생각이 드나요?";
const ANSWERS = [
  { key: "fine", label: "괜찮아 보여요" },
  { key: "more", label: "더 알아볼래요" },
  { key: "worried", label: "걱정돼요" },
];

export default function RiskCard({ code }: { code: string }) {
  const [r, setR] = useState<Risk | null>(null);
  const [failed, setFailed] = useState(false);
  const [open, setOpen] = useState<string | null>(null);
  const [showOk, setShowOk] = useState(false);
  const [last, setLast] = useState<MyRecord | null>(null);
  const [picked, setPicked] = useState<string | null>(null);
  const [memo, setMemo] = useState("");
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    setR(null);
    setFailed(false);
    setOpen(null);
    setShowOk(false);
    setPicked(null);
    setMemo("");
    setSaved(false);
    setLast(null);
    fetchRisk(code).then(setR).catch(() => setFailed(true));
    fetchMyRecords(KIND, code, 1)
      .then((rows) => setLast(rows[0] ?? null))
      .catch(() => {});
  }, [code]);

  if (failed) return <p className={styles["muted"]}>위험 신호를 불러오지 못했습니다.</p>;
  if (!r) return <p className={styles["muted"]}>공시와 재무를 살펴보는 중…</p>;
  if (!r.available) return <p className={styles["muted"]}>{r.message}</p>;

  const problems = r.checks.filter((c) => c.status !== "ok");
  const oks = r.checks.filter((c) => c.status === "ok");
  const shown = showOk ? r.checks : problems;

  async function save() {
    const a = ANSWERS.find((x) => x.key === picked);
    if (!a || !r) return;
    setSaving(true);
    try {
      const rec = await saveMyRecord({
        kind: KIND,
        stock_code: code,
        question: QUESTION,
        answer: a.key,
        answer_label: a.label,
        memo,
        context: { counts: r.counts, flagged: problems.map((c) => c.key) },
      });
      setLast(rec);
      setSaved(true);
      setPicked(null);
      setMemo("");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div>
      <p className={styles["lead"]}>
        최근 1년 공시와 지난 실적에서 초보가 놓치기 쉬운 함정 {r.checks.length}가지를 살펴봤어요.{" "}
        <b className={styles["danger"]}>
          {ICON.danger} {r.counts.danger}
        </b>{" "}
        <b className={styles["caution"]}>
          {ICON.caution} {r.counts.caution}
        </b>{" "}
        <b className={styles["ok"]}>
          {ICON.ok} {r.counts.ok}
        </b>
      </p>
      {problems.length === 0 && !showOk && (
        <p className={styles["clean"]}>살펴본 항목에서 눈에 띄는 위험 신호가 없어요. 그래도 숫자가 전부는 아니에요.</p>
      )}

      <ul className={styles["list"]}>
        {shown.map((c) => (
          <li key={c.key} className={styles[c.status]}>
            <button className={styles["row"]} onClick={() => setOpen(open === c.key ? null : c.key)} aria-expanded={open === c.key}>
              <span className={styles["icon"]}>{ICON[c.status]}</span>
              <span className={styles["body"]}>
                <span className={styles["title"]}>{c.title}</span>
                <span className={styles["summary"]}>{c.summary}</span>
              </span>
              <span className={styles["chev"]}>{open === c.key ? "▲" : "▼"}</span>
            </button>
            {open === c.key && (
              <div className={styles["detail"]}>
                <p>💡 {c.why}</p>
                {c.evidence.length > 0 && (
                  <ul className={styles["evidence"]}>
                    {c.evidence.map((e, i) => (
                      <li key={i}>
                        {e.date && <span className={styles["date"]}>{e.date}</span>}
                        {e.url ? (
                          <a href={e.url} target="_blank" rel="noreferrer">
                            {e.text} ↗
                          </a>
                        ) : (
                          e.text
                        )}
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            )}
          </li>
        ))}
      </ul>
      {oks.length > 0 && (
        <button className={`ui-more ${styles["more"]}`} onClick={() => setShowOk(!showOk)}>
          {showOk ? "문제 없는 항목 접기" : `🟢 문제 없는 항목 ${oks.length}개도 보기`}
        </button>
      )}

      <div className={styles["ask"]}>
        <p className={styles["q"]}>📝 {QUESTION}</p>
        {last && (
          <p className={styles["muted"]}>
            {saved ? "저장했어요. " : ""}지난 답({last.created_at.slice(0, 10)}): <b>{last.answer_label}</b>
            {last.memo && ` — “${last.memo}”`}
          </p>
        )}
        <div className={styles["chips"]}>
          {ANSWERS.map((a) => (
            <button key={a.key} className={`ui-chip ${picked === a.key ? "on" : ""}`} onClick={() => setPicked(a.key)}>
              {a.label}
            </button>
          ))}
        </div>
        {picked && (
          <div className={styles["memo"]}>
            <input
              value={memo}
              maxLength={500}
              onChange={(e) => setMemo(e.target.value)}
              placeholder="한 줄 메모 (선택) — 예: 전환사채가 몇 번 더 나오는지 볼래요"
            />
            <button className="ui-btn" onClick={save} disabled={saving}>
              {saving ? "저장 중…" : "기록하기"}
            </button>
          </div>
        )}
        <p className={styles["muted"]}>답은 이 PC의 마이데이터에만 쌓여요. 나중에 내 생각과 실제 결과를 비교해 볼 수 있어요.</p>
      </div>
    </div>
  );
}
