"use client";
// 공시 목록. 공시마다 좋은 소식/나쁜 소식 꼬리표, 분류, 쉬운 설명 한 줄을 보여준다.
// 리포트 카드처럼 "자세히"(왜 그렇게 보는지 + 원문에서 확인할 것)와 "원문 ↗"이 있다.
// 순서는 최신순 그대로. 좋은 소식 / 나쁜 소식 / 내용 확인 필터로 골라 볼 수 있다.
// limit: 앞의 몇 개만 보여주고 나머지는 "더 보기"로 펼친다.

import { useState } from "react";

import type { Disclosure } from "@/lib/api";
import ToneFilter, { type Tone } from "@/components/ToneFilter/ToneFilter";
import styles from "./DisclosureList.module.css";

// 공시 이름만 보고 붙이는 것이라 "보통"이라고 단서를 단다 (뉴스의 "추정"과 같은 뜻)
const TONE = {
  warn: { label: "⚠️ 나쁜 소식 (보통)", cls: "tone-bad" },
  good: { label: "👍 좋은 소식 (보통)", cls: "tone-good" },
  key: { label: "🔎 내용 확인", cls: "tone-key" },
  info: null,
};

// 필터용: 공시 등급 → 좋은/나쁜/내용 확인
const TONE_OF: Record<Disclosure["level"], Tone | null> = { good: "good", warn: "bad", key: "check", info: null };
const byDate = (a: Disclosure, b: Disclosure) => b.date.localeCompare(a.date) || b.rcept_no.localeCompare(a.rcept_no);

function Item({ d }: { d: Disclosure }) {
  const [open, setOpen] = useState(false);
  const tone = TONE[d.level];
  const hasDetail = !!d.why || d.checks.length > 0;

  return (
    <li className={`${styles["item"]} ${styles[`item-${d.level}`]}`}>
      <div className={styles["badges"]}>
        {tone && <span className={`${styles["tone"]} ${styles[tone.cls]}`}>{tone.label}</span>}
        <span className={`${styles["badge"]} ${styles[d.level]}`}>{d.category}</span>
        {d.is_correction && <span className={styles["sub"]}>정정</span>}
        {!d.by_company && <span className={styles["sub"]}>제출: {d.filer}</span>}
        <span className={styles["date"]}>{d.date}</span>
      </div>
      <p className={styles["title"]}>{d.title}</p>
      <p className={styles["explain"]}>{d.explain}</p>

      {open && (
        <div className={styles["detail"]}>
          {d.why && (
            <>
              <h4>왜 그렇게 보나요</h4>
              <p>{d.why}</p>
            </>
          )}
          {d.checks.length > 0 && (
            <>
              <h4>원문에서 확인할 것</h4>
              <ul>
                {d.checks.map((c) => (
                  <li key={c}>{c}</li>
                ))}
              </ul>
            </>
          )}
        </div>
      )}

      <div className={styles["actions"]}>
        {hasDetail && <button onClick={() => setOpen((v) => !v)}>{open ? "접기" : "자세히"}</button>}
        <a href={d.url} target="_blank" rel="noreferrer">
          원문 ↗
        </a>
      </div>
    </li>
  );
}

export default function DisclosureList({
  items,
  empty,
  limit,
  skipInfo = false,
}: {
  items: Disclosure[];
  empty?: string;
  limit?: number;
  skipInfo?: boolean; // 참고용(정기 보고서·지분 보고)은 아예 빼고 건수만 알려준다. 삼성전자는 1년에 3천 건 가까이 된다
}) {
  if (items.length === 0) return <p className={styles["empty"]}>{empty ?? "공시가 없습니다."}</p>;

  const kept = skipInfo ? items.filter((d) => d.level !== "info") : items;
  const skipped = items.length - kept.length;
  const sorted = [...kept].sort(byDate);
  const skipNote =
    skipped > 0 ? (
      <p className={styles["empty"]}>
        정기 보고서·임원 지분 보고 같은 참고용 공시 {skipped.toLocaleString("ko-KR")}건은 뺐어요.
      </p>
    ) : null;

  if (sorted.length === 0)
    return (
      <>
        <p className={styles["empty"]}>중요 공시는 없어요.</p>
        {skipNote}
      </>
    );

  return (
    <>
      <ToneFilter
        items={sorted}
        toneOf={(d) => TONE_OF[d.level]}
        // 필터는 건수가 많은 '최근 공시'에만. 하루치 목록은 몇 건뿐이라 버튼이 오히려 복잡하다
        labels={skipInfo ? { good: "👍 좋은 소식", bad: "⚠️ 나쁜 소식", check: "🔎 내용 확인" } : {}}
        limit={limit ?? sorted.length}
      >
        {(shown) =>
          shown.length === 0 ? (
            <p className={styles["empty"]}>해당하는 공시가 없어요.</p>
          ) : (
            <ul className={styles["list"]}>
              {shown.map((d) => (
                <Item key={d.rcept_no} d={d} />
              ))}
            </ul>
          )
        }
      </ToneFilter>
      {skipNote}
      {skipInfo && (
      <details className={styles["legend"]}>
        <summary>꼬리표 뜻</summary>
        <ul>
          <li>
            <b>👍 좋은 소식 (보통)</b>: 배당, 자사주 매입·소각, 큰 공급 계약처럼 주주에게 보통 좋게 받아들여지는 공시
          </li>
          <li>
            <b>⚠️ 나쁜 소식 (보통)</b>: 유상증자, 전환사채, 계약 해지, 소송·사고처럼 주가에 부담이 될 수 있는 공시
          </li>
          <li>
            <b>🔎 내용 확인</b>: 실적 발표, 합병·분할, 시설 투자처럼 큰 일이지만 좋을지 나쁠지는 숫자와 조건을 봐야
            아는 공시. &quot;자세히&quot;에 무엇을 확인할지 적어 뒀어요.
          </li>
          <li>&quot;보통&quot;은 공시 제목만 보고 붙였다는 뜻이에요. 실제 영향은 원문의 금액·조건에 따라 달라요.</li>
        </ul>
      </details>
      )}
    </>
  );
}
