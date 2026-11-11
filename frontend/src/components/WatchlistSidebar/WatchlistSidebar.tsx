"use client";
// 차트 화면 왼쪽의 관심 종목 목록. NewStocks의 LikeStockTab을 옮긴 것 (로그인 없이 동작).

import { useRouter } from "next/navigation";
import { BiXCircle } from "react-icons/bi";

import StockProfile from "@/components/StockProfile/StockProfile";
import type { WatchlistItem } from "@/lib/api";
import styles from "./WatchlistSidebar.module.css";

type Props = {
  items: WatchlistItem[];
  currentCode: string;
  onRemove: (code: string) => void;
};

export default function WatchlistSidebar({ items, currentCode, onRemove }: Props) {
  const router = useRouter();

  return (
    <div className={styles["container"]}>
      <div className={styles["like-title"]}>관심 종목</div>
      <div className={styles["like-hint"]}>차트 위 ☆를 눌러 추가</div>
      <div className={styles["like-content"]}>
        {items.map((s) => (
          <div
            key={s.code}
            className={`${styles["like-content-stock"]} ${s.code === currentCode ? styles["active"] : ""}`}
            onClick={() => router.push(`/${s.code}`)}
          >
            <StockProfile stockName={s.name} stockId={s.code} size="small" />
            <div className={styles["right"]}>
              {s.change_pct !== null && (
                <span className={s.change_pct > 0 ? "up" : s.change_pct < 0 ? "down" : ""}>
                  {s.change_pct > 0 ? "+" : ""}
                  {s.change_pct.toFixed(2)}%
                </span>
              )}
              <BiXCircle
                size="16"
                className={styles["delete-button"]}
                onClick={(e) => {
                  e.stopPropagation();
                  onRemove(s.code);
                }}
              />
            </div>
          </div>
        ))}
        {items.length === 0 && <div className={styles["empty"]}>아직 관심 종목이 없습니다.</div>}
      </div>
    </div>
  );
}
