// 종목 로고 + 이름 + 코드. NewStocks의 StockProfile을 옮긴 것.
import styles from "./StockProfile.module.css";
import { stockLogoUrl } from "@/lib/api";

interface Props {
  stockName: string;
  stockId: string;
  stockMarket?: string;
  size?: "middle" | "small";
}

export default function StockProfile({ stockName, stockId, stockMarket, size = "middle" }: Props) {
  const styleBySize = {
    middle: ["stock-img-box-mid", "stock-name-mid", "stock-info-mid"],
    small: ["stock-img-box-small", "stock-name-small", "stock-info-small"],
  };

  return (
    <div className={styles["stock-profile-wrapper"]}>
      <div className={`${styles["stock-img-box"]} ${styles[styleBySize[size][0]]}`}>
        {/* 로고가 없는 종목은 이미지를 숨겨 회색 원만 남긴다 */}
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          src={stockLogoUrl(stockId)}
          alt=""
          className={styles["stock-img"]}
          onError={(e) => (e.currentTarget.style.display = "none")}
        />
      </div>
      <div className={styles["stock-info-wrapper"]}>
        <div className={styles[styleBySize[size][1]]}>{stockName}</div>
        <div className={styles[styleBySize[size][2]]}>
          {stockMarket ? `${stockMarket} ${stockId}` : stockId}
        </div>
      </div>
    </div>
  );
}
