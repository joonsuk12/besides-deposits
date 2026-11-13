"use client";
// 공시 목록. 공시마다 초보용 분류(꼬리표 색)와 쉬운 설명 한 줄을 보여준다.
// limit: 중요한 순서(확인 필요 → 주주에게 좋은 쪽 → 중요 → 참고, 같으면 최신순)로 앞의 몇 개만 보여주고
//        나머지는 "더 보기"로 펼친다.

import type { Disclosure } from "@/lib/api";
import ShowMore from "@/components/ShowMore/ShowMore";
import styles from "./DisclosureList.module.css";

const LEVEL_LABEL = {
  warn: "확인 필요",
  good: "주주에게 좋은 쪽",
  key: "중요",
  info: "참고",
};
const LEVEL_RANK = { warn: 0, good: 1, key: 2, info: 3 };

export const byImportance = (a: Disclosure, b: Disclosure) =>
  LEVEL_RANK[a.level] - LEVEL_RANK[b.level] || b.date.localeCompare(a.date);

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
  if (items.length === 0)
    return <p className={styles["empty"]}>{empty ?? "공시가 없습니다."}</p>;

  const kept = skipInfo ? items.filter((d) => d.level !== "info") : items;
  const skipped = items.length - kept.length;
  const sorted = limit ? [...kept].sort(byImportance) : kept;
  const skipNote =
    skipped > 0 ? (
      <p className={styles["empty"]}>
        정기 보고서·임원 지분 보고 같은 참고용 공시{" "}
        {skipped.toLocaleString("ko-KR")}건은 뺐어요.
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
      <ShowMore items={sorted} limit={limit ?? sorted.length}>
        {(shown) => (
          <ul className={styles["list"]}>
            {shown.map((d) => (
              <li key={d.rcept_no} className={styles["item"]}>
                <div className={styles["badges"]}>
                  <span
                    className={`${styles["badge"]} ${styles[d.level]}`}
                    title={LEVEL_LABEL[d.level]}
                  >
                    {d.category}
                  </span>
                  {d.is_correction && (
                    <span className={styles["sub"]}>정정</span>
                  )}
                  {!d.by_company && (
                    <span className={styles["sub"]}>제출: {d.filer}</span>
                  )}
                  <span className={styles["date"]}>{d.date}</span>
                </div>
                <a
                  href={d.url}
                  target="_blank"
                  rel="noreferrer"
                  className={styles["title"]}
                >
                  {d.title}
                </a>
                <p className={styles["explain"]}>{d.explain}</p>
              </li>
            ))}
          </ul>
        )}
      </ShowMore>
      {skipNote}
    </>
  );
}
