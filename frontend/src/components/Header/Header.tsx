"use client";
// 상단 바: 로고, 종목 검색, 메뉴(차트 / 내 관심종목). NewStocks의 Header를 옮긴 것.
// 커뮤니티·로그인 메뉴는 빠지고 그 자리에 "내 관심종목"이 들어갔다.

import SearchBox from "../SearchBox/SearchBox";

import styles from "./Header.module.css";
import Link from "next/link";
import Image from "next/image";
import { useRouter } from "next/navigation";

import { BiBarChartAlt2 } from "react-icons/bi";
import { FaRegStar } from "react-icons/fa";

import Logoimg from "@/assets/logo.png";
import { goToStart, type Stock } from "@/lib/api";

export default function Header() {
  const router = useRouter();

  const handleSearch = (stock: Stock) => router.push(`/${stock.code}`);

  return (
    <header>
      <div className={styles["header"]}>
        <div className={styles["header-left"]}>
          <Link href="/" className={styles["home-link"]}>
            <Image className={styles["header-logo"]} src={Logoimg} alt="로고" />
            <h1>주식초보나들이</h1>
          </Link>
        </div>

        <div className={styles["search-box-container"]}>
          <SearchBox searchFunc={handleSearch} />
        </div>

        <div className={styles["header-right"]}>
          <div className={styles["header-link"]} onClick={goToStart}>
            <BiBarChartAlt2 size="29" />
            <span className={styles["tooltip-chart"]}>차트</span>
          </div>
          <div className={styles["header-link"]}>
            <Link className={styles["community-link"]} href="/watchlist">
              <FaRegStar size="26" />
              <span className={styles["tooltip-community"]}>내 관심종목</span>
            </Link>
          </div>
        </div>
      </div>
    </header>
  );
}
