"use client";
// 앞의 몇 개만 보여주고 나머지는 "더보기"로 펼친다.
// 초보에게 한 번에 너무 많은 정보를 보여주지 않으려고 뉴스·공시·리포트 목록에 같이 쓴다.
//   <ShowMore items={list} limit={3}>{(shown) => <NewsList items={shown} />}</ShowMore>

import { useState, type ReactNode } from "react";

import styles from "./ShowMore.module.css";

export default function ShowMore<T>({
  items,
  limit = 3,
  unit = "건",
  children,
}: {
  items: T[];
  limit?: number;
  unit?: string;
  children: (shown: T[]) => ReactNode;
}) {
  const [open, setOpen] = useState(false);
  const hidden = items.length - limit;
  const shown = open || hidden <= 0 ? items : items.slice(0, limit);

  return (
    <>
      {children(shown)}
      {hidden > 0 && (
        <button className={styles["more"]} onClick={() => setOpen((o) => !o)}>
          {open ? "접기 ▲" : `${hidden}${unit} 더 보기 ▼`}
        </button>
      )}
    </>
  );
}
