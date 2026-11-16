import { BRAND } from "@/lib/brand";
import styles from './footer.module.css'
import Logoimg from '@/assets/logo.png'
import Image from 'next/image';

export default function Footer() {
  return (
    <div className={styles["footer-container"]}>
      <div className={styles["LOGO"]}>
      <Image
            className={styles["header-logo"]}
            src={Logoimg}
            alt="Logoimg"
          />
        {/* <p>
          <svg width="30" height="28" viewBox="0 0 32 32" xmlns="http://www.w3.org/2000/svg">
            <g fill="none" fillRule="evenodd">
              <path
                d="M10 0h12a10 10 0 0110 10v12a10 10 0 01-10 10H10A10 10 0 010 22V10A10 10 0 0110 0z"
                fill="#FFF"
              />
              <path
                d="M5.3 10.6l10.4 6v11.1l-10.4-6v-11zm11.4-6.2l9.7 5.5-9.7 5.6V4.4z"
                fill="#555AB9"
              />
              <path
                d="M27.2 10.6v11.2l-10.5 6V16.5l10.5-6zM15.7 4.4v11L6 10l9.7-5.5z"
                fill="#91BAF8"
              />
            </g>
          </svg>
        </p> */}
        <div className={styles["logo-title"]}>
          <div id={styles["main-title"]}>{BRAND.ko}</div>
          <div id={styles["sub-title"]}>{BRAND.en}</div>
        </div>
      </div>
      <div className={styles["footer-content"]}>
        <div id={styles["footer-content-text"]}>개인용 서비스 · 화면 원작: NEWStocks (2023 SSAFY A210 OH GOOD 팀)</div>
        <div>투자 판단의 책임은 본인에게 있습니다. 이 서비스는 매수·매도를 권유하지 않습니다.</div>
      </div>
    </div>
  )
}