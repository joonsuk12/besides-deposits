'use client'
// 시작 페이지. NewStocks의 랜딩 페이지 화면을 그대로 옮기고 문구만 이 서비스에 맞게 바꿨다.
import styles from './page.module.css'
import LandingView from '@/components/LandingView/LandingView'
import Footer from '@/components/Footer/Footer'
import graphimg from '@/assets/graphimg.png'
import Image from 'next/image';
import { HiArrowNarrowRight } from 'react-icons/hi';
import { goToStart } from '@/lib/api';

export default function Home() {
  return (
    <div className={styles.main}>
      <div>
        <div className={styles["landing-main-image"]}>
        <div className={styles["chart"]}>
          <Image
            src={graphimg}
            alt="stockimg"
            priority
          />
        </div>
        </div>
        <div className={styles["landing-main-container"]}>
          <div className={styles["title-animation"]}>
            <div className={styles["title-mini"]}>주식 초보를 위한 첫 나들이 🚶</div>
            <div className={styles["title-main"]}><span>주식초보나들이</span></div>
            <div className={styles["title"]}><span>차트</span> · <span>뉴스</span> · <span>리포트</span>를 쉽게</div>
          </div>
          <div className={styles["head-description"]}>
            <div>차트 위에 그날의 뉴스를, 어려운 증권사 리포트는 쉬운 요약으로</div>
            <div>처음이어도 천천히 둘러보세요</div>
          </div>
          <div className={styles["title-botton-box"]}>
            <div className={styles["Button-width"]}>
              <button onClick={goToStart} className={styles["button-box"]} style={{ color: "#4FE7B0", border: "2px solid #4FE7B0" }}>
                <div>시작하기</div>
                <HiArrowNarrowRight size="14"/>
              </button>
            </div>
          </div>
        </div>
      </div>

      <LandingView />

      <Footer />
    </div>
  )
}
