"use client";
// 검색 자동완성 목록. NewStocks의 AutocompleteBox를 옮긴 것.

import { forwardRef } from "react";
import StockProfile from "@/components/StockProfile/StockProfile";
import styles from "./AutocompleteBox.module.css";
import type { Stock } from "@/lib/api";

interface Props {
  stockSearchList: Stock[];
  selectedItem: number | null;
  handleItemClick: (idx: number) => void;
  handleItemHover: (idx: number) => void;
}

const AutocompleteBox = forwardRef<HTMLDivElement, Props>(
  ({ stockSearchList, selectedItem, handleItemHover, handleItemClick }, ref) => {
    return (
      <div className={styles["container"]}>
        <div className={styles["scroll-container"]}>
          {stockSearchList.map(({ name, code, market }, idx) => (
            <div
              key={code}
              ref={idx === selectedItem ? ref : null}
              className={`${styles["stock-item-box"]} ${
                idx === selectedItem ? styles["stock-item-box-selected"] : ""
              }`}
              onMouseEnter={() => handleItemHover(idx)}
              onClick={() => handleItemClick(idx)}
            >
              <StockProfile stockName={name} stockId={code} stockMarket={market} size="small" />
            </div>
          ))}
        </div>
      </div>
    );
  },
);

AutocompleteBox.displayName = "AutocompleteBox";

export default AutocompleteBox;
