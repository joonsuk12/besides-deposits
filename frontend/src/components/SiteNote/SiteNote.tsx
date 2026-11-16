// 화면 맨 아래 안내: 투자 권유가 아니라는 점과 데이터 출처.
// 혼자 쓸 때도 기억해 두면 좋고, 나중에 서비스를 공개하면 꼭 있어야 하는 문구라 미리 한곳에 둔다.
import Link from "next/link";

import styles from "./SiteNote.module.css";

export default function SiteNote() {
  return (
    <footer className={styles["note"]}>
      <p>
        이 서비스의 요약·분류·꼬리표는 공개된 정보를 쉽게 읽도록 정리한 것이며, <b>특정 종목의 매수·매도를 권유하지 않습니다.</b>{" "}
        투자 판단과 책임은 본인에게 있습니다.
      </p>
      <p>
        데이터 출처: 주가 KRX(pykrx·FinanceDataReader) · 공시 금융감독원 OpenDART · 뉴스·증권사 리포트·기업 지표 네이버 증권 · 차트{" "}
        <a href="https://www.tradingview.com/" target="_blank" rel="noreferrer">
          TradingView Lightweight Charts
        </a>
        .
        원문은 각 출처에서 확인하세요. · <Link href="/guide">도움말</Link> · <Link href="/intro">서비스 소개</Link>
      </p>
    </footer>
  );
}
