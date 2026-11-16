"use client";
// 상단 바: 로고(→ 홈), 종목 검색, 메뉴(차트 / 오늘의 리포트 / 관심종목 / 도움말). NewStocks의 Header를 옮긴 것.
// 메뉴는 아이콘만 있으면 뜻을 알기 어려워 글자를 붙였다. 좁은 화면에서는 글자를 숨기고 아이콘만 남긴다.
// 지금 있는 화면의 메뉴는 민트색으로 표시한다.

import { BRAND } from "@/lib/brand";
import Image from "next/image";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { BiBarChartAlt2 } from "react-icons/bi";
import { FaRegStar } from "react-icons/fa";
import { HiOutlineDocumentText, HiOutlineQuestionMarkCircle } from "react-icons/hi";

import Logoimg from "@/assets/logo.png";
import { goToStart, type Stock } from "@/lib/api";
import SearchBox from "../SearchBox/SearchBox";
import styles from "./Header.module.css";

export default function Header() {
  const router = useRouter();
  const pathname = usePathname();
  const handleSearch = (stock: Stock) => router.push(`/${stock.code}`);

  // 종목 화면 주소는 /005930 같은 6자리 코드
  const onChart = /^\/[0-9A-Z]{6}$/.test(pathname);
  const on = (active: boolean) => `${styles["nav-item"]} ${active ? styles["active"] : ""}`;

  return (
    <header className={styles["header"]}>
      <Link href="/" className={styles["brand"]}>
        <Image className={styles["logo"]} src={Logoimg} alt="" />
        <span className={styles["name"]}>{BRAND.ko}</span>
      </Link>

      <div className={styles["search"]}>
        <SearchBox searchFunc={handleSearch} />
      </div>

      <nav className={styles["nav"]} aria-label="메뉴">
        <button className={on(onChart)} onClick={goToStart} aria-label="차트">
          <BiBarChartAlt2 size={20} aria-hidden />
          <span>차트</span>
        </button>
        <Link className={on(pathname === "/reports")} href="/reports" aria-label="오늘의 리포트">
          <HiOutlineDocumentText size={20} aria-hidden />
          <span>오늘의 리포트</span>
        </Link>
        <Link className={on(pathname === "/watchlist")} href="/watchlist" aria-label="내 관심종목">
          <FaRegStar size={18} aria-hidden />
          <span>관심종목</span>
        </Link>
        <Link className={on(pathname === "/guide")} href="/guide" aria-label="도움말">
          <HiOutlineQuestionMarkCircle size={20} aria-hidden />
          <span>도움말</span>
        </Link>
      </nav>
    </header>
  );
}
