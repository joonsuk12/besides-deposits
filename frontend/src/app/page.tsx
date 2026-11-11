'use client'
// 시작 페이지. NewStocks의 랜딩 페이지를 그대로 옮긴 것 (서비스 이름만 바꿈).
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
            <div className={styles["title-mini"]}>100% 주식 오답노트 솔루션 📝</div>
            <div className={styles["title-main"]}><span>주식초보나들이</span></div>
            <div className={styles["title"]}><span>주식 뉴스</span> & <span>오답노트</span> 플랫폼</div>
          </div>
          <div className={styles["head-description"]}>
            <div>주식정보, 뉴스, 오답노트까지</div>
            <div>기존에 없던 서비스를 경험해보세요 </div>
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
