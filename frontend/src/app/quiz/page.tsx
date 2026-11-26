"use client";
// 오늘의 퀴즈 (주소: /quiz). 내 관심종목의 실제 공시·지표·리포트로 "읽는 법"을 묻는 정답 있는 문제를 하루 3개.
// 주가 방향을 맞히는 문제는 내지 않는다 (2026-11-25 타임머신 평가: 운에 가깝다). 타임머신은 "그때 사실 읽기" 유형으로 들어왔다.
// 답하면 바로 정답·해설이 나오고, 기록은 마이데이터에 쌓여 연속 학습일·유형별 정답률로 보인다.

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import {
  fetchQuizExtra,
  fetchQuizStats,
  fetchQuizToday,
  submitQuizAnswer,
  type QuizQuestion,
  type QuizStats,
} from "@/lib/api";
import styles from "./quiz.module.css";

function QuestionCard({
  q,
  index,
  onAnswered,
}: {
  q: QuizQuestion;
  index: number;
  onAnswered: (qid: string, q: QuizQuestion) => void;
}) {
  const [sending, setSending] = useState(false);
  const r = q.result;

  async function pick(key: string) {
    if (r || sending) return;
    setSending(true);
    try {
      const result = await submitQuizAnswer(q.qid, key);
      onAnswered(q.qid, { ...q, result });
    } finally {
      setSending(false);
    }
  }

  return (
    <section className={`ui-card ${styles["card"]}`}>
      <div className={styles["head"]}>
        <span className={styles["num"]}>Q{index + 1}</span>
        <span className={styles["type"]}>{q.type_label}</span>
        <Link href={`/${q.stock_code}`} className={styles["stock"]}>
          {q.stock_name}
        </Link>
      </div>
      <p className={styles["prompt"]}>{q.prompt}</p>
      {q.context.length > 0 && (
        <ul className={styles["context"]}>
          {q.context.map((c) => (
            <li key={c}>{c}</li>
          ))}
        </ul>
      )}
      <div className={styles["options"]}>
        {q.options.map((o) => {
          const state = !r ? "" : o.key === r.correct_key ? "right" : o.key === r.chosen_key ? "wrong" : "dim";
          return (
            <button
              key={o.key}
              className={`${styles["option"]} ${state ? styles[state] : ""}`}
              onClick={() => pick(o.key)}
              disabled={!!r || sending}
            >
              {state === "right" && "✅ "}
              {state === "wrong" && "❌ "}
              {o.label}
            </button>
          );
        })}
      </div>
      {r && (
        <div className={`${styles["result"]} ${r.correct ? styles["ok"] : styles["ng"]}`}>
          <b>{r.correct ? "🎯 맞았어요!" : `🙈 정답은 "${r.correct_label}"`}</b>
          <p>{r.explanation}</p>
          {r.checks.length > 0 && (
            <>
              <p className={styles["sub-h"]}>더 확인해 볼 것</p>
              <ul>
                {r.checks.map((c) => (
                  <li key={c}>{c}</li>
                ))}
              </ul>
            </>
          )}
          {r.note && <p className={styles["note"]}>💡 {r.note}</p>}
          {r.link && (
            <a href={r.link} target="_blank" rel="noreferrer" className={styles["link"]}>
              공시 원문 보기 ↗
            </a>
          )}
        </div>
      )}
    </section>
  );
}

export default function QuizPage() {
  const [questions, setQuestions] = useState<QuizQuestion[] | null>(null);
  const [stats, setStats] = useState<QuizStats | null>(null);
  const [failed, setFailed] = useState(false);
  const [loadingExtra, setLoadingExtra] = useState(false);
  const [noMore, setNoMore] = useState(false);

  const loadStats = useCallback(() => {
    fetchQuizStats()
      .then(setStats)
      .catch(() => {});
  }, []);

  useEffect(() => {
    fetchQuizToday()
      .then((t) => setQuestions(t.questions))
      .catch(() => setFailed(true));
    loadStats();
  }, [loadStats]);

  const onAnswered = (qid: string, updated: QuizQuestion) => {
    setQuestions((qs) => (qs ?? []).map((q) => (q.qid === qid ? updated : q)));
    loadStats();
  };

  async function more() {
    if (!questions) return;
    setLoadingExtra(true);
    try {
      const q = await fetchQuizExtra(questions.map((x) => x.qid));
      if (q) setQuestions([...questions, q]);
      else setNoMore(true);
    } finally {
      setLoadingExtra(false);
    }
  }

  const done = questions?.filter((q) => q.result).length ?? 0;
  const allDone = !!questions && questions.length > 0 && done === questions.length;

  return (
    <div className={styles["page"]}>
      <h1>📚 오늘의 퀴즈</h1>
      <p className={styles["lead"]}>
        내 관심종목에서 실제로 나온 공시·지표·리포트로 <b>읽는 법</b>을 연습해요. 주가가 오를지 맞히는 게 아니라, 정답이
        있는 문제라 풀수록 실력이 쌓여요.
      </p>

      {stats && (
        <div className={styles["strip"]}>
          <span>
            🔥 <b>{stats.streak}일</b> 연속
          </span>
          <span>
            오늘{" "}
            <b>
              {done}/{questions?.length ?? 3}
            </b>
          </span>
          <span>
            전체 <b>{stats.total ? Math.round((stats.correct / stats.total) * 100) : 0}%</b> ({stats.correct}/
            {stats.total})
          </span>
          <Link href="/mydata" className={styles["more-link"]}>
            내 기록 →
          </Link>
        </div>
      )}

      {failed && (
        <p className={styles["muted"]}>문제를 불러오지 못했습니다. 백엔드(8100번 포트)가 켜져 있는지 확인해 주세요.</p>
      )}
      {!questions && !failed && <p className={styles["muted"]}>오늘의 문제를 고르는 중…</p>}
      {questions && questions.length === 0 && (
        <p className={styles["muted"]}>
          문제를 만들 재료가 없어요. 관심종목(★)을 추가하면 그 종목의 공시·지표로 문제가 나와요.
        </p>
      )}

      <div className={styles["list"]}>
        {questions?.map((q, i) => (
          <QuestionCard key={q.qid} q={q} index={i} onAnswered={onAnswered} />
        ))}
      </div>

      {allDone && (
        <div className={styles["done"]}>
          <b>오늘 문제를 다 풀었어요 🎉</b>
          {!noMore ? (
            <button className="ui-btn" onClick={more} disabled={loadingExtra}>
              {loadingExtra ? "문제 고르는 중…" : "한 문제 더 풀기"}
            </button>
          ) : (
            <span className={styles["muted"]}>지금 만들 수 있는 문제를 다 풀었어요. 내일 새 문제가 나와요.</span>
          )}
        </div>
      )}

      {stats && stats.recent_wrong.length > 0 && (
        <section className={`ui-card ${styles["review"]}`}>
          <h2>🔁 다시 볼 것 (최근 틀린 문제)</h2>
          <ul>
            {stats.recent_wrong.map((w) => (
              <li key={w.created_at}>
                <span className={styles["type"]}>{w.type_label}</span> {w.prompt}
                <span className={styles["answer"]}>정답: {w.correct_label}</span>
              </li>
            ))}
          </ul>
        </section>
      )}
    </div>
  );
}
