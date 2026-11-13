"use client";
// 공시 목록. 공시마다 초보용 분류(꼬리표 색)와 쉬운 설명 한 줄을 보여준다.
// hideInfo: 정기 보고서·지분 보고 같은 참고용(info)은 접어 두고 중요한 것만 먼저 보여준다.

import { useState } from "react";

import type { Disclosure } from "@/lib/api";
import styles from "./DisclosureList.module.css";

const LEVEL_LABEL = { warn: "확인 필요", good: "주주에게 좋은 쪽", key: "중요", info: "참고" };

export default function DisclosureList({
  items,
  empty,
  hideInfo = false,
}: {
  items: Disclosure[];
  empty?: string;
  hideInfo?: boolean;
}) {
  const [showAll, setShowAll] = useState(!hideInfo);
  const shown = showAll ? items : items.filter((d) => d.level !== "info");
  const hidden = items.length - shown.length;

  if (items.length === 0) return <p className={styles["empty"]}>{empty ?? "공시가 없습니다."}</p>;

  return (
    <div>
      <ul className={styles["list"]}>
        {shown.map((d) => (
          <li key={d.rcept_no} className={styles["item"]}>
            <div className={styles["badges"]}>
              <span className={`${styles["badge"]} ${styles[d.level]}`} title={LEVEL_LABEL[d.level]}>
                {d.category}
              </span>
              {d.is_correction && <span className={styles["sub"]}>정정</span>}
              {!d.by_company && <span className={styles["sub"]}>제출: {d.filer}</span>}
              <span className={styles["date"]}>{d.date}</span>
            </div>
            <a href={d.url} target="_blank" rel="noreferrer" className={styles["title"]}>
              {d.title}
            </a>
            <p className={styles["explain"]}>{d.explain}</p>
          </li>
        ))}
      </ul>
      {shown.length === 0 && <p className={styles["empty"]}>중요 공시는 없고, 참고용 공시만 있습니다.</p>}
      {hidden > 0 && (
        <button className={styles["more"]} onClick={() => setShowAll(true)}>
          참고용 공시 {hidden}건 더 보기 (정기 보고서, 지분 보고 등)
        </button>
      )}
    </div>
  );
}
